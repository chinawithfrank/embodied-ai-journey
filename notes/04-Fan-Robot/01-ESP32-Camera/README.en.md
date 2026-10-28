[← Fan Robot](../README.en.md) · [Home](../../../README.en.md) · [中文](README.md) | **English**

# 01 · ESP32-S3 and OV2640: First Eyes

## Why start with capture, not a model?

My tennis-ball detector used a computer webcam. On a physical robot, a frame first has to reach the microcontroller, then travel to the computer. Before making a robot follow anything, I want to see a moving hand in the browser, save an actual photograph, and understand which part failed when the image disappears.

This experiment provides camera firmware and a Python client. It does **not** implement hand recognition, distance estimation, motor control, fan control, or reinforcement learning.

## Hardware and an important limitation

The board was described as **ESP32-S3 N16R8**. Although the initial message mentioned OV5640, the user subsequently confirmed **OV2640**. The firmware can identify either sensor, but neither a sensor name nor N16R8 specifies a connector pinout.

The initial OV5640 product pictures were corrected by the user. The actual module is marked **BYDZ / OV2640** on the front and **BY-OV2640-V1.5** on the back. It includes the matching camera connector and peripheral circuitry; install the camera ribbon in that connector. The earlier concern about an OV5640-branded carrier is no longer applicable. Keep power off while installing the camera and wiring the module.

The corrected pictures show a24-contact camera connector, a2×9 header, and a rear component marked Y1. The product schematic supplied later explicitly identifies **Y1 as24MHz**, with its output on pin3 routed through R1 to SEN-MCLK and camera connector P1 pin13 MCLK. This confirms a carrier-provided clock, not an ESP32-generated clock. Internal regulators derive2.8V and1.2V from the module's3.3V input; do not wire these internal rails separately to the ESP32.

![User-supplied module schematic](images/by_ov2640_schematic.png)

![User-supplied dimensions and header layout](images/by_ov2640_layout.png)

The user has verified8388608 bytes of PSRAM, a working access point, and actual browser video after enabling capture. Python snapshots and extended stability still need separate verification. With the component side facing the viewer and the header at the bottom, the visible labels read left to right:

```text
Row nearer the lens: GND SCL SDA  D0  D2 D4 D6 PCLK PWDN
Row farther away:   3V3 VS  HREF RST D1 D3 D5 D7   FLASH
```

There is **no XCLK pin on this header**. FLASH is associated with illumination, not XCLK or the flash-memory interface; leave it disconnected. VS means VSYNC and RST means RESET. The 3V3 label indicates a3.3V supply connection, not5V; verify carrier/lens compatibility and supply capacity first. The view reverses when inspecting the back of the board.

The first GPIO map below remains **proposed manual wiring for an external-clock DVP breakout**, included as a comparison. The second configuration is for this **BY-OV2640-V1.5** module with its schematic-confirmed24MHz clock. Do not transfer that frequency to unrelated boards. MIPI and SPI/FIFO modules cannot simply use this firmware.

Disconnect the XiaoZhi kit's screen, microphone, amplifier, and other peripherals during this first experiment. Leave motors and the fan disconnected. Uploading replaces the existing firmware: keep its recovery procedure if you want to restore XiaoZhi later.

## How the image travels

```text
OV2640 → 8-bit DVP → ESP32-S3 JPEG buffers in PSRAM
                              ↓
                 HTTP snapshot / MJPEG stream
                              ↓
                     Browser or Python
```

SCCB configures the camera; it does not carry the full image. DVP data and synchronization signals carry frames. JPEG reduces transport bandwidth. MJPEG sends successive JPEG images to a browser. This is a network camera, not a USB UVC device that automatically becomes `/dev/video0`.

## Configure and wire

From the repository root:

```bash
cd ros_ws/src/fan_robot
cp -i firmware/esp32_camera/camera_config.by_ov2640_v15.example.h \
      firmware/esp32_camera/camera_config.local.h
```

