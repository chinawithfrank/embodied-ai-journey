#include <cassert>
#include <tuple>
#include <vector>
#include "autonomy/safe_levels.hpp"
struct Gpio {
    std::vector<std::tuple<char,int,int>> events;
    int fail_at = -1;
    bool latch(int pin, int value) {
        events.emplace_back('L',pin,value);
        return int(events.size()) != fail_at;
    }
    bool output(int pin, int value) {
        events.emplace_back('O',pin,value);
        return int(events.size()) != fail_at;
    }
};
int main() {
    const int pins[] = {1,2,38,39};
    const int off[] = {0,0,0,0};
    Gpio gpio;
    assert(robot::safe_levels(gpio,pins,off,4));
    assert(gpio.events.size()==12);
    for (unsigned i=0;i<4;++i) {
        assert(gpio.events[i*3] == std::make_tuple('L',pins[i],0));
        assert(gpio.events[i*3+1] == std::make_tuple('O',pins[i],0));
        assert(gpio.events[i*3+2] == std::make_tuple('L',pins[i],0));
    }
    // A failure on one output must not skip the remaining bridge inputs.
    for (int failure=1;failure<=12;++failure) {
        Gpio broken; broken.fail_at=failure;
        assert(!robot::safe_levels(broken,pins,off,4));
        assert(broken.events.size()==12);
        assert(broken.events.back()==std::make_tuple('L',39,0));
    }
    // Active-low fan must be held HIGH, not accidentally switched on at boot.
    const int fan[] = {40}, active_low_off[] = {1};
    Gpio inverted;
    assert(robot::safe_levels(inverted,fan,active_low_off,1));
    assert(inverted.events.front()==std::make_tuple('L',40,1));
    assert(inverted.events.back()==std::make_tuple('L',40,1));
}
