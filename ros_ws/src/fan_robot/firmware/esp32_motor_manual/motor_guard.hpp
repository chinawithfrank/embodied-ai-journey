#pragma once

#include <cstdint>

namespace manual_motor {

class MotorGuard {
public:
  static constexpr int maximum_percent = 100;
  static constexpr uint32_t heartbeat_ms = 600;
  static constexpr uint32_t arm_idle_ms = 5000;
  static constexpr uint32_t maximum_session_ms = 3000;
  static constexpr uint32_t reverse_pause_ms = 100;
  static constexpr uint32_t diagnostic_ms = 500;

  bool armed = false;
  uint32_t session = 0;
  uint32_t sequence = 0;
  int output_a = 0;
  int output_b = 0;
  const char *reason = "disarmed";

  bool arm(uint32_t now) {
    tick(now);
    if (armed) {
      return false;
    }
    session = session >= 2000000000 ? 1 : session + 1;
    sequence = 0;
    diagnostic = false;
    requested_a = requested_b = output_a = output_b = 0;
    armed_at = last_heartbeat = now;
    armed = true;
    reason = "armed";
    return true;
  }

  void stop(uint32_t now, const char *why = "manual_stop") {
    if (output_a || output_b) {
      coast_at = now;
    }
    armed = false;
    requested_a = requested_b = output_a = output_b = 0;
    reason = why;
  }

  bool drive(uint32_t token, uint32_t order, int motor_a, int motor_b, uint32_t now) {
    tick(now);
    if (!armed || diagnostic || token != session || order <= sequence ||
        motor_a < -maximum_percent || motor_a > maximum_percent ||
        motor_b < -maximum_percent || motor_b > maximum_percent) {
      stop(now, "rejected_command");
      return false;
    }
    if (sequence == 0) {
      started_at = now;
    }
    sequence = order;
    last_heartbeat = now;
    requested_a = motor_a;
    requested_b = motor_b;
    tick(now);
    return true;
  }

  bool diagnose(uint32_t token, uint32_t order, uint32_t now) {
    tick(now);
    if (!armed || token != session || sequence != 0 || order != 1) {
      stop(now, "rejected_diagnostic");
      return false;
    }
    diagnostic = true;
    sequence = order;
    started_at = last_heartbeat = now;
    requested_a = 100;
    requested_b = 0;
    tick(now);
    return true;
  }

  void tick(uint32_t now) {
    if (!armed) {
      return;
    }
    if (diagnostic && uint32_t(now - started_at) >= diagnostic_ms) {
      stop(now, "diagnostic_complete");
      return;
    }
    if (sequence == 0 && uint32_t(now - armed_at) >= arm_idle_ms) {
      stop(now, "arm_timeout");
      return;
    }
    if (sequence > 0 && uint32_t(now - last_heartbeat) >= heartbeat_ms) {
      stop(now, "heartbeat_timeout");
      return;
    }
    if (sequence > 0 && uint32_t(now - started_at) >= maximum_session_ms) {
      stop(now, "session_timeout");
      return;
    }
    if ((direction_a * requested_a < 0) || (direction_b * requested_b < 0)) {
      if (output_a || output_b) {
        coast_at = now;
        output_a = output_b = 0;
      }
      if (uint32_t(now - coast_at) < reverse_pause_ms) {
        reason = "reverse_pause";
        return;
      }
    }
    if ((output_a || output_b) && !requested_a && !requested_b) {
      coast_at = now;
    }
    output_a = requested_a;
    output_b = requested_b;
    if (output_a) {
      direction_a = output_a > 0 ? 1 : -1;
    }
    if (output_b) {
      direction_b = output_b > 0 ? 1 : -1;
    }
    reason = output_a || output_b ? "running" : "armed";
  }

private:
  bool diagnostic = false;
  int requested_a = 0;
  int requested_b = 0;
  uint32_t armed_at = 0;
  uint32_t last_heartbeat = 0;
  uint32_t started_at = 0;
  uint32_t coast_at = 0;
  int direction_a = 0;
  int direction_b = 0;
};

inline bool motor_pins_conflict(const int *pins, unsigned count,
                                const int *reserved, unsigned reserved_count) {
  for (unsigned index = 0; index < count; ++index) {
    if (pins[index] < 0) {
      continue;
    }
    for (unsigned other = 0; other < index; ++other) {
      if (pins[index] == pins[other]) {
        return true;
      }
    }
    for (unsigned other = 0; other < reserved_count; ++other) {
      if (pins[index] == reserved[other]) {
        return true;
      }
    }
  }
  return false;
}

}
