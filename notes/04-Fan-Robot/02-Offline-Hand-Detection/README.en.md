[← Fan robot](../README.en.md) · [中文](README.md) | **English**

# Find a Hand Without Sending Images to a Computer

The previous experiment delivered real OV2640 video. A person could understand it; the board could not. Instead of first recognizing a toy tennis ball on a computer, this experiment narrows the goal to finding a hand **inside the ESP32-S3**, without a computer, router, or Internet service during operation.

This is hand detection, not personal identity, finger landmarks, or gesture classification. An existing quantized model makes a practical starting point, but does not guarantee robustness in this room, under this lighting, or for every pose. No motors, servos, or fans are controlled.

## What Runs Where

```text
OV2640 JPEG 320×240 → ESP32 RGB888 decode → HandDetect → box, confidence, center, offset
                                                             ├→ serial JSON
                                                             └→ optional local AP preview
```

The model is linked into Flash. Downloads happen during initial development, never during inference. The optional browser displays results; it does not run the detector. Closing every viewer does not stop detection. A Wi-Fi-disabled build is also supported.

The new [`firmware/esp32_hand`](../../../ros_ws/src/fan_robot/firmware/esp32_hand) project uses **ESP-IDF 5.4.2**, `hand_detect` **0.1.2**, ESP-DL **3.3.4**, and `esp32-camera` **2.1.3**. It is C++ firmware, not an Arduino `.ino` or a Python/Ultralytics program. No tennis-ball weights, dataset download, SD card, or model conversion is required. The original camera sketch is preserved; flashing this project replaces the running firmware. Re-upload the original sketch to roll back.

## Wiring and Configuration

Keep the proven N16R8 + BY-OV2640-V1.5 wiring: D0–D7 = GPIO4–11, SCL21, SDA18, VS16, HREF17, PCLK13, RST14, PWDN12, 3.3V and common ground. FLASH remains disconnected. The carrier supplies 24MHz; `xclk_pin = -1`. Do not add GPIO15 or repurpose native USB GPIO19/20.

The project reuses the private `firmware/esp32_camera/camera_config.local.h` for pins, clock, and image orientation without overwriting it. For a new checkout only, copy `camera_config.by_ov2640_v15.example.h` to that filename and confirm wiring before enabling it. Existing Wi-Fi credentials are not used. The new optional AP is `FanRobot-Hand`, password `fanrobot123`. Use only on a trusted local network; do not expose it publicly.

## Install and Build

