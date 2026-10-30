#pragma once

#include <cstdint>

namespace manual_fan {

class FanGuard {
public:
  static constexpr uint32_t heartbeat_ms = 1000;
  static constexpr uint32_t arm_idle_ms = 5000;
  static constexpr uint32_t maximum_run_ms = 30000;
  bool armed = false;
  bool running = false;
  uint32_t session = 0;
  uint32_t sequence = 0;
  const char *reason = "disarmed";

  bool arm(uint32_t now) {
    tick(now);
    if (armed) {
      return false;
    }
    session = session >= 2000000000 ? 1 : session + 1;
    sequence = 0;
    armed_at = now;
    armed = true;
    running = false;
    reason = "armed";
    return true;
  }

  bool run(uint32_t token, uint32_t order, uint32_t now) {
    tick(now);
    if (!armed || token != session || order <= sequence) {
      stop("rejected_command");
      return false;
    }
    if (!running) {
      started_at = now;
    }
    running = true;
    last_heartbeat = now;
    sequence = order;
    reason = "running";
    return true;
  }

  void stop(const char *why = "manual_stop") {
    armed = running = false;
    reason = why;
  }

  void tick(uint32_t now) {
    if (!armed) {
      return;
    }
    if (!running && uint32_t(now - armed_at) >= arm_idle_ms) {
      stop("arm_timeout");
    } else if (running && uint32_t(now - last_heartbeat) >= heartbeat_ms) {
      stop("heartbeat_timeout");
    } else if (running && uint32_t(now - started_at) >= maximum_run_ms) {
      stop("run_timeout");
    }
  }

private:
  uint32_t armed_at = 0;
  uint32_t started_at = 0;
  uint32_t last_heartbeat = 0;
};

}
