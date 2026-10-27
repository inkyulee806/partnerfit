# -*- coding: utf-8 -*-
"""한국어 index.html(원본)에서 en/zh/ja 페이지, hreflang, 언어 선택기, sitemap, 공유 이미지를 생성한다.
사용: python3 tools/build_i18n.py [--images]   (저장소 루트에서)
원본 문구를 고치면 tools/i18n_data.py의 한국어 키도 같이 고친 뒤 다시 실행한다."""
import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from i18n_data import P

BASE = "https://partnerfit-nine.vercel.app"
LANGS = [  # code, dir, hreflang, html lang, og:locale, inLanguage, native name
    ("ko", "",    "ko",    "ko",    "ko_KR", "ko",    "한국어"),
    ("en", "en/", "en",    "en",    "en_US", "en",    "English"),
    ("zh", "zh/", "zh-CN", "zh-CN", "zh_CN", "zh-CN", "中文"),
    ("ja", "ja/", "ja",    "ja",    "ja_JP", "ja",    "日本語"),
]
IDX = {"en": 1, "zh": 2, "ja": 3}

def switcher(cur):
    a = []
    for c, d, h, hl, _, _, n in LANGS:
        cur_attr = ' aria-current="page"' if c == cur else ""
        a.append(f'<a href="/{d}" hreflang="{h}" lang="{hl}"{cur_attr}>{n}</a>')
    return '<!--LANG--><nav class="lang" aria-label="Language">' + "".join(a) + '</nav><!--/LANG-->'

def hreflang_block():
    ls = [f'<link rel="alternate" hreflang="{h}" href="{BASE}/{d}">' for c, d, h, *_ in LANGS]
    ls.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}/">')
    return "<!--HREFLANG-->" + "\n".join(ls) + "<!--/HREFLANG-->"

def sub_block(s, tag, new):
    pat = re.compile(rf"<!--{tag}-->.*?<!--/{tag}-->", re.S)
    assert pat.search(s), f"marker {tag} missing"
    return pat.sub(lambda m: new, s)

src = open("index.html", encoding="utf-8").read()
src = sub_block(src, "LANG", switcher("ko"))
src = sub_block(src, "HREFLANG", hreflang_block())
open("index.html", "w", encoding="utf-8").write(src)

pairs = sorted(P, key=lambda t: -len(t[0]))
for ko, *_ in pairs:
    assert ko in src, f"원문에 없음: {ko[:40]}"

ALLOWED = ["파트너핏", "한국어"]
for code, d, h, hl, loc, inl, native in LANGS[1:]:
    s = src
    for t in pairs:
        s = s.replace(t[0], t[IDX[code]])
    def one(a, b):
        global s
        assert s.count(a) == 1, f"{code}: {a[:50]} x{s.count(a)}"
        s = s.replace(a, b)
    url = f"{BASE}/{d}"
    one('<html lang="ko">', f'<html lang="{hl}">')
    one(f'<link rel="canonical" href="{BASE}/">', f'<link rel="canonical" href="{url}">')
    one(f'<meta property="og:url" content="{BASE}/">', f'<meta property="og:url" content="{url}">')
    one('content="ko_KR"', f'content="{loc}"')
    one(f'"@id": "{BASE}/#webpage",\n      "url": "{BASE}/",', f'"@id": "{BASE}/#webpage",\n      "url": "{url}",')
    assert s.count('"inLanguage": "ko"') == 2
    s = s.replace('"inLanguage": "ko"', f'"inLanguage": "{inl}"')
    s = s.replace(f"{BASE}/og-image.png", f"{BASE}/og-image-{code}.png")
    one('src="report-example.png"', f'src="../report-example-{code}.png"')
    one('"./firebase-config.js"', '"../firebase-config.js"')
    s = sub_block(s, "LANG", switcher(code))
    left = s
    for a in ALLOWED: left = left.replace(a, "")
    h_left = re.findall(r"[가-힣]+", left)
    assert not h_left, f"{code}: 한글 잔존 {h_left[:5]}"
    os.makedirs(code, exist_ok=True)
    open(f"{code}/index.html", "w", encoding="utf-8").write(s)
    print("wrote", f"{code}/index.html")

