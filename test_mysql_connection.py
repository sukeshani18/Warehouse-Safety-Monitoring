import mysql.connector
import csv


# ==========================================
# 1. CSV FILE
# ==========================================

csv_path = r"E:\vs_code\YOLO\Warehouse_Safety_Monitoring\database\safety_events_full.csv"


# ==========================================
# 2. CONNECT TO MYSQL
# ==========================================

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1995",
    database="warehouse_safety"
)

cursor = connection.cursor()

print("MySQL connection successful.")


# ==========================================
# 3. INSERT QUERY
# ==========================================

sql = """
INSERT INTO safety_events (
    event_id,
    person_id,
    zone,
    event,
    timestamp,
    frame,
    duration_seconds,
    severity,
    evidence
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


# ==========================================
# 4. READ FULL CSV
# ==========================================

events_inserted = 0

with open(
    csv_path,
    "r",
    newline="",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        event_data = (
            int(row["event_id"]),
            int(row["person_id"]),
            row["zone"],
            row["event"],
            row["timestamp"],
            int(row["frame"]),
            float(row["duration_seconds"]),
            row["severity"],
            row["evidence"]
        )

        cursor.execute(
            sql,
            event_data
        )

        events_inserted += 1


# ==========================================
# 5. COMMIT
# ==========================================

connection.commit()


# ==========================================
# 6. CLOSE
# ==========================================

cursor.close()
connection.close()


# ==========================================
# 7. RESULT
# ==========================================

print("\n================================")
print("FULL CSV IMPORT COMPLETED")
print("================================")

print("Events inserted:", events_inserted)

print("Database: warehouse_safety")

print("Table: safety_events")

print("================================")