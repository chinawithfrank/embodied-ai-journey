#include <Arduino.h>
#include <WiFi.h>
#include <driver/gpio.h>
#include <esp_camera.h>
#include <esp_http_server.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include "camera_clock.h"

#if __has_include("camera_config.local.h")
#include "camera_config.local.h"
#else
#include "camera_config.example.h"
#endif

#if !CONFIG_IDF_TARGET_ESP32S3
#error "Select an ESP32-S3 board before compiling."
#endif

static httpd_handle_t control_server = nullptr;
static httpd_handle_t stream_server = nullptr;
static SemaphoreHandle_t camera_mutex = nullptr;
static bool camera_ready = false;
static const char *camera_status = "not_initialized";
static uint16_t sensor_pid = 0;

static const char index_html[] PROGMEM = R"HTML(
<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>风扇机器人 · 第一双眼睛</title>
<style>
body{max-width:900px;margin:32px auto;padding:0 20px;font-family:system-ui;background:#101923;color:#e4edf5}
img{display:block;width:100%;min-height:160px;background:#060c12;border-radius:12px;margin:20px 0}
button,a{padding:10px 14px;margin:4px;border-radius:6px;color:#101923;background:#8bd8c8;border:0;display:inline-block}
pre{white-space:pre-wrap;background:#192735;padding:16px;border-radius:8px}p{line-height:1.7}
</style></head><body>
<h1>风扇机器人的第一双眼睛</h1>
<p>这一阶段只采集画面，不控制轮子或风扇。先确认“看得见”，再学习“看懂”。</p>
<p id="status">正在读取相机状态……</p>
<button id="start">开始视频</button><button id="stop">停止视频</button>
<a href="/capture" target="_blank" rel="noopener">打开一张照片</a>
<button id="refresh">刷新状态</button><img id="camera" alt="尚未开始视频">
<pre id="details"></pre>
<p>仅限可信局域网或开发板热点使用；当前页面没有登录认证。一次只开一个视频窗口。</p>
<script>
const picture=document.getElementById('camera');
function stop(){picture.removeAttribute('src');}
async function refresh(){
  try{
    const response=await fetch('/health',{cache:'no-store'});
    if(!response.ok)throw new Error('HTTP '+response.status);
    const health=await response.json();
    document.getElementById('status').textContent=health.camera_ready
      ?'相机已就绪，点击“开始视频”。'
      :'相机未就绪：'+health.status+'。请检查配置和串口日志。';
    document.getElementById('details').textContent=JSON.stringify(health,null,2);
    document.getElementById('start').disabled=!health.camera_ready;
  }catch(error){document.getElementById('status').textContent='无法连接开发板：'+error.message;}
}
document.getElementById('start').onclick=()=>{
  const endpoint=new URL('/stream',location.href);endpoint.port='81';
  endpoint.searchParams.set('session',Date.now());picture.src=endpoint.href;
  document.getElementById('status').textContent='正在请求视频；停止后可查看单张照片。';
};
picture.onerror=()=>{document.getElementById('status').textContent='视频中断，请检查信号、相机日志，再重新开始。';};
document.getElementById('stop').onclick=()=>{stop();refresh();};
document.getElementById('refresh').onclick=refresh;
window.addEventListener('pagehide',stop);refresh();
</script></body></html>
)HTML";

static bool validate_pins() {
  const int required_pins[] = {
    camera_settings::data_pins[0], camera_settings::data_pins[1],
    camera_settings::data_pins[2], camera_settings::data_pins[3],
    camera_settings::data_pins[4], camera_settings::data_pins[5],
    camera_settings::data_pins[6], camera_settings::data_pins[7],
    camera_settings::pclk_pin,
    camera_settings::vsync_pin, camera_settings::href_pin,
    camera_settings::sda_pin, camera_settings::scl_pin,
  };
  uint64_t used_pins = 0;
  for (int pin : required_pins) {
    if (!GPIO_IS_VALID_GPIO(pin) || (used_pins & (1ULL << pin))) {
      return false;
    }
    used_pins |= 1ULL << pin;
  }
  const int output_pins[] = {
    camera_settings::sda_pin,
    camera_settings::scl_pin,
  };
  for (int pin : output_pins) {
    if (!GPIO_IS_VALID_OUTPUT_GPIO(pin)) {
      return false;
    }
  }
  const int optional_pins[] = {
    camera_settings::xclk_pin, camera_settings::power_down_pin,
    camera_settings::reset_pin,
  };
  for (int pin : optional_pins) {
    if (pin == -1) {
      continue;
    }
    if (!GPIO_IS_VALID_OUTPUT_GPIO(pin) || (used_pins & (1ULL << pin))) {
      return false;
    }
    used_pins |= 1ULL << pin;
  }
  return true;
}

static void initialize_camera() {
  if (!camera_settings::wiring_confirmed) {
    camera_status = "wiring_not_confirmed";
    Serial.println("Camera disabled: confirm the DVP wiring in camera_config.local.h first.");
    return;
  }
  const char *clock_error = validate_camera_clock(
    camera_settings::xclk_pin, camera_settings::xclk_frequency_hz,
    camera_settings::onboard_clock_confirmed);
  if (clock_error != nullptr) {
    camera_status = clock_error;
    Serial.println("Check the carrier schematic and oscillator frequency before enabling capture.");
    return;
  }
  if (!validate_pins()) {
    camera_status = "invalid_or_duplicate_gpio";
    return;
  }
  if (camera_settings::require_psram && !psramFound()) {
    camera_status = "psram_not_detected";
    Serial.println("PSRAM missing. For WROOM-1-N16R8 check OPI PSRAM and the board selection.");
    return;
  }
  camera_mutex = xSemaphoreCreateMutex();
  if (camera_mutex == nullptr) {
    camera_status = "mutex_allocation_failed";
    return;
  }
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = camera_settings::data_pins[0];
  config.pin_d1 = camera_settings::data_pins[1];
  config.pin_d2 = camera_settings::data_pins[2];
  config.pin_d3 = camera_settings::data_pins[3];
  config.pin_d4 = camera_settings::data_pins[4];
  config.pin_d5 = camera_settings::data_pins[5];
  config.pin_d6 = camera_settings::data_pins[6];
  config.pin_d7 = camera_settings::data_pins[7];
  config.pin_xclk = camera_settings::xclk_pin;
  config.pin_pclk = camera_settings::pclk_pin;
  config.pin_vsync = camera_settings::vsync_pin;
  config.pin_href = camera_settings::href_pin;
  config.pin_sccb_sda = camera_settings::sda_pin;
  config.pin_sccb_scl = camera_settings::scl_pin;
  config.pin_pwdn = camera_settings::power_down_pin;
  config.pin_reset = camera_settings::reset_pin;
  config.xclk_freq_hz = camera_settings::xclk_frequency_hz;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = psramFound() ? FRAMESIZE_VGA : FRAMESIZE_QVGA;
  config.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  config.fb_count = psramFound() ? 2 : 1;
  config.grab_mode = CAMERA_GRAB_LATEST;
  config.jpeg_quality = camera_settings::jpeg_quality;

  const esp_err_t result = esp_camera_init(&config);
  if (result != ESP_OK) {
    camera_status = "camera_init_failed";
    Serial.printf("Camera init failed: %s (0x%x)\n", esp_err_to_name(result), result);
    return;
  }
  sensor_t *sensor = esp_camera_sensor_get();
  if (sensor == nullptr) {
    camera_status = "sensor_not_found";
    esp_camera_deinit();
    return;
  }
  sensor_pid = sensor->id.PID;
  if (sensor_pid != OV2640_PID && sensor_pid != OV5640_PID) {
    camera_status = "unsupported_sensor";
    esp_camera_deinit();
    return;
  }
  sensor->set_vflip(sensor, camera_settings::vertical_flip);
  sensor->set_hmirror(sensor, camera_settings::horizontal_mirror);
  camera_ready = true;
  camera_status = "ready";
  Serial.printf("Camera ready: %s, PID=0x%04x\n",
                sensor_pid == OV2640_PID ? "OV2640" : "OV5640", sensor_pid);
}

static esp_err_t index_handler(httpd_req_t *request) {
  httpd_resp_set_type(request, "text/html; charset=utf-8");
  return httpd_resp_send(request, index_html, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t health_handler(httpd_req_t *request) {
  char payload[384];
  snprintf(payload, sizeof(payload),
           "{\"camera_ready\":%s,\"status\":\"%s\",\"sensor\":\"%s\","
           "\"sensor_pid\":%u,\"xclk_source\":\"%s\",\"xclk_frequency_hz\":%d,"
           "\"psram_bytes\":%u,\"free_heap_bytes\":%u,"
           "\"uptime_ms\":%lu}",
           camera_ready ? "true" : "false", camera_status,
           sensor_pid == OV2640_PID ? "OV2640" : sensor_pid == OV5640_PID ? "OV5640" : "unknown",
           sensor_pid, camera_settings::xclk_pin == -1 ? "onboard" : "esp32",
           camera_settings::xclk_frequency_hz,
           ESP.getPsramSize(), ESP.getFreeHeap(), millis());
  httpd_resp_set_type(request, "application/json");
  httpd_resp_set_hdr(request, "Cache-Control", "no-store");
  return httpd_resp_send(request, payload, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t unavailable(httpd_req_t *request, const char *reason) {
  httpd_resp_set_status(request, "503 Service Unavailable");
  httpd_resp_set_type(request, "text/plain; charset=utf-8");
  return httpd_resp_send(request, reason, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t capture_handler(httpd_req_t *request) {
  if (!camera_ready) {
    return unavailable(request, camera_status);
  }
  if (xSemaphoreTake(camera_mutex, pdMS_TO_TICKS(2000)) != pdTRUE) {
    return unavailable(request, "camera_busy: stop other viewers and retry");
  }
  camera_fb_t *frame = esp_camera_fb_get();
  esp_err_t result;
  if (frame == nullptr || frame->format != PIXFORMAT_JPEG) {
    result = unavailable(request, "jpeg_capture_failed");
  } else {
    httpd_resp_set_type(request, "image/jpeg");
    httpd_resp_set_hdr(request, "Cache-Control", "no-store");
    result = httpd_resp_send(request, reinterpret_cast<const char *>(frame->buf), frame->len);
  }
  if (frame != nullptr) {
    esp_camera_fb_return(frame);
  }
  xSemaphoreGive(camera_mutex);
  return result;
}

static esp_err_t stream_handler(httpd_req_t *request) {
  if (!camera_ready) {
    return unavailable(request, camera_status);
  }
  esp_err_t result = httpd_resp_set_type(
    request, "multipart/x-mixed-replace;boundary=fanrobotframe");
  httpd_resp_set_hdr(request, "Cache-Control", "no-store");
  while (result == ESP_OK) {
    if (xSemaphoreTake(camera_mutex, pdMS_TO_TICKS(2000)) != pdTRUE) {
      return ESP_FAIL;
    }
    camera_fb_t *frame = esp_camera_fb_get();
    if (frame == nullptr || frame->format != PIXFORMAT_JPEG) {
      if (frame != nullptr) {
        esp_camera_fb_return(frame);
      }
      xSemaphoreGive(camera_mutex);
      Serial.println("Stream failed to capture a JPEG frame.");
      return ESP_FAIL;
    }
    char header[128];
    const int length = snprintf(header, sizeof(header),
      "\r\n--fanrobotframe\r\nContent-Type: image/jpeg\r\nContent-Length: %zu\r\n\r\n",
      frame->len);
    result = httpd_resp_send_chunk(request, header, length);
    if (result == ESP_OK) {
      result = httpd_resp_send_chunk(
        request, reinterpret_cast<const char *>(frame->buf), frame->len);
    }
    esp_camera_fb_return(frame);
    xSemaphoreGive(camera_mutex);
    delay(camera_settings::stream_interval_ms);
  }
  return result;
}

static void start_servers() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;
  config.stack_size = 8192;
  config.send_wait_timeout = 3;
  config.recv_wait_timeout = 3;
  ESP_ERROR_CHECK(httpd_start(&control_server, &config));
  const httpd_uri_t index_uri = {.uri = "/", .method = HTTP_GET, .handler = index_handler, .user_ctx = nullptr};
  const httpd_uri_t health_uri = {.uri = "/health", .method = HTTP_GET, .handler = health_handler, .user_ctx = nullptr};
  const httpd_uri_t capture_uri = {.uri = "/capture", .method = HTTP_GET, .handler = capture_handler, .user_ctx = nullptr};
  ESP_ERROR_CHECK(httpd_register_uri_handler(control_server, &index_uri));
  ESP_ERROR_CHECK(httpd_register_uri_handler(control_server, &health_uri));
  ESP_ERROR_CHECK(httpd_register_uri_handler(control_server, &capture_uri));
  config.server_port = 81;
  config.ctrl_port += 1;
  ESP_ERROR_CHECK(httpd_start(&stream_server, &config));
  const httpd_uri_t stream_uri = {.uri = "/stream", .method = HTTP_GET, .handler = stream_handler, .user_ctx = nullptr};
  ESP_ERROR_CHECK(httpd_register_uri_handler(stream_server, &stream_uri));
}

static bool start_network() {
  if (!camera_settings::use_access_point && strlen(camera_settings::wifi_name) > 0) {
    WiFi.mode(WIFI_STA);
    WiFi.begin(camera_settings::wifi_name, camera_settings::wifi_password);
    const unsigned long started = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - started < camera_settings::wifi_timeout_ms) {
      delay(250);
    }
    if (WiFi.status() == WL_CONNECTED) {
      WiFi.setSleep(false);
      Serial.printf("Network: Wi-Fi station, http://%s/\n", WiFi.localIP().toString().c_str());
      return true;
    }
    Serial.println("Wi-Fi connection timed out; starting the local access point instead.");
  }
  WiFi.mode(WIFI_AP);
  if (!WiFi.softAP(camera_settings::access_point_name, camera_settings::access_point_password)) {
    Serial.println("Failed to start access point. Check its name and password (8+ characters).");
    return false;
  }
  Serial.printf("Network: access point '%s', http://%s/\n",
                camera_settings::access_point_name, WiFi.softAPIP().toString().c_str());
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("Fan robot: camera-only experiment. No motor or fan outputs are configured.");
  Serial.printf("PSRAM: %u bytes\n", ESP.getPsramSize());
  Serial.printf("Camera clock: %s, %d Hz (XCLK GPIO %d)\n",
                camera_settings::xclk_pin == -1 ? "onboard" : "esp32",
                camera_settings::xclk_frequency_hz, camera_settings::xclk_pin);
  initialize_camera();
  Serial.printf("Camera status: %s\n", camera_status);
  if (start_network()) {
    start_servers();
    Serial.println("Web page / | Status /health | JPEG /capture | MJPEG port 81 /stream");
  }
}

void loop() {
  delay(1000);
}
