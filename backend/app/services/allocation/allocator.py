
from pathlib import Path
from datetime import date, datetime
import json
import re

import pandas as pd

from app.database.connection import SessionLocal
from app.models import (
    Course,
    Faculty,
    FacultySkill,
    Availability,
    Room,
    Section,
    WorkloadAssignment,
)


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[3]

FORECAST_PATH = (
    BASE_DIR / "data" / "output"
    / "course_demand_forecast_2026.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "output"

ALLOCATION_PATH = OUTPUT_DIR / "section_allocations.csv"
UNMET_DEMAND_PATH = OUTPUT_DIR / "unmet_demand.csv"
SUMMARY_PATH = OUTPUT_DIR / "allocation_summary.json"

ACADEMIC_YEAR = 2026

SEMESTER_DATES = {
    1: (date(2026, 1, 1), date(2026, 6, 30)),
    2: (date(2026, 7, 1), date(2026, 12, 31)),
}

DAYS = [
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def normalize_skill(value):
    """Normalize course and skill names for matching."""

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).lower()
    )


def time_to_minutes(value):
    """Convert HH:MM into minutes."""

    hours, minutes = map(int, value.split(":"))
    return hours * 60 + minutes


def minutes_to_time(value):
    """Convert minutes into HH:MM."""

    hours = value // 60
    minutes = value % 60

    return f"{hours:02d}:{minutes:02d}"


def dates_overlap(start1, end1, start2, end2):
    """Check whether two date ranges overlap."""

    if end1 is None:
        end1 = date.max

    if end2 is None:
        end2 = date.max

    return start1 <= end2 and start2 <= end1


def is_date_active(record, semester_start, semester_end):
    """Check whether a record is active during a semester."""

    return dates_overlap(
        record.effective_start_date,
        record.effective_end_date,
        semester_start,
        semester_end,
    )


def interval_conflict(bookings, semester, day, start, end):
    """Check whether a scheduled time overlaps an existing booking."""

    for booked_semester, booked_day, booked_start, booked_end in bookings:

        if booked_semester != semester:
            continue

        if booked_day != day:
            continue

        if start < booked_end and booked_start < end:
            return True

    return False


def get_room_preference(course_name):
    """Prefer a laboratory for practical or technical courses."""

    name = str(course_name).lower()

    lab_keywords = [
        "lab",
        "practical",
        "programming",
        "computer",
    ]

    if any(keyword in name for keyword in lab_keywords):
        return "LAB"

    return "CLASSROOM"


def get_time_slots(availability, duration_hours):
    """Generate hourly start times that fit inside an availability window."""

    start = time_to_minutes(availability.start_time)
    end = time_to_minutes(availability.end_time)

    duration = duration_hours * 60

    slots = []

    current = start

    while current + duration <= end:
        slots.append((
            current,
            current + duration
        ))

        current += 60

    return slots


# ---------------------------------------------------------
# LOAD INPUT DATA
# ---------------------------------------------------------

def load_forecast():

    if not FORECAST_PATH.exists():
        raise FileNotFoundError(
            f"Forecast file not found: {FORECAST_PATH}"
        )

    df = pd.read_csv(FORECAST_PATH)

    required_columns = [
        "course_id",
        "course_name",
        "academic_year",
        "semester",
        "predicted_demand",
        "target_section_size",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Forecast is missing columns: {missing}"
        )

    section_column = (
        "predicted_sections_required"
        if "predicted_sections_required" in df.columns
        else "predicted_sections"
    )

    if section_column not in df.columns:
        raise ValueError(
            "Forecast does not contain a predicted section column."
        )

    df["sections_to_create"] = pd.to_numeric(
        df[section_column],
        errors="raise"
    ).astype(int)

    df["predicted_demand"] = pd.to_numeric(
        df["predicted_demand"],
        errors="raise"
    ).astype(int)

    df["target_section_size"] = pd.to_numeric(
        df["target_section_size"],
        errors="raise"
    ).astype(int)

    if (df["sections_to_create"] < 0).any():
        raise ValueError("Negative section counts found.")

    if (df["target_section_size"] <= 0).any():
        raise ValueError("Invalid target section size found.")

    if (df["predicted_demand"] < 0).any():
        raise ValueError("Negative predicted demand found.")

    if not (df["academic_year"] == ACADEMIC_YEAR).all():
        raise ValueError("Unexpected academic year in forecast.")

    if not df["semester"].isin([1, 2]).all():
        raise ValueError("Unexpected semester in forecast.")

    return df.sort_values(
        ["course_id", "semester"]
    ).reset_index(drop=True)


