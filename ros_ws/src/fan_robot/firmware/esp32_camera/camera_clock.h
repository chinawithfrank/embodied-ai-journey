#pragma once

inline const char *validate_camera_clock(int xclk_pin, int frequency_hz,
                                        bool onboard_clock_confirmed) {
  if (xclk_pin < -1) {
    return "invalid_xclk_gpio";
  }
  if (xclk_pin == -1 && !onboard_clock_confirmed) {
    return "onboard_clock_not_confirmed";
  }
  if (frequency_hz <= 0) {
    return "clock_frequency_not_confirmed";
  }
  return nullptr;
}
