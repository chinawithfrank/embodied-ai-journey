#include "../esp32_camera/camera_app.hpp"
#include "motor_server.hpp"

void setup() {
  setup_camera_app(false);
  manual_motor::begin();
}

void loop() {
  loop_camera_app();
}