Use a fresh terminal outside the YOLO venv and ROS environment. If ESP-IDF 5.4.2 is already installed, activate it rather than reinstalling. Follow the [official prerequisites](https://docs.espressif.com/projects/esp-idf/en/v5.4.2/esp32s3/get-started/index.html) for macOS or Ubuntu.

```bash
mkdir -p ~/esp
cd ~/esp
git clone --branch v5.4.2 --depth 1 --recursive --shallow-submodules \
  https://github.com/espressif/esp-idf.git esp-idf-v5.4.2
cd esp-idf-v5.4.2
./install.sh esp32s3
. ./export.sh
idf.py --version
```

Do not clone over an existing installation. In subsequent terminals, just run `. ~/esp/esp-idf-v5.4.2/export.sh`. From the repository root:

```bash
cd ros_ws/src/fan_robot/firmware/esp32_hand
idf.py set-target esp32s3
idf.py build
```

The first build downloads dependencies and the model. Close Arduino's serial monitor. Keep the previously working native USB connection, not the TTL connector. Find the actual port with `ls /dev/cu.usbmodem*` on macOS or `ls /dev/ttyACM*` on Ubuntu. Replace the placeholder below:

```bash
idf.py -p /dev/cu.usbmodemXXXX flash monitor
```

Exit monitoring with `Ctrl+]`. If download mode fails, hold BOOT, tap RST, release BOOT, recheck the port, and retry. USB console settings are supplied by this project's configuration, not Arduino's CDC menu.

## Watch and Test

Serial lines starting with `HAND` contain JSON. A detected hand produces `found: true` and a target containing `bbox_xyxy`, `center_px`, confidence, and `error_normalized`. No hand produces `not_found`, `found: false`, and `target: null`. Multiple hands select the highest-confidence detection, not a persistent identity.

Optionally connect a phone to `FanRobot-Hand` and open [the local page](http://192.168.4.1/). A green box and red center should follow a clearly visible hand. The page uses the `X-Detection` header paired with the exact JPEG from `/capture`, rather than overlaying another frame's result. It uses no CDN or cloud. `/state` provides JSON for diagnostics. This firmware does not expose the old `/health` or port81 MJPEG endpoints; the previous Python check/view client is not its interface.

Keep the hand in focus, fully visible, and reasonably large against a simple background. Move it left/right, then remove it. Check the missing-target state rather than only celebrating one successful box.

## Prove Offline Operation

1. Disconnect all viewers while keeping serial monitoring. Detection and frame IDs must continue without computer inference.
2. Disable mobile data and use only the board's AP. A working page demonstrates no Internet dependency, though local Wi-Fi is still used for display.
3. For no radio at all, run `idf.py menuconfig` → `Fan robot: offline hand detector` and disable `Enable optional local Wi-Fi AP and browser preview`. Build and flash again.
4. There is now no hotspot or page. Serial detection must continue. With only a reliable USB supply it also runs without a computer, but a person cannot observe the result without a display or serial connection.

The minimum cycle interval defaults to400ms, an upper target of2.5 updates/second, not a promised rate. `processing_ms` includes capture, decoding, and inference; it is not a measured exposure timestamp or a full control-loop latency. Data older than3 seconds is invalidated. Capture/decode failures clear the previous target.

Pixel coordinates start at the top left. `error_x = 2 × center_x / (width - 1) - 1`, with negative left and positive right; `error_y` follows the same rule vertically. Pixels and box area are not calibrated distance. Future airflow aiming needs camera/fan calibration, emergency stops, target-loss stopping, and speed limits before any actuation.

## Reading and Troubleshooting

- `main/app_main.cpp`: camera initialization, JPEG decode, `detector.run(image)`, serial publishing, optional AP preview.
- `main/observation.hpp`: valid boxes, confidence selection, clipping, offsets, and expiration.
- `main/Kconfig.projbuild`: preview switch, confidence (default50%), and minimum cycle time.
- `sdkconfig.defaults`: S3,16MB Flash, OPI PSRAM, USB console, and Flash-resident model.
- `wiring_not_confirmed`: check the private header, not just the example template.
- `8mb_opi_psram_required`: verify hardware, PSRAM settings, and power; do not bypass the guard.
- Always `not_found`: check focus, lighting, hand size, pose, and background before modest threshold changes.
- Capture/decode errors or stale results: check wiring, supply, and timing; old coordinates are not usable.

On2026-10-27, the AP-preview firmware compiled successfully with the pinned versions, including its hand model:3,107,136 bytes (about2.96MiB), fitting the7MiB app partition. All15 host tests passed, covering the existing camera client and clock guards plus target selection, invalid detections, clipping, offsets, and expiration. Preview JavaScript syntax and local documentation links were also checked.

A separate configuration with `FAN_ENABLE_PREVIEW` disabled also built successfully:2,554,688 bytes (about2.44MiB). This verifies the radio-disabled build, not physical disconnected operation. The generated `dependencies.lock` is retained to pin the resolved transitive dependencies.

**Physical hand-detection acceptance has not been performed here.** After flashing, test entry/removal, occlusion, empty backgrounds, two hands, preview disabled, disconnected networking, sustained operation, and power cycling before adding actuators.

Sources: [official HandDetect component](https://components.espressif.com/components/espressif/hand_detect/versions/0.1.2/readme), [pinned model implementation](https://github.com/espressif/esp-dl/tree/v3.3.4/models/hand_detect), [ESP-DL setup and deployment](https://docs.espressif.com/projects/esp-dl/en/latest/getting_started/readme.html).
