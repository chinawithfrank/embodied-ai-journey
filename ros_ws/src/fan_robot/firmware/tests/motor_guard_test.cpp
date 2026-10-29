#include <cassert>
#include <cstring>
#include "motor_guard.hpp"

using manual_motor::MotorGuard;

static void startup_and_limits() {
  MotorGuard guard;
  assert(!guard.armed && guard.output_a == 0 && guard.output_b == 0);
  assert(!guard.drive(1, 1, 20, 0, 0));
  assert(guard.arm(10));
  assert(!guard.arm(11));
  assert(guard.drive(guard.session, 1, 20, -30, 20));
  assert(guard.output_a == 20 && guard.output_b == -30);
  assert(!guard.drive(guard.session, 2, 101, 0, 30));
  assert(!guard.armed && !guard.output_a && !guard.output_b);
  assert(guard.arm(40));
  assert(!guard.drive(guard.session, 1, 0, -101, 50));
}

static void full_range_jog() {
  MotorGuard guard;
  assert(guard.arm(0));
  assert(guard.drive(guard.session, 1, 60, -60, 10));
  assert(guard.output_a == 60 && guard.output_b == -60);
  assert(guard.drive(guard.session, 2, 80, -80, 20));
  assert(guard.output_a == 80 && guard.output_b == -80);
  assert(guard.drive(guard.session, 3, 100, -100, 30));
  assert(guard.output_a == 100 && guard.output_b == -100);
  assert(guard.drive(guard.session, 4, -100, 100, 40));
  assert(!guard.output_a && !guard.output_b);
  guard.tick(139);
  assert(!guard.output_a && !guard.output_b);
  guard.tick(140);
  assert(guard.output_a == -100 && guard.output_b == 100);
  guard.tick(640);
  assert(!guard.armed && !guard.output_a && !guard.output_b);
  assert(!strcmp(guard.reason, "heartbeat_timeout"));
  assert(guard.arm(700));
  assert(guard.drive(guard.session, 1, -100, 100, 710));
  guard.stop(720);
  assert(!guard.armed && !guard.output_a && !guard.output_b);
}

static void expiry_and_replay() {
  MotorGuard guard;
  assert(guard.arm(0));
  guard.tick(4999);
  assert(guard.armed);
  guard.tick(5000);
  assert(!guard.armed && !strcmp(guard.reason, "arm_timeout"));
  assert(guard.arm(6000));
  const auto old_session = guard.session;
  assert(guard.drive(old_session, 1, 20, 20, 6100));
  guard.tick(6699);
  assert(guard.output_a == 20);
  guard.tick(6700);
  assert(!guard.armed && !strcmp(guard.reason, "heartbeat_timeout"));
  assert(!guard.drive(old_session, 2, 20, 20, 6710));
  assert(guard.arm(6720));
  assert(!guard.drive(old_session, 3, 20, 20, 6730));
  assert(!guard.armed);
  assert(guard.arm(6800));
  assert(guard.drive(guard.session, 5, 20, 20, 6810));
  assert(!guard.drive(guard.session, 4, 20, 20, 6820));
  assert(!guard.output_a && !guard.output_b);
}

static void maximum_duration() {
  MotorGuard guard;
  assert(guard.arm(0));
  for (uint32_t now = 100, order = 1; now < 3100; now += 100, ++order) {
    assert(guard.drive(guard.session, order, 100, -100, now));
  }
  guard.tick(3100);
  assert(!guard.armed && !strcmp(guard.reason, "session_timeout"));
}

