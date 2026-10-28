#include <cstdio>
#include <cstring>
#include "cJSON.h"
#include "driver/gpio.h"
#include "esp_camera.h"
#include "esp_check.h"
#include "esp_event.h"
#include "esp_heap_caps.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_psram.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "nvs_flash.h"
#include "dl_image_jpeg.hpp"
#include "hand_detect.hpp"
#include "camera_clock.h"
#include "observation.hpp"

#if __has_include("camera_config.local.h")
#include "camera_config.local.h"
#else
#include "camera_config.by_ov2640_v15.example.h"
#endif

#if !CONFIG_IDF_TARGET_ESP32S3
#error "This firmware targets ESP32-S3 N16R8."
#endif

static constexpr const char *TAG = "offline_hand";
static constexpr size_t MAX_JPEG_BYTES = 96 * 1024;
static SemaphoreHandle_t observation_mutex;
static HandObservation latest;
static uint8_t *latest_jpeg;
static size_t latest_jpeg_size;
static bool camera_ready;

static char *observation_json(const HandObservation &observation) {
    cJSON *root = cJSON_CreateObject();
    if (!root) {
        return nullptr;
    }
    cJSON_AddStringToObject(root, "status", observation.status);
    cJSON_AddBoolToObject(root, "found", observation.found);
    cJSON_AddNumberToObject(root, "frame_id", observation.frame_id);
    cJSON_AddNumberToObject(root, "width", observation.width);
    cJSON_AddNumberToObject(root, "height", observation.height);
    cJSON_AddNumberToObject(root, "processing_ms", observation.processing_us / 1000.0);
    cJSON_AddNumberToObject(root, "age_ms", observation.captured_us > 0
        ? (esp_timer_get_time() - observation.captured_us) / 1000.0 : 0);
    cJSON *target = observation.found ? cJSON_CreateObject() : cJSON_CreateNull();
    if (!target) {
        cJSON_Delete(root);
        return nullptr;
    }
    cJSON_AddItemToObject(root, "target", target);
    if (observation.found) {
        cJSON_AddNumberToObject(target, "confidence", observation.score);
        const double box[] = {double(observation.left), double(observation.top),
                              double(observation.right), double(observation.bottom)};
        const double center[] = {observation.center_x, observation.center_y};
        const double error[] = {observation.error_x, observation.error_y};
        cJSON_AddItemToObject(target, "bbox_xyxy", cJSON_CreateDoubleArray(box, 4));
        cJSON_AddItemToObject(target, "center_px", cJSON_CreateDoubleArray(center, 2));
        cJSON_AddItemToObject(target, "error_normalized", cJSON_CreateDoubleArray(error, 2));
    }
    char *payload = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);
    return payload;
}

static void publish(const HandObservation &observation, const camera_fb_t *frame = nullptr) {
    xSemaphoreTake(observation_mutex, portMAX_DELAY);
    latest = observation;
    latest_jpeg_size = 0;
    if (frame && latest_jpeg && frame->len <= MAX_JPEG_BYTES) {
        memcpy(latest_jpeg, frame->buf, frame->len);
        latest_jpeg_size = frame->len;
    }
    xSemaphoreGive(observation_mutex);
    char *payload = observation_json(fresh_observation(observation, esp_timer_get_time()));
    if (payload) {
        printf("HAND %s\n", payload);
        cJSON_free(payload);
    }
}

static void publish_failure(const char *status) {
    HandObservation observation;
    xSemaphoreTake(observation_mutex, portMAX_DELAY);
    observation.frame_id = latest.frame_id;
    xSemaphoreGive(observation_mutex);
    observation.status = status;
    publish(observation);
}

static bool valid_pins() {
    const int inputs[] = {
        camera_settings::data_pins[0], camera_settings::data_pins[1],
        camera_settings::data_pins[2], camera_settings::data_pins[3],
        camera_settings::data_pins[4], camera_settings::data_pins[5],
        camera_settings::data_pins[6], camera_settings::data_pins[7],
        camera_settings::pclk_pin, camera_settings::vsync_pin, camera_settings::href_pin,
    };
    const int outputs[] = {camera_settings::sda_pin, camera_settings::scl_pin,
        camera_settings::reset_pin, camera_settings::power_down_pin, camera_settings::xclk_pin};
    uint64_t used = 0;
    for (int pin : inputs) {
        if (!GPIO_IS_VALID_GPIO(pin) || (used & (1ULL << pin))) {
            return false;
        }
        used |= 1ULL << pin;
    }
    for (int pin : outputs) {
        if (pin == -1) {
            continue;
        }
        if (!GPIO_IS_VALID_OUTPUT_GPIO(pin) || (used & (1ULL << pin))) {
            return false;
        }
        used |= 1ULL << pin;
    }
    return true;
}

