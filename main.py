from ultralytics import YOLO
import cv2
import numpy as np
import csv
import os


# ==========================================
# 1. LOAD MODEL
# ==========================================

model = YOLO("models/yolo11n.pt")


# ==========================================
# 2. OPEN WAREHOUSE VIDEO
# ==========================================

video_path = r"E:\vs_code\YOLO\Warehouse_Safety_Monitoring\Input\cam_00.mp4"

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Error: Could not open warehouse video.")
    raise SystemExit


fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print("================================")
print("WAREHOUSE VIDEO OPENED")
print("================================")
print("Resolution:", width, "x", height)
print("FPS:", fps)
print("Total frames:", total_frames)
print("Duration:", round(total_frames / fps, 2), "seconds")
print("")


# ==========================================
# 3. PROCESS FULL VIDEO
# ==========================================

frame_number = 0


# ==========================================
# 4. RESTRICTED ZONE
# ==========================================

zone_points = np.array([
    (700, 260),
    (1050, 260),
    (1350, 1080),
    (500, 1080)
], dtype=np.int32)

zone_name = "RESTRICTED_ZONE_1"


# ==========================================
# 5. PROJECT PATHS
# ==========================================

project_path = r"E:\vs_code\YOLO\Warehouse_Safety_Monitoring"

output_video_path = os.path.join(
    project_path,
    "output",
    "warehouse_safety_full.mp4"
)

events_folder = os.path.join(
    project_path,
    "output",
    "events"
)

csv_path = os.path.join(
    project_path,
    "database",
    "safety_events_full.csv"
)


# ==========================================
# 6. OUTPUT VIDEO
# ==========================================

fourcc = cv2.VideoWriter_fourcc(*"mp4v")

out = cv2.VideoWriter(
    output_video_path,
    fourcc,
    fps,
    (width, height)
)

if not out.isOpened():
    cap.release()
    print("Error: Could not create output video.")
    raise SystemExit


# ==========================================
# 7. TRACKING / EVENT VARIABLES
# ==========================================

previous_status = {}

entry_info = {}

safety_events = []

event_number = 0


# ==========================================
# 8. SEVERITY FUNCTION
# ==========================================

def calculate_severity(duration_seconds):

    if duration_seconds > 5:
        return "HIGH"

    elif duration_seconds >= 2:
        return "MEDIUM"

    else:
        return "LOW"


# ==========================================
# 9. PROCESS FULL VIDEO
# ==========================================

