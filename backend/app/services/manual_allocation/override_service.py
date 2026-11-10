
from pathlib import Path
from datetime import date, datetime, time
import json
import os
import re
import tempfile

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


BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = BASE_DIR / "data" / "output"
OVERRIDE_PATH = OUTPUT_DIR / "manual_allocation_overrides.json"


SEMESTER_DATES = {
    1: (date(2026, 1, 1), date(2026, 6, 30)),
    2: (date(2026, 7, 1), date(2026, 12, 31)),
}

VALID_DAYS = {
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
}

ACTIVE_ASSIGNMENT_STATUSES = ["PROPOSED", "APPROVED"]


# ---------------------------------------------------------
# FILE STORAGE
# ---------------------------------------------------------

def load_overrides():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not OVERRIDE_PATH.exists():
        return {}

    with open(OVERRIDE_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "Manual override file has an invalid format."
        )

    return data


def save_overrides(overrides):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".tmp",
            dir=OUTPUT_DIR,
            delete=False,
        ) as file:
            json.dump(overrides, file, indent=4)
            temp_path = file.name

        os.replace(temp_path, OVERRIDE_PATH)

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


# ---------------------------------------------------------
# GENERAL HELPERS
# ---------------------------------------------------------

def normalize_skill(value):
    """
    Normalize skill/course names for comparison.

    Example:
        Python Programming -> pythonprogramming
    """

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).lower(),
    )


def time_to_minutes(value):
    """
    Convert a database time/string value into minutes.
    Supports both datetime.time and HH:MM strings.
    """

    if isinstance(value, time):
        return value.hour * 60 + value.minute

    if isinstance(value, str):
        parts = value.strip().split(":")

        if len(parts) < 2:
            raise ValueError("Invalid time format.")

        hours = int(parts[0])
        minutes = int(parts[1])

        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError("Invalid time value.")

        return hours * 60 + minutes

    raise ValueError("Unsupported time value.")


def dates_overlap(start1, end1, start2, end2):
    if start1 is None:
        start1 = date.min

    if end1 is None:
        end1 = date.max

    if start2 is None:
        start2 = date.min

    if end2 is None:
        end2 = date.max

    return start1 <= end2 and start2 <= end1


def is_active_during(record, start_date, end_date):
    return dates_overlap(
        record.effective_start_date,
        record.effective_end_date,
        start_date,
        end_date,
    )


def intervals_overlap(start1, end1, start2, end2):
    """
    Adjacent classes are allowed.

    Example:
        09:00-10:00 and 10:00-11:00 do not conflict.
    """

    return start1 < end2 and start2 < end1


def get_room_preference(course_name):
    name = str(course_name).lower()

    lab_keywords = [
        "lab",
        "practical",
        "programming",
        "computer",
    ]

    if any(word in name for word in lab_keywords):
        return "LAB"

    return "CLASSROOM"


def get_original_faculty(db, section_id):
    return (
        db.query(WorkloadAssignment)
        .filter(
            WorkloadAssignment.section_id == section_id,
            WorkloadAssignment.status.in_(
                ACTIVE_ASSIGNMENT_STATUSES
            ),
        )
        .first()
    )


def get_effective_faculty_id(assignment, overrides):
    """
    Return the faculty member after considering
    an already-applied manual override.
    """

    override = overrides.get(assignment.section_id, {})

    return override.get(
        "faculty_id",
        assignment.faculty_id,
    )


def get_effective_room_id(section, overrides):
    """
    Return the room after considering
    an already-applied manual override.
    """

    override = overrides.get(section.section_id, {})

    return override.get(
        "room_id",
        section.room_id,
    )


def get_section_time_range(section):
    if (
        not section.scheduled_day
        or not section.start_time
        or not section.end_time
    ):
        return None

    try:
        start = time_to_minutes(section.start_time)
        end = time_to_minutes(section.end_time)
    except (TypeError, ValueError):
        return None

    if end <= start:
        return None

    return start, end


