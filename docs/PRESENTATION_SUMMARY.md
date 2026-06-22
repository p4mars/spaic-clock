# Cognitive Robot — Technical Summary

## 1. Project Overview

The goal of this project is to build an autonomous robotic system using the **MIRTE Master** mobile manipulator. The robot must:

1. **Navigate** to Station A (a clock display), **read the time** shown on a digital clock using computer vision, then
2. **Navigate** to Station B (an abacus), and **place the correct number of rings** on the abacus poles to represent each digit of the time it read.

The system is divided into two phases:

- **Phase 1 (Manual / Mapping):** A human operator drives the robot around the environment. While driving, SLAM builds a map. The operator positions the robot near the two stations and presses a key to register their locations. The map and station poses are saved to YAML files.
- **Phase 2 (Autonomous / Mission):** The robot localises itself on the saved map, then autonomously executes the full task: navigate → read clock → navigate → place rings.

---

## 2. System Architecture

The system consists of five main components, each implemented as a ROS2 node:

| Component | File | Role |
|---|---|---|
| Read Time Service | `read_time_service.py` | OCR-based clock reading |
| Detect Station Service | `detect_station_service.py` | ArUco marker detection + 3D pose |
| Detect Abacus Service | `detect_abacus_service.py` | ML-based abacus detection |
| Abacus Manipulation Node | `abacus_manipulation_node.py` | Arm control for ring placement |
| Station Demo (Mission) | `plan_nav/station_demo.py` | High-level mission orchestrator |

---

## 3. Method Explanations

---

### 3.1 Reading the Clock — `read_time_service.py`

**What it does:** Reads the time from a digital clock display visible in the robot's camera, using Optical Character Recognition (OCR).

**Algorithm:**
1. A camera image frame is received.
2. The frame is passed to **EasyOCR**, a deep-learning OCR model, which attempts to find text in the image matching the pattern `NN:NN` (two digits, a colon, two digits).
3. Only detections above a confidence threshold (default: 0.70) are accepted.
4. If no valid time is found in the current frame, the robot **rotates in a zigzag pattern**: first 10° left, then 20° right, then 30° left, etc. (alternating, increasing angle per iteration).
5. After each rotation, a new frame is taken and re-evaluated.
6. This repeats up to a maximum of 10 iterations. If no time is found, the service returns `found = false`.
7. Each attempt saves a **debug image** and a text file with all OCR detections to `~/ocr_debug/` on disk.

**Sensors used:**
- Front RGB camera (`/camera/color/image_raw`)

**ROS Topics / Services:**
- Subscribes to: `/camera/color/image_raw`
- Publishes to: `/mirte_base_controller/cmd_vel` (to rotate the robot during scanning)
- Exposes service: `/read_time` → returns `found` (bool) + `time_digits` (4 integers, e.g. `[1,0,2,8]` for 10:28)

**What can go wrong:**
- **Frame rate issues:** The robot runs EasyOCR on a laptop CPU over WiFi. If the camera stream lags or drops frames, the robot may be rotating while no usable image arrives.
- **Reflections / bad lighting:** OCR accuracy degrades significantly under glare, shadows, or poor contrast on the clock display.
- **False positives:** Other text in the scene (e.g. labels or stickers) could match the `NN:NN` pattern and be returned as a time reading.
- **Rotation overshoot:** The robot may rotate too far before a new image arrives, causing it to miss the clock entirely.
- **EasyOCR model load time:** The model (~200 MB) takes several seconds to load on startup. If the service is called before it finishes loading, it may fail silently.

---

### 3.2 Detecting the Stations — `detect_station_service.py`

**What it does:** Detects physical ArUco marker tags placed at the two stations and returns their 3D position and orientation relative to the robot.