The local header is ignored by Git. Firmware prefers it over the example. The interactive copy asks before overwriting a local header; preserve your credentials and edits. The board-specific example has the confirmed24MHz settings but deliberately retains `wiring_confirmed = false` until each reader checks their own wiring. Without a local header, firmware still falls back to the protected generic external-clock example.

For a **verified, separately wired DVP module**, the proposed mapping is:

| Camera signal | ESP32-S3 GPIO |
|---|---:|
| D0/Y2, D1/Y3, D2/Y4, D3/Y5 | 4, 5, 6, 7 |
| D4/Y6, D5/Y7, D6/Y8, D7/Y9 | 8, 9, 10, 11 |
| XCLK | 15 |
| PCLK | 13 |
| VSYNC | 16 |
| HREF | 17 |
| SIOD/SDA | 18 |
| SIOC/SCL | 21 |
| PWDN | 12 |
| RESET/RST | 14 |
| GND | GND |
| Module power | Confirm using its schematic; do not infer from the product title |

Use GPIO labels, not physical header positions. Confirm whether alternative camera labels actually mean Y2–Y9 before translating them. Keep connections short and connect only with power off. A module accepting 5V power does not imply 5V-compatible GPIO. A bare image sensor has additional power requirements.

The proposed map avoids native USB GPIO19/20 and the usual memory/boot-strapping areas, but still needs checking against the actual board. Do not freely allocate GPIO26–37 on an N16R8 module. Board-mounted camera connectors require their own schematic mapping instead of this table. If the camera provides its own oscillator, do not drive an existing clock output.

The pictured18-pin carrier has no XCLK header pin: **do not connect GPIO15 to FLASH, PCLK, or another arbitrarily chosen contact**.

Set `wiring_confirmed = true` only after verifying and completing the wiring. Set PWDN or RESET to `-1` only if the module circuitry already handles that signal correctly, not merely because it is unknown.

### BY-OV2640-V1.5 onboard24MHz clock: the current configuration

The provided schematic now confirms both the24MHz frequency and its connection to the camera. GPIO15 is not used to generate a clock for this module.

Once confirmed, the candidate GPIO assignments remain the same for D0–D7, SDA/SCL, VS/HREF/PCLK, RST, and PWDN. GND connects to ground; 3V3 requires a verified3.3V supply with sufficient capacity. Leave FLASH disconnected and omit the GPIO15 clock connection.

Choose the other template from `ros_ws/src/fan_robot`:

```bash
cp -i firmware/esp32_camera/camera_config.by_ov2640_v15.example.h \
      firmware/esp32_camera/camera_config.local.h
```

The board-specific template sets `xclk_pin = -1`, `onboard_clock_confirmed = true`, and `xclk_frequency_hz = 24000000`, while leaving wiring confirmation false for other readers. After wiring, the local configuration should be:

```cpp
constexpr bool wiring_confirmed = true;
constexpr bool onboard_clock_confirmed = true;
constexpr int xclk_frequency_hz = 24000000;
constexpr int xclk_pin = -1;
```

The user's existing private local header has been updated to these values without changing credentials or pin assignments. **Recompile and upload for the board to use the new settings.** The generic `camera_config.onboard_clock.example.h` remains protected and unconfigured for unknown hardware; it is no longer the recommended template for this known module.

Disabling the output pin does **not** mean passing a zero frequency to the driver: its internal calculations still use this value. Firmware rejects an unconfirmed clock or a nonpositive frequency before camera initialization. Old local headers also need `constexpr bool onboard_clock_confirmed = false;` in `camera_settings`; false remains correct when the ESP32 supplies XCLK.

The frequency and route are established by the user-supplied product schematic above. The separate software behavior is based on Espressif's [camera initialization](https://github.com/espressif/esp32-camera/blob/master/driver/esp_camera.c) and [S3 camera backend](https://github.com/espressif/esp32-camera/blob/master/target/esp32s3/ll_cam.c). Hardware and driver evidence answer different questions.

## Build and upload

