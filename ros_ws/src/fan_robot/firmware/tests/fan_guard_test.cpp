#include <cassert>
#include <cstring>
#include "fan_guard.hpp"
#include "motor_guard.hpp"

using manual_fan::FanGuard;

static void startup_and_lease() {
  FanGuard fan;
  assert(!fan.armed && !fan.running);
  assert(!fan.run(1, 1, 0));
  assert(fan.arm(10));
  assert(!fan.running);
  assert(!fan.arm(20));
  fan.tick(5009);
  assert(fan.armed);
  fan.tick(5010);
  assert(!fan.armed && !fan.running);
  assert(!strcmp(fan.reason, "arm_timeout"));
  assert(fan.arm(5100));
  assert(fan.run(fan.session, 1, 5110));
  assert(fan.running);
  fan.tick(6109);
  assert(fan.running);
  fan.tick(6110);
  assert(!fan.running && !fan.armed);
  assert(!strcmp(fan.reason, "heartbeat_timeout"));
}

static void replay_and_stop() {
  FanGuard fan;
  assert(fan.arm(0));
  const auto old_session = fan.session;
  assert(fan.run(old_session, 1, 10));
  assert(!fan.run(old_session, 1, 20));
  assert(!fan.running);
  assert(fan.arm(30));
  assert(!fan.run(old_session, 2, 40));
  assert(!fan.running);
  assert(fan.arm(50));
  assert(!fan.run(fan.session, 0, 60));
  assert(fan.arm(70));
  assert(fan.run(fan.session, 5, 80));
  assert(!fan.run(fan.session, 4, 90));
  assert(!fan.running);
  assert(fan.arm(100));
  assert(fan.run(fan.session, 1, 110));
  fan.stop();
  assert(!fan.armed && !fan.running);
  assert(!fan.run(fan.session, 2, 120));
}

static void maximum_duration_and_wrap() {
  FanGuard fan;
  assert(fan.arm(0));
  for (uint32_t now = 10, order = 1; now < 30010; now += 500, ++order) {
    assert(fan.run(fan.session, order, now));
    assert(!fan.arm(now));
  }
  fan.tick(30010);
  assert(!fan.running && !fan.armed);
  assert(!strcmp(fan.reason, "run_timeout"));
  const uint32_t near_wrap = UINT32_MAX - 200;
  assert(fan.arm(near_wrap));
  assert(fan.run(fan.session, 1, near_wrap + 10));
  fan.tick(near_wrap + 1009);
  assert(fan.running);
  fan.tick(near_wrap + 1010);
  assert(!fan.running);
}

static void motor_independence_and_pin_conflicts() {
  FanGuard fan;
  manual_motor::MotorGuard motor;
  assert(fan.arm(0) && motor.arm(0));
  assert(fan.run(fan.session, 1, 10));
  assert(motor.drive(motor.session, 1, 80, 80, 10));
  motor.stop(20);
  assert(fan.running);
  assert(motor.arm(30));
  assert(motor.drive(motor.session, 1, 80, 80, 40));
  fan.stop();
  assert(motor.output_a == 80 && motor.output_b == 80);
  const int fan_pin[] = {40};
  const int reserved[] = {1, 2, 38, 39, 4, 21, 19, 20, 35, -1, -1};
  assert(!manual_motor::motor_pins_conflict(fan_pin, 1, reserved, 11));
  const int motor_sleep[] = {40};
  assert(manual_motor::motor_pins_conflict(fan_pin, 1, motor_sleep, 1));
}

int main() {
  startup_and_lease();
  replay_and_stop();
  maximum_duration_and_wrap();
  motor_independence_and_pin_conflicts();
}
