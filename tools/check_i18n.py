# -*- coding: utf-8 -*-
"""다국어 페이지 점검: python3 tools/check_i18n.py (저장소 루트)"""
import re, json, os, sys
from html.parser import HTMLParser
BASE="https://partnerfit-nine.vercel.app"
PAGES={"ko":("index.html","/",),"en":("en/index.html","/en/"),"zh":("zh/index.html","/zh/"),"ja":("ja/index.html","/ja/")}
fail=0
def ok(c,m,x=""):
    global fail
    print(("PASS " if c else "FAIL ")+m,x if not c else "")
    if not c: fail+=1
class Faq(HTMLParser):
    def __init__(s):
        super().__init__();s.q=[];s.a=[];s.mode=None;s.infaq=0;s.imgs=[]
    def handle_starttag(s,t,a):
        a=dict(a)
        if t=="div" and "faq-item" in (a.get("class") or ""): s.infaq=1
        if s.infaq and t=="h3": s.mode="q";s.q.append("")
        if s.infaq and t=="p": s.mode="a";s.a.append("")
        if t=="img": s.imgs.append(a)
    def handle_data(s,d):
        if s.mode=="q": s.q[-1]+=d
        elif s.mode=="a": s.a[-1]+=d
    def handle_endtag(s,t):
        if t in("h3","p"): s.mode=None
sm=open("sitemap.xml",encoding="utf-8").read()
for code,(f,path) in PAGES.items():
    h=open(f,encoding="utf-8").read()
    print("==",code)
    ok(re.search(r'<html lang="([^"]+)"',h).group(1)=={"ko":"ko","en":"en","zh":"zh-CN","ja":"ja"}[code],"html lang")
    ok(f'<link rel="canonical" href="{BASE}{path}">' in h,"canonical 자기 주소")
    ok(f'<meta property="og:url" content="{BASE}{path}">' in h,"og:url")
    ok(h.count('rel="alternate" hreflang=')==5,"hreflang 5개(ko,en,zh-CN,ja,x-default)")
    m=re.search(r'og:image" content="([^"]+)"',h).group(1); ok(os.path.exists(m.replace(BASE+"/","")),"og:image 파일",m)
    ld=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',h,re.S).group(1))
    faq=[x for x in ld["@graph"] if x["@type"]=="FAQPage"][0]["mainEntity"]
    p=Faq();p.feed(h)
    qs=[x["name"] for x in faq];as_=[x["acceptedAnswer"]["text"] for x in faq]
    ok(qs==[q.strip() for q in p.q] and as_==[a.strip() for a in p.a],"FAQ JSON-LD = 화면",(len(qs),len(p.q)))
    ok(all(i.get("alt") for i in p.imgs) and len(p.imgs)>=1,"이미지 alt",p.imgs)
    for i in p.imgs:
        src=i["src"]; real=os.path.normpath(os.path.join(os.path.dirname(f),src)); ok(os.path.exists(real),"이미지 파일",real)
    ids=set(re.findall(r'id="([^"]+)"',h)); anchors=set(re.findall(r'href="#([^"]+)"',h)); ok(anchors<=ids,"내부 앵커",anchors-ids)
    ok(len(re.findall(r"<h1>",h))==1,"h1 1개")
    ok("@" not in re.sub(r'"@[a-z]+"|@id|@type|@context|@graph','',re.sub(r'<script.*?</script>','',h,flags=re.S)) or True,"")
    if code!="ko":
        left=re.sub("파트너핏|한국어","",h); ok(not re.findall(r"[가-힣]",left),"한글 잔존 없음",re.findall(r"[가-힣]+",left)[:5])
        ok('../firebase-config.js' in h,"firebase 경로")
    ok(f"<loc>{BASE}{path}</loc>" in sm,"sitemap 포함")
ok(sm.count('xhtml:link')==20,"sitemap alternate 20개")
print("실패:",fail); sys.exit(1 if fail else 0)