# ---------------------------------------------------------
# RESOURCE LISTS
# ---------------------------------------------------------

def get_resources():
    """
    Return active faculty and rooms.

    Faculty skills are included so the frontend can
    display the faculty member's available expertise.
    """

    db = SessionLocal()

    try:
        faculty_records = (
            db.query(Faculty)
            .filter(Faculty.status == "ACTIVE")
            .order_by(Faculty.faculty_name)
            .all()
        )

        room_records = (
            db.query(Room)
            .filter(Room.is_active.is_(True))
            .order_by(Room.room_name)
            .all()
        )

        faculty_ids = [
            item.faculty_id
            for item in faculty_records
        ]

        skill_records = []

        if faculty_ids:
            skill_records = (
                db.query(FacultySkill)
                .filter(
                    FacultySkill.faculty_id.in_(faculty_ids)
                )
                .all()
            )

        skills_by_faculty = {}

        for skill in skill_records:
            skills_by_faculty.setdefault(
                skill.faculty_id,
                [],
            ).append(skill.skill_name)

        return {
            "faculty": [
                {
                    "faculty_id": item.faculty_id,
                    "faculty_name": item.faculty_name,
                    "department": item.department,
                    "max_weekly_workload": (
                        item.max_weekly_workload
                    ),
                    "skills": skills_by_faculty.get(
                        item.faculty_id,
                        [],
                    ),
                }
                for item in faculty_records
            ],
            "rooms": [
                {
                    "room_id": item.room_id,
                    "room_name": item.room_name,
                    "building": item.building,
                    "capacity": item.capacity,
                    "room_type": item.room_type,
                }
                for item in room_records
            ],
        }

    finally:
        db.close()


# ---------------------------------------------------------
# VALIDATE A PROPOSED REASSIGNMENT
# ---------------------------------------------------------