while True:

    success, frame = cap.read()

    if not success:
        break

    frame_number += 1


    # ======================================
    # YOLO TRACKING
    # ======================================

    results = model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        classes=[0],
        verbose=False
    )


    frame = results[0].plot()


    # ======================================
    # DRAW RESTRICTED ZONE
    # ======================================

    cv2.polylines(
        frame,
        [zone_points],
        isClosed=True,
        color=(0, 0, 255),
        thickness=3
    )


    cv2.putText(
        frame,
        zone_name,
        (700, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )


    # ======================================
    # CHECK TRACKED PERSONS
    # ======================================

    if results[0].boxes.id is not None:

        track_ids = results[0].boxes.id.int().cpu().tolist()

        boxes = results[0].boxes.xyxy.cpu().tolist()


        for track_id, box in zip(track_ids, boxes):

            x1, y1, x2, y2 = box


            # ==================================
            # PERSON FOOT POINT
            # ==================================

            foot_x = int((x1 + x2) / 2)
            foot_y = int(y2)


            # ==================================
            # CHECK RESTRICTED ZONE
            # ==================================

            inside_zone = cv2.pointPolygonTest(
                zone_points,
                (foot_x, foot_y),
                False
            ) >= 0


            was_inside = previous_status.get(
                track_id,
                False
            )


            # ==================================
            # ENTRY EVENT
            # ==================================

            if inside_zone and not was_inside:

                event_number += 1

                entry_frame = frame_number

                entry_time = frame_number / fps


                timestamp = (
                    f"{int(entry_time // 3600):02d}:"
                    f"{int((entry_time % 3600) // 60):02d}:"
                    f"{int(entry_time % 60):02d}"
                )


                # Store entry information
                entry_info[track_id] = {
                    "frame": entry_frame,
                    "time": entry_time
                }


                # Evidence filename
                evidence_filename = (
                    f"event_{event_number:04d}"
                    f"_person_{track_id}"
                    f"_ENTRY"
                    f"_frame_{frame_number}.jpg"
                )


                evidence_path = os.path.join(
                    events_folder,
                    evidence_filename
                )


                # Display event
                cv2.putText(
                    frame,
                    f"ENTRY EVENT: ID {track_id}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )


                # Save evidence
                saved = cv2.imwrite(
                    evidence_path,
                    frame
                )


                print("\n========== ENTRY EVENT ==========")
                print("Event ID:", event_number)
                print("Person ID:", track_id)
                print("Zone:", zone_name)
                print("Timestamp:", timestamp)
                print("Frame:", frame_number)
                print("Duration: 0 seconds")
                print("Severity: PENDING")
                print("Evidence saved:", saved)


                safety_events.append({
                    "event_id": event_number,
                    "person_id": track_id,
                    "zone": zone_name,
                    "event": "Restricted Zone Entry",
                    "timestamp": timestamp,
                    "frame": frame_number,
                    "duration_seconds": 0,
                    "severity": "PENDING",
                    "evidence": evidence_filename
                })


            # ==================================
            # EXIT EVENT
            # ==================================

            elif not inside_zone and was_inside:

                event_number += 1

                exit_time = frame_number / fps


                timestamp = (
                    f"{int(exit_time // 3600):02d}:"
                    f"{int((exit_time % 3600) // 60):02d}:"
                    f"{int(exit_time % 60):02d}"
                )


                # Calculate duration
                if track_id in entry_info:

                    entry_time = entry_info[track_id]["time"]

                    duration_seconds = round(
                        exit_time - entry_time,
                        2
                    )

                else:

                    duration_seconds = 0


                # ==================================
                # CALCULATE SEVERITY
                # ==================================

                severity = calculate_severity(
                    duration_seconds
                )


                # ==================================
                # EXIT EVIDENCE
                # ==================================

                evidence_filename = (
                    f"event_{event_number:04d}"
                    f"_person_{track_id}"
                    f"_EXIT"
                    f"_frame_{frame_number}.jpg"
                )


                evidence_path = os.path.join(
                    events_folder,
                    evidence_filename
                )


                # Display exit event
                cv2.putText(
                    frame,
                    f"EXIT EVENT: ID {track_id}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 0, 0),
                    2
                )


                cv2.putText(
                    frame,
                    f"Severity: {severity}",
                    (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
                )


                # Save evidence
                saved = cv2.imwrite(
                    evidence_path,
                    frame
                )


                print("\n========== EXIT EVENT ==========")
                print("Event ID:", event_number)
                print("Person ID:", track_id)
                print("Zone:", zone_name)
                print("Timestamp:", timestamp)
                print("Frame:", frame_number)
                print("Duration:", duration_seconds, "seconds")
                print("Severity:", severity)
                print("Evidence saved:", saved)


                safety_events.append({
                    "event_id": event_number,
                    "person_id": track_id,
                    "zone": zone_name,
                    "event": "Restricted Zone Exit",
                    "timestamp": timestamp,
                    "frame": frame_number,
                    "duration_seconds": duration_seconds,
                    "severity": severity,
                    "evidence": evidence_filename
                })


                # Remove entry information
                if track_id in entry_info:

                    del entry_info[track_id]


            # ==================================
            # DISPLAY PERSON INSIDE ZONE
            # ==================================

            if inside_zone:

                cv2.putText(
                    frame,
                    f"ID {track_id} IN RESTRICTED ZONE",
                    (
                        int(x1),
                        max(int(y1) - 10, 30)
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 0, 255),
                    2
                )


            # ==================================
            # UPDATE PERSON STATUS
            # ==================================

            previous_status[track_id] = inside_zone


    # ======================================
    # SAVE FRAME
    # ======================================

    out.write(frame)


    # ======================================
    # PROGRESS
    # ======================================

    if frame_number % 300 == 0:

        elapsed_video_time = frame_number / fps

        print(
            f"Progress: {frame_number}/{total_frames} "
            f"frames | "
            f"Video time: {elapsed_video_time:.1f}s | "
            f"Events: {len(safety_events)}"
        )


# ==========================================
# 10. RELEASE VIDEO
# ==========================================

cap.release()

out.release()


# ==========================================
# 11. SAVE CSV
# ==========================================

with open(
    csv_path,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    fieldnames = [
        "event_id",
        "person_id",
        "zone",
        "event",
        "timestamp",
        "frame",
        "duration_seconds",
        "severity",
        "evidence"
    ]


    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )


    writer.writeheader()

    writer.writerows(
        safety_events
    )


# ==========================================
# 12. FINAL RESULTS
# ==========================================

print("\n================================")
print("FULL VIDEO PROCESSING COMPLETED")
print("================================")

print("Frames processed:", frame_number)

print(
    "Video duration:",
    round(frame_number / fps, 2),
    "seconds"
)

print(
    "Total safety events:",
    len(safety_events)
)

print("Output video:")
print(output_video_path)

print("\nCSV:")
print(csv_path)

print("\nEvent images:")
print(events_folder)

print("================================")