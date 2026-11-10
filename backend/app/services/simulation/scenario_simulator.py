
import json
import math
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import text

from app.database.connection import SessionLocal
from app.services.allocation.allocator import (
    load_forecast,
    load_resources,
    find_allocation,
    SEMESTER_DATES,
    SUMMARY_PATH,
)


def validate_parameters(
    demand_change_pct,
    faculty_availability_reduction_pct,
    room_capacity_change_pct,
):
    """Validate scenario adjustment percentages."""

    if not -30 <= demand_change_pct <= 50:
        raise ValueError("Demand adjustment must be between -30% and 50%.")

    if not 0 <= faculty_availability_reduction_pct <= 50:
        raise ValueError(
            "Faculty availability reduction must be between 0% and 50%."
        )

    if not -30 <= room_capacity_change_pct <= 30:
        raise ValueError(
            "Room capacity adjustment must be between -30% and 30%."
        )


def calculate_allocation_rate(allocated, planned):
    if planned == 0:
        return 0.0

    return round((allocated / planned) * 100, 2)


def run_scenario(
    demand_change_pct=0,
    faculty_availability_reduction_pct=0,
    room_capacity_change_pct=0,
):
    """
    Run a what-if allocation simulation.

    Important:
    - Reads the original forecast and database.
    - Applies scenario changes in memory.
    - Does not insert, update, or delete database records.
    - Does not overwrite existing CSV or JSON files.
    """

    validate_parameters(
        demand_change_pct,
        faculty_availability_reduction_pct,
        room_capacity_change_pct,
    )

    forecast = load_forecast()

    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(
            "Baseline allocation summary was not found."
        )

    with open(SUMMARY_PATH, "r", encoding="utf-8") as file:
        baseline = json.load(file)

    db = SessionLocal()

    try:
        # Enforce read-only access on this SQLite connection.
        db.execute(text("PRAGMA query_only=ON"))

        original_resources = load_resources(db)

        # Make a separate resource dictionary for this simulation.
        resources = dict(original_resources)

        faculty = resources["faculty"]

        # Simulate a percentage reduction in faculty availability.
        faculty_ids = sorted(faculty.keys())

        unavailable_count = round(
            len(faculty_ids)
            * faculty_availability_reduction_pct
            / 100
        )

        unavailable_ids = set(
            faculty_ids[:unavailable_count]
        )

        resources["availability"] = {
            faculty_id: records
            for faculty_id, records in resources["availability"].items()
            if faculty_id not in unavailable_ids
        }

        # Simulate room capacity changes without modifying ORM objects.
        adjusted_rooms = []

        for room in resources["rooms"]:
            adjusted_capacity = max(
                1,
                int(round(
                    room.capacity
                    * (1 + room_capacity_change_pct / 100)
                )),
            )

            adjusted_rooms.append(
                SimpleNamespace(
                    room_id=room.room_id,
                    room_name=room.room_name,
                    capacity=adjusted_capacity,
                    room_type=room.room_type,
                )
            )

        resources["rooms"] = adjusted_rooms

        faculty_workload = {}
        faculty_bookings = {}
        room_bookings = {}

        total_demand = 0
        total_planned_sections = 0
        allocated_sections = 0
        unallocated_sections = 0
        total_allocated_capacity = 0

        unmet_rows = []

        for _, row in forecast.iterrows():

            course_id = str(row["course_id"])
            course = resources["courses"].get(course_id)

            if course is None:
                raise ValueError(
                    f"Course not found in database: {course_id}"
                )

            semester = int(row["semester"])

            original_demand = int(row["predicted_demand"])

            predicted_demand = max(
                0,
                int(round(
                    original_demand
                    * (1 + demand_change_pct / 100)
                )),
            )

            target_size = int(row["target_section_size"])

            planned_sections = (
                math.ceil(predicted_demand / target_size)
                if predicted_demand > 0
                else 0
            )

            weekly_hours = min(
                max(int(course.credits), 1),
                3,
            )

            remaining_demand = predicted_demand

            course_allocated_sections = 0
            course_unallocated_sections = 0
            course_allocated_capacity = 0

            for _ in range(planned_sections):

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

                if allocation:

                    person = allocation["faculty"]
                    room = allocation["room"]

                    faculty_id = person.faculty_id
                    room_id = room.room_id

                    workload_key = (faculty_id, semester)

                    faculty_workload[workload_key] = (
                        faculty_workload.get(workload_key, 0)
                        + weekly_hours
                    )

                    faculty_bookings.setdefault(
                        faculty_id, []
                    ).append((
                        semester,
                        allocation["day"],
                        allocation["start_minutes"],
                        allocation["end_minutes"],
                    ))

                    room_bookings.setdefault(
                        room_id, []
                    ).append((
                        semester,
                        allocation["day"],
                        allocation["start_minutes"],
                        allocation["end_minutes"],
                    ))

                    allocated_sections += 1
                    course_allocated_sections += 1

                    course_allocated_capacity += target_size
                    total_allocated_capacity += target_size

                    remaining_demand = max(
                        0,
                        remaining_demand - target_size,
                    )

                else:
                    unallocated_sections += 1
                    course_unallocated_sections += 1

            total_demand += predicted_demand
            total_planned_sections += planned_sections

            unmet_rows.append({
                "course_id": course_id,
                "course_name": course.course_name,
                "semester": semester,
                "predicted_demand": predicted_demand,
                "planned_sections": planned_sections,
                "allocated_sections": course_allocated_sections,
                "unallocated_sections": course_unallocated_sections,
                "allocated_capacity": course_allocated_capacity,
                "unmet_demand": remaining_demand,
            })

        total_unmet_demand = sum(
            item["unmet_demand"] for item in unmet_rows
        )

        simulated = {
            "total_predicted_demand": total_demand,
            "total_planned_sections": total_planned_sections,
            "allocated_sections": allocated_sections,
            "unallocated_sections": unallocated_sections,
            "total_allocated_capacity": total_allocated_capacity,
            "total_unmet_demand": total_unmet_demand,
            "active_faculty": len(faculty) - len(unavailable_ids),
            "active_rooms": len(adjusted_rooms),
            "allocation_rate_pct": calculate_allocation_rate(
                allocated_sections,
                total_planned_sections,
            ),
        }

        baseline_result = {
            "total_predicted_demand": baseline.get(
                "total_predicted_demand", 0
            ),
            "total_planned_sections": baseline.get(
                "total_planned_sections", 0
            ),
            "allocated_sections": baseline.get(
                "allocated_sections", 0
            ),
            "unallocated_sections": baseline.get(
                "unallocated_sections", 0
            ),
            "total_allocated_capacity": baseline.get(
                "total_allocated_capacity", 0
            ),
            "total_unmet_demand": baseline.get(
                "total_unmet_demand", 0
            ),
            "active_faculty": baseline.get("active_faculty", 0),
            "active_rooms": baseline.get("active_rooms", 0),
            "allocation_rate_pct": calculate_allocation_rate(
                baseline.get("allocated_sections", 0),
                baseline.get("total_planned_sections", 0),
            ),
        }

        top_unmet_courses = sorted(
            unmet_rows,
            key=lambda item: item["unmet_demand"],
            reverse=True,
        )[:10]

        return {
            "scenario_parameters": {
                "demand_change_pct": demand_change_pct,
                "faculty_availability_reduction_pct":
                    faculty_availability_reduction_pct,
                "room_capacity_change_pct": room_capacity_change_pct,
            },
            "baseline": baseline_result,
            "simulated": simulated,
            "changes": {
                key: simulated[key] - baseline_result[key]
                for key in [
                    "total_predicted_demand",
                    "total_planned_sections",
                    "allocated_sections",
                    "unallocated_sections",
                    "total_allocated_capacity",
                    "total_unmet_demand",
                ]
            },
            "top_unmet_courses": top_unmet_courses,
            "database_modified": False,
            "output_files_modified": False,
        }

    finally:
        db.close()
