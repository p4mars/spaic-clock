# Phase 2 Real — Reached Station A, /read_time camera timeout (2026-06-15, 14:36)

Launch: `phase2_real.launch.py` after full `colcon build` (RunAbacus now built) + Tier 1 (detect_station removed).
Result: **Big progress.** Mission node alive, localized, navigated to Station A successfully. Failed only at clock reading because the camera delivered no frames.

(Trimmed: removed the ~hundreds of duplicate "Distance remaining" and TF-drop lines.)

## What worked (vs previous runs)
- `station_demo` + `abacus_manipulation_node` started cleanly — no more `RunAbacus` ImportError. Full build fixed it.
- Localization came up, AMCL activated, 2D pose accepted:
    station_clock_mission: 2D pose estimate received. Pose set. Starting mission.
    station_clock_mission: Waiting 40 s for AMCL to converge before navigating...
- Navigated to Station A and SUCCEEDED:
    bt_navigator: Goal succeeded
    station_clock_mission: Successfully reached Station A.

## What failed: camera never delivered a frame for OCR
    station_clock_mission: Calling /read_time to detect the clock at Station A...
    read_time_service: Received /read_time request — starting scan.
    read_time_service: Waiting for camera frame...        (repeated ~30×, 1/s)
    read_time_service: [ERROR] Camera never became available after 30 s — aborting.
    station_clock_mission: [WARN] Clock was not detected by /read_time.
    station_clock_mission: [ERROR] Clock detection failed. Stopping mission.
        Set CONTINUE_TO_STATION_B_IF_TIME_NOT_FOUND=True to continue anyway.
- read_time subscribes `/camera/color/image_raw/compressed` — zero frames arrived in 30 s = camera-over-WiFi starvation (the same saturation; detect_abacus still streams raw depth continuously).

## Lingering (non-fatal this run)
- One early localization hiccup: `lifecycle_manager_localization: amcl unable to be reached after 4.00s by bond → Aborting bringup`, but it recovered and localized.
- TF still flaky: many `Invalid frame ID "odom"`, `timestamp earlier than cache`, RViz `queue is full`, and `map`/`base_link` "two unconnected trees" until AMCL published map→odom.

## Changes applied after this run (for next attempt)
1. `read_time_service.py`: camera-wait timeout 30 s → **120 s**.
2. `station_demo.py`: `CONTINUE_TO_STATION_B_IF_TIME_NOT_FOUND` False → **True** (proceed to B even if clock not read).
Both are band-aids; real fix = reduce camera/WiFi load (lazy depth in detect_abacus) or run CV near the camera.
