Standalone scripts used while developing and testing the computer-vision parts.
None of these are part of the robot pipeline — they are not built or launched by ROS.

Contents:
* aruro/ — ArUco marker generation + offline detection tests, with sample photos
* clock_reading/ — offline OCR test on a sample clock image
* station_detector.py — early station-detection prototype
* test_roboflow.py — quick check of the Roboflow abacus model on a single image
* results.json — saved output from a station_detector.py run

The printable ArUco markers actually used at the stations live in docs/aruco_markers/.