# ---------------------------------------------------------
# LOAD DATABASE RESOURCES
# ---------------------------------------------------------

def load_resources(db):

    faculty_records = (
        db.query(Faculty)
        .filter(Faculty.status == "ACTIVE")
        .all()
    )

    skill_records = db.query(FacultySkill).all()

    availability_records = (
        db.query(Availability)
        .filter(Availability.status == "AVAILABLE")
        .all()
    )

    leave_records = (
        db.query(Availability)
        .filter(Availability.status == "ON_LEAVE")
        .all()
    )

    room_records = (
        db.query(Room)
        .filter(Room.is_active == True)
        .all()
    )

    courses = {
        course.course_id: course
        for course in db.query(Course).all()
    }

    faculty = {
        person.faculty_id: person
        for person in faculty_records
    }

    # Skill map:
    # normalized course name -> faculty skill records
    skills_by_course = {}

    for skill in skill_records:

        if skill.faculty_id not in faculty:
            continue

        key = normalize_skill(skill.skill_name)

        skills_by_course.setdefault(key, []).append(skill)

    # Availability map:
    # faculty ID -> availability records
    availability_by_faculty = {}

    for record in availability_records:

        availability_by_faculty.setdefault(
            record.faculty_id,
            []
        ).append(record)

    # Leave map:
    # (faculty ID, semester) -> unavailable weekdays
    leave_days = {}

    for leave in leave_records:

        for semester, (start, end) in SEMESTER_DATES.items():

            if not is_date_active(leave, start, end):
                continue

            key = (leave.faculty_id, semester)

            leave_days.setdefault(key, set()).add(
                leave.day_of_week.upper()
            )

    return {
        "faculty": faculty,
        "skills": skills_by_course,
        "availability": availability_by_faculty,
        "leave_days": leave_days,
        "rooms": room_records,
        "courses": courses,
    }


# ---------------------------------------------------------
# FACULTY AND ROOM MATCHING
# ---------------------------------------------------------

def find_allocation(
    course,
    semester,
    target_capacity,
    weekly_hours,
    resources,
    faculty_workload,
    faculty_bookings,
    room_bookings,
):
    """Find a valid faculty, room, and timetable slot."""

    semester_start, semester_end = SEMESTER_DATES[semester]

    skill_key = normalize_skill(course.course_name)

    matching_skills = resources["skills"].get(skill_key, [])

    qualified_faculty = []

    for skill in matching_skills:

        person = resources["faculty"][skill.faculty_id]

        if not is_date_active(
            skill,
            semester_start,
            semester_end
        ):
            continue

        if faculty_workload.get(
            (person.faculty_id, semester), 0
        ) + weekly_hours > person.max_weekly_workload:
            continue

        qualified_faculty.append((person, skill.proficiency_level))

    # Highest proficiency first, then lowest current workload.
    qualified_faculty.sort(
        key=lambda item: (
            -item[1],
            faculty_workload.get(
                (item[0].faculty_id, semester), 0
            ),
            item[0].faculty_id,
        )
    )

    if not qualified_faculty:
        return None, "NO_QUALIFIED_FACULTY"

    suitable_rooms = [
        room
        for room in resources["rooms"]
        if room.capacity >= target_capacity
    ]

    preferred_type = get_room_preference(course.course_name)

    suitable_rooms.sort(
        key=lambda room: (
            room.room_type != preferred_type,
            room.capacity,
            room.room_id,
        )
    )

    if not suitable_rooms:
        return None, "NO_SUITABLE_ROOM"

    # Search faculty, available slots, and rooms.
    for person, proficiency in qualified_faculty:

        faculty_id = person.faculty_id

        blocked_days = resources["leave_days"].get(
            (faculty_id, semester), set()
        )

        availability_records = (
            resources["availability"].get(faculty_id, [])
        )

        active_availability = [
            item
            for item in availability_records
            if is_date_active(
                item,
                semester_start,
                semester_end
            )
            and item.day_of_week.upper() not in blocked_days
        ]

        active_availability.sort(
            key=lambda item: (
                DAYS.index(item.day_of_week.upper())
                if item.day_of_week.upper() in DAYS
                else 99,
                item.start_time,
            )
        )

        for available in active_availability:

            day = available.day_of_week.upper()

            if day not in DAYS:
                continue

            slots = get_time_slots(
                available,
                weekly_hours
            )

            for start, end in slots:

                if interval_conflict(
                    faculty_bookings.get(faculty_id, []),
                    semester,
                    day,
                    start,
                    end,
                ):
                    continue

                for room in suitable_rooms:

                    if interval_conflict(
                        room_bookings.get(room.room_id, []),
                        semester,
                        day,
                        start,
                        end,
                    ):
                        continue

                    return {
                        "faculty": person,
                        "proficiency": proficiency,
                        "room": room,
                        "day": day,
                        "start": minutes_to_time(start),
                        "end": minutes_to_time(end),
                        "start_minutes": start,
                        "end_minutes": end,
                    }, None

    return None, "NO_COMPATIBLE_FACULTY_ROOM_SLOT"