1. Install Arduino IDE 2 and add the stable Espressif board index:

   ```text
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```

2. Install **esp32 by Espressif Systems**. The build target for this experiment is **3.3.12**. Its camera driver is bundled; do not install an unrelated library to obtain `esp_camera.h`.
3. Open `firmware/esp32_camera/esp32_camera.ino` without renaming the sketch directory.
4. For a generic ESP32-S3-WROOM-1-N16R8 board, select `ESP32S3 Dev Module`, `Flash Size = 16MB`, `PSRAM = OPI PSRAM`, and an appropriate partition scheme. Prefer manufacturer settings for specialized boards.
5. For native USB, configure USB CDC as required by the board. A USB-UART bridge is a different interface; select the corresponding serial port. Use 115200 for the serial monitor and reduce upload speed if necessary.
6. Upload and reset. If bootloader entry fails, hold BOOT, tap RESET, release BOOT, and retry the upload.

With wiring unconfirmed, the expected status is `wiring_not_confirmed`. This verifies only the serial/network/web portion, not the camera.

The firmware is Arduino C++; the computer client is Python. Ordinary MicroPython is not assumed to contain a camera driver. No ROS2 build is needed. `firmware/COLCON_IGNORE` prevents embedded sources from being mistaken for ROS2 packages.

## Browser experiment

The default is a password-protected local access point:

```text
SSID: FanRobot-Camera
Password: fanrobot123
Page: http://192.168.4.1/
```

Keep the connection even if the device reports no Internet. The password is public experiment configuration; change it locally if needed. Disable interfering proxies/VPNs or automatic mobile-network switching while troubleshooting.

| Endpoint | Purpose |
|---|---|
| `/` on port80 | Preview and diagnostic page |
| `/health` on port80 | Initialization status, sensor identity, memory |
| `/capture` on port80 | One JPEG image |
| `/stream` on port81 | MJPEG video |

After enabling and uploading, serial output should show `Camera clock: onboard, 24000000 Hz (XCLK GPIO -1)`. Successful initialization should additionally show `Camera ready: OV2640` and `Camera status: ready`. The `/health` response includes `xclk_source: onboard` and `xclk_frequency_hz: 24000000` to identify stale firmware/configuration. These are configuration values, not physical frequency measurements.

Use one video viewer at a time. Stop browser video before Python capture. A mutex protects camera buffer access, but this is not a multi-viewer streaming service. `camera_ready` means initialization succeeded, not that every future frame is guaranteed to arrive.

For your home network, set `use_access_point = false` and fill `wifi_name`/`wifi_password` in the local header, then upload again. Use 2.4GHz Wi-Fi and a network where client devices can communicate. Read the new IP from serial output. The firmware falls back to its AP when connection times out.

The HTTP services have no login or encryption. Do not expose them to the public Internet. Avoid recording other people's private surroundings.

## Python experiment

From `ros_ws/src/fan_robot`, with the computer connected to the camera network:

```bash
python3 tools/camera_client.py --url http://192.168.4.1 check
python3 tools/camera_client.py --url http://192.168.4.1 snapshot \
  --output captures/first.jpg
```

These commands use only the Python standard library. They do not import Torch, Ultralytics, OpenCV, or ROS. `check` returns exit status1 when the camera is not ready. `snapshot` checks the response type and basic JPEG markers and refuses to overwrite a file. Open the saved photograph to verify actual image content; markers alone are not full decoding.

If Python runs on your Ubuntu GPU host while you browse on a Mac, the Ubuntu host also needs camera-network access. Use home-network mode for easier cross-machine access.

Optional desktop preview:

```bash
python3 -m venv .venv
source .venv/bin/activate
env -u PYTHONPATH python -m pip install -r tools/requirements.txt
python tools/camera_client.py --url http://192.168.4.1 view --fps 5
```

Press `s` to save the current frame, `q` to quit. Preview polls `/capture`; requested FPS is not guaranteed capture throughput. Use GUI OpenCV, not the headless package, and run in a graphical desktop session. SSH-only users can use snapshots or a browser instead.

