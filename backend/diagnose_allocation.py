
import re
from collections import Counter

from app.database.connection import SessionLocal
from app.models import (
    Course,
    Faculty,
    FacultySkill,
    Availability,
    WorkloadAssignment,
)


def normalize(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


db = SessionLocal()

try:
    faculty = db.query(Faculty).filter(
        Faculty.status == "ACTIVE"
    ).all()

    courses = db.query(Course).all()
    skills = db.query(FacultySkill).all()

    availability = db.query(Availability).filter(
        Availability.status == "AVAILABLE"
    ).all()

    assignments = db.query(WorkloadAssignment).filter(
        WorkloadAssignment.academic_year == 2026,
        WorkloadAssignment.status == "PROPOSED",
    ).all()

    print("\nALLOCATION DIAGNOSTICS")
    print("=" * 55)

    # 1. Faculty skill coverage.
    skill_map = {}

    for skill in skills:
        skill_map.setdefault(
            normalize(skill.skill_name), set()
        ).add(skill.faculty_id)

    matched_courses = 0
    unmatched_courses = []

    for course in courses:
        key = normalize(course.course_name)
        matching = skill_map.get(key, set())

        if matching:
            matched_courses += 1
        else:
            unmatched_courses.append(course.course_name)

    print("\nFACULTY SKILL COVERAGE")
    print("-" * 55)
    print("Total courses:", len(courses))
    print("Courses with matching skills:", matched_courses)
    print("Courses without matching skills:", len(unmatched_courses))
    print("Unmatched course names:", sorted(set(unmatched_courses))[:20])

    # 2. Faculty skill distribution.
    faculty_skill_counts = Counter(
        skill.faculty_id for skill in skills
    )

    print("\nFACULTY SKILL DISTRIBUTION")
    print("-" * 55)
    print("Faculty with skills:", len(faculty_skill_counts))
    print("Faculty without skills:", len(faculty) - len(faculty_skill_counts))

    # 3. Availability distribution.
    availability_counts = Counter(
        item.faculty_id for item in availability
    )

    print("\nAVAILABILITY DISTRIBUTION")
    print("-" * 55)
    print("Faculty with availability:", len(availability_counts))
    print("Faculty without availability:", len(faculty) - len(availability_counts))
    print("Total available slots:", len(availability))

    # 4. Actual workload distribution.
    workload_by_faculty = Counter()

    for assignment in assignments:
        workload_by_faculty[
            (assignment.faculty_id, assignment.semester)
        ] += assignment.weekly_hours

    print("\nFACULTY WORKLOAD")
    print("-" * 55)

    for semester in [1, 2]:
        workloads = [
            workload_by_faculty[(person.faculty_id, semester)]
            for person in faculty
        ]

        assigned = [value for value in workloads if value > 0]

        print(f"\nSemester {semester}:")
        print("Faculty assigned:", len(assigned))
        print("Total weekly workload:", sum(assigned))
        print("Maximum assigned workload:", max(assigned, default=0))
        print("Average workload among assigned faculty:",
              round(sum(assigned) / len(assigned), 2) if assigned else 0)

    # 5. Most frequently assigned faculty.
    print("\nTOP ASSIGNED FACULTY")
    print("-" * 55)

    for semester in [1, 2]:
        top = sorted(
            [
                (person.faculty_name,
                 workload_by_faculty[(person.faculty_id, semester)])
                for person in faculty
                if workload_by_faculty[(person.faculty_id, semester)] > 0
            ],
            key=lambda item: item[1],
            reverse=True
        )[:10]

        print(f"\nSemester {semester}:")
        for name, hours in top:
            print(name, "-", hours, "hours")

    # 6. Availability date ranges.
    print("\nAVAILABILITY DATE RANGES")
    print("-" * 55)

    for item in availability[:5]:
        print(
            item.faculty_id,
            item.day_of_week,
            item.start_time,
            item.end_time,
            item.effective_start_date,
            item.effective_end_date,
        )

finally:
    db.close()
