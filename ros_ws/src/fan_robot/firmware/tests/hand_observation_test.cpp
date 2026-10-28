#include <cassert>
#include <cstring>
#include <limits>
#include "observation.hpp"

int main() {
    HandObservation observation;
    observation.captured_us = 100;
    observation.status = "not_found";
    assert(!observation.found);
    assert(!consider_hand(observation, 0.49f, 10, 20, 100, 120, 0.5f));
    assert(!consider_hand(observation, std::numeric_limits<float>::quiet_NaN(),
                          10, 20, 100, 120, 0.5f));
    assert(!consider_hand(observation, 1.1f, 10, 20, 100, 120, 0.5f));
    assert(!consider_hand(observation, 0.8f, 400, 20, 500, 120, 0.5f));
    assert(!consider_hand(observation, 0.8f, 30, 30, 10, 10, 0.5f));
    assert(consider_hand(observation, 0.8f, -30, -20, 400, 300, 0.5f));
    assert(observation.left == 0 && observation.top == 0);
    assert(observation.right == 319 && observation.bottom == 239);
    assert(observation.center_x == 159.5f && observation.center_y == 119.5f);
    assert(observation.error_x == 0 && observation.error_y == 0);
    assert(!consider_hand(observation, 0.7f, 1, 1, 20, 20, 0.5f));
    assert(consider_hand(observation, 0.9f, 1, 1, 21, 21, 0.5f));
    assert(observation.center_x == 11 && observation.center_y == 11);
    assert(observation.error_x < 0 && observation.error_y < 0);
    assert(fresh_observation(observation, 3000100).found);
    HandObservation expired = fresh_observation(observation, 3000101);
    assert(!expired.found && !strcmp(expired.status, "stale"));
    assert(expired.center_x == 0 && expired.right == 0 && expired.score == 0);
    assert(observation.found);
    HandObservation missing;
    assert(!fresh_observation(missing, 9000000).found);
    assert(!strcmp(fresh_observation(missing, 9000000).status, "waiting"));
    missing.status = "capture_failed";
    assert(!strcmp(fresh_observation(missing, 9000000).status, "capture_failed"));
}
