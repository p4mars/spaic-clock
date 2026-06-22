# Phase 2 Real — Mission COMPLETED but rough navigation (2026-06-15, ~15:1x)

Launch: `phase2_real.launch.py` with lazy-depth + transform_tolerance=1.5s.
Outcome: **MISSION COMPLETE** — clock read **13:20**, navigated to Station A and Station B,
abacus manipulation ran with digits [1,3,2,0]. detect_abacus at the end returned "No predictions"
(abacus not re-detected) but mission finished cleanly.

(Trimmed: removed the thousands of duplicate "Distance remaining" lines and repeated TF-error blocks.)

## What worked
- read_time: `Time found: [1, 3, 2, 0]` → `Clock detected successfully: 13:20` (camera fix holding).
- Reached Station A (`Goal succeeded`), reached Abacus/Station B (`Goal succeeded`).
- Abacus sequence: Pole 1/4 rings=1, Pole 2/4 rings=3, Pole 3/4 rings=2, Pole 4/4 rings=0 → `Abacus sequence complete`.
- `MISSION COMPLETE | Clock: 13:20`.

## The navigation errors (rough but non-fatal)
Recurring during the A→B drive and after the clock scan:
- `tf_help: Transform data too old when converting from map to odom` / `odom to map`
- `transformPoseInTargetFrame: Extrapolation Error ... Lookup would require extrapolation into the past.
   Requested time X but the earliest data is at time Y` (gap sometimes ~10 s!)
- `controller: Unable to transform robot pose into global plan's frame`
- `controller: Controller patience exceeded` → `[follow_path] Aborting handle`
- Nav2 recovery kicked in: `Running backup`, `Running spin`, `Running wait`, `clear local/global costmap`,
  `Planner loop missed its desired rate (0.12–0.19 Hz)`, `Control loop missed its desired rate`.
- Robot stalled at a fixed `Distance remaining` for long stretches, then recovered and continued.

The "extrapolation into the past" with a LARGE gap (requested ~10 s older than earliest buffered TF) means
the `map→odom` TF stopped updating for several seconds and then jumped — i.e. AMCL/TF went stale in bursts,
not just the steady ~1 s WiFi lag. transform_tolerance=1.5 s helped enough to finish, but bursts exceeded it.

## USER'S THEORY (to verify next time)
A teammate was **walking inside the mapped area** during the run. The user thinks this likely confused
localization/positioning: a moving person shows up in the laser scan, enters the costmaps as a phantom
obstacle, and can make AMCL's pose estimate jump — which would produce exactly these map→odom staleness/jump
+ extrapolation errors and trigger the controller aborts + recovery behaviors. Plan: re-run with the area
clear of people and compare. (Plausible contributor on top of the baseline WiFi-TF lag.)

## Still open
- Underlying WiFi-TF jitter (phone hotspot, ~200 ms avg / 600 ms peaks) remains the baseline cause of TF staleness.
- detect_abacus at Station B returned no predictions this run (separate from nav).
- Robust long-term fix still: real router/AP, or run Nav2 on the robot.
