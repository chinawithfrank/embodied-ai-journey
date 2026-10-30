#pragma once

namespace manual_fan {
static const char fan_panel[] PROGMEM = R"HTML(
<section style="border:2px solid #8bd8c8;padding:16px;margin-top:24px">
<h2>独立风扇开关 · LR7843</h2>
<p>需确认模块兼容5V负载及3.3V控制，风扇带防护罩、固定空载。
这里只做供电开关，不调速、不自动追踪；叶片断电后仍可能惯性转动。</p>
<p>开启后可继续在本页操作电机；切后台/失焦会请求停止，断联约1秒关闭，单次最多30秒。</p>
<button id="fanStart" disabled>解锁并开启风扇</button>
<button id="fanStop" class="stop">关闭风扇</button>
<p id="fanMessage">正在检查风扇配置</p><pre id="fanDetail"></pre></section>
<script>(()=>{
const start=document.getElementById('fanStart'),message=document.getElementById('fanMessage');
const detail=document.getElementById('fanDetail');
let session=0,sequence=0,epoch=0,timer=null,configured=false,pending=false;
function lock(){start.disabled=!configured||pending||Boolean(session);}
async function post(path,body){
 const response=await fetch('/api/fan/'+path,{method:'POST',
  headers:{'Content-Type':'application/json'},body:JSON.stringify(body),cache:'no-store',
  signal:AbortSignal.timeout(500)});
 const state=await response.json();
 if(!response.ok)throw new Error(state.error||state.reason||'请求被拒绝');
 return state;
}
function stop(){
 epoch++;session=0;pending=false;clearTimeout(timer);lock();
 message.textContent='已请求关闭风扇并锁定';
 void post('stop',{}).catch(()=>{message.textContent='停止未确认，请断开风扇电源；板端租期到时会撤销输出';});
}
async function run(current){
 if(current!==epoch||!session)return;
 const state=await post('run',{session,sequence:++sequence});
 if(current!==epoch)return;
 detail.textContent=JSON.stringify(state,null,2);
 message.textContent='风扇输出开启：可在本页点动电机，最多30秒';
 timer=setTimeout(()=>{run(current).catch(error=>{
  if(current===epoch){stop();message.textContent='已锁定：'+error.message;}
 });},200);
}
start.onclick=async()=>{
 const current=++epoch;pending=true;lock();
 try{
  const state=await post('arm',{});
  if(current!==epoch){void post('stop',{}).catch(()=>{});return;}
  session=state.session;sequence=0;
  await run(current);
 }catch(error){if(current===epoch){stop();message.textContent='不能开启：'+error.message;}}
 finally{if(current===epoch){pending=false;lock();}}
};
document.getElementById('fanStop').onclick=stop;
document.getElementById('stopAll').onclick=()=>{
 stop();
 void fetch('/api/stop',{method:'POST',headers:{'Content-Type':'application/json'},
  body:'{}',signal:AbortSignal.timeout(500)}).catch(()=>{
   message.textContent='全部停止未确认，请使用物理电源开关';
  });
};
window.addEventListener('blur',stop);window.addEventListener('pagehide',stop);
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
async function poll(){
 const current=epoch;
 try{
  const response=await fetch('/api/fan/status',{cache:'no-store',signal:AbortSignal.timeout(500)});
  if(!response.ok)throw new Error('状态不可用');
  const state=await response.json();if(current!==epoch)return;
  configured=state.ready;
  if(!pending){
   detail.textContent=JSON.stringify(state,null,2);
   if(!state.armed||!configured){
    if(session){epoch++;session=0;clearTimeout(timer);}
    message.textContent=configured?'风扇已关闭：'+state.reason:'风扇禁用：'+state.reason;
   }
  }
  lock();
 }catch(error){if(current===epoch){configured=false;stop();message.textContent='风扇连接失败，不自动恢复';}}
 finally{setTimeout(poll,700);}
}poll();
})();</script>
)HTML";
}
