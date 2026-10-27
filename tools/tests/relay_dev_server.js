const http=require('http'),fs=require('fs'),path=require('path');
const ROOT='/home/claude/partnerfit', relay=require(ROOT+'/api/relay.js');
const calls=[]; globalThis.__calls=calls;
const REPORT_O={language:"en",summary:{},candidates:[{name:"TEST-SEEN",country:"Czechia",website:"https://seen.example",role:"importer",products:["x"],score_breakdown:{product_match:{status:"scored",points:80}},fit_reasons:[{text:"r",source_url:"https://seen.example/p"}],contact:{},priority:"high"},{name:"TEST-UNSEEN",country:"Czechia",website:"https://fabricated.example",role:"importer",products:["x"],score_breakdown:{product_match:{status:"scored",points:80}},fit_reasons:[{text:"r",source_url:"https://fabricated.example/p"}],contact:{},priority:"high"}],email_drafts:[],sources:[]};
let nMsg=0, nPoll=0;
const J=(status,obj)=>({status,ok:status<300,text:async()=>JSON.stringify(obj),json:async()=>obj});
global.fetch=async(url,init={})=>{
  url=String(url); const h=init.headers||{}; let body=init.body;
  calls.push({url,method:init.method||'GET',headers:h,body});
  if(url.startsWith('https://identitytoolkit.googleapis.com')) return JSON.parse(body).idToken==='good'?J(200,{users:[{localId:'u1'}]}):J(400,{error:{message:'INVALID'}});
  if(url==='https://api.openai.com/v1/models') return h.Authorization==='Bearer sk-good'?J(200,{data:[{id:'gpt-5'},{id:'gpt-4.1'}]}):J(401,{error:{message:'Incorrect API key'}});
  if(url==='https://api.openai.com/v1/responses') return J(200,{id:'resp_1',status:'queued'});
  if(url==='https://api.openai.com/v1/responses/resp_1'){ nPoll++; return J(200,{id:'resp_1',status:nPoll<2?'in_progress':'completed',output:[{type:'message',content:[{type:'output_text',text:JSON.stringify(REPORT_O),annotations:[{url:'https://www.seen.example/page'}]}]}]}); }
  if(url.startsWith('https://api.anthropic.com/v1/models')) return J(200,{data:[{id:'claude-sonnet-5-5'},{id:'claude-opus-5-5'}]});
  if(url==='https://api.anthropic.com/v1/messages'){ nMsg++; if(nMsg===1) return J(200,{stop_reason:'pause_turn',content:[{type:'server_tool_use',id:'s1',name:'web_search',input:{query:'q'}}]});
    return J(200,{stop_reason:'end_turn',content:[{type:'web_search_tool_result',tool_use_id:'s1',content:[{type:'web_search_result',url:'https://www.seen.example/page',title:'t'}]},{type:'text',text:JSON.stringify(REPORT_O)}]}); }
  return J(404,{error:{message:'unmocked '+url}});
};
http.createServer((req,res)=>{
  if(req.url==='/__calls'){ res.setHeader('content-type','application/json'); return res.end(JSON.stringify(calls.filter(c=>!c.url.includes('identitytoolkit')))); }
  if(req.url==='/__reset'){ calls.length=0; nMsg=0; nPoll=0; return res.end('ok'); }
  if(req.url.startsWith('/api/relay')) return relay(req,res);
  let f=path.join(ROOT,decodeURIComponent(req.url.split('?')[0])); if(f.endsWith('/')) f+='index.html';
  fs.readFile(f,(e,d)=>{ if(e){res.statusCode=404;return res.end('nf');} res.setHeader('content-type',f.endsWith('.js')?'text/javascript':f.endsWith('.html')?'text/html; charset=utf-8':'application/octet-stream'); res.end(d); });
}).listen(8850,'127.0.0.1');