## Acceptance and troubleshooting

Check the actual OV2640 identity, PSRAM detection, approximately one minute of updating video, a readable saved photograph, stop/restart behavior, exposure recovery, and visible latency while moving your hand. The13 simulated-HTTP client tests and one host-compiled C++ clock/profile test pass. The complete firmware compiles with Arduino-ESP32 3.3.12 and the enabled local24MHz configuration: ESP32S3 Dev Module,16MB Flash, OPI PSRAM, Hardware CDC and JTAG, CDC On Boot Enabled, and the16M Flash partition scheme. It uses approximately983KB of program storage and56.5KB of static RAM. The user uploaded it and confirmed8MB PSRAM, the AP page, and actual browser video. Python snapshots, measured frame rates, and extended capture stability still need separate checks.

| Symptom | First checks |
|---|---|
| Compilation fails with `ctags: bad CPU type in executable` | Host-tool architecture mismatch on the Mac, not camera wiring or the ESP32 target; check Rosetta |
| `wiring_not_confirmed` | Local header, wiring confirmation flag, upload |
| `onboard_clock_not_confirmed` | Verify the actual carrier-provided clock rather than blindly enabling the flag |
| `clock_frequency_not_confirmed` | Provide the confirmed positive frequency, even when `xclk_pin = -1` |
| `invalid_or_duplicate_gpio` | Required/duplicate GPIO assignments; software validation cannot verify physical wiring |
| `psram_not_detected` | Board identity and OPI PSRAM settings; do not simply disable the guard |
| `camera_init_failed` | Serial error code, power, SCCB, RESET/PWDN, connector orientation |
| Sensor identified but capture fails | Data order, PCLK, HREF, VSYNC, XCLK, short and reliable wiring |
| Corruption or resets | Stable power and signal quality before increasing resolution |
| Page works but video fails | Port81, another open video session, actual capture status |
| HTTP503 | Read diagnostic text; stop other viewers and check camera initialization/capture |
| Inverted image | Adjust `vertical_flip`/`horizontal_mirror` and upload |
| Blurry image | Protective film, lighting, focus; autofocus is not implemented |

The actual Mac reports `arm64`, while its installed Arduino `ctags/5.8-arduino11/ctags` is `x86_64`. A native IDE can still launch Intel-only helper tools. Follow [Arduino troubleshooting](https://support.arduino.cc/hc/en-us/articles/7765785712156-Error-bad-CPU-type-in-executable-on-macOS) and [Apple's instructions](https://support.apple.com/102527): run `softwareupdate --install-rosetta` in Terminal, review the license prompt yourself, wait for installation, then fully quit and reopen the IDE before compiling. Installation and successful recompilation are not claimed here. If it fails, keep the output for diagnosis instead of deleting Arduino15 or substituting an arbitrary ctags binary.

Default capture is 640×480 JPEG with PSRAM and a100ms streaming interval. The external-clock template uses20MHz; the onboard-clock template requires the confirmed carrier frequency. Reducing the interval does not guarantee a higher frame rate. Later servo code must not reuse camera GPIOs or an active camera-clock LEDC timer/channel.

The next experiment is now [offline hand detection on ESP32](../02-Offline-Hand-Detection/README.en.md), superseding the earlier colored-balloon baseline and computer-side tennis-ball proposal. It uses ESP-IDF and an on-device model, preserves the original sketch for rollback, and keeps the proven wiring. Validate boxes, center offsets, target loss, and disconnected operation before adding any actuators. Pixels are not physical distance, centered hands do not prove airflow contact, and pretrained detection is not reinforcement learning.

Driver references: [Espressif camera driver](https://github.com/espressif/esp32-camera), [Arduino-ESP32 installation](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html), [Flash/PSRAM configuration](https://docs.espressif.com/projects/esp-idf/en/v5.1/esp32s3/api-guides/flash_psram_config.html).
