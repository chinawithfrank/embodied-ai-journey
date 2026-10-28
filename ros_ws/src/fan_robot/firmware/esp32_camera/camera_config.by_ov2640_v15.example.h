#pragma once

namespace camera_settings {
constexpr bool wiring_confirmed = false;
constexpr bool require_psram = true;
constexpr bool use_access_point = true;
constexpr char access_point_name[] = "FanRobot-Camera";
constexpr char access_point_password[] = "fanrobot123";
constexpr char wifi_name[] = "";
constexpr char wifi_password[] = "";
constexpr unsigned long wifi_timeout_ms = 20000;
constexpr unsigned long stream_interval_ms = 100;
constexpr bool onboard_clock_confirmed = true;
constexpr int xclk_frequency_hz = 24000000;
constexpr int jpeg_quality = 14;
constexpr bool vertical_flip = false;
constexpr bool horizontal_mirror = false;

constexpr int data_pins[] = {4, 5, 6, 7, 8, 9, 10, 11};
constexpr int xclk_pin = -1;
constexpr int pclk_pin = 13;
constexpr int vsync_pin = 16;
constexpr int href_pin = 17;
constexpr int sda_pin = 18;
constexpr int scl_pin = 21;
constexpr int power_down_pin = 12;
constexpr int reset_pin = 14;
}
