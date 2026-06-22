Custom ROS 2 service definitions used by the cognitive_robot package.

ROS 2 requires .srv files to live in their own ament_cmake package (hence the
separate folder and CMakeLists.txt). colcon build compiles these into the Python
classes the nodes import, e.g. `from cognitive_robot_interfaces.srv import ReadTime`.

Services defined here:
* DetectAbacus.srv  — /detect_abacus  (find the abacus in the camera view)
* DetectStation.srv — /detect_station (detect the station's ArUco marker)
* ReadTime.srv      — /read_time      (OCR the digital clock)
* RunAbacus.srv     — abacus manipulation

Do not remove this package: the CV and manipulation nodes fail to import without it.
Rebuild it with `colcon build` (not `--packages-select cognitive_robot`) whenever a
.srv file changes.