**Algorithm:**
1. A colour image frame is captured.
2. **OpenCV's ArUco detector** (DICT_6X6_250 dictionary) scans the image for marker patterns.
3. Marker IDs are mapped to station names: ID 0 → "Station A", ID 1 → "Station B".
4. **Hybrid 3D measurement** is used (intentionally splitting position and rotation across two methods):
   - **Yaw (rotation):** Estimated via `cv2.solvePnP` using the known physical marker size and the camera's intrinsic parameters. This is accurate for angular estimates.
   - **Position (x, y, z):** Measured directly from the **depth camera**, not from solvePnP. The marker's pixel centre is projected into 3D space using a `PinholeCameraModel`. Depth is sampled as the **median** over a 5-pixel radius window around the centre, filtering out zero/invalid pixels. This avoids the systematic position errors that solvePnP introduces when intrinsic calibration is imperfect.
5. An annotated image with the detected marker and axes is saved to `~/aruco_photos/`.

**Sensors used:**
- Front RGB camera (`/camera/color/image_raw`)
- Depth camera (`/camera/depth/image_raw`, values in millimetres as uint16)
- Camera intrinsics (`/camera/color/camera_info`, for PinholeCameraModel projection)

**ROS Topics / Services:**
- Subscribes to: `/camera/color/image_raw`, `/camera/depth/image_raw`, `/camera/color/camera_info`
- Exposes service: `/detect_station` → returns `detected`, `marker_id`, `station_name`, `distance_m`, `x_m`, `y_m`, `z_m`, `yaw`

**What can go wrong:**
- **Marker not visible:** If the marker is partially occluded, at an extreme angle, or too far away, detection fails.
- **Depth holes:** Depth cameras produce invalid (zero) readings on shiny, transparent, or very close surfaces. The median filter mitigates this but cannot recover if most samples are invalid.
- **Only one detection returned:** If multiple ArUco markers are visible simultaneously, the system logs a warning and returns only the first one found. This could cause confusion near both stations.
- **Camera info not yet published:** The node uses a hardcoded fallback intrinsic matrix if `/camera/color/camera_info` has not yet been received. This fallback reduces accuracy.

---

### 3.3 Detecting the Abacus — `detect_abacus_service.py`

**What it does:** Detects the physical abacus (Station B setup) in the camera image using a cloud-hosted machine learning object detection model, and returns its 3D position.

**Algorithm:**
1. A colour frame is captured and resized to 320×240 pixels to reduce upload size.
2. The frame is sent over HTTP to a **Roboflow serverless inference API** using the custom-trained model `abacus_recognition_v1/3`.
3. The API returns bounding boxes with class labels and confidence scores.
4. The bounding box centre pixel is scaled back to the original image resolution.
5. The **depth camera** is sampled at the bounding box centre to get the distance.
6. The pixel + depth pair is projected to real-world 3D coordinates using `PinholeCameraModel`.
7. If confidence is below 0.70, the service returns `confidence = 0.0` (no detection).

**Sensors used:**
- Front RGB camera (`/camera/color/image_raw`)
- Depth camera (`/camera/depth/image_raw`)
- Camera intrinsics (`/camera/color/camera_info`)

**ROS Topics / Services:**
- Subscribes to: `/camera/color/image_raw`, `/camera/depth/image_raw`, `/camera/color/camera_info`
- Exposes service: `/detect_abacus` → returns `confidence`, `x`, `y` (pixel), `bbox_width`, `bbox_height`, `distance_m`, `x_m`, `y_m`

**What can go wrong:**
- **Network dependency:** The system requires an active internet connection to reach the Roboflow API. Any network interruption causes detection to fail.
- **API latency:** The round-trip to the cloud adds latency (typically 0.5–2 seconds per call). In a time-critical pipeline, this can be significant.
- **Model generalisation:** The custom model was trained on a specific abacus setup. Minor changes in lighting, angle, background, or abacus appearance can cause it to miss detections.
- **Depth at bounding box centre:** The centre of the detected bounding box may not correspond to a valid depth reading (e.g. the pole is thin and has depth holes). The sampled depth can then be incorrect.
- **No 2D-to-3D orientation estimate:** The current implementation only returns the abacus's distance and rough lateral position, not its full 3D pose. The robot therefore cannot know if it is properly aligned in front of the abacus before placing rings.

---

### 3.4 Arm Manipulation — `abacus_manipulation_node.py`