# ---------------------------------------------------------
# MAIN ALLOCATION ENGINE
# ---------------------------------------------------------

def run_allocation():

    print("\nACADEMIC RESOURCE ALLOCATION")
    print("=" * 60)

    df = load_forecast()

    print(f"Forecast records loaded: {len(df):,}")

    db = SessionLocal()

    try:

        resources = load_resources(db)

        faculty = resources["faculty"]
        rooms = resources["rooms"]

        print(f"Active faculty: {len(faculty):,}")
        print(f"Active rooms: {len(rooms):,}")

        # Remove previous proposed results for 2026.
        # Delete workload assignments first because they
        # reference sections.
        db.query(WorkloadAssignment).filter(
            WorkloadAssignment.academic_year == ACADEMIC_YEAR,
            WorkloadAssignment.status == "PROPOSED",
        ).delete(synchronize_session=False)

        db.query(Section).filter(
            Section.academic_year == ACADEMIC_YEAR,
            Section.status == "PROPOSED",
        ).delete(synchronize_session=False)

        faculty_workload = {}
        faculty_bookings = {}
        room_bookings = {}

        allocation_rows = []
        unmet_rows = []

        section_counter = 1
        assignment_counter = 1

        total_demand = 0
        total_allocated_capacity = 0

        allocated_sections = 0
        unallocated_sections = 0

        reason_counts = {}

        # Process each course and semester.
        for _, row in df.iterrows():

            course_id = str(row["course_id"])

            course = resources["courses"].get(course_id)

            if course is None:
                raise ValueError(
                    f"Course not found in database: {course_id}"
                )

            semester = int(row["semester"])

            predicted_demand = int(row["predicted_demand"])

            target_size = int(row["target_section_size"])

            planned_sections = int(row["sections_to_create"])

            semester_start, semester_end = SEMESTER_DATES[semester]

            weekly_hours = min(
                max(int(course.credits), 1),
                3
            )

            remaining_demand = predicted_demand

            course_allocated_sections = 0
            course_unallocated_sections = 0
            course_allocated_capacity = 0

            for section_number in range(1, planned_sections + 1):

                section_id = f"SEC-{section_counter:09d}"
                section_counter += 1

                section_demand = min(
                    target_size,
                    remaining_demand
                )

                if remaining_demand <= 0:
                    break

                allocation, reason = find_allocation(
                    course=course,
                    semester=semester,
                    target_capacity=target_size,
                    weekly_hours=weekly_hours,
                    resources=resources,
                    faculty_workload=faculty_workload,
                    faculty_bookings=faculty_bookings,
                    room_bookings=room_bookings,
                )

                faculty_id = None
                faculty_name = None
                room_id = None
                room_name = None
                scheduled_day = None
                start_time = None
                end_time = None

                if allocation:

                    person = allocation["faculty"]
                    room = allocation["room"]

                    faculty_id = person.faculty_id
                    faculty_name = person.faculty_name

                    room_id = room.room_id
                    room_name = room.room_name

                    scheduled_day = allocation["day"]
                    start_time = allocation["start"]
                    end_time = allocation["end"]

                    faculty_workload_key = (
                        faculty_id,
                        semester
                    )

                    faculty_workload[faculty_workload_key] = (
                        faculty_workload.get(
                            faculty_workload_key, 0
                        ) + weekly_hours
                    )

                    faculty_bookings.setdefault(
                        faculty_id, []
                    ).append((
                        semester,
                        scheduled_day,
                        allocation["start_minutes"],
                        allocation["end_minutes"],
                    ))

                    room_bookings.setdefault(
                        room_id, []
                    ).append((
                        semester,
                        scheduled_day,
                        allocation["start_minutes"],
                        allocation["end_minutes"],
                    ))

                    # Save workload assignment.
                    workload_assignment = WorkloadAssignment(
                        workload_assignment_id=(
                            f"WLA-{assignment_counter:09d}"
                        ),
                        faculty_id=faculty_id,
                        section_id=section_id,
                        weekly_hours=weekly_hours,
                        academic_year=ACADEMIC_YEAR,
                        semester=semester,
                        effective_start_date=semester_start,
                        effective_end_date=semester_end,
                        status="PROPOSED",
                    )

                    assignment_counter += 1

                    db.add(workload_assignment)

                    allocated_sections += 1
                    course_allocated_sections += 1

                    course_allocated_capacity += target_size
                    total_allocated_capacity += target_size

                    remaining_demand = max(
                        0,
                        remaining_demand - target_size
                    )

                else:

                    unallocated_sections += 1
                    course_unallocated_sections += 1

                    reason_counts[reason] = (
                        reason_counts.get(reason, 0) + 1
                    )

                # Save section, including unallocated sections.
                section = Section(
                    section_id=section_id,
                    course_id=course_id,
                    room_id=room_id,
                    section_number=section_number,
                    academic_year=ACADEMIC_YEAR,
                    semester=semester,
                    section_capacity=target_size,
                    scheduled_day=scheduled_day,
                    start_time=start_time,
                    end_time=end_time,
                    start_date=semester_start,
                    end_date=semester_end,
                    status="PROPOSED",
                )

                db.add(section)

                allocation_rows.append({
                    "section_id": section_id,
                    "course_id": course_id,
                    "course_name": course.course_name,
                    "semester": semester,
                    "section_number": section_number,
                    "section_capacity": target_size,
                    "faculty_id": faculty_id,
                    "faculty_name": faculty_name,
                    "room_id": room_id,
                    "room_name": room_name,
                    "scheduled_day": scheduled_day,
                    "start_time": start_time,
                    "end_time": end_time,
                    "weekly_hours": weekly_hours if allocation else 0,
                    "allocation_status": (
                        "ALLOCATED" if allocation else "UNALLOCATED"
                    ),
                    "failure_reason": reason,
                })

            total_demand += predicted_demand

            course_unmet_demand = remaining_demand

            unmet_rows.append({
                "course_id": course_id,
                "course_name": course.course_name,
                "semester": semester,
                "predicted_demand": predicted_demand,
                "planned_sections": planned_sections,
                "allocated_sections": course_allocated_sections,
                "unallocated_sections": course_unallocated_sections,
                "allocated_capacity": course_allocated_capacity,
                "unmet_demand": course_unmet_demand,
            })

        # Commit all database records.
        db.commit()

        # Save output files.
        allocation_df = pd.DataFrame(allocation_rows)
        unmet_df = pd.DataFrame(unmet_rows)

        allocation_df.to_csv(
            ALLOCATION_PATH,
            index=False
        )

        unmet_df.to_csv(
            UNMET_DEMAND_PATH,
            index=False
        )

        total_unmet_demand = int(
            unmet_df["unmet_demand"].sum()
        )

        total_planned_sections = int(
            df["sections_to_create"].sum()
        )

        summary = {
            "academic_year": ACADEMIC_YEAR,
            "forecast_records": int(len(df)),
            "total_predicted_demand": int(total_demand),
            "total_planned_sections": total_planned_sections,
            "allocated_sections": allocated_sections,
            "unallocated_sections": unallocated_sections,
            "total_allocated_capacity": int(
                total_allocated_capacity
            ),
            "total_unmet_demand": total_unmet_demand,
            "active_faculty": len(faculty),
            "active_rooms": len(rooms),
            "faculty_assignment_failures": reason_counts,
            "allocation_algorithm": "Greedy Constraint-Based Allocation",
            "generated_at": datetime.now().isoformat(),
        }

        with open(
            SUMMARY_PATH,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(summary, file, indent=4)

        print("\nALLOCATION COMPLETED")
        print("=" * 60)

        print(f"Total predicted demand: {total_demand:,}")
        print(f"Total planned sections: {total_planned_sections:,}")
        print(f"Allocated sections: {allocated_sections:,}")
        print(f"Unallocated sections: {unallocated_sections:,}")
        print(f"Total unmet demand: {total_unmet_demand:,}")

        print("\nALLOCATION FAILURE REASONS")

        for reason, count in reason_counts.items():
            print(f"{reason}: {count}")

        print("\nOUTPUT FILES")
        print(f"Allocations: {ALLOCATION_PATH}")
        print(f"Unmet demand: {UNMET_DEMAND_PATH}")
        print(f"Summary: {SUMMARY_PATH}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ---------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":
    run_allocation()