# sitemap
lm = re.search(r'"dateModified": "(\d{4}-\d\d-\d\d)"', src).group(1)
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for c, d, *_ in LANGS:
    sm.append("  <url>")
    sm.append(f"    <loc>{BASE}/{d}</loc>")
    sm.append(f"    <lastmod>{lm}</lastmod>")
    for c2, d2, h2, *_ in LANGS:
        sm.append(f'    <xhtml:link rel="alternate" hreflang="{h2}" href="{BASE}/{d2}"/>')
    sm.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}/"/>')
    sm.append("  </url>")
sm.append("</urlset>")
open("sitemap.xml", "w", encoding="utf-8").write("\n".join(sm) + "\n")
print("wrote sitemap.xml")

if "--images" in sys.argv:
    from playwright.sync_api import sync_playwright
    OG = {  # brand, title, line1, line2
        "ko": ("PartnerFit(파트너핏)", "AI 해외 바이어·서플라이어 발굴", "출처가 달린 후보 · 점수 보고서 · 이메일 초안", "무료로 이용할 수 있습니다"),
        "en": ("PartnerFit", "AI Overseas Buyer & Supplier Discovery", "Sourced candidates · Scored report · Email drafts", "Free to use"),
        "zh": ("PartnerFit", "AI 海外买家与供应商开发", "附来源的候选 · 评分报告 · 邮件草稿", "可免费使用"),
        "ja": ("PartnerFit", "AIで海外のバイヤー・サプライヤーを発掘", "出典付きの候補 · スコア付きレポート · メール文案", "無料でご利用いただけます"),
    }
    RP = {  # title, meta, note, row labels, candidates
        "ko": dict(t="PartnerFit 보고서 (예시 · 가상 데이터)", m="조건: 바이어 · 체코 · 화장품 원료  /  후보 3곳 표시",
                   score="적합도", why="추천 근거", contact="공개 연락처", prio="우선순위",
                   rows=[("Alpha Beauty Distribution (가상)","체코 · 유통사",82,"취급 품목 일치 [1] · 유통 채널 확인 [2]","이메일 확인됨 [3] / 전화 확인 필요","높음"),
                         ("Beta Cosmetic Trade (가상)","독일 · 무역사",71,"유사 원료 거래 단서 [1] · 규모 정보 부족","이메일 확인 필요","보통"),
                         ("Gamma Ingredients (가상)","폴란드 · 수요기업",64,"사용 품목 일부 일치 [1] · 인증 확인 필요","양식 URL 확인됨 [2]","보통")],
                   note="※ 가상 데이터입니다. 실제 기업·점수가 아니며, [n]은 출처 링크 자리표시입니다."),
        "en": dict(t="PartnerFit report (example · fictional data)", m="Criteria: buyers · Czechia · cosmetic raw materials  /  3 candidates shown",
                   score="Fit score", why="Reasons", contact="Public contact", prio="Priority",
                   rows=[("Alpha Beauty Distribution (fictional)","Czechia · distributor",82,"Product match [1] · distribution channel verified [2]","Email verified [3] / phone needs verification","High"),
                         ("Beta Cosmetic Trade (fictional)","Germany · trading company",71,"Signs of similar ingredient trade [1] · size info lacking","Email needs verification","Medium"),
                         ("Gamma Ingredients (fictional)","Poland · end user",64,"Partial match on products used [1] · certification to verify","Contact form URL verified [2]","Medium")],
                   note="* Fictional data. These are not real companies or scores; [n] marks a source-link placeholder."),
        "zh": dict(t="PartnerFit 报告（示例 · 虚构数据）", m="条件：买家 · 捷克 · 化妆品原料  /  显示 3 家候选",
                   score="匹配度", why="推荐依据", contact="公开联系方式", prio="优先顺序",
                   rows=[("Alpha Beauty Distribution（虚构）","捷克 · 经销商",82,"经营品类一致 [1] · 流通渠道已确认 [2]","邮箱已确认 [3] / 电话需确认","高"),
                         ("Beta Cosmetic Trade（虚构）","德国 · 贸易商",71,"有类似原料交易线索 [1] · 规模信息不足","邮箱需确认","中"),
                         ("Gamma Ingredients（虚构）","波兰 · 需求企业",64,"使用品类部分一致 [1] · 认证需确认","表单链接已确认 [2]","中")],
                   note="※ 虚构数据。并非真实企业和评分；[n] 为来源链接占位符。"),
        "ja": dict(t="PartnerFit レポート（例 · 架空データ）", m="条件：バイヤー · チェコ · 化粧品原料  /  候補3社を表示",
                   score="適合度", why="推薦根拠", contact="公開連絡先", prio="優先順位",
                   rows=[("Alpha Beauty Distribution（架空）","チェコ · 流通企業",82,"取扱品目が一致 [1] · 流通経路を確認 [2]","メール確認済み [3] / 電話は要確認","高"),
                         ("Beta Cosmetic Trade（架空）","ドイツ · 貿易企業",71,"類似原料の取引の手がかり [1] · 規模情報が不足","メールは要確認","中"),
                         ("Gamma Ingredients（架空）","ポーランド · 需要企業",64,"使用品目が一部一致 [1] · 認証は要確認","フォームURL確認済み [2]","中")],
                   note="※ 架空のデータです。実在の企業・スコアではなく、[n] は出典リンクの位置を示す仮表記です。"),
    }
    with sync_playwright() as p:
        b = p.chromium.launch()
        for c, d, h, hl, *_ in LANGS:
            b_, t_, l1, l2 = OG[c]
            html = f"""<html lang="{hl}"><body style="margin:0;width:1200px;height:630px;background:#f4f6fa;font-family:'Noto Sans CJK KR','Noto Sans CJK SC','Noto Sans CJK JP',sans-serif;color:#1c2127;display:flex;flex-direction:column;justify-content:center;padding:0 90px;box-sizing:border-box"><div style="font-size:30px;color:#1e3a6e;font-weight:700">■ {b_}</div><div style="font-size:60px;font-weight:700;margin-top:28px;line-height:1.25">{t_}</div><div style="font-size:30px;color:#566170;margin-top:28px;line-height:1.5">{l1}<br>{l2}</div></body></html>"""
            pg = b.new_page(viewport={"width": 1200, "height": 630}); pg.set_content(html); pg.screenshot(path=f"og-image-{c}.png"); pg.close()
            r = RP[c]
            rows = "".join(f'<div style="background:#fff;border:1px solid #d9dfea;border-radius:8px;padding:18px 24px;margin-top:16px;display:grid;grid-template-columns:1fr auto;gap:8px 20px"><div><div style="font-size:25px;font-weight:700">{n}</div><div style="font-size:17px;color:#566170;margin-top:3px">{k}</div></div><div style="text-align:right"><div style="font-size:15px;color:#566170">{r["score"]}</div><div style="font-size:40px;font-weight:700;color:#1e3a6e;line-height:1.05">{sc}</div></div><div style="font-size:17px;line-height:1.55"><b style="color:#1e3a6e">{r["why"]}</b> {w}<br><b style="color:#1e3a6e">{r["contact"]}</b> {ct}</div><div style="text-align:right;align-self:end"><span style="background:#e8eef9;color:#1e3a6e;border-radius:4px;padding:4px 12px;font-size:16px;font-weight:600;white-space:nowrap">{r["prio"]}: {pr}</span></div></div>' for n,k,sc,w,ct,pr in r["rows"])
            html = f"""<html lang="{hl}"><body style="margin:0;width:1000px;height:720px;background:#f4f6fa;font-family:'Noto Sans CJK KR','Noto Sans CJK SC','Noto Sans CJK JP',sans-serif;color:#1c2127;padding:28px 36px;box-sizing:border-box"><div style="font-size:28px;color:#1e3a6e;font-weight:700">{r["t"]}</div><div style="font-size:17px;color:#566170;margin-top:6px">{r["m"]}</div>{rows}<div style="font-size:15px;color:#566170;margin-top:18px">{r["note"]}</div></body></html>"""
            pg = b.new_page(viewport={"width": 1000, "height": 720}); pg.set_content(html); pg.screenshot(path=f"report-example-{c}.png"); pg.close()
        b.close()
    print("wrote images")
