ROS 2 launch files — each starts a whole phase with one `ros2 launch` command.
Files come in Gazebo / real-robot pairs. See docs/integration.md for the full run guide.

* phase1_gazebo.launch.py / phase1_real.launch.py — Phase 1: manual map generation
  + station registration.
* phase2_gazebo.launch.py / phase2_real.launch.py — Phase 2: autonomous navigation
  to the stations.
* demo_gazebo.launch.py / demo.launch.py — just the perception (CV) services, without
  mapping or navigation (Gazebo / real robot).

Run e.g.:
    ros2 launch cognitive_robot phase1_gazebo.launch.py

Rebuild after editing a launch file (`ros2 launch` reads from install/, not src/):
    colcon build --packages-select cognitive_robot && source install/setup.bash