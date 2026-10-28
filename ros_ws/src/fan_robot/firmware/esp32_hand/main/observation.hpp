#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>

struct HandObservation {
    bool found = false;
    float score = 0;
    int left = 0;
    int top = 0;
    int right = 0;
    int bottom = 0;
    int width = 320;
    int height = 240;
    float center_x = 0;
    float center_y = 0;
    float error_x = 0;
    float error_y = 0;
    uint32_t frame_id = 0;
    int64_t captured_us = 0;
    int64_t processing_us = 0;
    const char *status = "waiting";
};

inline bool consider_hand(HandObservation &observation, float score,
                          int left, int top, int right, int bottom, float threshold) {
    if (!std::isfinite(score) || score < threshold || score > 1 ||
        (observation.found && score <= observation.score) ||
        observation.width < 2 || observation.height < 2) {
        return false;
    }
    left = std::max(0, left);
    top = std::max(0, top);
    right = std::min(observation.width - 1, right);
    bottom = std::min(observation.height - 1, bottom);
    if (right <= left || bottom <= top) {
        return false;
    }
    observation.found = true;
    observation.score = score;
    observation.left = left;
    observation.top = top;
    observation.right = right;
    observation.bottom = bottom;
    observation.center_x = (left + right) / 2.0f;
    observation.center_y = (top + bottom) / 2.0f;
    observation.error_x = 2 * observation.center_x / (observation.width - 1) - 1;
    observation.error_y = 2 * observation.center_y / (observation.height - 1) - 1;
    observation.status = "detected";
    return true;
}

inline HandObservation fresh_observation(HandObservation observation, int64_t now_us) {
    if (observation.captured_us > 0 && now_us - observation.captured_us > 3000000) {
        observation.found = false;
        observation.score = 0;
        observation.center_x = observation.center_y = 0;
        observation.error_x = observation.error_y = 0;
        observation.left = observation.top = observation.right = observation.bottom = 0;
        observation.status = "stale";
    }
    return observation;
}
