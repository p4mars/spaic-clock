"""
ArUco Marker Detection Test Script
Dit script opent je webcam en detecteert ArUco markers in real-time.
Als een marker wordt gevonden, tekent het groene lijnen eromheen en toont het welk station het is.
"""

import cv2
from cv2 import aruco

# ===== SETUP =====
# Laad het ArUco woordenboek (DICT_6X6_250 bevat 250 verschillende marker patronen)
dict_ = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)

# Maak detector parameters aan (standaard instellingen zijn meestal prima)
params = aruco.DetectorParameters()

# Maak de ArUco detector aan
detector = aruco.ArucoDetector(dict_, params)

# Open de webcam (0 = eerste webcam, of /dev/video0 op Linux)
cap = cv2.VideoCapture(0)

print("Webcam geopend. Hou een marker voor de camera.")
print("Druk op 'q' om te stoppen.")

# ===== MAIN LOOP =====
while True:
    # Lees een frame van de webcam
    ret, frame = cap.read()
    
    # Als het lezen mislukt, stop dan
    if not ret:
        print("Kon geen frame lezen van webcam")
        break
    
    # ===== DETECTIE =====
    # Zoek naar ArUco markers in dit frame
    # corners = lijst met 4 hoekpunten per gevonden marker
    # ids = lijst met marker IDs (0, 1, 2, etc.)
    corners, ids, _ = detector.detectMarkers(frame)
    
    # ===== ALS ER MARKERS GEVONDEN ZIJN =====
    if ids is not None:
        # Teken groene lijnen rond alle gevonden markers
        aruco.drawDetectedMarkers(frame, corners, ids)
        
        # Loop door alle gevonden marker IDs
        for id_ in ids.flatten():
            if id_ == 0:
                # Marker ID 0 = Station A (de klok)
                cv2.putText(frame, "STATION A GEVONDEN", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            elif id_ == 1:
                # Marker ID 1 = Station B (de abacus)
                cv2.putText(frame, "STATION B GEVONDEN", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # ===== TOON HET BEELD =====
    cv2.imshow('ArUco Detectie Test - Druk Q om te stoppen', frame)
    
    # Wacht 1ms op toetsdruk. Als 'q' ingedrukt: stop de loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ===== OPRUIMEN =====
cap.release()  # Sluit de webcam
cv2.destroyAllWindows()  # Sluit alle OpenCV vensters
print("Test gestopt.")