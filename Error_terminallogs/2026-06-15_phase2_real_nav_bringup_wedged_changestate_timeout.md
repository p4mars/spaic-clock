# Phase 2 Real — Nav2 navigation bringup WEDGED (change_state timeout) (2026-06-15, 15:51)

Launch: `phase2_real.launch.py` (lazy-depth + transform_tolerance=1.5s).
Symptom: `station_demo` prints `Still waiting for Nav2 action server...` forever (~5+ min), costmap never loads.
Root: the Nav2 NAVIGATION lifecycle bringup got stuck at the first node and never activated bt_navigator.

(Trimmed: removed the ~300 identical "Still waiting for Nav2 action server..." lines.)

## Smoking gun
    [lifecycle_manager_navigation]: Starting managed nodes bringup...
    [lifecycle_manager_navigation]: Configuring controller_server
    [controller_server] ... (configures local_costmap, all DWB critics) ... done
    [controller_server.rclcpp] failed to send response to /controller_server/change_state (timeout):
                               client will not receive response
=> controller_server finished Configure, but the change_state SERVICE RESPONSE back to
   lifecycle_manager_navigation was lost (timeout). The manager never advanced to
   smoother_server / planner_server / behavior_server / bt_navigator. bt_navigator never
   activated → no /navigate_to_pose action server → station_demo waits forever.
   (No "Managed nodes are active" for navigation; localization DID reach "Managed nodes are active".)

## Contrast with prior runs
- Earlier failures: localization bond abort, or nav came up slowly but DID finish.
- This run: localization OK; NAVIGATION wedged at step 1 due to a lost lifecycle service response.
  This is a DDS/IPC failure under load, not "slow bringup" — waiting does not fix it; must Ctrl-C + relaunch.

## Also seen (secondary, not the blocker)
- AMCL: `cannot publish a pose ... set the initial pose`, then on 2D Pose Estimate:
  `Failed to transform initial pose in time (extrapolation into the future ...)` — pose set kept
  failing to apply due to odom→base_link TF being slightly behind (WiFi lag). Moot since nav never started.
- Pervasive `Message Filter dropping ... queue is full` / `timestamp earlier than cache` (WiFi saturation).

## Battery question (user asked: will charging fix it?)
NO — not the cause. Nav2 runs on the LAPTOP; a lost change_state SERVICE RESPONSE is a DDS/comms issue,
not robot power. Charging doesn't hurt but won't address this.
Likely real causes: (a) leftover ROS2 processes from prior Ctrl-C causing DDS contention/duplicate nodes;
(b) WiFi/DDS saturation dropping the service reply.

## Fix before next run
1. Kill stale processes, then relaunch:
   `pkill -f ros2; pkill -f nav2; pkill -f rviz`  (wait ~3 s)  then `ros2 launch ... phase2_real.launch.py`
2. If it wedges again at controller_server Configure → DDS-over-WiFi load → get off phone hotspot or run Nav2 on robot.
