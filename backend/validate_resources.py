
from sqlalchemy import func, text
from sqlalchemy.orm import configure_mappers

from app.database.connection import SessionLocal
from app.models import (
    Program,
    Course,
    Prerequisite,
    Faculty,
    FacultySkill,
    Availability,
    Room,
    StudentPlan,
    RegistrationInterest,
    Section,
    WorkloadAssignment,
)

# Register all SQLAlchemy relationships
configure_mappers()


def validate_resources():
    db = SessionLocal()

    try:
        print("\nRESOURCE DATA VALIDATION")
        print("=" * 45)

        # -----------------------------------------
        # 1. Record counts
        # -----------------------------------------

        counts = {
            "Programs": db.query(Program).count(),
            "Courses": db.query(Course).count(),
            "Prerequisites": db.query(Prerequisite).count(),
            "Faculty": db.query(Faculty).count(),
            "Faculty Skills": db.query(FacultySkill).count(),
            "Availability": db.query(Availability).count(),
            "Rooms": db.query(Room).count(),
            "Student Plans": db.query(StudentPlan).count(),
            "Registration Interests": db.query(
                RegistrationInterest
            ).count(),
            "Sections": db.query(Section).count(),
            "Workload Assignments": db.query(
                WorkloadAssignment
            ).count(),
        }

        for name, count in counts.items():
            print(f"{name:<28}: {count}")

        # -----------------------------------------
        # 2. Expected count checks
        # -----------------------------------------

        print("\nEXPECTED COUNT VALIDATION")
        print("-" * 45)

        expected = {
            "Programs": (counts["Programs"], 100),
            "Courses": (counts["Courses"], 1000),
            "Faculty": (counts["Faculty"], 500),
            "Availability": (counts["Availability"], 5025),
            "Rooms": (counts["Rooms"], 50),
        }

        count_errors = 0

        for name, (actual, target) in expected.items():
            passed = actual == target

            print(
                f"{name:<20}: {actual} / {target} "
                f"{'PASS' if passed else 'FAIL'}"
            )

            if not passed:
                count_errors += 1

        # -----------------------------------------
        # 3. Primary key validation
        # -----------------------------------------

        print("\nPRIMARY KEY VALIDATION")
        print("-" * 45)

        primary_key_checks = [
            ("Faculty IDs", Faculty, Faculty.faculty_id),
            ("Room IDs", Room, Room.room_id),
            ("Skill IDs", FacultySkill, FacultySkill.skill_id),
            (
                "Availability IDs",
                Availability,
                Availability.availability_id,
            ),
        ]

        duplicate_errors = 0

        for label, model, column in primary_key_checks:
            duplicates = (
                db.query(column, func.count(column))
                .group_by(column)
                .having(func.count(column) > 1)
                .count()
            )

            print(f"{label}: {duplicates} duplicates")

            duplicate_errors += duplicates

        # -----------------------------------------
        # 4. Foreign key validation
        # -----------------------------------------

        print("\nFOREIGN KEY VALIDATION")
        print("-" * 45)

        foreign_key_issues = db.execute(
            text("PRAGMA foreign_key_check")
        ).fetchall()

        print(f"Foreign key violations: {len(foreign_key_issues)}")

        # -----------------------------------------
        # 5. Faculty skill validation
        # -----------------------------------------

        print("\nFACULTY SKILL VALIDATION")
        print("-" * 45)

        faculty_without_skills = (
            db.query(Faculty)
            .filter(~Faculty.skills.any())
            .count()
        )

        print(
            "Faculty without skills: "
            f"{faculty_without_skills}"
        )

        # -----------------------------------------
        # 6. Availability validation
        # -----------------------------------------

        print("\nAVAILABILITY VALIDATION")
        print("-" * 45)

        faculty_without_availability = (
            db.query(Faculty)
            .filter(~Faculty.availabilities.any())
            .count()
        )

        print(
            "Faculty without availability: "
            f"{faculty_without_availability}"
        )

        invalid_availability = (
            db.query(Availability)
            .filter(
                Availability.start_time >= Availability.end_time
            )
            .count()
        )

        print(
            "Invalid availability time slots: "
            f"{invalid_availability}"
        )

        # -----------------------------------------
        # 7. Room validation
        # -----------------------------------------

        print("\nROOM VALIDATION")
        print("-" * 45)

        invalid_rooms = (
            db.query(Room)
            .filter(Room.capacity <= 0)
            .count()
        )

        print(f"Rooms with invalid capacity: {invalid_rooms}")

        # -----------------------------------------
        # 8. Faculty workload validation
        # -----------------------------------------

        print("\nFACULTY WORKLOAD VALIDATION")
        print("-" * 45)

        invalid_workload = (
            db.query(Faculty)
            .filter(Faculty.max_weekly_workload <= 0)
            .count()
        )

        print(f"Invalid workload limits: {invalid_workload}")

        # -----------------------------------------
        # 9. Final summary
        # -----------------------------------------

        total_issues = (
            count_errors
            + duplicate_errors
            + len(foreign_key_issues)
            + faculty_without_skills
            + faculty_without_availability
            + invalid_availability
            + invalid_rooms
            + invalid_workload
        )

        print("\nFINAL VALIDATION SUMMARY")
        print("=" * 45)

        if total_issues == 0:
            print("STATUS: ALL RESOURCE CHECKS PASSED")
        else:
            print(f"STATUS: {total_issues} ISSUE(S) FOUND")

    finally:
        db.close()


if __name__ == "__main__":
    validate_resources()
