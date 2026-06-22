# Phase 2 Real — Localization bond abort → AMCL never active → all goals rejected (2026-06-15, 16:29)

Launch: `phase2_real.launch.py` (lazy-depth, transform_tolerance=1.5s).
Symptom (user): "map loaded, but costmap takes ages / never loads after setting the 2D pose estimate."
Outcome: Station A goal REJECTED 30×, `Failed to reach Station A. Stopping mission.`

(Trimmed: removed hundreds of identical `global_costmap: Invalid frame ID "map"` and rviz `queue full` lines.)

## Root cause chain
    [lifecycle_manager_localization] Server map_server was unable to be reached after 4.00s by bond.
    [lifecycle_manager_localization] Failed to bring up all requested nodes. Aborting bringup.
=> localization bringup ABORTED (map_server bond heartbeat missed the 4 s window under load).
   => AMCL never activated:
        amcl: AMCL cannot publish a pose or update the transform. Please set the initial pose...
        amcl: Received initial pose request, but AMCL is not yet in the active state
   => no map->odom TF => `map` frame never exists:
        global_costmap: Timed out ... Invalid frame ID "map" ... frame does not exist   (forever)
   => global costmap can't initialize => planner can't plan => Nav2 rejects the goal:
        station_clock_mission: Goal to Station A rejected (attempt 1..30/30)
        station_clock_mission: ERROR Failed to reach Station A. Stopping mission.
   Map DID display because map_server published /map once before the abort — but localization was dead.

## Classification
Same family as the early-day failures (localization lifecycle bond timeout under load) — NOT the
nav-side change_state wedge from the 15:51 run, and NOT a code regression (the 15:1x run completed
the full mission). Intermittent: driven by system load / DDS-WiFi contention at bringup.

## What to do
1. Clean restart (kills leftover processes from prior Ctrl-C that add contention):
     pkill -f ros2; pkill -f nav2; pkill -f rviz   (LAPTOP only; ~3 s) then relaunch.
2. Before setting 2D Pose Estimate, confirm localization is up:
     watch for `[lifecycle_manager_localization]: Managed nodes are active`.
     If instead you see the `map_server ... bond ... Aborting bringup` line → Ctrl-C + relaunch
     (setting the pose is futile; AMCL is not active).
3. Charging the battery does NOT fix this (laptop-side lifecycle/DDS timing, not robot power).

## Durable fixes (unchanged)
- Reduce DDS/WiFi load: get off the phone hotspot (real router/AP) or run Nav2 on the robot.
- (Investigate) raising lifecycle_manager `bond_timeout` for localization+navigation, IF nav2_bringup
  will read it from the params yaml — uncertain in Humble; reducing load is the reliable lever.
