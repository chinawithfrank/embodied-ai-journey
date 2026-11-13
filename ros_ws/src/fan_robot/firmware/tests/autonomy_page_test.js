const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../esp32_hand/main/autonomy/runtime.hpp'), 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
const flush = () => new Promise(resolve => setImmediate(resolve));
function app(deferArm=false) {
  const elements = Object.fromEntries(['safe','start','stop','status'].map(id=>[id,{checked:false,textContent:''}]));
  const a={elements,events:{},timers:[],calls:[],armed:false,fail:false};
  const document={hidden:false,getElementById:id=>elements[id],addEventListener:(id,fn)=>a.events[id]=fn};
  a.document=document;
  vm.runInNewContext(source, {AbortSignal,document,window:{addEventListener:(id,fn)=>a.events[id]=fn},
    setTimeout:fn=>a.timers.push(fn),fetch:async (url,opts)=>{
      a.calls.push({url,opts});
      if(a.fail) throw Error('network lost');
      if(url==='/robot/arm') a.armed=true;
      if(url==='/robot/stop') a.armed=false;
      const response={ok:true,json:async()=>({armed:a.armed,session:7})};
      if(deferArm && url==='/robot/arm') return new Promise(resolve=>a.release=()=>resolve(response));
      return response;
    }});
  a.poll=async()=>{a.timers.shift()();await flush();};
  a.count=url=>a.calls.filter(c=>c.url===url).length;
  return a;
}
(async()=>{
  const a=app();await flush();
  await a.elements.start.onclick();assert.equal(a.count('/robot/arm'),0);
  a.elements.safe.checked=true;await a.elements.start.onclick();await a.poll();
  assert.equal(a.calls.at(-1).opts.headers['X-Robot-Session'],'7');
  await a.elements.stop.onclick();const before=a.count('/robot/heartbeat');await a.poll();
  assert.equal(a.count('/robot/heartbeat'),before);
  await a.elements.start.onclick();a.document.hidden=true;a.events.visibilitychange();await flush();
  assert.equal(a.armed,false);
  a.document.hidden=false;await a.elements.start.onclick();a.fail=true;await a.poll();
  const failed=a.count('/robot/heartbeat');a.fail=false;await a.poll();
  assert.equal(a.count('/robot/heartbeat'),failed); // no reconnect/rearm after network failure
  const b=app(true);await flush();b.elements.safe.checked=true;
  const pending=b.elements.start.onclick();await flush();await b.elements.stop.onclick();
  b.release();await pending;await b.poll();assert.equal(b.armed,false);
  assert.equal(b.count('/robot/heartbeat'),0); // late arm cannot resurrect a stopped page
})().catch(error=>{console.error(error);process.exitCode=1;});
