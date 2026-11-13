#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace robot {
// Sensor-independent contract. Size is sqrt(box area / image area), not metres.
struct Target {
    bool valid = false;
    uint32_t frame = 0;
    int64_t captured_ms = 0;
    float x = 0, y = 0, size = 0;
};
struct Command { int left = 0, right = 0; bool fan = false; };
struct Config {
    float target_size = 0.35f;
    float x_enter = 0.12f, x_exit = 0.20f;
    float size_enter = 0.04f, size_exit = 0.07f;
    float y_limit = 0.45f;
    int duty = 80;
    int turn_sign = 1;
    int pulse_ms = 100, cooldown_ms = 300, stale_ms = 1000;
    int turn_min_ms = 100, turn_max_ms = 350, turn_cooldown_ms = 150;
    int stable_frames = 3;
    bool valid() const {
        return std::isfinite(target_size) && target_size > size_exit && target_size < 1-size_exit &&
            x_enter > 0 && x_exit > x_enter && x_exit < 1 &&
            size_enter > 0 && size_exit > size_enter && y_limit > 0 && y_limit <= 1 &&
            duty >= 10 && duty <= 100 && (turn_sign == 1 || turn_sign == -1) &&
            pulse_ms > 0 && pulse_ms <= 200 && cooldown_ms >= 100 &&
            turn_min_ms > 0 && turn_max_ms >= turn_min_ms && turn_max_ms <= 400 &&
            turn_cooldown_ms >= 100 && turn_max_ms < stale_ms &&
            stale_ms >= 100 && stale_ms <= 1500 && stable_frames >= 2;
    }
};
// This gate owns arming and output expiry, independently of perception/behaviour.
class Supervisor {
public:
    bool armed = false;
    const char *reason = "disarmed";
    uint32_t session = 0;
    bool arm(int64_t now) {
        if (armed) return false;
        ++session; armed = true; deadline = now + 30000; lease = now + 1000;
        reason = "armed"; return true;
    }
    bool heartbeat(uint32_t token, int64_t now) {
        tick(now);
        if (!armed || token != session) return false;
        lease = now + 1000; return true;
    }
    void stop(const char *why = "stopped") { armed = false; reason = why; }
    void tick(int64_t now) {
        if (armed && (now >= lease || now >= deadline)) stop("lease_or_session_expired");
    }
private:
    int64_t deadline = 0, lease = 0;
};
class HandFollower {
public:
    explicit HandFollower(Config settings = {}) : cfg(settings) {}
    const char *state = "idle";
    void reset() { output = {}; stable = 0; aligned = false; settled = false;
        last_frame = 0; next_pulse = 0; pulse_end = 0; state = "idle"; }
    Command step(const Target &t, int64_t now, bool enabled) {
        if (!enabled || !cfg.valid()) { reset(); state = "disarmed"; return {}; }
        if (!t.valid || !t.frame || t.captured_ms <= 0 || now < t.captured_ms ||
            now-t.captured_ms > cfg.stale_ms || !std::isfinite(t.x) ||
            !std::isfinite(t.y) || !std::isfinite(t.size) ||
            std::abs(t.x)>1 || std::abs(t.y)>1 || t.size<=0 || t.size>1) {
            output = {}; stable = 0; aligned = settled = false; state = "waiting_hand";
            return output;
        }
        if (now >= pulse_end) output.left = output.right = 0;
        // Repeated frames cannot start another pulse or satisfy settling.
        if (t.frame == last_frame) return output;
        last_frame = t.frame;
        const bool was_moving = output.left || output.right;
        const Command previous = output;
        output = {};
        if (std::abs(t.y) > cfg.y_limit) {
            stable = 0; aligned = settled = false; state = "adjust_hand_height"; return output;
        }
        aligned = std::abs(t.x) <= (aligned ? cfg.x_exit : cfg.x_enter);
        const float distance_error = cfg.target_size-t.size;
        settled = aligned && std::abs(distance_error) <= (settled ? cfg.size_exit : cfg.size_enter);
        if (settled) {
            // Do not count an observation captured while tracks were still moving.
            if (was_moving || t.captured_ms < pulse_end) stable = 0;
            else ++stable;
            state = stable >= cfg.stable_frames ? "blowing" : "settling";
            output.fan = stable >= cfg.stable_frames;
            return output;
        }
        stable = 0;
        state = aligned ? "ranging" : "aligning";
        // A fresh observation may stop a turn early, but never extend its deadline.
        // Keep an unfinished turn only while the target remains on the same side.
        if (was_moving && !aligned && previous.left == -previous.right &&
            previous.left * ((t.x > 0 ? 1 : -1)*cfg.turn_sign) > 0) {
            output = previous;
            return output;
        }
        if (now < next_pulse || t.captured_ms < pulse_end) return output;
        if (!aligned) {
            const int turn = (t.x > 0 ? 1 : -1)*cfg.turn_sign*cfg.duty;
            output.left = turn; output.right = -turn;
        } else {
            output.left = output.right = (distance_error > 0 ? 1 : -1)*cfg.duty;
        }
        const float fraction = std::clamp((std::abs(t.x)-cfg.x_enter)/(1-cfg.x_enter), 0.0f, 1.0f);
        const int duration = aligned ? cfg.pulse_ms : cfg.turn_min_ms +
            static_cast<int>(std::lround(fraction*(cfg.turn_max_ms-cfg.turn_min_ms)));
        pulse_end = now+duration;
        next_pulse = pulse_end+(aligned ? cfg.cooldown_ms : cfg.turn_cooldown_ms);
        return output;
    }
private:
    Config cfg;
    Command output;
    uint32_t last_frame = 0;
    int stable = 0;
    bool aligned = false, settled = false;
    int64_t pulse_end = 0, next_pulse = 0;
};
} // namespace robot
