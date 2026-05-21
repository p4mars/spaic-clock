"""
ArUco Marker Detection on a Single Photo
Detects ArUco markers in a static image and shows which station was found.
"""

import cv2
from cv2 import aruco

# ===== SETUP =====
# Load the ArUco dictionary (DICT_6X6_250 contains 250 different marker patterns)
dict_ = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)

# Create detector parameters (default settings work fine)
params = aruco.DetectorParameters()

# Create the ArUco detector
detector = aruco.ArucoDetector(dict_, params)

# ===== LOAD PHOTO =====
frame = cv2.imread('test_clock.jpg')  # replace with your photo path

# Check if the image loaded successfully
if frame is None:
    print("Cannot load photo!")
    exit()

# ===== DETECTION =====
# Search for ArUco markers in the image
# corners = list of 4 corner points per detected marker
# ids = list of marker IDs (0, 1, 2, etc.)
corners, ids, _ = detector.detectMarkers(frame)

# ===== RESULT =====
# Check if any markers were found
if ids is not None:
    # Draw green lines around all detected markers
    aruco.drawDetectedMarkers(frame, corners, ids)
    
    # Loop through all detected marker IDs
    for id_ in ids.flatten():
        if id_ == 0:
            # Marker ID 0 = Station A (the clock)
            cv2.putText(frame, "STATION A FOUND", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            print(f"Station A detected at position: {corners[0]}")
        elif id_ == 1:
            # Marker ID 1 = Station B (the abacus)
            cv2.putText(frame, "STATION B FOUND", (50, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            print(f"Station B detected at position: {corners[0]}")
else:
    print("No markers found in the photo")

# ===== SHOW RESULT =====
cv2.imshow('Detection result - Press any key to close', frame)
cv2.waitKey(0)  # Wait until you press a key
cv2.destroyAllWindows()