// PartnerFit API 중계 함수 (Vercel Serverless, Node).
// 브라우저가 보낸 AI 공급자 호출을 허용된 엔드포인트로만 전달한다.
// - 로그인(Firebase ID 토큰)한 사용자만 사용 가능
// - 사용자의 API 키는 요청 한 번 동안만 메모리에서 쓰고 저장·기록하지 않는다 (이 파일은 키를 로그에 남기지 않는다)
const FIREBASE_API_KEY = "AIzaSyCEyygWPB4SsFOHe6My8UqkbWFLvZ2szOY"; // 공개 웹 키(firebase-config.js와 동일)
const ALLOW = [
  { host: "api.openai.com", path: /^\/v1\/(models|responses(\/[A-Za-z0-9_-]+(\/cancel)?)?)$/, search: /^$/ },
  { host: "api.openai.com", path: /^\/v1\/models$/, search: /^(\?limit=\d{1,3})?$/ },
  { host: "api.anthropic.com", path: /^\/v1\/(models|messages)$/, search: /^(\?limit=\d{1,3})?$/ },
];
const MAX_BODY = 600 * 1024;
const UPSTREAM_TIMEOUT_MS = 280 * 1000;

function send(res, code, obj) {
  res.statusCode = code;
  res.setHeader("Content-Type", "application/json");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(obj));
}

async function readJson(req) {
  if (req.body && typeof req.body === "object") return req.body;
  const chunks = []; let size = 0;
  for await (const c of req) { size += c.length; if (size > MAX_BODY) throw new Error("too large"); chunks.push(c); }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

async function verifyIdToken(token) {
  if (!token) return null;
  const r = await fetch("https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=" + FIREBASE_API_KEY, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ idToken: token }),
  });
  if (!r.ok) return null;
  const j = await r.json().catch(() => null);
  return j && j.users && j.users[0] ? j.users[0].localId : null;
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") return send(res, 405, { relayError: "method not allowed" });
  const origin = req.headers.origin;
  if (origin) {
    let ok = false;
    try { ok = new URL(origin).host === req.headers.host; } catch (e) {}
    if (!ok) return send(res, 403, { relayError: "origin not allowed" });
  }
  let uid;
  try {
    const auth = req.headers.authorization || "";
    uid = await verifyIdToken(auth.startsWith("Bearer ") ? auth.slice(7) : "");
  } catch (e) { return send(res, 502, { relayError: "auth check failed" }); }
  if (!uid) return send(res, 401, { relayError: "login required" });

  let p;
  try { p = await readJson(req); } catch (e) { return send(res, 400, { relayError: "bad request" }); }
  let u;
  try { u = new URL(String(p.url)); } catch (e) { return send(res, 400, { relayError: "bad url" }); }
  const rule = u.protocol === "https:" && !u.username && !u.port && ALLOW.find(a => a.host === u.hostname && a.path.test(u.pathname) && a.search.test(u.search));
  if (!rule) return send(res, 403, { relayError: "target not allowed" });
  const method = p.method === "POST" ? "POST" : "GET";
  const key = typeof p.key === "string" ? p.key.trim() : "";
  if (!key || key.length > 400 || /[\r\n]/.test(key)) return send(res, 400, { relayError: "api key missing" });
  const body = method === "POST" ? String(p.body == null ? "" : p.body) : undefined;
  if (body && body.length > MAX_BODY) return send(res, 413, { relayError: "too large" });

  const headers = u.hostname === "api.openai.com"
    ? { Authorization: "Bearer " + key, "Content-Type": "application/json" }
    : { "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json" };

  // 긴 호출 동안 연결이 끊기지 않도록 공백을 보내고, 마지막에 JSON 한 덩어리를 보낸다.
  res.statusCode = 200;
  res.setHeader("Content-Type", "application/json");
  res.setHeader("Cache-Control", "no-store");
  const beat = setInterval(() => { try { res.write(" "); } catch (e) {} }, 10000);
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), UPSTREAM_TIMEOUT_MS);
  try {
    const r = await fetch(u.toString(), { method, headers, body, signal: ac.signal });
    const text = await r.text();
    res.end(JSON.stringify({ status: r.status, body: text }));
  } catch (e) {
    res.end(JSON.stringify({ relayError: e && e.name === "AbortError" ? "upstream timeout" : "upstream request failed" }));
  } finally { clearTimeout(timer); clearInterval(beat); }
};