def validate_override(
    section_id,
    faculty_id=None,
    room_id=None,
):
    """
    Validate a faculty and/or room reassignment.

    This function does not modify the database
    or save an override.
    """

    if not faculty_id and not room_id:
        raise ValueError(
            "Select a replacement faculty member or room."
        )

    db = SessionLocal()

    try:
        # ---------------------------------------------
        # SECTION VALIDATION
        # ---------------------------------------------

        section = (
            db.query(Section)
            .filter(
                Section.section_id == section_id
            )
            .first()
        )

        if section is None:
            raise ValueError("Section not found.")

        if section.status not in ["PROPOSED", "OPEN"]:
            raise ValueError(
                "Only proposed or open sections can be reassigned."
            )

        if section.semester not in SEMESTER_DATES:
            raise ValueError(
                "Unsupported semester for reassignment."
            )

        if (
            not section.scheduled_day
            or not section.start_time
            or not section.end_time
        ):
            raise ValueError(
                "This section does not have a complete timetable."
            )

        day = section.scheduled_day.strip().upper()

        if day not in VALID_DAYS:
            raise ValueError(
                "Invalid section timetable day."
            )

        start_date, end_date = SEMESTER_DATES[
            section.semester
        ]

        start_minutes = time_to_minutes(
            section.start_time
        )

        end_minutes = time_to_minutes(
            section.end_time
        )

        if end_minutes <= start_minutes:
            raise ValueError(
                "Invalid section time range."
            )

        # ---------------------------------------------
        # COURSE VALIDATION
        # ---------------------------------------------

        course = (
            db.query(Course)
            .filter(
                Course.course_id == section.course_id
            )
            .first()
        )

        if course is None:
            raise ValueError("Course not found.")

        # ---------------------------------------------
        # ORIGINAL ASSIGNMENT
        # ---------------------------------------------

        original_assignment = get_original_faculty(
            db,
            section_id,
        )

        if original_assignment is None:
            raise ValueError(
                "This section has no active faculty assignment."
            )

        current_overrides = load_overrides()

        existing_override = current_overrides.get(
            section_id,
            {},
        )

        # Current effective assignment may already
        # include a previously applied override.

        current_faculty_id = existing_override.get(
            "faculty_id",
            original_assignment.faculty_id,
        )

        current_room_id = existing_override.get(
            "room_id",
            section.room_id,
        )

        selected_faculty_id = (
            faculty_id
            if faculty_id
            else current_faculty_id
        )

        selected_room_id = (
            room_id
            if room_id
            else current_room_id
        )

        # ---------------------------------------------
        # PREVENT NO-OP REASSIGNMENTS
        # ---------------------------------------------

        if (
            selected_faculty_id == current_faculty_id
            and selected_room_id == current_room_id
        ):
            raise ValueError(
                "No changes detected. Select a different "
                "faculty member or room."
            )

        if not selected_faculty_id:
            raise ValueError(
                "A faculty member must be assigned."
            )

        if not selected_room_id:
            raise ValueError(
                "A room must be assigned."
            )

        # ---------------------------------------------
        # SELECTED FACULTY
        # ---------------------------------------------

        selected_faculty = (
            db.query(Faculty)
            .filter(
                Faculty.faculty_id == selected_faculty_id,
                Faculty.status == "ACTIVE",
            )
            .first()
        )

        if selected_faculty is None:
            raise ValueError(
                "Selected faculty member does not exist "
                "or is inactive."
            )

        # ---------------------------------------------
        # SELECTED ROOM
        # ---------------------------------------------

        selected_room = (
            db.query(Room)
            .filter(
                Room.room_id == selected_room_id,
                Room.is_active.is_(True),
            )
            .first()
        )

        if selected_room is None:
            raise ValueError(
                "Selected room does not exist or is inactive."
            )

        errors = []
        warnings = []

        # ---------------------------------------------
        # FACULTY SKILL VALIDATION
        # ---------------------------------------------

        skills = (
            db.query(FacultySkill)
            .filter(
                FacultySkill.faculty_id == selected_faculty_id
            )
            .all()
        )

        matching_skills = [
            skill
            for skill in skills
            if (
                normalize_skill(skill.skill_name)
                == normalize_skill(course.course_name)
                and is_active_during(
                    skill,
                    start_date,
                    end_date,
                )
            )
        ]

        if not matching_skills:
            errors.append(
                "Selected faculty does not have an active "
                "matching skill for this course."
            )

        # ---------------------------------------------
        # LOAD SAME-SEMESTER ASSIGNMENTS
        # ---------------------------------------------

        workload_assignments = (
            db.query(WorkloadAssignment)
            .filter(
                WorkloadAssignment.academic_year
                == section.academic_year,
                WorkloadAssignment.semester
                == section.semester,
                WorkloadAssignment.status.in_(
                    ACTIVE_ASSIGNMENT_STATUSES
                ),
            )
            .all()
        )

        # ---------------------------------------------
        # FACULTY WORKLOAD VALIDATION
        # ---------------------------------------------

        total_workload = 0

        for assignment in workload_assignments:

            if assignment.section_id == section_id:
                continue

            if not dates_overlap(
                assignment.effective_start_date,
                assignment.effective_end_date,
                start_date,
                end_date,
            ):
                continue

            effective_faculty_id = (
                get_effective_faculty_id(
                    assignment,
                    current_overrides,
                )
            )

            if effective_faculty_id == selected_faculty_id:
                total_workload += (
                    assignment.weekly_hours or 0
                )

        proposed_weekly_hours = (
            original_assignment.weekly_hours or 0
        )

        if (
            total_workload + proposed_weekly_hours
            > selected_faculty.max_weekly_workload
        ):
            errors.append(
                "Faculty weekly workload limit would be exceeded."
            )

        # ---------------------------------------------
        # FACULTY AVAILABILITY VALIDATION
        # ---------------------------------------------

        availability_records = (
            db.query(Availability)
            .filter(
                Availability.faculty_id
                == selected_faculty_id,
                Availability.status == "AVAILABLE",
                Availability.day_of_week == day,
            )
            .all()
        )

        has_available_slot = False

        for record in availability_records:

            if not is_active_during(
                record,
                start_date,
                end_date,
            ):
                continue

            available_start = time_to_minutes(
                record.start_time
            )

            available_end = time_to_minutes(
                record.end_time
            )

            if (
                available_start <= start_minutes
                and available_end >= end_minutes
            ):
                has_available_slot = True
                break

        if not has_available_slot:
            errors.append(
                "Selected faculty is not available for "
                "the section's scheduled time."
            )

        # ---------------------------------------------
        # FACULTY LEAVE VALIDATION
        # ---------------------------------------------

        leave_records = (
            db.query(Availability)
            .filter(
                Availability.faculty_id
                == selected_faculty_id,
                Availability.status == "ON_LEAVE",
                Availability.day_of_week == day,
            )
            .all()
        )

        for leave in leave_records:

            if is_active_during(
                leave,
                start_date,
                end_date,
            ):
                errors.append(
                    "Selected faculty has a leave record "
                    "for this weekday during the semester."
                )
                break

        # ---------------------------------------------
        # FACULTY TIMETABLE CONFLICT VALIDATION
        # ---------------------------------------------

        for assignment in workload_assignments:

            if assignment.section_id == section_id:
                continue

            effective_faculty_id = (
                get_effective_faculty_id(
                    assignment,
                    current_overrides,
                )
            )

            if effective_faculty_id != selected_faculty_id:
                continue

            other_section = (
                db.query(Section)
                .filter(
                    Section.section_id
                    == assignment.section_id
                )
                .first()
            )

            if other_section is None:
                continue

            # Explicitly restrict the comparison to
            # the same academic year and semester.

            if (
                other_section.academic_year
                != section.academic_year
                or other_section.semester
                != section.semester
            ):
                continue

            if (
                not other_section.scheduled_day
                or other_section.scheduled_day.strip().upper()
                != day
            ):
                continue

            other_range = get_section_time_range(
                other_section
            )

            if other_range is None:
                continue

            other_start, other_end = other_range

            if intervals_overlap(
                start_minutes,
                end_minutes,
                other_start,
                other_end,
            ):
                errors.append(
                    "Selected faculty has a timetable conflict "
                    f"with section {other_section.section_id} "
                    f"({other_section.scheduled_day} "
                    f"{other_section.start_time}-"
                    f"{other_section.end_time})."
                )
                break

        # ---------------------------------------------
        # ROOM CAPACITY VALIDATION
        # ---------------------------------------------

        if (
            selected_room.capacity
            < section.section_capacity
        ):
            errors.append(
                "Selected room capacity is smaller than "
                "the section capacity."
            )

        # ---------------------------------------------
        # ROOM TYPE VALIDATION
        # ---------------------------------------------

        preferred_type = get_room_preference(
            course.course_name
        )

        if selected_room.room_type not in [
            preferred_type,
            "LECTURE_HALL",
        ]:
            warnings.append(
                f"Room type {selected_room.room_type} differs "
                f"from the preferred type {preferred_type}."
            )

        # ---------------------------------------------
        # ROOM TIMETABLE CONFLICT VALIDATION
        # ---------------------------------------------

        # Fetch only sections from the same academic
        # year and semester as the target section.

        other_sections = (
            db.query(Section)
            .filter(
                Section.academic_year
                == section.academic_year,
                Section.semester == section.semester,
                Section.status.in_(["PROPOSED", "OPEN"]),
            )
            .all()
        )

        for other in other_sections:

            if other.section_id == section_id:
                continue

            effective_room_id = get_effective_room_id(
                other,
                current_overrides,
            )

            if effective_room_id != selected_room_id:
                continue

            if (
                not other.scheduled_day
                or other.scheduled_day.strip().upper() != day
            ):
                continue

            other_range = get_section_time_range(other)

            if other_range is None:
                continue

            other_start, other_end = other_range

            if intervals_overlap(
                start_minutes,
                end_minutes,
                other_start,
                other_end,
            ):
                errors.append(
                    f"Room conflict: {selected_room_id} is "
                    f"already assigned to section "
                    f"{other.section_id} "
                    f"({other.scheduled_day} "
                    f"{other.start_time}-{other.end_time}, "
                    f"Semester {other.semester})."
                )
                break

        # ---------------------------------------------
        # VALIDATION RESPONSE
        # ---------------------------------------------

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,

            "section": {
                "section_id": section.section_id,
                "course_id": course.course_id,
                "course_name": course.course_name,
                "semester": section.semester,
                "section_capacity": section.section_capacity,
                "scheduled_day": day,
                "start_time": section.start_time,
                "end_time": section.end_time,
                "weekly_hours": proposed_weekly_hours,
            },

            # Original database assignment.
            "original_assignment": {
                "faculty_id": original_assignment.faculty_id,
                "room_id": section.room_id,
            },

            # Effective assignment before this change.
            "current_assignment": {
                "faculty_id": current_faculty_id,
                "room_id": current_room_id,
            },

            # Proposed assignment.
            "proposed_assignment": {
                "faculty_id": selected_faculty.faculty_id,
                "faculty_name": selected_faculty.faculty_name,
                "room_id": selected_room.room_id,
                "room_name": selected_room.room_name,
            },

            "workload": {
                "existing_weekly_hours": total_workload,
                "proposed_weekly_hours": proposed_weekly_hours,
                "maximum_weekly_hours": (
                    selected_faculty.max_weekly_workload
                ),
            },
        }

    finally:
        db.close()


