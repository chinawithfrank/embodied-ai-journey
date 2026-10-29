[← Fan robot](../README.en.md) · [中文](README.md) | **English**

# Keep the Camera Wired, Jog Two N20 Motors Manually

The camera is already working. Instead of rewiring it or immediately attempting visual following, the next small goal is to hold a browser button, turn one motor, and release the button to remove drive.

Hardware: ESP32-S3 N16R8, the existing BY-OV2640-V1.5 camera, a DRV8833 module, and two nominal6V/60rpm N20 geared motors. There is no fan output or autonomous movement.

## What Remains Intact

The new [`esp32_motor_manual`](../../../ros_ws/src/fan_robot/firmware/esp32_motor_manual) Arduino sketch preserves the camera wiring and its port80 page, `/health`, `/capture`, and port81 MJPEG stream. Camera code is shared through `camera_app.hpp`; the original camera-only sketch still builds independently. Its private pin configuration is not overwritten.

Motor controls use a separate server on port82 and an independent stop-checking task, so the heartbeat is not checked inside a long video transmission loop. Separate wiring and supplies still need physical validation: motor noise can cause camera corruption or resets.

**One ESP32 runs one firmware at a time.** This is an Arduino camera-plus-manual-motor build, not the previous ESP-IDF hand-detection build. Uploading it temporarily replaces hand detection; that project's source is unchanged and does not drive motors.

## Power Before Signals

The user has confirmed three1.5V dry cells in series, nominal4.5V, with the holder's built-in switch and known positive/negative output leads. Extra wires in the photograph belong to the switch. This is a user-confirmed wiring plan, not a measured voltage or startup-current result.

Use it first for short, unloaded single-motor tests.4.5V is below the motor's6V nominal rating and within the driver's supply range, but reliable startup—especially for both motors—depends on cell chemistry/condition, contacts, and actual current. Do not expect rated60rpm or automatically change the battery arrangement to reach6V. A current-limited bench supply would give more controlled testing if available, but the selected4.5V battery plan does not require adding the LR7843. Other readers without a supply still need one and a physical disconnect; do not draw motor power from ESP32. Before vehicle integration, verify startup/stall current and the module's thermal/current limits.

