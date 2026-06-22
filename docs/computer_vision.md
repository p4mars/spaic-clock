> **Note:** Commands use my specific directory paths — adjust them for your own setup.

---

# Computer Vision — Command Reference

---

## 0. First-Time Setup

Install the required Python packages (only needed once):

```bash
python3 -m pip install easyocr inference-sdk
```

> Use `python3 -m pip` (not plain `pip`) to ensure packages are installed into the same Python environment that ROS nodes use.

Then build the full workspace so ROS picks up all packages:

```bash
cd ~/mirte_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

> **If the build fails** with `failed to create symbolic link ... Is a directory` on `cognitive_robot_interfaces`, clear the stale build cache and retry:
> ```bash
> rm -rf ~/mirte_ws/build/cognitive_robot_interfaces
> rm -rf ~/mirte_ws/install/cognitive_robot_interfaces
> colcon build
> ```

- `easyocr` — time-reading service (OCR on digital clock)
- `inference-sdk` — abacus detection service (Roboflow)

---

## 1. Gazebo Simulation

Run all of these on your **laptop**, each in a separate terminal.

Run this in **every new terminal** before anything else:

```bash
cd ~/mirte_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
```

---

**Terminal 1 — Launch Gazebo**
```bash
killall gzserver gzclient 2>/dev/null
sleep 2
ros2 launch mirte_gazebo gazebo_mirte_master_empty.launch.xml
```

**Terminal 2 — Launch the Demo**
```bash
ros2 launch cognitive_robot demo_gazebo.launch.py
```

Or without Gazebo:
```bash
ros2 launch cognitive_robot demo.launch.py
```

**Terminal 3 — Keyboard Teleop** *(optional — to drive the robot manually)*
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/mirte_base_controller/cmd_vel_unstamped
```

**Terminal 4 — Call a CV Service**
```bash
# Abacus detection
ros2 service call /detect_abacus cognitive_robot_interfaces/srv/DetectAbacus '{}'

# Station / ArUco detection
ros2 service call /detect_station cognitive_robot_interfaces/srv/DetectStation '{}'

# Time reading
ros2 service call /read_time cognitive_robot_interfaces/srv/ReadTime
```

---

## 2. Real Robot

- `[LAPTOP]` — run on your laptop
- `[ROBOT]` — run on the robot (via SSH or web editor)

**Before you start:**
- Connect laptop WiFi to: `Mirte-XXXXXX` (password: `mirte_mirte`)
- Open browser: `http://192.168.42.1:8000` (user: `mirte` / pass: `mirte_mirte`)

SSH into the robot:
```bash
ssh mirte@172.20.10.4
```

Run this in **every new `[LAPTOP]` terminal** before anything else:
```bash
cd ~/mirte_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=4
```

Run this in **every new `[ROBOT]` terminal** before anything else:
```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=4
```

---

**`[ROBOT]` Terminal 1 — Verify the camera is visible**
```bash
ros2 topic list | grep camera
```
- If the list is empty: wrong `ROS_DOMAIN_ID`, or WiFi not connected correctly.
- If ROS nodes seem broken, restart the ROS service:
  ```bash
  sudo service mirte-ros restart   # password: mirte_mirte
  ```

**`[LAPTOP]` Terminal 2 — Launch the Demo**
```bash
ros2 launch cognitive_robot demo.launch.py
```

**`[LAPTOP]` Terminal 3 — Call a CV Service**
```bash
# Abacus detection
ros2 service call /detect_abacus cognitive_robot_interfaces/srv/DetectAbacus '{}'

# Station / ArUco detection
ros2 service call /detect_station cognitive_robot_interfaces/srv/DetectStation '{}'

# Time reading
ros2 service call /read_time cognitive_robot_interfaces/srv/ReadTime
```

---

### After a code change — rebuild and source

```bash
cd ~/mirte_ws
colcon build --packages-select cognitive_robot
source install/setup.bash
```

---

## 3. `/read_time` service — how it works & tuning

When the mission node calls `/read_time`, the service grabs a front-camera frame
and runs EasyOCR looking for an `NN:NN` time. If nothing valid is found it rotates
the robot slightly (alternating left/right with increasing angles) and retries,
until it reads a time or runs out of attempts. It returns `found=True` + four
digits (e.g. `[1,4,3,2]` for `14:32`), or `found=False`.

OCR runs on the **laptop**, not the robot — the EasyOCR model (~200 MB) is too
heavy for the robot's CPU. The robot only supplies the camera stream and executes
rotation commands.

### Tunable parameters

Pass at launch with `--ros-args -p name:=value`:

| Parameter | Default | Description |
|---|---|---|
| `confidence_threshold` | `0.1` | Min OCR confidence to accept a reading. Raise if you get wrong times; lower if valid times are rejected. |
| `step_degrees` | `10` | Degrees added per scan iteration (0°, ±10°, ±20°…). |
| `max_iterations` | `10` | Max scan attempts before giving up. |
| `rotation_speed` | `0.5` | Rotation speed (rad/s). |
| `debug_save_dir` | `~/ocr_debug` | Where debug images are saved (laptop). |
| `camera_topic` | `/camera/color/image_raw` | Camera to read. Gazebo: `/camera/image_raw`. |
| `cmd_vel_topic` | `/mirte_base_controller/cmd_vel` | Rotation-command topic. Gazebo: `/cmd_vel`. |

### Debug images

Each scan attempt writes a pair of files into `debug_save_dir`:
`attempt_<timestamp>_iter<N>.jpg` (the camera frame) and `.txt` (the OCR
detections with confidence and accept/reject verdict). Inspect these to see why a
read succeeded or failed.

### Collecting test photos

`make_photo_for_testing_algorithm` saves front-camera frames on demand for offline
OCR testing (not part of the live pipeline):

```bash
ros2 run cognitive_robot make_photo_for_testing_algorithm
# Press Enter to save a frame, type 'q' to quit. Saved to ~/photos/
```