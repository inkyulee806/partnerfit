
import json,urllib.request
from playwright.sync_api import sync_playwright
FS_STUB="""window.__db=window.__db||{};
export const getFirestore=()=>({});export const serverTimestamp=()=>"TS";
let n=0;export const collection=(db,c)=>({c});
export const doc=(a,c,id)=>a&&a.c&&!c?{c:a.c,id:"gen"+(++n)}:{c,id};
const k=r=>r.c+"/"+r.id;
export const setDoc=async(r,d,o)=>{ if(window.__failfs) throw new Error("denied"); window.__db[k(r)]=o&&o.merge?{...(window.__db[k(r)]||{}),...d}:d; };
export const deleteDoc=async r=>{ delete window.__db[k(r.ref||r)]; };
export const query=(c,w)=>({c:c.c,w});export const where=(f,o,v)=>({f,v});
export const getDocs=async q=>({docs:Object.entries(window.__db).filter(([p,d])=>p.startsWith(q.c+"/")&&d.uid===q.w.v).map(([p])=>({ref:{c:p.split("/")[0],id:p.split("/")[1]}}))});"""
APP="export const initializeApp=()=>({});"
AUTH="""export const getAuth=()=>({get currentUser(){ return window.__user?{...window.__user,getIdToken:async()=>window.__tok||'good'}:null }});export class GoogleAuthProvider{};export class OAuthProvider{addScope(){}};
export const signInWithPopup=async()=>{};export const signOut=async()=>{};
export const onAuthStateChanged=(a,cb)=>{ setTimeout(()=>cb(window.__user||null),50); };"""
B="http://127.0.0.1:8850"
def calls(): return json.loads(urllib.request.urlopen(B+"/__calls").read())
def run(prov,key,model):
    urllib.request.urlopen(B+"/__reset").read()
    with sync_playwright() as p:
        b=p.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":800}); errs=[]; direct=[]
        pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.on("request",lambda r: direct.append(r.url) if ("api.openai.com" in r.url or "api.anthropic.com" in r.url) else None)
        pg.route("**/firebase-app.js",lambda r:r.fulfill(body=APP,content_type="text/javascript"))
        pg.route("**/firebase-firestore.js",lambda r:r.fulfill(body=FS_STUB,content_type="text/javascript"))
        pg.route("**/firebase-auth.js",lambda r:r.fulfill(body=AUTH,content_type="text/javascript"))
        pg.add_init_script("window.__user={displayName:'T',uid:'u1',email:'t@x.com',providerData:[{providerId:'google.com'}]}")
        pg.goto(B+"/app/index.html"); pg.wait_for_timeout(300)
        pg.select_option("#provider",prov)
        pg.fill("#apikey","sk-bad"); pg.click("#verify"); pg.wait_for_timeout(500); print(prov,"bad key ->",pg.inner_text("#keystatus"))
        pg.fill("#apikey",key); pg.click("#verify"); pg.wait_for_timeout(500); print(prov,"good key ->",pg.inner_text("#keystatus"),"| models",pg.eval_on_selector_all("#model option","o=>o.map(x=>x.value)"))
        for k,v in {"f-countries":"Czechia","f-tproducts":"cosmetics","c-name":"TESTCO","c-model":"manufacturer","p-item":"serum"}.items(): pg.fill("#"+k,v)
        pg.check("#consent"); pg.click("#run"); pg.wait_for_selector("#report:not([hidden])",timeout=30000)
        txt=pg.inner_text("#report"); print(prov,"SEEN:", "TEST-SEEN" in txt,"| UNSEEN:", "TEST-UNSEEN" in txt)
        c=calls(); print(prov,"upstream:",[(x["method"],x["url"].replace("https://","")) for x in c])
        print(prov,"browser direct calls to providers:",direct,"| errs",errs)
        keyhdr=[x["headers"] for x in c if x["url"].endswith("/v1/messages") or x["url"].endswith("/v1/responses")][0]; print(prov,"provider headers:",{k:v for k,v in keyhdr.items()})
        # unauth token
        pg.evaluate("window.__tok='bad'"); pg.fill("#apikey",key); pg.click("#verify"); pg.wait_for_timeout(500); print(prov,"bad token ->",pg.inner_text("#keystatus"))
        b.close()
run("openai","sk-good","gpt-5")
run("anthropic","sk-ant-good","claude-sonnet-5-5")
