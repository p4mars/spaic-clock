# Phase 2 Real — Localization abort + mission crash (2026-06-15, 14:11)

Launch: `ros2 launch cognitive_robot phase2_real.launch.py` (after compressed-color pull + Tier 1 detect_station removed).
Symptom: map loads in RViz, but after "2D Pose Estimate" the costmap and pose estimate never appear; navigation cannot start. (Intermittent across runs.)

This file keeps only the diagnostic lines — the raw log had hundreds of duplicate
"Timed out waiting for transform" / "Message Filter dropping" lines, omitted here.

---

## 1. BUILD BUG — mission nodes crash on startup (root functional failure)
`station_demo` AND `abacus_manipulation_node` both die immediately:

    ImportError: cannot import name 'RunAbacus' from 'cognitive_robot_interfaces.srv'
    process has died [station_demo ... exit code 1]
    process has died [abacus_manipulation_node ... exit code 1]

Cause: `RunAbacus.srv` exists in source + is in CMakeLists.txt, but `cognitive_robot_interfaces`
was never rebuilt (README's `colcon build --packages-select cognitive_robot` does NOT rebuild interfaces).
=> The autonomous mission was never actually running.
FIX: `cd ~/mirte_ws && colcon build && source install/setup.bash`

## 2. LOCALIZATION ABORTED — AMCL never activates (why pose estimate is ignored)
    [lifecycle_manager_localization] map_server was unable to be reached after 4.00s by bond.
    [lifecycle_manager_localization] Failed to bring up all requested nodes. Aborting bringup.
    ...
    [amcl] Received initial pose request, but AMCL is not yet in the active state

map_server's bond heartbeat missed the default 4 s window (system overloaded) -> localization
bringup aborted -> AMCL never activated -> 2D pose estimate ignored -> no map->odom -> no `map`
frame -> global costmap can't initialize -> navigation can't start.
NOTE: nav2 params have NO bond_timeout set (using fragile 4.0 s default).

## 3. SYSTEM SATURATION (underlying environmental cause)
- TF dropped wholesale all run: `Message Filter dropping message ... queue is full` (odom + laser).
- Bringup glacial: controller activation alone took ~22 s.
- `controller_server`: Invalid frame ID "odom" ... frame does not exist  (odom->base_link TF not reaching it in time).
- `amcl`: dropping 'laser' ... timestamp earlier than all data in transform cache (clock/late TF).
- WiFi = iPhone hotspot, ping avg 208 ms / peak 617 ms.
- Still one continuous RAW depth stream from detect_abacus (`/camera/depth/image_raw`), plus EasyOCR + RViz on the laptop.

## Priority fixes
1. (mandatory) Full `colcon build` — fixes #1, mission node will start.
2. Reduce load so localization bond doesn't time out (#2): drop remaining CV/depth load during nav,
   and/or move Nav2 onto the robot (README fallback: `mirte_navigation minimal_navigation_launch.py`).
3. Long term: get off the phone hotspot; make CV depth subscription lazy.