# ---------------------------------------------------------
# PREVIEW
# ---------------------------------------------------------

def preview_override(
    section_id,
    faculty_id=None,
    room_id=None,
):
    """
    Preview a proposed reassignment without saving it.
    """

    result = validate_override(
        section_id=section_id,
        faculty_id=faculty_id,
        room_id=room_id,
    )

    result["preview_only"] = True
    result["saved"] = False

    return result


# ---------------------------------------------------------
# APPLY VALIDATED OVERRIDE
# ---------------------------------------------------------

def apply_override(
    section_id,
    faculty_id=None,
    room_id=None,
):
    """
    Revalidate and save an approved manual override.

    The original database and allocation CSV are not modified.
    """

    # Always validate again before saving.
    result = validate_override(
        section_id=section_id,
        faculty_id=faculty_id,
        room_id=room_id,
    )

    if not result["valid"]:
        return {
            **result,
            "saved": False,
            "message": (
                "Reassignment rejected. "
                "Resolve validation errors first."
            ),
        }

    overrides = load_overrides()

    original = result["original_assignment"]
    current = result["current_assignment"]
    proposed = result["proposed_assignment"]
    section = result["section"]

    override_record = {
        "section_id": section_id,
        "course_id": section["course_id"],
        "course_name": section["course_name"],
        "semester": section["semester"],

        "original_faculty_id": original["faculty_id"],
        "original_room_id": original["room_id"],

        "previous_faculty_id": current["faculty_id"],
        "previous_room_id": current["room_id"],

        "faculty_id": proposed["faculty_id"],
        "faculty_name": proposed["faculty_name"],

        "room_id": proposed["room_id"],
        "room_name": proposed["room_name"],

        "scheduled_day": section["scheduled_day"],
        "start_time": section["start_time"],
        "end_time": section["end_time"],
        "weekly_hours": section["weekly_hours"],

        "status": "APPLIED",
        "updated_at": datetime.now().isoformat(),
    }

    overrides[section_id] = override_record

    save_overrides(overrides)

    return {
        **result,
        "saved": True,
        "message": (
            "Manual allocation override applied successfully."
        ),
        "override": override_record,
    }


# ---------------------------------------------------------
# LIST APPLIED OVERRIDES
# ---------------------------------------------------------

def get_overrides():
    """
    Return all saved manual allocation overrides.
    """

    overrides = load_overrides()

    return {
        "total_overrides": len(overrides),
        "overrides": list(overrides.values()),
    }
