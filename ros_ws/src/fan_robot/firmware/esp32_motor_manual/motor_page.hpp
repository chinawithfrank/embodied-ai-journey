#pragma once

namespace manual_motor {
static const char motor_page[] PROGMEM = R"HTML(<!doctype html><html lang="zh-CN">
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>双 N20 电机 · 手动点动</title><style>
body{max-width:850px;margin:24px auto;padding:0 18px;background:#101923;color:#e4edf5;font:17px system-ui}
button{padding:18px;margin:6px;border:0;border-radius:10px;background:#8bd8c8;font:inherit;touch-action:none}
button:disabled{opacity:.4}.stop{background:#ff7777}.drive{user-select:none;-webkit-user-select:none}
img{width:100%;background:#060c12;min-height:100px}pre{white-space:pre-wrap}a{color:#8bd8c8}
</style><h1>双 N20 电机 · 手动点动</h1>
<p>先固定电机、架空轮子。解锁后按住才转，松开即停；每次最长3秒，停止后需重新解锁。</p>
<p>只是电机电压占空比，不是转速闭环，也不是根据摄像头自动行动。</p>
<h2 id="message">正在检查驱动配置</h2><button id="arm" disabled>解锁一次</button>
<button id="stop" class="stop">停止并锁定</button>
<p>占空比 <input id="speed" type="range" min="10" max="100" step="5" value="20">
<span id="speedValue">20%</span>（上限100%，默认20%，不自动加起动冲击）</p>
<p>仅按本次4.5V电池 + 6V N20配置测试。40%不起动但100%诊断能转时，
先只接A，分别试60%、80%，每次空载按住0.2～0.5秒；只嗡响不转立即停。
100%为持续驱动，不证明中间占空比的PWM波形正确；不要增加电池电压或连续堵转。</p>
<div><button class="drive" data-a="1" data-b="0" disabled>A 正转</button>
<button class="drive" data-a="-1" data-b="0" disabled>A 反转</button></div>
<div><button class="drive" data-a="0" data-b="1" disabled>B 正转</button>
<button class="drive" data-a="0" data-b="-1" disabled>B 反转</button></div>
<div><button class="drive" data-a="1" data-b="1" disabled>两台正转</button>
<button class="drive" data-a="-1" data-b="-1" disabled>两台反转</button></div>
<h3>单电机诊断（仅限本次4.5V电池 + 6V N20）</h3>
<p>只连接电机A并固定空载，撤掉IN1接3V3的测试线、恢复GPIO接线。
重新解锁后按住下方按钮：A正转持续高电平，板端500ms限时后锁定，松手可提前停止。
此项忽略滑块设置、固定100%，只做单次诊断；无反应或堵转立即断电，不要反复测试。</p>
<button class="drive stop" data-diagnostic="true" disabled>A 正转100%诊断 · 最长0.5秒</button>
<pre id="detail"></pre><h2>相机接线保持不变</h2>
<button id="videoStart">打开视频</button><button id="videoStop">关闭视频</button>
<a id="cameraLink" target="_blank" rel="noopener">原相机页面</a>
<img id="video" alt="可选相机预览"><script>
const message=document.getElementById('message'),detail=document.getElementById('detail');
const armButton=document.getElementById('arm'),buttons=[...document.querySelectorAll('.drive')];
let session=0,sequence=0,epoch=0,pressed=false,timer=null,configured=false;
function lockButtons(){buttons.forEach(button=>button.disabled=!session);}
async function post(path,body){
 const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify(body),cache:'no-store',signal:AbortSignal.timeout(400)});
 const state=await response.json();
 if(!response.ok)throw new Error(state.error||state.reason||'命令被拒绝');
 return state;
}
function stop(){
 epoch++;pressed=false;session=0;clearTimeout(timer);lockButtons();
 message.textContent='已请求停止并锁定；重新解锁才能运行';
 void post('/api/stop',{}).catch(()=>{message.textContent='连接中断，请求未确认；板端超时将停机';});
}
armButton.onclick=async()=>{
 const current=++epoch;armButton.disabled=true;
 try{
  const state=await post('/api/arm',{});
  if(current!==epoch){void post('/api/stop',{}).catch(()=>{});return;}
  session=state.session;sequence=0;lockButtons();
  message.textContent='已解锁，请在5秒内按住一个按钮';
 }catch(error){stop();message.textContent='不能解锁：'+error.message;}
 finally{armButton.disabled=!configured||Boolean(session);}
};
async function sendDrive(current,motorA,motorB){
 if(!pressed||current!==epoch||!session)return;
 try{
  const state=await post('/api/drive',{session,sequence:++sequence,a:motorA,b:motorB});
  if(current!==epoch)return;
  detail.textContent=JSON.stringify(state,null,2);message.textContent='点动中：松开即停';
  timer=setTimeout(()=>sendDrive(current,motorA,motorB),150);
 }catch(error){if(current===epoch){stop();message.textContent='已锁定：'+error.message;}}
}
async function sendDiagnostic(current){
 try{
  const state=await post('/api/diagnose',{session,sequence:++sequence});
  if(current!==epoch)return;
  detail.textContent=JSON.stringify(state,null,2);
  message.textContent='单次A正转诊断：松手停止，板端500ms限时';
  timer=setTimeout(()=>{if(current===epoch){stop();}},500);
 }catch(error){if(current===epoch){stop();message.textContent='诊断已锁定：'+error.message;}}
}
buttons.forEach(button=>{
 button.oncontextmenu=event=>event.preventDefault();
 button.onpointerdown=event=>{
  if(!event.isPrimary||event.button!==0||!session||pressed)return;
  event.preventDefault();button.setPointerCapture(event.pointerId);pressed=true;
  const speed=Number(document.getElementById('speed').value),current=++epoch;
  if(button.dataset.diagnostic){void sendDiagnostic(current);}
  else{void sendDrive(current,Number(button.dataset.a)*speed,Number(button.dataset.b)*speed);}
 };
 button.onlostpointercapture=()=>{if(pressed)stop();};
});
window.addEventListener('pointerup',()=>{if(pressed)stop();});
window.addEventListener('pointercancel',()=>{if(pressed)stop();});
window.addEventListener('blur',stop);window.addEventListener('pagehide',stop);
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
document.getElementById('stop').onclick=stop;
document.getElementById('speed').oninput=event=>{
 document.getElementById('speedValue').textContent=event.target.value+'%';if(pressed)stop();
};
const camera=new URL(location.href);camera.port='80';camera.pathname='/';camera.search='';camera.hash='';
document.getElementById('cameraLink').href=camera.href;
const video=document.getElementById('video');
document.getElementById('videoStart').onclick=()=>{
 const stream=new URL(camera);stream.port='81';stream.pathname='/stream';video.src=stream.href;
};
document.getElementById('videoStop').onclick=()=>video.removeAttribute('src');
window.addEventListener('pagehide',()=>video.removeAttribute('src'));
async function poll(){
 const current=epoch;
 try{
  const response=await fetch('/api/status',{cache:'no-store',signal:AbortSignal.timeout(600)});
  if(!response.ok)throw new Error('状态不可用');
  const state=await response.json();if(current!==epoch)return;
  configured=state.ready;armButton.disabled=!configured||Boolean(session);
  if(!pressed){detail.textContent=JSON.stringify(state,null,2);
   if(!state.armed){session=0;lockButtons();armButton.disabled=!configured;
    message.textContent=configured?'已锁定：点击解锁一次':state.reason;}}
 }catch(error){configured=false;armButton.disabled=true;if(session||pressed)stop();
  message.textContent='连接失败，不可控制电机';}
 finally{setTimeout(poll,800);}
}poll();</script></html>)HTML";
}