static void reverse_deadtime() {
  MotorGuard guard;
  assert(guard.arm(0));
  assert(guard.drive(guard.session, 1, 20, 20, 10));
  assert(guard.drive(guard.session, 2, -20, 20, 20));
  assert(!guard.output_a && !guard.output_b);
  guard.tick(119);
  assert(!guard.output_a);
  guard.tick(120);
  assert(guard.output_a == -20 && guard.output_b == 20);
  assert(guard.drive(guard.session, 3, 0, 0, 130));
  assert(guard.drive(guard.session, 4, 20, 0, 140));
  assert(!guard.output_a);
  guard.tick(230);
  assert(guard.output_a == 20);
  guard.stop(240);
  assert(guard.arm(250));
  assert(guard.drive(guard.session, 1, -20, 0, 260));
  assert(!guard.output_a);
  guard.tick(340);
  assert(guard.output_a == -20);
}

static void clock_wrap() {
  MotorGuard guard;
  const uint32_t near_wrap = UINT32_MAX - 200;
  assert(guard.arm(near_wrap));
  assert(guard.drive(guard.session, 1, 20, 20, near_wrap + 10));
  guard.tick(100);
  assert(guard.armed);
  guard.tick(500);
  assert(!guard.armed && !guard.output_a && !guard.output_b);
}

static void pin_conflicts() {
  const int reserved[] = {4, 13, 18, 19, 20, 21, 35};
  const int safe[] = {1, 2, 38, 39, -1, -1};
  const int duplicate[] = {1, 2, 38, 1};
  const int camera[] = {1, 2, 13, 39};
  const int usb[] = {1, 2, 19, 39};
  const int psram[] = {1, 2, 35, 39};
  assert(!manual_motor::motor_pins_conflict(safe, 6, reserved, 7));
  assert(manual_motor::motor_pins_conflict(duplicate, 4, reserved, 7));
  assert(manual_motor::motor_pins_conflict(camera, 4, reserved, 7));
  assert(manual_motor::motor_pins_conflict(usb, 4, reserved, 7));
  assert(manual_motor::motor_pins_conflict(psram, 4, reserved, 7));
}

static void diagnostic_pulse() {
  MotorGuard guard;
  assert(!guard.diagnose(1, 1, 0));
  assert(guard.arm(10));
  assert(guard.diagnose(guard.session, 1, 20));
  assert(guard.output_a == 100 && guard.output_b == 0);
  guard.tick(519);
  assert(guard.output_a == 100);
  guard.tick(520);
  assert(!guard.armed && !guard.output_a && !guard.output_b);
  assert(!strcmp(guard.reason, "diagnostic_complete"));
  assert(guard.arm(600));
  assert(guard.diagnose(guard.session, 1, 610));
  assert(!guard.diagnose(guard.session, 2, 620));
  assert(!guard.armed && !guard.output_a);
  assert(guard.arm(700));
  assert(guard.diagnose(guard.session, 1, 710));
  assert(!guard.drive(guard.session, 2, 40, 0, 720));
  assert(!guard.armed && !guard.output_a);
  assert(guard.arm(800));
  assert(!guard.diagnose(guard.session - 1, 1, 810));
  assert(guard.arm(900));
  assert(!guard.diagnose(guard.session, 2, 910));
  assert(guard.arm(1000));
  assert(guard.drive(guard.session, 1, -20, 0, 1010));
  assert(!guard.diagnose(guard.session, 2, 1020));
  assert(guard.arm(1030));
  assert(guard.diagnose(guard.session, 1, 1040));
  assert(!guard.output_a);
  guard.tick(1120);
  assert(guard.output_a == 100);
  guard.stop(1130);
  assert(!guard.output_a && !guard.armed);
  assert(guard.arm(1200));
  assert(guard.drive(guard.session, 1, 20, 0, 1210));
  assert(guard.output_a == 20);
  guard.stop(1220);
  const uint32_t near_wrap = UINT32_MAX - 200;
  assert(guard.arm(near_wrap));
  assert(guard.diagnose(guard.session, 1, near_wrap));
  guard.tick(299);
  assert(!guard.armed && !guard.output_a);
}

int main() {
  full_range_jog();
  diagnostic_pulse();
  startup_and_limits();
  expiry_and_replay();
  maximum_duration();
  reverse_deadtime();
  clock_wrap();
  pin_conflicts();
}
