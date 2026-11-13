#pragma once
#include "driver/gpio.h"
#include "safe_levels.hpp"
#include "../../../esp32_motor_manual/motor_guard.hpp"
#if __has_include("../../../esp32_motor_manual/motor_config.local.h")
#include "../../../esp32_motor_manual/motor_config.local.h"
#else
#include "../../../esp32_motor_manual/motor_config.example.h"
#endif
#if __has_include("../../../esp32_fan_manual/fan_config.local.h")
#include "../../../esp32_fan_manual/fan_config.local.h"
#else
#include "../../../esp32_fan_manual/fan_config.example.h"
#endif
namespace output_safety {
static bool initialized = false;
static bool valid_pins() {
    const int pins[] = {motor_settings::input_pins[0], motor_settings::input_pins[1],
        motor_settings::input_pins[2], motor_settings::input_pins[3], fan_settings::control_pin};
    const int reserved[] = {camera_settings::data_pins[0],camera_settings::data_pins[1],
        camera_settings::data_pins[2],camera_settings::data_pins[3],camera_settings::data_pins[4],
        camera_settings::data_pins[5],camera_settings::data_pins[6],camera_settings::data_pins[7],
        camera_settings::xclk_pin,camera_settings::pclk_pin,camera_settings::vsync_pin,
        camera_settings::href_pin,camera_settings::sda_pin,camera_settings::scl_pin,
        camera_settings::reset_pin,camera_settings::power_down_pin,
        0,3,19,20,26,27,28,29,30,31,32,33,34,35,36,37,43,44,45,46,48};
    if (manual_motor::motor_pins_conflict(pins,5,reserved,sizeof(reserved)/sizeof(reserved[0]))) return false;
    for (int pin : pins) if (!GPIO_IS_VALID_OUTPUT_GPIO(pin)) return false;
    // Current wiring uses J1 to hold DRV8833 awake. Fail closed for unsupported variants.
    return motor_settings::sleep_pin == -1 && motor_settings::fault_pin == -1;
}

struct Gpio {
    bool latch(int pin, int level) {
        return gpio_set_level(static_cast<gpio_num_t>(pin), level) == ESP_OK;
    }
    bool output(int pin, int level) {
        gpio_config_t config = {};
        config.pin_bit_mask = 1ULL << pin;
        config.mode = GPIO_MODE_OUTPUT;
        config.pull_down_en = level ? GPIO_PULLDOWN_DISABLE : GPIO_PULLDOWN_ENABLE;
        config.pull_up_en = level ? GPIO_PULLUP_ENABLE : GPIO_PULLUP_DISABLE;
        return gpio_config(&config) == ESP_OK;
    }
};
// Called before camera/model/mutex allocation. Permission to move never gates stopping.
static bool initialize() {
    if (!valid_pins()) return false; // Never drive camera/USB/storage or conflicting pins.
    Gpio gpio;
    bool ok = true;
    if (motor_settings::wiring_confirmed) {
        const int low[] = {0, 0, 0, 0};
        ok = robot::safe_levels(gpio, motor_settings::input_pins, low, 4) && ok;
    }
    if (fan_settings::wiring_confirmed) {
        const int pin[] = {fan_settings::control_pin};
        const int off[] = {!fan_settings::active_high};
        ok = robot::safe_levels(gpio, pin, off, 1) && ok;
    }
    initialized = ok;
    return ok;
}
} // namespace output_safety