**What it does:** Controls the MIRTE Master's 4-DOF robotic arm to place rings onto the four poles of the abacus, one digit at a time.

**Algorithm:**
1. Receives a request with 4 digits (e.g. `[1, 0, 2, 8]` for 10:28).
2. For **each of the 4 abacus poles** (in order):
   - Raises the arm to a safe **transit position** (elbow fully up).
   - Rotates `shoulder_pan` to the pre-calculated angle for that pole.
   - Lowers the arm to a **working height** (elbow 90° forward).
   - For **each ring that must be placed** (determined by the digit value):
     - Raises arm to a **receive position** so an operator can physically place a ring on the arm end-effector.
     - Waits for the operator to **press Enter** on the keyboard.
     - Lowers arm back to working height over the pole.
     - Dips the shoulder slightly (**ring release motion**) to let the ring slide down onto the pole.
     - Returns to working height.
3. Returns to a **home (neutral) pose** after all poles are done.

**Sensors used:**
- None (open-loop joint trajectory control, no feedback)

**ROS Topics / Services:**
- Publishes to: `/mirte_master_arm_controller/joint_trajectory` (JointTrajectory messages)
- Exposes service: `/abacus/run_sequence` (request: `time_digits`, response: `success`)

**What can go wrong:**
- **Open-loop control:** The arm moves to pre-calculated joint angles without verifying whether rings were actually placed correctly. If the robot is slightly misaligned relative to the abacus, rings may miss the pole.
- **Fixed timing:** Each motion waits a fixed 2 seconds for the controller to reach the target. If the arm is slow (due to load or controller tuning), it may not have fully reached the target before the next command is sent.
- **Pre-calibrated pole angles:** The shoulder pan angles for the 4 poles are hardcoded constants. If the robot stops at a slightly different distance or angle relative to the abacus, all placements will be offset.
- **Operator dependency:** The current design requires a human to physically place rings on the arm for each ring placement. This makes the manipulation semi-autonomous rather than fully autonomous.

---

### 3.5 Mission Orchestration — `plan_nav/station_demo.py`

**What it does:** The high-level coordinator that sequences the entire autonomous mission from start to finish.

**Algorithm (Mission Flow):**
1. Waits for the Nav2 navigation action server to become available.
2. Waits for the operator to click **"2D Pose Estimate"** in RViz to set the robot's initial pose on the map.
3. Waits **5 seconds** for AMCL (Adaptive Monte Carlo Localisation) to converge and publish a stable `map → odom` transform.
4. Loads the saved Station A and Station B poses from YAML files on disk.
5. **Sends a navigation goal to Station A** via the Nav2 `/navigate_to_pose` action. Waits for completion.
6. **Calls `/read_time`** service. Extracts the 4 time digits from the response.
7. **Sends a navigation goal to Station B.** Waits for completion.
8. **Calls `/abacus/run_sequence`** with the 4 digits. Waits for the arm sequence to complete.
9. **Calls `/detect_abacus`** to confirm the abacus is still visible (post-verification).
10. Logs a completion summary.

**Sensors used:**
- LiDAR (`/scan`) — used by AMCL for localisation
- Wheel odometry (`/odom`) — used by AMCL for motion prediction
- All camera sensors (indirectly through the service calls above)

**ROS Topics / Services:**
- Subscribes to: `/initialpose` (to detect the RViz 2D pose estimate click)
- Action client: `/navigate_to_pose` (Nav2)
- Service clients: `/read_time`, `/detect_abacus`, `/abacus/run_sequence`

**What can go wrong:**
- **AMCL not converged:** The 5-second fixed delay after pose estimate is a heuristic. On a slow machine or in a complex map, AMCL may not have found a stable estimate yet, causing navigation to fail immediately.
- **Navigation failure:** If Nav2 cannot find a path to the goal (e.g. obstacle in the way, incorrect map), the mission stalls. Up to 5 retries with 2-second delays are attempted.
- **Time not found:** If OCR fails at Station A, the mission can either abort or continue to Station B with no digits (configurable). Continuing with no digits means no rings are placed.
- **YAML files missing:** If Phase 1 was not completed or files were not saved, the mission cannot load the station poses and crashes at startup.
- **No sensor readiness check:** The system does not verify that all cameras, the depth sensor, or the OCR service are ready before starting the mission. A slow startup can cause the first service call to fail.

