[← Fan Robot](../README.en.md) · [中文](README.md) | **English**

# Add Airflow Without Rewiring the Camera or Motors

MotorA now turns at80% PWM but not60%. That establishes one working PWM setting, not complete dual-motor acceptance. The next action is deliberately simple: independently switch a5V fan while retaining camera video and manual wheel controls. There is no automatic tracking or speed regulation.

## Hardware Confirmation Comes First

On2026-10-30 the user supplied photographs: a Delta AFB0405MA-A two-wire brushless fan labeled DC5V/0.10A, and an LR7843/PC817 module marked PWM/GND on the signal side and +/LOAD/- on the load side. Labels are identified, but the module's minimum supply and logic specifications remain unverified. **Fan output still defaults disabled.** The [Infineon MOSFET datasheet](https://www.infineon.com/assets/row/public/documents/24/49/infineon-irlr7843-datasheet-en.pdf) does not establish a breakout's pinout or low-voltage compatibility. Threshold voltage is not a full-load turn-on rating.

Confirm the actual module supports3.3V logic and the selected approximately4.5V load supply. If its documented range starts at6V, do not raise voltage on this5V fan to accommodate it. This photographed fan is two-wire, with no separate tachometer/PWM connection. Unlike the N20 brushed motors, do not reverse its red/black power leads to test direction: the internal electronics may be damaged.