static bool initialize_camera() {
    const char *clock_error = validate_camera_clock(camera_settings::xclk_pin,
        camera_settings::xclk_frequency_hz, camera_settings::onboard_clock_confirmed);
    const char *error = !camera_settings::wiring_confirmed ? "wiring_not_confirmed"
        : clock_error ? clock_error : !valid_pins() ? "invalid_or_duplicate_gpio" : nullptr;
    if (error) {
        publish_failure(error);
        return false;
    }
    if (!esp_psram_is_initialized() || esp_psram_get_size() < 8 * 1024 * 1024) {
        publish_failure("8mb_opi_psram_required");
        return false;
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
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = camera_settings::jpeg_quality;
    config.fb_count = 1;
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
    esp_err_t result = esp_camera_init(&config);
    if (result != ESP_OK) {
        ESP_LOGE(TAG, "Camera initialization: %s", esp_err_to_name(result));
        publish_failure("camera_init_failed");
        return false;
    }
    sensor_t *sensor = esp_camera_sensor_get();
    if (!sensor || sensor->id.PID != OV2640_PID) {
        esp_camera_deinit();
        publish_failure("expected_ov2640");
        return false;
    }
    sensor->set_vflip(sensor, camera_settings::vertical_flip);
    sensor->set_hmirror(sensor, camera_settings::horizontal_mirror);
    camera_ready = true;
    ESP_LOGI(TAG, "OV2640 ready: JPEG 320x240, PSRAM %u bytes, XCLK %s %d Hz",
        static_cast<unsigned>(esp_psram_get_size()),
        camera_settings::xclk_pin == -1 ? "onboard" : "ESP32",
        camera_settings::xclk_frequency_hz);
    return true;
}

#if CONFIG_FAN_ENABLE_PREVIEW
static const char PAGE[] = R"HTML(<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>ESP32 离线识别手</title>
<style>body{max-width:800px;margin:30px auto;padding:0 18px;font:17px system-ui;
background:#101923;color:#e4edf5}canvas{width:100%;background:#05090d}pre{white-space:pre-wrap}</style>
<h1>手在哪里？ESP32 本地识别</h1><p>检测在开发板内运行。手机只显示结果，不上传云端；关闭页面也继续检测。</p>
<h2 id="status">等待相机和模型</h2><canvas id="image" width="320" height="240"></canvas>
<pre id="detail"></pre><script>
const canvas=document.getElementById('image'),ctx=canvas.getContext('2d');
const labels={detected:'检测到手',not_found:'没有检测到手',stale:'画面过期，目标已清空'};
async function refresh(){
 try{
  const response=await fetch('/capture',{cache:'no-store',signal:AbortSignal.timeout(2500)});
  if(!response.ok){
   const state=await fetch('/state',{cache:'no-store',signal:AbortSignal.timeout(2500)});
   const report=await state.json();throw new Error(report.status||'图像不可用');
  }
  const state=JSON.parse(response.headers.get('X-Detection'));
  const picture=await createImageBitmap(await response.blob());
  canvas.width=picture.width;canvas.height=picture.height;ctx.drawImage(picture,0,0);picture.close();
  if(state.found){
   const [left,top,right,bottom]=state.target.bbox_xyxy;
   const [centerX,centerY]=state.target.center_px;
   ctx.strokeStyle='#00ff66';ctx.lineWidth=2;ctx.strokeRect(left,top,right-left,bottom-top);
   ctx.fillStyle='#ff5050';ctx.beginPath();ctx.arc(centerX,centerY,4,0,Math.PI*2);ctx.fill();
  }
  document.getElementById('status').textContent=labels[state.status]||state.status;
  document.getElementById('detail').textContent=JSON.stringify(state,null,2);
 }catch(error){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  document.getElementById('status').textContent='目标不可用：'+error.message;
  document.getElementById('detail').textContent='没有新鲜图像，不保留旧坐标。';
 }finally{setTimeout(refresh,400);}
}refresh();</script></html>)HTML";

static esp_err_t index_handler(httpd_req_t *request) {
    httpd_resp_set_type(request, "text/html; charset=utf-8");
    return httpd_resp_send(request, PAGE, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t state_handler(httpd_req_t *request) {
    xSemaphoreTake(observation_mutex, portMAX_DELAY);
    HandObservation observation = fresh_observation(latest, esp_timer_get_time());
    xSemaphoreGive(observation_mutex);
    char *payload = observation_json(observation);
    if (!payload) {
        return httpd_resp_send_500(request);
    }
    httpd_resp_set_type(request, "application/json");
    httpd_resp_set_hdr(request, "Cache-Control", "no-store");
    esp_err_t result = httpd_resp_send(request, payload, HTTPD_RESP_USE_STRLEN);
    cJSON_free(payload);
    return result;
}

static esp_err_t capture_handler(httpd_req_t *request) {
    auto *jpeg = static_cast<uint8_t *>(heap_caps_malloc(MAX_JPEG_BYTES, MALLOC_CAP_SPIRAM));
    if (!jpeg) {
        return httpd_resp_send_500(request);
    }
    xSemaphoreTake(observation_mutex, portMAX_DELAY);
    HandObservation observation = fresh_observation(latest, esp_timer_get_time());
    size_t size = latest_jpeg_size;
    if (!strcmp(observation.status, "stale")) {
        size = 0;
    }
    if (size) {
        memcpy(jpeg, latest_jpeg, size);
    }
    xSemaphoreGive(observation_mutex);
    if (!size) {
        heap_caps_free(jpeg);
        httpd_resp_set_status(request, "503 Service Unavailable");
        return httpd_resp_send(request, "No fresh inference frame; see /state", HTTPD_RESP_USE_STRLEN);
    }
    char *payload = observation_json(observation);
    if (!payload) {
        heap_caps_free(jpeg);
        return httpd_resp_send_500(request);
    }
    httpd_resp_set_type(request, "image/jpeg");
    httpd_resp_set_hdr(request, "Cache-Control", "no-store");
    httpd_resp_set_hdr(request, "X-Detection", payload);
    esp_err_t result = httpd_resp_send(request, reinterpret_cast<char *>(jpeg), size);
    cJSON_free(payload);
    heap_caps_free(jpeg);
    return result;
}

static esp_err_t start_preview() {
    esp_err_t result = nvs_flash_init();
    if (result == ESP_ERR_NVS_NO_FREE_PAGES || result == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_LOGE(TAG, "NVS needs explicit maintenance; not erasing stored data automatically.");
        return result;
    }
    ESP_RETURN_ON_ERROR(result, TAG, "NVS initialization");
    ESP_RETURN_ON_ERROR(esp_netif_init(), TAG, "network initialization");
    ESP_RETURN_ON_ERROR(esp_event_loop_create_default(), TAG, "event loop");
    if (!esp_netif_create_default_wifi_ap()) {
        return ESP_ERR_NO_MEM;
    }
    wifi_init_config_t initialization = WIFI_INIT_CONFIG_DEFAULT();
    ESP_RETURN_ON_ERROR(esp_wifi_init(&initialization), TAG, "Wi-Fi initialization");
    ESP_RETURN_ON_ERROR(esp_wifi_set_storage(WIFI_STORAGE_RAM), TAG, "Wi-Fi storage");
    wifi_config_t config = {};
    snprintf(reinterpret_cast<char *>(config.ap.ssid), sizeof(config.ap.ssid), "FanRobot-Hand");
    snprintf(reinterpret_cast<char *>(config.ap.password), sizeof(config.ap.password), "fanrobot123");
    config.ap.ssid_len = strlen(reinterpret_cast<char *>(config.ap.ssid));
    config.ap.channel = 1;
    config.ap.max_connection = 2;
    config.ap.authmode = WIFI_AUTH_WPA2_PSK;
    ESP_RETURN_ON_ERROR(esp_wifi_set_mode(WIFI_MODE_AP), TAG, "AP mode");
    ESP_RETURN_ON_ERROR(esp_wifi_set_config(WIFI_IF_AP, &config), TAG, "AP configuration");
    ESP_RETURN_ON_ERROR(esp_wifi_start(), TAG, "Wi-Fi start");
    httpd_config_t http_config = HTTPD_DEFAULT_CONFIG();
    http_config.stack_size = 8192;
    http_config.lru_purge_enable = true;
    http_config.send_wait_timeout = 2;
    httpd_handle_t server = nullptr;
    ESP_RETURN_ON_ERROR(httpd_start(&server, &http_config), TAG, "HTTP server");
    httpd_uri_t index = {};
    index.uri = "/";
    index.method = HTTP_GET;
    index.handler = index_handler;
    httpd_uri_t state = index;
    state.uri = "/state";
    state.handler = state_handler;
    httpd_uri_t capture = index;
    capture.uri = "/capture";
    capture.handler = capture_handler;
    ESP_RETURN_ON_ERROR(httpd_register_uri_handler(server, &index), TAG, "index route");
    ESP_RETURN_ON_ERROR(httpd_register_uri_handler(server, &state), TAG, "state route");
    ESP_RETURN_ON_ERROR(httpd_register_uri_handler(server, &capture), TAG, "capture route");
    ESP_LOGI(TAG, "Optional preview: FanRobot-Hand / fanrobot123 / http://192.168.4.1");
    return ESP_OK;
}
#endif

extern "C" void app_main() {
    ESP_LOGI(TAG, "Offline hand detector. No motor, servo, or fan outputs are configured.");
    observation_mutex = xSemaphoreCreateMutex();
    if (!observation_mutex) {
        ESP_LOGE(TAG, "Cannot allocate observation mutex");
        return;
    }
    initialize_camera();
#if CONFIG_FAN_ENABLE_PREVIEW
    latest_jpeg = static_cast<uint8_t *>(heap_caps_malloc(MAX_JPEG_BYTES, MALLOC_CAP_SPIRAM));
    esp_err_t preview_result = start_preview();
    if (!latest_jpeg || preview_result != ESP_OK) {
        ESP_LOGE(TAG, "Preview unavailable; serial inference can continue: %s", esp_err_to_name(preview_result));
    }
#else
    ESP_LOGI(TAG, "Wi-Fi is disabled. Inference continues without a network.");
#endif
    if (!camera_ready) {
        ESP_LOGE(TAG, "Camera unavailable; correct the reported configuration and reflash.");
        return;
    }
    HandDetect detector;
    detector.set_score_thr(CONFIG_FAN_HAND_SCORE_PERCENT / 100.0f);
    uint32_t frame_id = 0;
    while (true) {
        const int64_t started = esp_timer_get_time();
        camera_fb_t *frame = esp_camera_fb_get();
        if (!frame) {
            publish_failure("capture_failed");
        } else if (frame->len > MAX_JPEG_BYTES || frame->format != PIXFORMAT_JPEG) {
            publish_failure("invalid_or_oversized_jpeg");
        } else {
            dl::image::jpeg_img_t jpeg = {};
            jpeg.data = frame->buf;
            jpeg.data_len = frame->len;
            auto image = dl::image::sw_decode_jpeg(jpeg, dl::image::DL_IMAGE_PIX_TYPE_RGB888);
            if (!image.data) {
                publish_failure("jpeg_decode_failed");
            } else {
                HandObservation observation;
                observation.width = image.width;
                observation.height = image.height;
                observation.frame_id = ++frame_id;
                observation.captured_us = started;
                observation.status = "not_found";
                for (const auto &hand : detector.run(image)) {
                    if (hand.box.size() >= 4) {
                        consider_hand(observation, hand.score, hand.box[0], hand.box[1],
                            hand.box[2], hand.box[3], CONFIG_FAN_HAND_SCORE_PERCENT / 100.0f);
                    }
                }
                observation.processing_us = esp_timer_get_time() - started;
                publish(observation, frame);
                heap_caps_free(image.data);
            }
        }
        if (frame) {
            esp_camera_fb_return(frame);
        }
        int64_t remaining_ms = CONFIG_FAN_HAND_INTERVAL_MS - (esp_timer_get_time() - started) / 1000;
        vTaskDelay(pdMS_TO_TICKS(std::max<int64_t>(10, remaining_ms)));
    }
}