The user also has a module sold as an isolated LR7843 MOSFET switch. It is **not a power source or a buck converter**; “isolated” in its title does not mean it generates isolated power. A battery or regulated supply is still required. Leave it out of this motor experiment, particularly out of the ESP32/DRV8833 common-ground connection. Its listing could not be inspected, so terminal assignments, module current ratings, and actual isolation circuitry remain unverified. Reference: [IRLR7843 device datasheet](https://www.infineon.com/assets/row/public/documents/24/49/infineon-irlr7843-datasheet-en.pdf).

- Keep ESP32 powered by its original USB. Do not power motors from its3.3V or5V header.
- Connect the independent supply negative, driver GND, and ESP32 GND together. Route motor return current directly to its supply, not through ESP32 or thin breadboard paths.
- Do not connect motor supply positive to ESP32's3.3V or parallel it with USB5V.
- A2-cell lithium pack reaches8.4V fully charged and is not a direct supply for these6V motors.
- Provide appropriate current limiting/fusing and a physical disconnect. Web stop is not an emergency-stop system.
- Follow the module's decoupling requirements. If needed, add suitable local bulk capacitance, for example100–470µF rated at least10V, with correct polarity and ceramic decoupling. Keep motor wiring short and away from camera signals.

The driver switches motor current in response to low-power control signals. Chip supply limits and headline currents are not guaranteed capabilities of an unknown breakout board. Reference: [TI DRV8833 datasheet](https://www.ti.com/lit/ds/symlink/drv8833.pdf).

## Additional Connections Only

Disconnect USB and motor power before wiring. User-supplied front/back photographs show the header-side left column labeled IN4,IN3,GND,VCC,IN2,IN1 from top to bottom; the right column shows EEP,OUT1–OUT4,ULT. J1 and en/sleep markings are also visible. This verifies silkscreen, not jumper continuity, genuine silicon, thermal capability, or enable circuitry. The table maps conventional module names to the existing software; confirm power definitions and bridge pairing against the actual seller's schematic rather than treating a lookalike board as an electrical measurement.

| Driver signal | Connection |
|---|---|
| IN1 / IN2 (AIN1 / AIN2) | ESP32 GPIO1 / GPIO2 |
| IN3 / IN4 (BIN1 / BIN2) | ESP32 GPIO38 / GPIO39 |
| OUT1 / OUT2 (conventional A pair) | MotorA's two leads; verify pairing |
| OUT3 / OUT4 (conventional B pair) | MotorB's two leads; test one unloaded motor first |
| VCC (motor-supply VM; confirm seller documentation) | Independent motor supply positive, not ESP32's3.3V |
| GND | Independent supply negative and ESP32 GND |

These GPIO numbers avoid the existing camera, native USB19/20, internal-memory-related pins, and common boot-strapping pins. Confirm that other newly added peripherals do not occupy them.

The module instructions subsequently supplied by the user confirm OUT1/2 are controlled by IN1/2, and OUT3/4 by IN3/4. They also confirm J1 is connected by default to hold EEP high; low EEP selects sleep, and external sleep control requires disconnecting J1. ULT signals protection by going low. Keep the original J1 connection, leave EEP/ULT disconnected from ESP32, and retain `sleep_pin = -1`, `fault_pin = -1`. A lit indicator does not measure bridge output. These details apply to this module, not every DRV8833 breakout.

If an actual `nSLEEP`/`SLP` pin is exposed, consider GPIO40 with an external10kΩ pulldown and configure `sleep_pin = 40`, **after checking whether the module already hard-wires it high**. Otherwise leave `sleep_pin = -1` and verify the module's enabled configuration. External10kΩ pulldowns on all four inputs help keep them inactive during reset; chip-internal pulldowns do not establish how an unknown module is wired.

Optionally configure `nFAULT` on GPIO41 only after confirming open-drain output and a3.3V pull-up. Never connect a signal pulled up to motor voltage directly to ESP32. Default `fault_pin = -1` means software does not monitor faults. The current VCC label is now documented; if changing to another module, do not guess the meaning of unfamiliar STBY or power terminals.

The driver reverses motor terminal polarity. This experiment holds one bridge input low and applies PWM to the other. Stop means electrical coasting, not instant shaft braking. PWM percentage is neither measured RPM nor a current limit;20% does not imply12rpm.

## Configure and Upload

Keep the repository layout intact: the new sketch includes shared camera code from the adjacent directory. Save `motor_config.example.h` as `motor_config.local.h` in the new sketch directory. Retain its `#pragma once`. Only change `wiring_confirmed` to `true` after checking power, common ground, module terminals, and all four control wires. Configure optional40/41 only if actually wired and verified. Do not replace the old `camera_config.local.h`.

Defaults leave motors disabled. Even when confirmed, startup is locked and does not start rotation. Duplicate/conflicting pins are rejected; software cannot check physical wiring.

Open `firmware/esp32_motor_manual/esp32_motor_manual.ino` in Arduino IDE. Keep the proven ESP32S3 Dev Module settings:16MB Flash, OPI PSRAM, native non-TTL USB, Hardware CDC and JTAG, and USB CDC On Boot enabled. Local validation uses Arduino-ESP32 3.3.12 and the16M Flash partition scheme.

**Disconnect VM motor power before uploading.** Serial should report port82 and stopped boot outputs. `wiring_not_confirmed` is expected before enabling the private configuration; the camera can still work.

Connect to the existing camera hotspot, normally `FanRobot-Camera` / `fanrobot123`, and open [manual controls](http://192.168.4.1:82/). Custom STA/AP settings retain their existing address. The [camera page](http://192.168.4.1/) and port81 stream remain available; keep only one video viewer open.

With Arduino CLI already installed, from the repository root:

```bash
arduino-cli compile \
  --fqbn 'esp32:esp32:esp32s3:FlashSize=16M,PSRAM=opi,CDCOnBoot=cdc,USBMode=hwcdc,PartitionScheme=fatflash' \
  ros_ws/src/fan_robot/firmware/esp32_motor_manual
```

No ROS build, Python server, or Internet is needed during operation. Module photographs and the three-cell power plan are now documented; outputs remain disabled by default until actual wiring is completed and confirmed. Neither photographs nor a stated voltage establish physical acceptance.

## First Jog and Stop Checks

Secure the motor body, leave its shaft clear, and raise wheels off the desk. Never test by pinching or deliberately stalling the shaft. With USB disconnected and the holder switch off, connect the switched battery positive to VCC, battery negative to GND, and a separate logic-ground link to ESP32 GND. Keep camera wiring unchanged. Power ESP32 from its original USB, verify locked outputs, then turn on motor power. Test MotorA alone before MotorB and both together. Start at20% duty, unlock once, then hold a direction button within5 seconds for about0.2–0.5 seconds before releasing. Re-unlock before reversing. The3-second software bound is not a recommended test duration. If the motor only hums, release and inspect power, wiring, friction, and enable state instead of forcing it or commanding full power.

Each hold is limited to3 seconds. Releasing, losing page focus, hiding/closing the page, or clicking stop requests lockout. An idle unlock expires after5 seconds. Buttons represent wiring direction, not guaranteed vehicle-forward direction; mounting may require swapping one motor's leads.

Heartbeat commands are sent about150ms after each acknowledged command. An independent board task checks about every20ms and locks outputs after600ms without a fresh valid command. New unlocks have new session IDs and commands require increasing sequence numbers: late or replayed commands cannot restart a stopped session. Reversals coast both bridges for100ms, including across a stop/re-unlock sequence.

These are software bounds, not certified safety or measured mechanical stopping times. A stalled task, driver failure, or power issue can invalidate them; keep the physical power switch.

Session IDs are replay safeguards, not authentication. Use one operator on a trusted local hotspot and never forward these control endpoints to the public Internet.

## Diagnostic: Direct Wiring Works, 40% PWM Does Not

On2026-10-28, the user confirmed that MotorA turns both directly from the three-cell battery and through the driver with IN1 tied to ESP32 3V3 and IN2 low. The webpage at40% still did not start it. This establishes a working power/motor/bridge path in that test, not correct GPIO or PWM operation.

The2026-10-28 version added a separate **A forward100% diagnostic** while retaining the then-normal40% jog limit and no automatic startup boost. This diagnostic remains available. Use only this4.5V supply and6V motor, secure it unloaded, and connect MotorA alone. Disconnect battery power and USB before removing all temporary3V3/GND input-test wires and restoring IN1/2/3/4 to GPIO1/2/38/39. Preserve common ground and camera wiring. Upload the updated sketch with motor power off, then reload port82.

Turn on motor power, unlock a fresh session, and hold the diagnostic button once. It drives A forward at a constant high logic level using LEDC's idle-output facility, with B stopped. The board expires the command500ms after acceptance and locks outputs; its independent task checks about every20ms, so this is a software deadline with scheduling latency, not a precise hardware pulse. Releasing or stopping can end it earlier. Repeating the command or sending ordinary drive heartbeats cannot extend it; reversal deadtime still applies.

`POST /api/diagnose` accepts only `session` and `sequence: 1` in a fresh unlocked session; duty, duration, direction and a second motor cannot be supplied. Expiry reports `diagnostic_complete`. If it turns, the GPIO constant-drive path works in that test; PWM behavior and startup torque still need investigation. If it does not, inspect GPIO numbering, wires, firmware version and output setup. Do not repeatedly stall the motor or increase battery voltage. Keep the physical disconnect reachable.

## Diagnostic Turns: Compare60%,80% and100%

On2026-10-29, the user confirmed MotorA turns using the webpage's100% diagnostic. That verifies the software-controlled GPIO constant-drive path in this test; it does not verify intermediate PWM waveforms or prove that friction alone explains the failure at40%. EEP and camera wiring need no further changes for this comparison.

Ordinary jog controls now allow **10–100%**, still defaulting to20%, without automatic startup boost.100% uses the constant-drive path verified on MotorA; lower settings retain20kHz PWM. Release-to-stop, heartbeat expiry, reversal delay and the3-second session limit remain. The separate diagnostic keeps its500ms deadline.

Keep the current4.5V dry-cell supply and6V motor, with MotorA secured unloaded and MotorB disconnected. Turn motor power off, upload the new sketch over USB without replacing either private hardware configuration, and refresh port82 to see the100% slider maximum. Turn motor power on, select60%, unlock and hold ordinary A-forward for0.2–0.5 seconds. Stop immediately if it hums without turning. If necessary, re-unlock and compare80%, then a brief100% jog. Record startup from rest, not merely whether an already-spinning motor keeps moving. Moving the slider during a jog requests stop and requires re-unlocking.

If60% or80% starts it, PWM drives this unloaded motor at that setting; record the threshold without generalizing to other loads, batteries or MotorB. If only100% turns it, investigate PWM frequency/output and startup conditions next rather than declaring the motor broken or raising battery voltage. This change enables comparison, not a claim that low-speed control is fixed. Verify MotorA directions and stop behavior before wiring/testing MotorB, then both together.100% is continuous battery drive through the bridge, not measured RPM or hardware current limiting. Recheck ratings before changing supply or motor.

## 80% Turns: Wire MotorB and Test Both, Wheels Raised

On2026-10-29, the user confirmed ordinary MotorA jogs do not turn at60%, but do turn at80%. PWM therefore drives this motor at the tested80% setting; this is not a precise minimum-start threshold or a guarantee for MotorB or combined startup.

The existing firmware already has MotorB and both-motor buttons. No code change or re-upload is needed. The page still defaults to20%, so select80% manually for this test.

1. Turn the battery switch off and unplug USB before wiring. Keep MotorA on OUT1/OUT2 and connect MotorB's two leads across OUT3/OUT4, not from an output to GND. Verify IN3 to GPIO38 and IN4 to GPIO39; retain IN1/GPIO1 and IN2/GPIO2. Battery positive goes through the switch to VCC; battery negative, driver GND and ESP32 GND remain common. Leave EEP/ULT disconnected and J1 unchanged.
2. Secure both motors; if wheels are fitted, support the chassis with wheels raised. Power ESP32 by its original USB, verify locked outputs, then switch on motor power. Keep camera wiring unchanged.
3. Select80% on port82, unlock and briefly hold B-forward for0.2–0.5 seconds. Release and verify stop, re-unlock and test B-reverse. MotorA should remain still. Test MotorA directions and stopping separately too. If a motor hums without turning, gets hot or does not stop as expected, switch motor power off immediately.
4. Once both channels work independently, re-unlock and briefly hold **both forward**, verify both turn and stop on release, then test both reverse. Use ordinary jog buttons, not the A-only100% diagnostic. The3-second bound is a safeguard, not a recommended test duration.
5. If each works alone but not together, or the camera/ESP32 corrupts video, resets or disconnects, power down and inspect cells, switch contacts, supply wiring and common ground. Single-motor success does not establish adequate combined startup supply. Do not mask this by raising voltage or removing stop protection.
6. Keep wheels raised while checking vehicle-forward direction. Mirrored motors may require opposite electrical directions; turn battery power off and unplug USB before swapping one motor's two output leads. Do not change camera or GPIO wiring for this.

After motor tests, open one camera preview and check startup interference. MotorB, simultaneous operation, stop timing and camera coexistence remain pending user confirmation. This step changes documentation only.

## Read the Code and Status

- `motor_guard.hpp`: lockout, lease timeout, sequence/session validation, duty bounds, reversal delay.
- `motor_server.hpp`: GPIO validation, LEDC timer1/channels2–5, independent task, port82 endpoints.
- `motor_page.hpp`: hold-to-run controls and optional video; no visual-control code.
- `/api/status`: `ready` means the software path is configured, not that motor voltage, current, or RPM has been measured. `a/b` report submitted duty commands.
- `invalid_or_conflicting_motor_gpio`: check reserved camera/USB/memory pins and duplicates.
- `requires_onboard_camera_clock`: this build intentionally requires the verified carrier-clock camera profile rather than risking another XCLK scheme's shared clock source.
- `driver_fault`: only monitored when configured; power down and inspect supply, overheating, overcurrent, and wiring before trying again.

LEDC timer0/channel0 are not reconfigured. The current camera actually uses its carrier's24MHz oscillator. Reference: [Espressif LEDC configuration](https://docs.espressif.com/projects/esp-idf/en/v5.4.2/esp32s3/api-reference/peripherals/ledc.html).

On2026-10-28, Arduino-ESP32 3.3.12 successfully built the original camera entry and the new sketch, including a separately enabled validation configuration with optional SLEEP/FAULT pins. That temporary configuration was removed; repository defaults still disable motors. The private camera configuration was not modified. All16 host tests passed, including startup lockout, duty limits, heartbeat/session expiry, replay/ordering rejection, reversal delay, clock rollover, and pin conflicts. Control-page JavaScript syntax and local documentation links also passed checks.

The user completed the direct-power/manual-input checks and confirmed MotorA's webpage100% diagnostic and ordinary80% jog turn on2026-10-29;60% does not turn it. **Reversal, stop timing, MotorB, both motors together and camera coexistence remain pending.** Verify stopped startup/reset, each direction independently, release-to-stop, the3-second jog limit, the500ms diagnostic limit, Wi-Fi-loss stopping, no automatic restart after reconnect, optional fault input, simultaneous motors, and camera stability before ground driving or visual control.

The diagnostic build also compiled successfully that day with the existing private motor profile (1,009,398 program bytes;56,724 static RAM bytes). It was not flashed; neither private motor nor camera settings were changed. All16 host tests passed again, with added coverage for diagnostic expiry, rejected repeats/extensions/stale sessions, early stop, reversal delay, ordinary-jog recovery and clock rollover. Simulated page checks passed for a single diagnostic request, timeout lockout and release-to-stop. These do not measure physical GPIO levels or mechanical stopping time.

On2026-10-29, the10–100% range build compiled successfully (1,009,742 program bytes;56,724 static RAM bytes), and all16 host tests passed. Added checks cover60/80/100%, signed100% boundaries on both motors, out-of-range rejection, heartbeat/session expiry and reversal delay at full duty. Page simulations verified the20% default, unchanged60/80/100 command values, and stop requests on release, blur, slider movement and diagnostic expiry. The tools did not flash hardware or edit either private configuration. The user subsequently reported60% does not turn MotorA, while80% does.