The user chooses the existing three-cell4.5V battery for both motors and fan, branching in parallel after the switch, while retaining USB power for ESP32/camera. [Delta's corresponding series specification](https://www.delta-fan.com/Download/Spec/AFB0405MA-AF00.pdf) gives4.5–5.5V operation; the full ordering suffix/source of the actual fan is not independently verified. Nominal4.5V is already the lower edge, so depleted cells, contacts, switch/module drop and motor startup can move the fan outside that range. This is a short experimental supply choice, not guaranteed combined-load operation. Do not power the fan from GPIO,3V3 or the board's5V header. LR7843 is a switch, not a regulator. If an independent supply is later used for comparison, prefer fixed regulated5V equipment over an unmeasured adjustable module.

## Conditional Wiring, Not an Assumed Terminal Order

GPIO40 is the candidate control output. Camera pins, USB19/20 and motor IN1/2/3/4 on GPIO1/2/38/39 remain unchanged. If optional motor SLEEP already uses40, the fan is disabled by conflict validation; do not share it. Other user-added peripherals also need checking.

The observed labels map to the following low-side-switch test arrangement; active-high3.3V control and4.5V module operation still require verification:

```text
Switched battery positive -> original DRV8833 VCC, module +, fan RED
Fan BLACK                 -> module LOAD
Battery negative          -> module -, original DRV8833 GND
ESP32 GPIO40       -> module logic IN/PWM
ESP32 GND          -> module logic signal GND
```

LOAD is not supply negative. A direct fan-to-battery-negative wire bypasses switching. The existing motor ground already joins ESP32 and battery negative, so this shared-battery system cannot claim complete galvanic isolation even with a PC817. Route load currents directly back to battery negative, not through ESP32 ground wires. Keep module signal GND on ESP32 GND and preserve the original motor ground; never switch either ground path. Future separately powered configurations need their own module-specific grounding check.

Before using the module, disconnect all power, temporarily disconnect/insulate DRV8833 VCC, secure the guarded fan and briefly test it directly from the battery: red positive, black negative, about1 second. If it does not start, stop rather than reversing leads or raising voltage. Without a meter, success establishes only this startup, not voltage margin. Disconnect power again, remove direct-test leads and wire the module; do not leave a fan-negative bypass. If direct drive works but switched drive does not, investigate module low-voltage/logic compatibility and wiring instead of assuming a firmware fault.

Provide a verified default-off bias, such as a10kΩ signal pulldown for a compatible active-high input. Software pulls only apply after initialization and cannot guarantee reset/flashing behavior. Active-low inputs need the opposite bias; never feed a5V pull-up into ESP32. Disconnect all USB/battery/fan power before wiring, secure the fan with a guard, and keep wires away from blades.

## Build the Combined Firmware

Open [`esp32_fan_manual.ino`](../../../ros_ws/src/fan_robot/firmware/esp32_fan_manual/esp32_fan_manual.ino) in Arduino IDE, retaining the repository structure. It reuses the original private camera and motor headers from their original directories. Do not replace or duplicate those files.

- Camera: unchanged port80 APIs and port81 MJPEG.
- Motors: unchanged port82 APIs,10–100% jog range with20% default, diagnostics and stop safeguards.
- Fan: additional controls on that same port82 page and `/api/fan/*`; no fourth HTTP server and no extra LEDC timer/channel.

Keep the proven ESP32S3 Dev Module/16MB Flash/OPI PSRAM/native USB/Hardware CDC and JTAG/USB CDC On Boot settings. Switch both load supplies off before uploading. Without a local fan profile, the UI reports `fan_wiring_not_confirmed`, GPIO40 is untouched, and old camera/motor functions remain available.

After confirming the actual module, load supply, logic, wiring and bias, copy `fan_config.example.h` to `fan_config.local.h` in the new sketch folder:

```cpp
#pragma once
namespace fan_settings {
constexpr bool wiring_confirmed = true;
constexpr int control_pin = 40;
constexpr bool active_high = true;
}
```

This ignored private file has not been created or enabled on the user's behalf. `active_high` describes module polarity, not automatic startup. Rebuild and upload with load supplies disconnected; refreshing the browser alone does not update firmware.

```bash
arduino-cli compile \
  --fqbn 'esp32:esp32:esp32s3:FlashSize=16M,PSRAM=opi,CDCOnBoot=cdc,USBMode=hwcdc,PartitionScheme=fatflash' \
  ros_ws/src/fan_robot/firmware/esp32_fan_manual
```

One ESP32 runs one firmware at a time. Previous camera/motor sketches remain available for rollback; this Arduino build does not include the separate ESP-IDF offline hand model. Retaining software/wiring does not guarantee physical interference-free operation.

## Test Fan First, Then Combine Loads

Connect to the existing hotspot, normally `FanRobot-Camera` / `fanrobot123`, or retain the original custom network settings. Open [port82](http://192.168.4.1:82/); the added fan panel is below the retained motor controls.

1. For a fan-only module test with the shared battery, disconnect DRV8833 VCC while power is off; the shared master switch cannot independently disconnect motors. Enable battery power: the fan must remain off at boot. If it starts, disconnect power and inspect logic, LOAD bypass wiring and bias.
2. Click the fan unlock/start button, then fan stop. `running` reports commanded GPIO state, not measured RPM; blades may coast.
3. Verify30-second expiry, background/blur/page-close stopping, Wi-Fi-loss stopping and no automatic restart after reconnect/reset.
4. After fan-only checks pass, power down, restore DRV8833 VCC, raise wheels and re-enable the battery. Select the previously tested80%, test A/B individually and together, then combine them with the fan in this same page. Motor release does not end the fan lease; fan stop does not change motor commands. Individual success does not establish adequate shared startup supply.
5. The combined banner's stop-all button requests both subsystems stop. Original motor stop only stops motors; fan stop only stops the fan. Keep physical disconnects reachable.
6. Finally open one video viewer and inspect load-startup resets, disconnections or corruption. Power down to diagnose supply/wiring, rather than raising voltage, removing timeouts or rewiring the camera.

The fan first arms a fresh session, then sends increasing-sequence run heartbeats about200ms after each reply. A separate task checks about every20ms: lack of a fresh heartbeat for1 second removes drive, each run expires after30 seconds, and an unused arm expires after5 seconds. Old/repeated commands cannot restart a stopped session. These are software bounds with scheduling/network latency, not certified emergency-stop or mechanical-stopping guarantees. Session IDs are not authentication; use a trusted local network, one operator, and no public port forwarding.

## Code and Status

`fan_guard.hpp` contains the hardware-independent lease; `fan_server.hpp` validates pins, drives a digital output and extends the existing server; `fan_page.hpp` adds separate browser controls and stop-all. The old motor API fields are unchanged.

`GET /api/fan/status` reports software readiness and commanded output. JSON `POST /api/fan/arm` and `stop` require `{}`; `run` requires only current `session` and increasing `sequence`. Invalid commands lock out the fan without changing motors. `invalid_or_conflicting_fan_gpio`, `fan_gpio_error` and `fan_watchdog_failed` are reasons to inspect/fix configuration, not remove safeguards.

Implementation began on2026-10-30; module/fan photographs were subsequently received and the shared4.5V battery plan recorded. Module low-voltage compatibility, actual fan switching and coexistence remain pending. This update changes documentation only, not firmware or private enable files; compilation and host tests do not establish physical acceptance.

That day, Arduino-ESP32 3.3.12 successfully built the original camera (982,811 bytes), original motor sketch (1,009,694 bytes), new default-disabled combination (1,015,690 bytes) and a temporary enabled-GPIO40 profile (1,016,430 bytes;56,764 static RAM bytes). The temporary header was outside the workspace and removed afterward. No private fan file was created, neither original private configuration was changed, and no device was flashed.

All18 host tests passed. Added coverage includes boot-off/arm expiry, heartbeat/30-second expiry, stale-session/repeated-order rejection, early stop, clock rollover, motor independence, browser no-autostart, separate/all-stop, delayed arm replies and no automatic continuation after expiry. Local documentation links and whitespace checks passed. These do not measure fan RPM/current, module logic levels or physical coexistence.
