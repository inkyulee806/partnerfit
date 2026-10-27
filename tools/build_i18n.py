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
        "ko": ("PartnerFit(파트너핏)", "AI 해외 바이어·서플라이어 발굴", "후보 탐색 · 적합성 분석 보고서 · 맞춤형 이메일 초안", "무료로 이용할 수 있습니다"),
        "en": ("PartnerFit", "AI Overseas Buyer & Supplier Discovery", "Candidate search · Fit-analysis report · Tailored email drafts", "Free to use"),
        "zh": ("PartnerFit", "AI 海外买家与供应商开发", "候选搜寻 · 匹配度分析报告 · 定制邮件草稿", "可免费使用"),
        "ja": ("PartnerFit", "AIで海外のバイヤー・サプライヤーを発掘", "候補探索 · 適合性分析レポート · カスタマイズしたメール文案", "無料でご利用いただけます"),
    }
    RP = {  # header, 4x(title, desc), note
        "ko": ("PartnerFit 보고서 구성 (예시)", [("1 후보 기업 개요","기업명 · 국가 · 사업 역할 · 취급 제품"),("2 거래 적합성","입력 조건과의 적합 여부 · 추천 근거"),("3 접촉 정보와 우선순위","공개 접촉 정보 · 접근 우선순위"),("4 이메일 초안","판매 제안 · 구매 문의 · 견적 요청 (다국어)")], "※ 항목 구성만 보여 주는 예시이며 실제 기업명·수치는 포함하지 않습니다."),
        "en": ("PartnerFit report structure (example)", [("1 Candidate company overview","Company name · country · business role · products"),("2 Trade fit","Fit with your terms · reasons for recommendation"),("3 Contact info and priority","Public contact details · approach priority"),("4 Email drafts","Sales proposal · purchase inquiry · quotation request (multilingual)")], "* Example showing the item structure only; no real company names or figures are included."),
        "zh": ("PartnerFit 报告构成（示例）", [("1 候选企业概况","企业名称 · 国家 · 业务角色 · 经营产品"),("2 交易匹配度","与输入条件的匹配情况 · 推荐依据"),("3 联系信息与优先顺序","公开联系信息 · 接洽优先顺序"),("4 邮件草稿","销售提案 · 采购咨询 · 报价请求（多语言）")], "※ 仅为展示项目构成的示例，不包含真实的企业名称和数据。"),
        "ja": ("PartnerFit レポート構成（例）", [("1 候補企業の概要","企業名 · 国 · 事業上の役割 · 取扱製品"),("2 取引適合性","入力条件との適合 · 推薦根拠"),("3 連絡先情報と優先順位","公開連絡先 · アプローチの優先順位"),("4 メール文案","販売提案 · 購入問い合わせ · 見積依頼（多言語）")], "※ 項目構成のみを示す例であり、実際の企業名・数値は含まれません。"),
    }
    with sync_playwright() as p:
        b = p.chromium.launch()
        for c, d, h, hl, *_ in LANGS:
            b_, t_, l1, l2 = OG[c]
            html = f"""<html lang="{hl}"><body style="margin:0;width:1200px;height:630px;background:#f4f6fa;font-family:'Noto Sans CJK KR','Noto Sans CJK SC','Noto Sans CJK JP',sans-serif;color:#1c2127;display:flex;flex-direction:column;justify-content:center;padding:0 90px;box-sizing:border-box"><div style="font-size:30px;color:#1e3a6e;font-weight:700">■ {b_}</div><div style="font-size:60px;font-weight:700;margin-top:28px;line-height:1.25">{t_}</div><div style="font-size:30px;color:#566170;margin-top:28px;line-height:1.5">{l1}<br>{l2}</div></body></html>"""
            pg = b.new_page(viewport={"width": 1200, "height": 630}); pg.set_content(html); pg.screenshot(path=f"og-image-{c}.png"); pg.close()
            hd, cards, note = RP[c]
            cs = "".join(f'<div style="background:#fff;border:1px solid #ddd9cc;padding:22px;height:110px"><b style="font-size:24px">{a}</b><div style="font-size:19px;color:#566170;margin-top:10px">{bb}</div></div>' for a, bb in cards)
            html = f"""<html lang="{hl}"><body style="margin:0;width:1000px;height:520px;background:#f4f6fa;font-family:'Noto Sans CJK KR','Noto Sans CJK SC','Noto Sans CJK JP',sans-serif;color:#1c2127;padding:36px 44px;box-sizing:border-box"><div style="font-size:20px;color:#1e3a6e;font-weight:700">{hd}</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:22px">{cs}</div><div style="font-size:16px;color:#566170;margin-top:16px">{note}</div></body></html>"""
            pg = b.new_page(viewport={"width": 1000, "height": 520}); pg.set_content(html); pg.screenshot(path=f"report-example-{c}.png"); pg.close()
        b.close()
    print("wrote images")
