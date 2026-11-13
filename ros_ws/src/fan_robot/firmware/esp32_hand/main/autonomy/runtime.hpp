#pragma once
// Included after camera_settings and ESP-IDF headers in app_main.cpp.
#include <cstdlib>
#include "driver/ledc.h"
#include "controller.hpp"
#include "../observation.hpp"
#include "output_safety.hpp"
#if __has_include("settings.local.h")
#include "settings.local.h"
#else
#include "settings.example.h"
#endif
namespace autonomy {
static SemaphoreHandle_t mutex;
static robot::Supervisor supervisor;
static robot::HandFollower follower(autonomy_settings::controller());
static robot::Target target;
static bool ready = false;
static bool fan_output_on = false;
static bool fan_output_known = false;
static const char *fault = "not_initialized";
static constexpr ledc_channel_t channels[] = {LEDC_CHANNEL_2, LEDC_CHANNEL_3, LEDC_CHANNEL_4, LEDC_CHANNEL_5};
static int64_t now_ms() { return esp_timer_get_time()/1000; }
static void coast() {
    for (auto channel : channels) ledc_stop(LEDC_LOW_SPEED_MODE, channel, 0);
    fan_output_known = gpio_set_level(static_cast<gpio_num_t>(fan_settings::control_pin),
        !fan_settings::active_high) == ESP_OK;
    fan_output_on = false;
}
static void publish(const HandObservation &o) {
    if (!mutex) return;
    robot::Target t;
    t.frame = o.frame_id; t.captured_ms = o.captured_us/1000;
    t.valid = o.found && o.width > 1 && o.height > 1;
    t.x = o.error_x; t.y = o.error_y;
    if (t.valid) t.size = std::sqrt(float(o.right-o.left)*(o.bottom-o.top)/(float(o.width)*o.height));
    xSemaphoreTake(mutex, portMAX_DELAY); target = t; xSemaphoreGive(mutex);
}
static void task(void *) {
    robot::Command previous;
    while (true) {
        xSemaphoreTake(mutex, portMAX_DELAY);
        supervisor.tick(now_ms());
        auto command = follower.step(target, now_ms(), ready && supervisor.armed);
        if (!ready || !supervisor.armed) {
            coast(); // Reassert stop even when the cached command is already zero.
            previous = {};
        } else if (command.left != previous.left || command.right != previous.right || command.fan != previous.fan) {
            // Every new pulse is separated by a zero-output cooldown in HandFollower.
            esp_err_t result = ESP_OK;
            int values[] = {command.left*autonomy_settings::left_sign, command.right*autonomy_settings::right_sign};
            for (unsigned i=0; i<4; ++i) {
                const int v = values[i/2];
                const int duty = ((i%2==0 && v>0) || (i%2==1 && v<0)) ? std::abs(v)*255/100 : 0;
                result |= ledc_set_duty(LEDC_LOW_SPEED_MODE, channels[i], duty);
                result |= ledc_update_duty(LEDC_LOW_SPEED_MODE, channels[i]);
            }
            const esp_err_t fan_result = gpio_set_level(static_cast<gpio_num_t>(fan_settings::control_pin),
                command.fan ? fan_settings::active_high : !fan_settings::active_high);
            fan_output_known = fan_result == ESP_OK;
            fan_output_on = command.fan;
            result |= fan_result;
            if (result != ESP_OK) { supervisor.stop("output_error"); ready=false; fault="output_error"; coast(); }
            previous = command;
        }
        xSemaphoreGive(mutex);
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}
static void begin() {
    if (!output_safety::initialized) { fault="safe_output_init_failed"; return; }
    fan_output_known = fan_settings::wiring_confirmed;
    mutex = xSemaphoreCreateMutex();
    if (!mutex) { fault="mutex_failed"; return; }
    if (!autonomy_settings::motion_confirmed || !motor_settings::wiring_confirmed ||
        !fan_settings::wiring_confirmed) { fault="calibration_or_wiring_not_confirmed"; return; }
    if (!autonomy_settings::controller().valid() ||
        std::abs(autonomy_settings::left_sign)!=1 || std::abs(autonomy_settings::right_sign)!=1 ||
        !output_safety::valid_pins()) { fault="invalid_settings_or_pins"; return; }
    // Camera uses LEDC timer 0; motors exclusively use timer 1, channels 2..5.
    gpio_config_t fan = {};
    fan.pin_bit_mask = 1ULL << fan_settings::control_pin; fan.mode=GPIO_MODE_OUTPUT;
    gpio_set_level(static_cast<gpio_num_t>(fan_settings::control_pin), !fan_settings::active_high);
    esp_err_t result = gpio_config(&fan);
    ledc_timer_config_t timer = {};
    timer.speed_mode=LEDC_LOW_SPEED_MODE; timer.duty_resolution=LEDC_TIMER_8_BIT;
    timer.timer_num=LEDC_TIMER_1; timer.freq_hz=20000; timer.clk_cfg=LEDC_AUTO_CLK;
    result |= ledc_timer_config(&timer);
    for (unsigned i=0; i<4; ++i) {
        ledc_channel_config_t channel = {};
        channel.gpio_num=motor_settings::input_pins[i]; channel.speed_mode=LEDC_LOW_SPEED_MODE;
        channel.channel=channels[i]; channel.timer_sel=LEDC_TIMER_1; channel.duty=0;
        result |= ledc_channel_config(&channel);
    }
    coast();
    if (result != ESP_OK) { fault="output_init_failed"; return; }
    ready=true; fault="none";
    if (xTaskCreate(task,"robot_control",4096,nullptr,5,nullptr)!=pdPASS) {
        ready=false; fault="task_failed"; coast();
        return;
    }
    if (autonomy_settings::auto_start) {
        xSemaphoreTake(mutex, portMAX_DELAY);
        follower.reset(); target = {};
        supervisor.arm(now_ms(), true);
        xSemaphoreGive(mutex);
        ESP_LOGI("robot", "AUTO_START: tracking enabled; waiting for a fresh hand");
    }
}
static esp_err_t control_handler(httpd_req_t *request) {
    if (!mutex) return httpd_resp_send_500(request);
    xSemaphoreTake(mutex, portMAX_DELAY);
    supervisor.tick(now_ms());
    bool accepted = true;
    if (request->method == HTTP_POST) {
        if (!strcmp(request->uri,"/robot/arm")) {
            accepted = ready && supervisor.arm(now_ms(), autonomy_settings::auto_start);
            if (accepted) { follower.reset(); target = {}; }
        } else if (!strcmp(request->uri,"/robot/stop")) {
            supervisor.stop(); follower.reset(); if (ready) coast();
        } else {
            char token[24] = {};
            char *end = nullptr;
            const bool header = httpd_req_get_hdr_value_str(request,"X-Robot-Session",token,sizeof(token))==ESP_OK;
            const unsigned long value = strtoul(token,&end,10);
            accepted = header && end != token && *end == '\0' && value <= UINT32_MAX &&
                supervisor.heartbeat(static_cast<uint32_t>(value),now_ms());
        }
    }
    if (ready && !supervisor.armed) coast();
    char json[512];
    snprintf(json,sizeof(json),"{\"ready\":%s,\"armed\":%s,\"session\":%lu,\"state\":\"%s\",\"reason\":\"%s\",\"fault\":\"%s\",\"size\":%.4f,\"x\":%.4f,\"y\":%.4f,\"fan_output_on\":%s,\"fan_rotation_confirmed\":null,\"auto_start\":%s}",
        ready?"true":"false",supervisor.armed?"true":"false",static_cast<unsigned long>(supervisor.session),
        follower.state,supervisor.reason,fault,target.size,target.x,target.y,
        fan_output_known ? (fan_output_on ? "true" : "false") : "null",
        autonomy_settings::auto_start ? "true" : "false");
    xSemaphoreGive(mutex);
    httpd_resp_set_type(request,"application/json"); httpd_resp_set_hdr(request,"Cache-Control","no-store");
    if (!accepted) httpd_resp_set_status(request,"409 Conflict");
    return httpd_resp_send(request,json,HTTPD_RESP_USE_STRLEN);
}
static const char PAGE[] = R"HTML(<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>手部跟随</title>
<style>body{max-width:720px;margin:32px auto;padding:16px;font:18px system-ui}button{padding:16px;margin:8px}pre{white-space:pre-wrap}</style>
<h1>桌面风扇机器人 · 手部跟随</h1><p>先打开<a href="/" target="_blank">相机预览</a>进行距离标定。状态中的 size 是手框相对尺寸。</p>
<p>只纠正左右位置；手太高或太低时履带停止。启用后检测到手就开风扇，丢手则关闭。</p>
<p id="modeStatus">正在读取运行模式</p><label><input id="safe" type="checkbox">已确认方向、安装和距离标定，并在有物理围挡的测试区域</label>
<p><button id="start">启用 30 秒</button><button id="stop">立即停止</button></p><p id="fanStatus" role="status">风扇状态：等待设备</p><p>显示的是设备开关输出；当前风扇没有转速反馈，无法确认扇叶是否实际转动。</p><pre id="status"></pre>
<script>
let session=null, generation=0, autoStart=false;
const status=document.getElementById('status');
const fanStatus=document.getElementById('fanStatus');
function render(s){autoStart=s.auto_start===true;document.getElementById('modeStatus').textContent=autoStart?'上电自动跟随；关闭网页或断开 Wi-Fi 不会停止。点击停止后须手动恢复或重启 ESP32。':'手动模式：每次 30 秒，关闭页面或断线后停止。';document.getElementById('start').textContent=autoStart?'恢复自动跟随':'启用 30 秒';status.textContent=JSON.stringify(s,null,2);fanStatus.textContent=s.fan_output_on===true?'风扇：已下发开启（转动未确认）':s.fan_output_on===false?'风扇：已下发关闭':'风扇：输出状态未知';}
function unknownFan(){fanStatus.textContent='风扇：连接异常，状态未知';}
async function call(path,method='GET',token=null){const r=await fetch(path,{method,cache:'no-store',headers:token===null?{}:{'X-Robot-Session':String(token)},signal:AbortSignal.timeout(700)});const s=await r.json();if(!r.ok)throw Error(JSON.stringify(s));return s;}
async function stop(){generation++;session=null;try{render(await call('/robot/stop','POST'));}catch(e){unknownFan();status.textContent='停止请求未确认，请关闭电池开关：'+e.message;}}
document.getElementById('start').onclick=async()=>{if(!document.getElementById('safe').checked||document.hidden)return;const g=++generation;session=null;try{const s=await call('/robot/arm','POST');if(g!==generation||(document.hidden && !s.auto_start)){await stop();return;}render(s);session=autoStart?null:s.session;}catch(e){unknownFan();status.textContent=e.message;}};
document.getElementById('stop').onclick=stop;
document.getElementById('safe').onchange=()=>{if(!document.getElementById('safe').checked)stop();};
document.addEventListener('visibilitychange',()=>{if(document.hidden && session!==null)stop();});
window.addEventListener('pagehide',()=>{if(session===null)return;session=null;fetch('/robot/stop',{method:'POST',keepalive:true}).catch(()=>{});});
async function poll(){const g=generation;try{const s=await call(session===null?'/robot/state':'/robot/heartbeat',session===null?'GET':'POST',session);if(g===generation){render(s);if(!s.armed)session=null;}}catch(e){if(g===generation){session=null;unknownFan();status.textContent=(autoStart?'通信异常，设备仍可能自动运行；需停止请关电池：':'通信异常，等待设备租期停机：')+e.message;}}finally{setTimeout(poll,250);}}poll();
</script></html>)HTML";
static esp_err_t page_handler(httpd_req_t *request) {
    httpd_resp_set_type(request,"text/html; charset=utf-8");
    return httpd_resp_send(request,PAGE,HTTPD_RESP_USE_STRLEN);
}
static esp_err_t routes(httpd_handle_t server) {
    httpd_uri_t route = {}; route.uri="/robot"; route.method=HTTP_GET; route.handler=page_handler;
    ESP_RETURN_ON_ERROR(httpd_register_uri_handler(server,&route),"robot","page");
    route.uri="/robot/state"; route.handler=control_handler;
    ESP_RETURN_ON_ERROR(httpd_register_uri_handler(server,&route),"robot","state");
    route.method=HTTP_POST;
    for (const char *path : {"/robot/arm","/robot/stop","/robot/heartbeat"}) {
        route.uri=path;
        ESP_RETURN_ON_ERROR(httpd_register_uri_handler(server,&route),"robot","control route");
    }
    return ESP_OK;
}
} // namespace autonomy
