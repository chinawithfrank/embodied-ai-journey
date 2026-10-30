#include "../esp32_camera/camera_app.hpp"
#include "../esp32_motor_manual/motor_server.hpp"
#include "fan_server.hpp"

void setup() {
  setup_camera_app(false, true);
  manual_fan::begin();
  manual_motor::begin(manual_fan::register_routes);
}

void loop() {
  loop_camera_app();
}
