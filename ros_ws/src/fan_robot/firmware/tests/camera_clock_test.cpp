#include <cassert>
#include <cstring>
#include "camera_clock.h"
#include "camera_config.by_ov2640_v15.example.h"

int main() {
  static_assert(!camera_settings::wiring_confirmed, "Readers must confirm their own wiring.");
  static_assert(camera_settings::onboard_clock_confirmed, "The supplied schematic confirms Y1.");
  static_assert(camera_settings::xclk_pin == -1, "Do not drive the carrier oscillator output.");
  static_assert(camera_settings::xclk_frequency_hz == 24000000, "Y1 is 24 MHz in the schematic.");
  assert(validate_camera_clock(camera_settings::xclk_pin,
                               camera_settings::xclk_frequency_hz,
                               camera_settings::onboard_clock_confirmed) == nullptr);
  assert(validate_camera_clock(15, 20000000, false) == nullptr);
  assert(validate_camera_clock(-1, 24000000, true) == nullptr);
  assert(std::strcmp(validate_camera_clock(-1, 24000000, false),
                     "onboard_clock_not_confirmed") == 0);
  assert(std::strcmp(validate_camera_clock(-1, 0, true),
                     "clock_frequency_not_confirmed") == 0);
  assert(std::strcmp(validate_camera_clock(15, 0, false),
                     "clock_frequency_not_confirmed") == 0);
  assert(std::strcmp(validate_camera_clock(15, -20000000, false),
                     "clock_frequency_not_confirmed") == 0);
  assert(std::strcmp(validate_camera_clock(-2, 20000000, true),
                     "invalid_xclk_gpio") == 0);
}
