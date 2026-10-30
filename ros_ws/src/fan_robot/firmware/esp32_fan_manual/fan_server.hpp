#pragma once

#include "fan_guard.hpp"
#include "fan_page.hpp"

#if __has_include("fan_config.local.h")
#include "fan_config.local.h"
#else
#include "fan_config.example.h"
#endif

namespace manual_fan {
static FanGuard guard;
static SemaphoreHandle_t mutex = nullptr;
static bool ready = false;
static bool gpio_ready = false;
static bool applied = false;
static const char *disabled_reason = "fan_wiring_not_confirmed";

static bool valid_pin() {
  const int reserved[] = {camera_settings::data_pins[0], camera_settings::data_pins[1],
    camera_settings::data_pins[2], camera_settings::data_pins[3],
    camera_settings::data_pins[4], camera_settings::data_pins[5],
    camera_settings::data_pins[6], camera_settings::data_pins[7],
    camera_settings::xclk_pin, camera_settings::pclk_pin, camera_settings::vsync_pin,
    camera_settings::href_pin, camera_settings::sda_pin, camera_settings::scl_pin,
    camera_settings::reset_pin, camera_settings::power_down_pin,
    motor_settings::input_pins[0], motor_settings::input_pins[1],
    motor_settings::input_pins[2], motor_settings::input_pins[3],
    motor_settings::sleep_pin, motor_settings::fault_pin,
    0, 3, 19, 20, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
    43, 44, 45, 46, 48};
  return GPIO_IS_VALID_OUTPUT_GPIO(fan_settings::control_pin) &&
    !manual_motor::motor_pins_conflict(&fan_settings::control_pin, 1,
      reserved, sizeof(reserved) / sizeof(reserved[0]));
}

static void apply() {
  if (!gpio_ready) {
    return;
  }
  const bool desired = ready && guard.running;
  const int level = desired == fan_settings::active_high ? 1 : 0;
  if (gpio_set_level(static_cast<gpio_num_t>(fan_settings::control_pin), level) != ESP_OK) {
    guard.stop("fan_gpio_error");
    ready = false;
    disabled_reason = "fan_gpio_error";
    gpio_set_level(static_cast<gpio_num_t>(fan_settings::control_pin),
      fan_settings::active_high ? 0 : 1);
    applied = false;
    return;
  }
  applied = desired;
}

static void watchdog(void *) {
  while (true) {
    xSemaphoreTake(mutex, portMAX_DELAY);
    guard.tick(millis());
    apply();
    xSemaphoreGive(mutex);
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

static void begin() {
  mutex = xSemaphoreCreateMutex();
  if (!mutex) {
    Serial.println("Fan disabled: mutex allocation failed.");
    return;
  }
  if (fan_settings::wiring_confirmed) {
    if (!valid_pin()) {
      disabled_reason = "invalid_or_conflicting_fan_gpio";
    } else {
      gpio_config_t output = {};
      output.pin_bit_mask = 1ULL << fan_settings::control_pin;
      output.mode = GPIO_MODE_OUTPUT;
      output.pull_down_en = fan_settings::active_high ? GPIO_PULLDOWN_ENABLE : GPIO_PULLDOWN_DISABLE;
      output.pull_up_en = fan_settings::active_high ? GPIO_PULLUP_DISABLE : GPIO_PULLUP_ENABLE;
      const auto pin = static_cast<gpio_num_t>(fan_settings::control_pin);
      if (gpio_set_level(pin, fan_settings::active_high ? 0 : 1) == ESP_OK &&
          gpio_config(&output) == ESP_OK) {
        gpio_ready = ready = true;
        apply();
        if (xTaskCreatePinnedToCore(watchdog, "fan_deadman", 3072, nullptr, 6, nullptr, 1) != pdPASS) {
          ready = false;
          disabled_reason = "fan_watchdog_failed";
          apply();
        }
      } else {
        disabled_reason = "fan_gpio_setup_failed";
      }
    }
  }
  Serial.printf("Fan control: GPIO%d, %s. Boot output is off; no PWM timer allocated.\n",
    fan_settings::control_pin, ready ? "ready" : disabled_reason);
}

static esp_err_t state(httpd_req_t *request, const char *error = "") {
  xSemaphoreTake(mutex, portMAX_DELAY);
  guard.tick(millis());
  apply();
  char payload[512];
  snprintf(payload, sizeof(payload),
    "{\"ready\":%s,\"armed\":%s,\"running\":%s,\"session\":%lu,\"sequence\":%lu,"
    "\"reason\":\"%s\",\"pin\":%d,\"heartbeat_ms\":%lu,\"maximum_run_ms\":%lu,\"error\":\"%s\"}",
    ready ? "true" : "false", guard.armed ? "true" : "false", applied ? "true" : "false",
    static_cast<unsigned long>(guard.session), static_cast<unsigned long>(guard.sequence),
    ready ? guard.reason : disabled_reason, fan_settings::control_pin,
    static_cast<unsigned long>(FanGuard::heartbeat_ms),
    static_cast<unsigned long>(FanGuard::maximum_run_ms), error);
  xSemaphoreGive(mutex);
  httpd_resp_set_type(request, "application/json");
  httpd_resp_set_hdr(request, "Cache-Control", "no-store");
  return httpd_resp_send(request, payload, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t reject(httpd_req_t *request, const char *status, const char *error) {
  xSemaphoreTake(mutex, portMAX_DELAY);
  guard.stop(error);
  apply();
  xSemaphoreGive(mutex);
  httpd_resp_set_status(request, status);
  return state(request, error);
}

static esp_err_t status_handler(httpd_req_t *request) {
  return state(request);
}

static esp_err_t post_handler(httpd_req_t *request) {
  char type[64] = {};
  httpd_req_get_hdr_value_str(request, "Content-Type", type, sizeof(type));
  if (strcmp(type, "application/json") || request->content_len == 0 || request->content_len > 192) {
    return reject(request, "400 Bad Request", "invalid_json_request");
  }
  char payload[193] = {};
  unsigned received = 0;
  while (received < request->content_len) {
    const int amount = httpd_req_recv(request, payload + received, request->content_len - received);
    if (amount <= 0) {
      return reject(request, "400 Bad Request", "incomplete_request");
    }
    received += amount;
  }
  cJSON *body = memchr(payload, '\0', received) ? nullptr
    : cJSON_ParseWithLengthOpts(payload, received + 1, nullptr, true);
  const bool stopping = strcmp(request->uri, "/api/fan/stop") == 0;
  const bool arming = strcmp(request->uri, "/api/fan/arm") == 0;
  int token = 0, order = 0;
  bool valid = cJSON_IsObject(body) && cJSON_GetArraySize(body) == (stopping || arming ? 0 : 2);
  if (valid && !stopping && !arming) {
    valid = manual_motor::integer_field(body, "session", 1, 2000000000, token) &&
      manual_motor::integer_field(body, "sequence", 1, 2000000000, order);
  }
  cJSON_Delete(body);
  if (!valid) {
    return reject(request, "400 Bad Request", "invalid_command_fields");
  }
  bool accepted = true;
  xSemaphoreTake(mutex, portMAX_DELAY);
  if (stopping) {
    guard.stop();
  } else if (!ready) {
    accepted = false;
  } else if (arming) {
    accepted = guard.arm(millis());
  } else {
    accepted = guard.run(token, order, millis());
  }
  apply();
  xSemaphoreGive(mutex);
  if (!accepted) {
    httpd_resp_set_status(request, "409 Conflict");
  }
  return state(request, accepted ? "" : "command_rejected");
}

static esp_err_t page_handler(httpd_req_t *request) {
  httpd_resp_set_type(request, "text/html; charset=utf-8");
  httpd_resp_set_hdr(request, "Cache-Control", "no-store");
  const char banner[] = "<div style='position:sticky;top:0;background:#101923;padding:8px'>"
    "相机 + 双电机 + 独立风扇 <button id='stopAll' class='stop'>停止电机和风扇</button></div>";
  const char *ending = strstr(manual_motor::motor_page, "</html>");
  if (!ending) {
    return ESP_FAIL;
  }
  esp_err_t result = httpd_resp_send_chunk(request, manual_motor::motor_page,
    ending - manual_motor::motor_page);
  if (result == ESP_OK) result = httpd_resp_send_chunk(request, banner, HTTPD_RESP_USE_STRLEN);
  if (result == ESP_OK) result = httpd_resp_send_chunk(request, fan_panel, HTTPD_RESP_USE_STRLEN);
  if (result == ESP_OK) result = httpd_resp_send_chunk(request, "</html>", HTTPD_RESP_USE_STRLEN);
  if (result == ESP_OK) result = httpd_resp_send_chunk(request, nullptr, 0);
  return result;
}

static esp_err_t register_routes(httpd_handle_t server) {
  if (!mutex) {
    return ESP_ERR_NO_MEM;
  }
  esp_err_t result = httpd_unregister_uri_handler(server, "/", HTTP_GET);
  const httpd_uri_t routes[] = {
    {.uri = "/", .method = HTTP_GET, .handler = page_handler, .user_ctx = nullptr},
    {.uri = "/api/fan/status", .method = HTTP_GET, .handler = status_handler, .user_ctx = nullptr},
    {.uri = "/api/fan/arm", .method = HTTP_POST, .handler = post_handler, .user_ctx = nullptr},
    {.uri = "/api/fan/run", .method = HTTP_POST, .handler = post_handler, .user_ctx = nullptr},
    {.uri = "/api/fan/stop", .method = HTTP_POST, .handler = post_handler, .user_ctx = nullptr},
  };
  for (const auto &route : routes) {
    if (result != ESP_OK) break;
    result = httpd_register_uri_handler(server, &route);
  }
  if (result != ESP_OK) {
    xSemaphoreTake(mutex, portMAX_DELAY);
    guard.stop("fan_routes_failed");
    ready = false;
    disabled_reason = "fan_routes_failed";
    apply();
    xSemaphoreGive(mutex);
  }
  return result;
}

}
