
from pathlib import Path
import random
import pandas as pd

from app.database.connection import SessionLocal
from app.models import Faculty, Room, WorkloadAssignment
from app.services.data.config import SEED


BASE_DIR = Path(__file__).resolve().parent

ALLOCATION_FILE = BASE_DIR / "data/output/section_allocations.csv"
OUTPUT_DIR = BASE_DIR / "data/output"
GROUND_TRUTH_DIR = BASE_DIR / "data/ground_truth"

ANOMALY_FILE = OUTPUT_DIR / "anomaly_injections.csv"
GROUND_TRUTH_FILE = GROUND_TRUTH_DIR / "anomaly_ground_truth.csv"


def generate_anomalies():
    if not ALLOCATION_FILE.exists():
        raise FileNotFoundError(ALLOCATION_FILE)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)

    df = pd.read_csv(ALLOCATION_FILE)

    allocated = df[
        df["allocation_status"] == "ALLOCATED"
    ].copy()

    if len(allocated) < 5:
        raise ValueError("At least five allocated sections are required.")

    # Sort first so the same seed produces the same records.
    allocated = allocated.sort_values(
        "section_id"
    ).reset_index(drop=True)

    selected_indices = rng.sample(
        range(len(allocated)), 5
    )

    selected = [
        allocated.iloc[index].to_dict()
        for index in selected_indices
    ]

    db = SessionLocal()

    try:
        faculty = {
            item.faculty_id: item
            for item in db.query(Faculty).all()
        }

        rooms = {
            item.room_id: item
            for item in db.query(Room).all()
        }

        assignments = db.query(WorkloadAssignment).filter(
            WorkloadAssignment.academic_year == 2026,
            WorkloadAssignment.status == "PROPOSED"
        ).all()

        workload = {}

        for item in assignments:
            key = (item.faculty_id, item.semester)
            workload[key] = (
                workload.get(key, 0) + item.weekly_hours
            )

        anomalies = []
        ground_truth = []

        def add_anomaly(
            anomaly_id,
            anomaly_type,
            entity_type,
            entity_id,
            source_section_id,
            expected_condition,
            injected_condition,
            details
        ):
            base = {
                "anomaly_id": anomaly_id,
                "anomaly_type": anomaly_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "source_section_id": source_section_id,
                "expected_condition": expected_condition,
                "injected_condition": injected_condition,
                "is_anomaly": True,
                "injection_source": "SYNTHETIC_TEST_DATA",
                "seed": SEED,
            }

            anomalies.append({**base, **details})

            ground_truth.append(base.copy())

        # 1. Faculty workload violation
        row = selected[0]
        person = faculty[row["faculty_id"]]

        current_hours = workload.get(
            (person.faculty_id, int(row["semester"])), 0
        )

        injected_hours = person.max_weekly_workload + 1

        add_anomaly(
            "ANM-001",
            "FACULTY_WORKLOAD_EXCEEDED",
            "FACULTY",
            person.faculty_id,
            row["section_id"],
            f"Weekly workload <= {person.max_weekly_workload}",
            f"Injected workload = {injected_hours}",
            {
                "course_id": row["course_id"],
                "semester": int(row["semester"]),
                "actual_weekly_workload": current_hours,
                "maximum_weekly_workload": person.max_weekly_workload,
                "injected_weekly_workload": injected_hours,
            }
        )

        # 2. Faculty without required skill
        row = selected[1]

        add_anomaly(
            "ANM-002",
            "FACULTY_SKILL_MISMATCH",
            "FACULTY",
            row["faculty_id"],
            row["section_id"],
            "Faculty must possess the course skill",
            "Injected skill_match = False",
            {
                "course_id": row["course_id"],
                "course_name": row["course_name"],
                "skill_match_before_injection": True,
                "skill_match_after_injection": False,
            }
        )

        # 3. Room capacity violation
        row = selected[2]
        room = rooms[row["room_id"]]

        required_capacity = int(row["section_capacity"])
        injected_capacity = max(1, required_capacity - 1)

        add_anomaly(
            "ANM-003",
            "ROOM_CAPACITY_EXCEEDED",
            "ROOM",
            room.room_id,
            row["section_id"],
            f"Room capacity >= {required_capacity}",
            f"Injected room capacity = {injected_capacity}",
            {
                "required_capacity": required_capacity,
                "actual_room_capacity": room.capacity,
                "injected_room_capacity": injected_capacity,
            }
        )

        # 4. Duplicate faculty timetable assignment
        row = selected[3]

        add_anomaly(
            "ANM-004",
            "FACULTY_TIMETABLE_CONFLICT",
            "FACULTY",
            row["faculty_id"],
            row["section_id"],
            "Faculty cannot teach overlapping sections",
            "Injected overlapping faculty booking",
            {
                "semester": int(row["semester"]),
                "day": row["scheduled_day"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "simulated_event_id": "SIM-EVENT-004",
            }
        )

        # 5. Room timetable conflict
        row = selected[4]

        add_anomaly(
            "ANM-005",
            "ROOM_TIMETABLE_CONFLICT",
            "ROOM",
            row["room_id"],
            row["section_id"],
            "Room cannot host overlapping sections",
            "Injected overlapping room booking",
            {
                "semester": int(row["semester"]),
                "day": row["scheduled_day"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "simulated_event_id": "SIM-EVENT-005",
            }
        )

        pd.DataFrame(anomalies).to_csv(
            ANOMALY_FILE, index=False
        )

        pd.DataFrame(ground_truth).to_csv(
            GROUND_TRUTH_FILE, index=False
        )

        print("\nANOMALY GENERATION COMPLETED")
        print("=" * 50)
        print("Anomalies generated:", len(anomalies))
        print("Unique anomaly types:", len(set(
            x["anomaly_type"] for x in anomalies
        )))

        print("\nANOMALY TYPES:")

        for item in anomalies:
            print(
                item["anomaly_id"],
                "-",
                item["anomaly_type"]
            )

        print("\nOUTPUT FILES:")
        print(ANOMALY_FILE)
        print(GROUND_TRUTH_FILE)

        print("\nOriginal allocation data was not modified.")

    finally:
        db.close()


if __name__ == "__main__":
    generate_anomalies()
