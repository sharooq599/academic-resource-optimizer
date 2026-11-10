
from sqlalchemy import text
from sqlalchemy.orm import configure_mappers

from app.database.connection import SessionLocal

# Import ALL models so SQLAlchemy can resolve relationships
from app.models.program import Program
from app.models.course import Course
from app.models.prerequisite import Prerequisite
from app.models.student import StudentPlan, RegistrationInterest
from app.models.faculty import Faculty
from app.models.faculty_skill import FacultySkill
from app.models.availability import Availability
from app.models.room import Room
from app.models.section import Section
from app.models.allocation import WorkloadAssignment

# Configure all SQLAlchemy relationships
configure_mappers()


def validate_master_data():

    db = SessionLocal()

    try:

        print("\nMASTER DATA VALIDATION")
        print("=" * 40)

        # 1. Record counts
        program_count = db.query(Program).count()
        course_count = db.query(Course).count()
        prerequisite_count = db.query(Prerequisite).count()

        print("Programs:", program_count)
        print("Courses:", course_count)
        print("Prerequisites:", prerequisite_count)

        # 2. Primary key uniqueness
        duplicate_programs = db.execute(
            text("""
                SELECT program_id
                FROM programs
                GROUP BY program_id
                HAVING COUNT(*) > 1
            """)
        ).fetchall()

        duplicate_courses = db.execute(
            text("""
                SELECT course_id
                FROM courses
                GROUP BY course_id
                HAVING COUNT(*) > 1
            """)
        ).fetchall()

        print("\nPRIMARY KEY VALIDATION")
        print("Duplicate programs:", len(duplicate_programs))
        print("Duplicate courses:", len(duplicate_courses))

        # 3. Foreign key validation
        foreign_key_errors = db.execute(
            text("PRAGMA foreign_key_check")
        ).fetchall()

        print("\nFOREIGN KEY VALIDATION")
        print("Foreign key violations:", len(foreign_key_errors))

        # 4. Prerequisite validation
        invalid_prerequisites = db.execute(
            text("""
                SELECT p.prerequisite_id
                FROM prerequisites p
                LEFT JOIN courses c1
                    ON p.course_id = c1.course_id
                LEFT JOIN courses c2
                    ON p.prerequisite_course_id = c2.course_id
                WHERE c1.course_id IS NULL
                   OR c2.course_id IS NULL
                   OR p.course_id = p.prerequisite_course_id
            """)
        ).fetchall()

        print("\nPREREQUISITE VALIDATION")
        print(
            "Invalid prerequisite records:",
            len(invalid_prerequisites)
        )

        # 5. Final result
        print("\nVALIDATION SUMMARY")

        success = (
            program_count == 100
            and course_count == 1000
            and len(duplicate_programs) == 0
            and len(duplicate_courses) == 0
            and len(foreign_key_errors) == 0
            and len(invalid_prerequisites) == 0
        )

        if success:
            print("STATUS: ALL CHECKS PASSED")
        else:
            print("STATUS: VALIDATION FAILED")

    except Exception as e:

        print("Validation error:", e)

    finally:

        db.close()


if __name__ == "__main__":
    validate_master_data()
