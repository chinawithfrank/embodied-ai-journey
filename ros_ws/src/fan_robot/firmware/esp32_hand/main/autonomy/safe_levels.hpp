#pragma once
namespace robot {
// Attempt every output even after a failure. Preload latch before output enable,
// then reassert it. No arming/calibration/camera state belongs in this operation.
template<class Gpio>
bool safe_levels(Gpio &gpio, const int *pins, const int *levels, unsigned count) {
    bool ok = true;
    for (unsigned i = 0; i < count; ++i) {
        ok = gpio.latch(pins[i], levels[i]) && ok;
        ok = gpio.output(pins[i], levels[i]) && ok;
        ok = gpio.latch(pins[i], levels[i]) && ok;
    }
    return ok;
}
}
