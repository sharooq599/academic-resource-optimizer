
from collections import defaultdict
from app.database.connection import SessionLocal
from app.models import (
    Course, Faculty, FacultySkill, Availability,
    Room, Section, WorkloadAssignment
)
import re

YEAR = 2026


def normalize(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end


def validate_allocation():
    db = SessionLocal()
    errors = []

    try:
        sections = db.query(Section).filter(
            Section.academic_year == YEAR,
            Section.status == "PROPOSED"
        ).all()

        assignments = db.query(WorkloadAssignment).filter(
            WorkloadAssignment.academic_year == YEAR,
            WorkloadAssignment.status == "PROPOSED"
        ).all()

        courses = {x.course_id: x for x in db.query(Course).all()}
        faculty = {x.faculty_id: x for x in db.query(Faculty).all()}
        rooms = {x.room_id: x for x in db.query(Room).all()}

        skills = defaultdict(set)
        for skill in db.query(FacultySkill).all():
            skills[skill.faculty_id].add(normalize(skill.skill_name))

        availability = defaultdict(list)
        for item in db.query(Availability).filter(
            Availability.status == "AVAILABLE"
        ).all():
            availability[item.faculty_id].append(item)

        assignments_by_section = defaultdict(list)
        for item in assignments:
            assignments_by_section[item.section_id].append(item)

        faculty_workload = defaultdict(int)
        faculty_bookings = defaultdict(list)
        room_bookings = defaultdict(list)

        allocated = 0
        unallocated = 0

        for section in sections:
            section_assignments = assignments_by_section.get(
                section.section_id, []
            )

            if not section_assignments:
                if section.room_id is not None:
                    errors.append(
                        f"{section.section_id}: room assigned without faculty assignment"
                    )
                unallocated += 1
                continue

            if len(section_assignments) != 1:
                errors.append(
                    f"{section.section_id}: expected one assignment, "
                    f"found {len(section_assignments)}"
                )
                continue

            assignment = section_assignments[0]
            allocated += 1

            course = courses.get(section.course_id)
            person = faculty.get(assignment.faculty_id)
            room = rooms.get(section.room_id)

            if not course:
                errors.append(f"{section.section_id}: missing course")
                continue

            if not person or person.status != "ACTIVE":
                errors.append(f"{section.section_id}: invalid faculty")
                continue

            if not room or not room.is_active:
                errors.append(f"{section.section_id}: invalid room")
                continue

            # Faculty skill validation
            if normalize(course.course_name) not in skills[person.faculty_id]:
                errors.append(
                    f"{section.section_id}: faculty lacks course skill"
                )

            # Room capacity validation
            if room.capacity < section.section_capacity:
                errors.append(
                    f"{section.section_id}: room capacity too small"
                )

            # Schedule completeness
            if not all([
                section.scheduled_day,
                section.start_time,
                section.end_time
            ]):
                errors.append(
                    f"{section.section_id}: incomplete timetable"
                )
                continue

            start = section.start_time
            end = section.end_time

            if start >= end:
                errors.append(
                    f"{section.section_id}: invalid time interval"
                )
                continue

            semester = section.semester
            faculty_id = person.faculty_id
            room_id = room.room_id

            # Availability validation
            valid_availability = any(
                a.day_of_week.upper() == section.scheduled_day.upper()
                and a.start_time <= start
                and a.end_time >= end
                for a in availability[faculty_id]
            )

            if not valid_availability:
                errors.append(
                    f"{section.section_id}: outside faculty availability"
                )

            # Faculty and room conflict validation
            booking = (semester, section.scheduled_day, start, end)

            for old in faculty_bookings[faculty_id]:
                if old[0] == semester and old[1] == section.scheduled_day:
                    if overlaps(start, end, old[2], old[3]):
                        errors.append(
                            f"{section.section_id}: faculty timetable conflict"
                        )

            for old in room_bookings[room_id]:
                if old[0] == semester and old[1] == section.scheduled_day:
                    if overlaps(start, end, old[2], old[3]):
                        errors.append(
                            f"{section.section_id}: room timetable conflict"
                        )

            faculty_bookings[faculty_id].append(booking)
            room_bookings[room_id].append(booking)

            # Faculty workload validation
            key = (faculty_id, semester)
            faculty_workload[key] += assignment.weekly_hours

            if faculty_workload[key] > person.max_weekly_workload:
                errors.append(
                    f"{faculty_id}, semester {semester}: workload exceeded"
                )

        print("\nALLOCATION VALIDATION")
        print("=" * 55)
        print("Total sections:", len(sections))
        print("Allocated sections:", allocated)
        print("Unallocated sections:", unallocated)
        print("Workload assignments:", len(assignments))

        print("\nVALIDATION ERRORS:", len(errors))

        for error in errors[:30]:
            print("FAIL:", error)

        if len(errors) > 30:
            print("Additional errors:", len(errors) - 30)

        if not errors:
            print("\nALL CHECKS PASSED!")

        else:
            print("\nVALIDATION NEEDS ATTENTION.")

    finally:
        db.close()


if __name__ == "__main__":
    validate_allocation()
