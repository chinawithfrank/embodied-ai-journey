#pragma once
#include "controller.hpp"
namespace autonomy_settings {
// Copy to settings.local.h only after direction/installation calibration.
constexpr bool motion_confirmed = false;
constexpr int left_sign = 1;   // Motor A is the physical LEFT track.
constexpr int right_sign = 1;  // +1 command must move this track forward.
inline robot::Config controller() {
    robot::Config config;
    config.target_size = 0.35f; // Measure sqrt(bbox_width*bbox_height/(image_width*image_height)).
    config.turn_sign = 1;      // Keep +1 after correcting the camera's 180-degree mount.
    config.turn_min_ms = 100;
    config.turn_max_ms = 350;  // Larger image error -> longer bounded turn.
    config.turn_cooldown_ms = 150;
    config.duty = 80;          // Existing hardware needed 80% to start; short pulses limit travel.
    return config;
}
}
