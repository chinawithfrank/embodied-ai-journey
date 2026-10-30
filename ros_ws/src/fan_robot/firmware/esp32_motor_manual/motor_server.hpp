#pragma once

#include <cmath>
#include <cstring>
#include <driver/ledc.h>
#include <cJSON.h>
#include "motor_guard.hpp"
#include "motor_page.hpp"

#if __has_include("motor_config.local.h")
#include "motor_config.local.h"
#else
#include "motor_config.example.h"
#endif

namespace manual_motor {
static MotorGuard guard;
static SemaphoreHandle_t guard_mutex = nullptr;
static bool ready = false;
static const char *disabled_reason = "wiring_not_confirmed";
static bool awake = false;
static uint32_t wake_at = 0;
static int applied_a = 0;
static int applied_b = 0;
static const ledc_channel_t channels[] = {
  LEDC_CHANNEL_2, LEDC_CHANNEL_3, LEDC_CHANNEL_4, LEDC_CHANNEL_5,
};

static void coast() {
  for (auto channel : channels) {
    ledc_stop(LEDC_LOW_SPEED_MODE, channel, 0);
  }
  applied_a = applied_b = 0;
  if (motor_settings::sleep_pin >= 0) {
    gpio_set_level(static_cast<gpio_num_t>(motor_settings::sleep_pin), 0);
  }
  awake = false;
}

static void apply_outputs() {
  if (!ready) {
    return;
  }
  if (!guard.armed) {
    coast();
    return;
  }
  if (!awake) {
    if (motor_settings::sleep_pin >= 0) {
      gpio_set_level(static_cast<gpio_num_t>(motor_settings::sleep_pin), 1);
    }
    awake = true;
    wake_at = millis();
  }
  if (uint32_t(millis() - wake_at) < 2) {
    return;
  }
  if (motor_settings::fault_pin >= 0 &&
      gpio_get_level(static_cast<gpio_num_t>(motor_settings::fault_pin)) == 0) {
    guard.stop(millis(), "driver_fault");
    coast();
    return;
  }
  if (guard.output_a == applied_a && guard.output_b == applied_b) {
    return;
  }
  const int commands[] = {guard.output_a, guard.output_b};
  esp_err_t result = ESP_OK;
  for (unsigned motor = 0; motor < 2; ++motor) {
    const unsigned base = motor * 2;
    const unsigned active = commands[motor] >= 0 ? base : base + 1;
    const unsigned inactive = commands[motor] >= 0 ? base + 1 : base;
    result |= ledc_set_duty(LEDC_LOW_SPEED_MODE, channels[inactive], 0);
    result |= ledc_update_duty(LEDC_LOW_SPEED_MODE, channels[inactive]);
    const int percent = commands[motor] < 0 ? -commands[motor] : commands[motor];
    if (percent == 100) {
      result |= ledc_stop(LEDC_LOW_SPEED_MODE, channels[active], 1);
    } else {
      result |= ledc_set_duty(LEDC_LOW_SPEED_MODE, channels[active], percent * 255 / 100);
      result |= ledc_update_duty(LEDC_LOW_SPEED_MODE, channels[active]);
    }
  }
  if (result != ESP_OK) {
    guard.stop(millis(), "pwm_error");
    coast();
    ready = false;
    disabled_reason = "pwm_error";
    return;
  }
  applied_a = guard.output_a;
  applied_b = guard.output_b;
}

static void watchdog_task(void *) {
  while (true) {
    xSemaphoreTake(guard_mutex, portMAX_DELAY);
    guard.tick(millis());
    apply_outputs();
    xSemaphoreGive(guard_mutex);
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

static bool valid_motor_pins() {
  const int pins[] = {motor_settings::input_pins[0], motor_settings::input_pins[1],
    motor_settings::input_pins[2], motor_settings::input_pins[3],
    motor_settings::sleep_pin, motor_settings::fault_pin};
  const int reserved[] = {camera_settings::data_pins[0], camera_settings::data_pins[1],
    camera_settings::data_pins[2], camera_settings::data_pins[3],
    camera_settings::data_pins[4], camera_settings::data_pins[5],
    camera_settings::data_pins[6], camera_settings::data_pins[7],
    camera_settings::xclk_pin, camera_settings::pclk_pin, camera_settings::vsync_pin,
    camera_settings::href_pin, camera_settings::sda_pin, camera_settings::scl_pin,
    camera_settings::reset_pin, camera_settings::power_down_pin,
    0, 3, 19, 20, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
    43, 44, 45, 46, 48};
  if (motor_pins_conflict(pins, 6, reserved, sizeof(reserved) / sizeof(reserved[0]))) {
    return false;
  }
  for (unsigned index = 0; index < 6; ++index) {
    if (index >= 4 && pins[index] == -1) {
      continue;
    }
    if (!GPIO_IS_VALID_GPIO(pins[index]) ||
        (index != 5 && !GPIO_IS_VALID_OUTPUT_GPIO(pins[index]))) {
      return false;
    }
  }
  return true;
}

static void initialize_outputs() {
  if (!motor_settings::wiring_confirmed) {
    return;
  }
  if (!valid_motor_pins()) {
    disabled_reason = "invalid_or_conflicting_motor_gpio";
    return;
  }
  if (camera_settings::xclk_pin != -1 || !camera_settings::onboard_clock_confirmed) {
    disabled_reason = "requires_onboard_camera_clock";
    return;
  }
  gpio_config_t outputs = {};
  outputs.mode = GPIO_MODE_OUTPUT;
  for (int pin : motor_settings::input_pins) {
    outputs.pin_bit_mask |= 1ULL << pin;
  }
  if (motor_settings::sleep_pin >= 0) {
    outputs.pin_bit_mask |= 1ULL << motor_settings::sleep_pin;
  }
  for (int pin : motor_settings::input_pins) {
    gpio_set_level(static_cast<gpio_num_t>(pin), 0);
  }
  if (motor_settings::sleep_pin >= 0) {
    gpio_set_level(static_cast<gpio_num_t>(motor_settings::sleep_pin), 0);
  }
  if (gpio_config(&outputs) != ESP_OK) {
    disabled_reason = "gpio_setup_failed";
    return;
  }
  if (motor_settings::fault_pin >= 0) {
    gpio_config_t fault = {};
    fault.pin_bit_mask = 1ULL << motor_settings::fault_pin;
    fault.mode = GPIO_MODE_INPUT;
    fault.pull_up_en = GPIO_PULLUP_ENABLE;
    if (gpio_config(&fault) != ESP_OK) {
      disabled_reason = "fault_gpio_setup_failed";
      return;
    }
  }
  ledc_timer_config_t timer = {};
  timer.speed_mode = LEDC_LOW_SPEED_MODE;
  timer.duty_resolution = LEDC_TIMER_8_BIT;
  timer.timer_num = LEDC_TIMER_1;
  timer.freq_hz = 20000;
  timer.clk_cfg = LEDC_USE_APB_CLK;
  if (ledc_timer_config(&timer) != ESP_OK) {
    disabled_reason = "pwm_timer_setup_failed";
    return;
  }
  for (unsigned index = 0; index < 4; ++index) {
    ledc_channel_config_t channel = {};
    channel.gpio_num = motor_settings::input_pins[index];
    channel.speed_mode = LEDC_LOW_SPEED_MODE;
    channel.channel = channels[index];
    channel.timer_sel = LEDC_TIMER_1;
    if (ledc_channel_config(&channel) != ESP_OK) {
      disabled_reason = "pwm_channel_setup_failed";
      coast();
      return;
    }
  }
  ready = true;
  if (xTaskCreatePinnedToCore(watchdog_task, "motor_deadman", 4096, nullptr, 6, nullptr, 1) != pdPASS) {
    coast();
    ready = false;
    disabled_reason = "watchdog_task_failed";
  }
}

static esp_err_t send_state(httpd_req_t *request, const char *error = nullptr) {
  xSemaphoreTake(guard_mutex, portMAX_DELAY);
  guard.tick(millis());
  apply_outputs();
  char payload[512];
  snprintf(payload, sizeof(payload),
    "{\"ready\":%s,\"armed\":%s,\"session\":%lu,\"sequence\":%lu,"
    "\"a\":%d,\"b\":%d,\"reason\":\"%s\",\"maximum_percent\":%d,"
    "\"heartbeat_ms\":%lu,\"maximum_session_ms\":%lu,\"error\":\"%s\"}",
    ready ? "true" : "false", guard.armed ? "true" : "false",
    static_cast<unsigned long>(guard.session), static_cast<unsigned long>(guard.sequence),
    applied_a, applied_b, ready ? guard.reason : disabled_reason, MotorGuard::maximum_percent,
    static_cast<unsigned long>(MotorGuard::heartbeat_ms),
    static_cast<unsigned long>(MotorGuard::maximum_session_ms), error ? error : "");
  xSemaphoreGive(guard_mutex);
  httpd_resp_set_type(request, "application/json");
  httpd_resp_set_hdr(request, "Cache-Control", "no-store");
  return httpd_resp_send(request, payload, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t reject(httpd_req_t *request, const char *status, const char *error) {
  xSemaphoreTake(guard_mutex, portMAX_DELAY);
  guard.stop(millis(), error);
  apply_outputs();
  xSemaphoreGive(guard_mutex);
  httpd_resp_set_status(request, status);
  return send_state(request, error);
}

static bool integer_field(cJSON *root, const char *key, int minimum, int maximum, int &value) {
  const cJSON *field = cJSON_GetObjectItemCaseSensitive(root, key);
  if (!cJSON_IsNumber(field) || !std::isfinite(field->valuedouble) ||
      field->valuedouble != std::floor(field->valuedouble) ||
      field->valuedouble < minimum || field->valuedouble > maximum) {
    return false;
  }
  value = static_cast<int>(field->valuedouble);
  return true;
}

static esp_err_t post_handler(httpd_req_t *request) {
  char content_type[64] = {};
  httpd_req_get_hdr_value_str(request, "Content-Type", content_type, sizeof(content_type));
  if (strcmp(content_type, "application/json") || request->content_len == 0 || request->content_len > 192) {
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
  if (!cJSON_IsObject(body)) {
    cJSON_Delete(body);
    return reject(request, "400 Bad Request", "invalid_json_object");
  }
  const bool stopping = strcmp(request->uri, "/api/stop") == 0;
  const bool arming = strcmp(request->uri, "/api/arm") == 0;
  const bool diagnosing = strcmp(request->uri, "/api/diagnose") == 0;
  int token = 0, order = 0, motor_a = 0, motor_b = 0;
  bool valid = cJSON_GetArraySize(body) == (stopping || arming ? 0 : diagnosing ? 2 : 4);
  if (!stopping && !arming) {
    valid = valid && integer_field(body, "session", 1, 2000000000, token)
      && integer_field(body, "sequence", 1, 2000000000, order);
    if (!diagnosing) {
      valid = valid
        && integer_field(body, "a", -MotorGuard::maximum_percent, MotorGuard::maximum_percent, motor_a)
        && integer_field(body, "b", -MotorGuard::maximum_percent, MotorGuard::maximum_percent, motor_b);
    }
  }
  cJSON_Delete(body);
  if (!valid) {
    return reject(request, "400 Bad Request", "invalid_command_fields");
  }
  bool accepted = true;
  xSemaphoreTake(guard_mutex, portMAX_DELAY);
  if (stopping) {
    guard.stop(millis());
  } else if (!ready) {
    accepted = false;
  } else if (arming) {
    accepted = guard.arm(millis());
  } else if (diagnosing) {
    accepted = guard.diagnose(token, order, millis());
  } else {
    accepted = guard.drive(token, order, motor_a, motor_b, millis());
  }
  apply_outputs();
  xSemaphoreGive(guard_mutex);
  if (!accepted) {
    httpd_resp_set_status(request, "409 Conflict");
  }
  return send_state(request, accepted ? nullptr : "command_rejected");
}

static esp_err_t page_handler(httpd_req_t *request) {
  httpd_resp_set_type(request, "text/html; charset=utf-8");
  return httpd_resp_send(request, motor_page, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t status_handler(httpd_req_t *request) {
  return send_state(request);
}

static void begin(esp_err_t (*register_extension)(httpd_handle_t) = nullptr) {
  guard_mutex = xSemaphoreCreateMutex();
  if (!guard_mutex) {
    Serial.println("Motor controls disabled: mutex allocation failed.");
    return;
  }
  initialize_outputs();
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 82;
  config.ctrl_port += 2;
  config.stack_size = 8192;
  config.send_wait_timeout = 1;
  config.recv_wait_timeout = 1;
  config.lru_purge_enable = true;
  if (register_extension) {
    config.max_uri_handlers = 12;
  }
  httpd_handle_t server = nullptr;
  esp_err_t result = httpd_start(&server, &config);
  if (result == ESP_OK) {
    const httpd_uri_t routes[] = {
      {.uri = "/", .method = HTTP_GET, .handler = page_handler, .user_ctx = nullptr},
      {.uri = "/api/status", .method = HTTP_GET, .handler = status_handler, .user_ctx = nullptr},
      {.uri = "/api/arm", .method = HTTP_POST, .handler = post_handler, .user_ctx = nullptr},
      {.uri = "/api/drive", .method = HTTP_POST, .handler = post_handler, .user_ctx = nullptr},
      {.uri = "/api/diagnose", .method = HTTP_POST, .handler = post_handler, .user_ctx = nullptr},
      {.uri = "/api/stop", .method = HTTP_POST, .handler = post_handler, .user_ctx = nullptr},
    };
    for (const auto &route : routes) {
      result = httpd_register_uri_handler(server, &route);
      if (result != ESP_OK) {
        break;
      }
    }
  }
  if (result == ESP_OK && register_extension) {
    result = register_extension(server);
  }
  if (result != ESP_OK) {
    xSemaphoreTake(guard_mutex, portMAX_DELAY);
    guard.stop(millis(), "motor_server_failed");
    apply_outputs();
    ready = false;
    disabled_reason = "motor_server_failed";
    xSemaphoreGive(guard_mutex);
  }
  Serial.printf("Manual motor controls: port 82, %s. Boot outputs are stopped.\n",
    ready ? "ready" : disabled_reason);
}

}