---

## 4. Mapping & Localisation (SLAM + Nav2)

**Phase 1 — SLAM Toolbox (Online Async):**
- Builds a 2D occupancy grid map in real-time from the LiDAR's `/scan` topic.
- Map resolution: 5 cm per cell.
- Uses Ceres solver for pose graph optimisation.
- Minimum travel of 0.5 m or 0.5 rad rotation before adding a new scan.
- Supports loop closure detection up to 3 m search radius.
- The operator saves the map by pressing **V** in the teleop window, which calls `map_saver_cli` to write `auto_map.yaml` + `auto_map.pgm`.

**Phase 2 — AMCL (Adaptive Monte Carlo Localisation):**
- Loads the saved map and localises the robot using a particle filter.
- Fuses LiDAR scans with wheel odometry.
- Parameters: 500–2000 particles, likelihood field sensor model.
- The Nav2 Behaviour Tree handles path planning and obstacle avoidance.

---

## 5. Station Registration (Phase 1)

During Phase 1, the operator drives the robot near each station and presses **B**. This triggers:
1. A call to `/detect_station` (ArUco detection + depth measurement).
2. A TF lookup to transform the detected position from the camera frame to the `map` frame.
3. A **standoff destination pose** is computed: the robot should stop at a fixed distance in front of the marker, facing it.
4. The destination pose is saved to `station_a_location.yaml` or `station_b_location.yaml`.

These YAML files are then read by `station_demo.py` in Phase 2 to send navigation goals.

---

## 6. Future Improvements

Several improvements could significantly enhance the robustness and autonomy of the system:

### Pipeline sensor readiness check
Before starting the mission, the system should verify that all sensors (cameras, depth sensor, LiDAR) are publishing and healthy. Currently, the robot may begin navigating before the camera stream or OCR service has fully initialised, which can silently cause the first service call to fail. A startup health-check that waits for confirmed messages on all critical topics would prevent this class of failure.

### Screen detection instead of ArUco markers
Station A is currently located by detecting an ArUco marker placed near the clock. A more robust approach would be to detect the actual clock display (screen) itself, removing the dependency on a manually placed physical tag. This would make the system more general and eliminate the single point of failure of marker placement.

### 2D-to-3D pose estimation for the abacus and screen
The abacus detection currently returns only a rough lateral position and distance — it does not give the robot a full 3D pose (position + orientation). Implementing a proper 2D-to-3D pipeline (e.g. using PnP on detected keypoints, or a depth-based plane fit) would allow the robot to determine exactly where and at what angle the abacus is, so it can align itself precisely before attempting ring placement.

### Smart alignment verification before ring placement
Currently the robot assumes it has stopped at the correct position in front of the abacus after navigation. It does not verify this assumption before starting the arm sequence. Adding a short visual verification step — comparing the observed abacus position to the expected position using `/detect_abacus` — would allow the robot to correct its final position if needed, significantly improving placement reliability.

### Fully autonomous ring placement (removing operator dependency)
The current arm sequence requires a human to physically place each ring on the arm end-effector before it is lowered onto the pole. A fully autonomous version would require the robot to pick rings from a tray using the gripper. This would involve adding grasp detection and a pick-and-place pipeline. The rings and their positions are known, which makes this a tractable engineering problem given more time.

### Auto-explore for Phase 1 map building
Currently the operator must manually drive the robot around the environment during Phase 1 to build the map. An autonomous exploration algorithm (e.g. frontier-based exploration) could replace this, having the robot automatically discover and map the environment. The station-detection logic (`/detect_station`, `/detect_abacus`) could be called periodically during exploration to register stations as they are encountered. However, the current low frame rate of the camera stream over WiFi would need to be resolved first, as it would reduce detection reliability during automated motion.
