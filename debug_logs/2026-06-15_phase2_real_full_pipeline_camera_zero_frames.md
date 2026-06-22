# Phase 2 Real — FULL pipeline ran; only camera (OCR + abacus detect) failed (2026-06-15, 14:44)

Launch: `phase2_real.launch.py`. Best run yet — whole mission executed end to end.
(Trimmed: removed the ~thousands of duplicate "Distance remaining" + TF-drop lines.)

## What worked (full pipeline)
1. Localized, AMCL active, 2D pose accepted, costmaps up.
2. Navigated to **Station A** → `bt_navigator: Goal succeeded` / `Successfully reached Station A`.
3. CONTINUE_TO_STATION_B flag worked: read_time failed but mission CONTINUED (logged `defaulting to [0,0,0,0]`).
4. Navigated to **Station B / Abacus** → `Goal succeeded` / `Successfully reached Abacus`.
5. **Abacus manipulation ran** — Pole 1..4/4, `Abacus sequence complete` (digits [0,0,0,0] = 0 rings).
6. `MISSION COMPLETE` reached (clock not found, abacus not detected, but pipeline finished).

## The ONLY remaining failure: camera delivers ZERO frames
- Station A `/read_time` (`/camera/color/image_raw/compressed`): waited FULL 120 s, never got a frame:
    read_time_service: Waiting for camera frame... (×120)
    read_time_service: [ERROR] Camera never became available after 120 s — aborting.
    station_clock_mission: /read_time did not finish within 120.0 s.
- Station B `/detect_abacus` (same): 30 s, zero frames, `Camera never became available after 30 s`.
- KEY: not "lag" anymore — ZERO frames in 120 s. Either the camera topic isn't publishing at all
  (robot-side camera node down) OR Nav2 TF/scan traffic fully starves the camera over WiFi during the run.

## Lingering (non-fatal)
- TF still flaky during nav: `Invalid frame ID "odom"`, `timestamp earlier than cache`, RViz `queue full`,
  brief `map`/`base_link` "two unconnected trees" until AMCL published map→odom. Did NOT prevent nav.
- Localization came up cleanly this run (no bond abort).

## Changes applied after this run
- `station_demo.py`: failed-clock default `[0,0,0,0]` → **`[1,2,0,1]` (12:01)** per user.
  (Earlier: read_time wait 30→120 s; CONTINUE_TO_STATION_B_IF_TIME_NOT_FOUND True — both confirmed working.)

## NEXT diagnostic (do before next run, laptop, ROS_DOMAIN_ID=4)
- `ros2 topic hz /camera/color/image_raw/compressed`  → is the camera publishing at all?
- `ros2 topic list | grep camera`                      → do camera topics exist?
- If zero when idle → camera node down on robot (no timeout helps).
- If frames when idle but zero during nav → bandwidth starvation → lazy-depth in detect_abacus, or run CV on robot.
