
from sqlalchemy import func, text
from sqlalchemy.orm import configure_mappers

from app.database.connection import SessionLocal
from app.models import (
    StudentPlan,
    RegistrationInterest,
    Course,
)

configure_mappers()


def validate_student_data():
    db = SessionLocal()

    try:
        print("\nSTUDENT DATA VALIDATION")
        print("=" * 50)

        # -----------------------------------------
        # 1. Record counts
        # -----------------------------------------

        total_plans = db.query(StudentPlan).count()
        total_interests = db.query(RegistrationInterest).count()

        unique_students = (
            db.query(func.count(func.distinct(StudentPlan.student_id)))
            .scalar()
        )

        print(f"Student plans             : {total_plans:,}")
        print(f"Unique students           : {unique_students:,}")
        print(f"Registration interests    : {total_interests:,}")

        # -----------------------------------------
        # 2. Expected count validation
        # -----------------------------------------

        print("\nEXPECTED COUNT VALIDATION")
        print("-" * 50)

        count_checks = {
            "Student plans": total_plans == 20000,
            "Unique students": unique_students == 20000,
            "Registration interests": (
                60000 <= total_interests <= 120000
            ),
        }

        count_errors = 0

        for label, passed in count_checks.items():
            print(f"{label:<30}: {'PASS' if passed else 'FAIL'}")

            if not passed:
                count_errors += 1

        # -----------------------------------------
        # 3. Duplicate validation
        # -----------------------------------------

        print("\nDUPLICATE VALIDATION")
        print("-" * 50)

        duplicate_plans = (
            db.query(
                StudentPlan.student_id,
                StudentPlan.academic_year,
                StudentPlan.semester,
            )
            .group_by(
                StudentPlan.student_id,
                StudentPlan.academic_year,
                StudentPlan.semester,
            )
            .having(func.count() > 1)
            .count()
        )

        duplicate_interests = (
            db.query(
                RegistrationInterest.student_plan_id,
                RegistrationInterest.course_id,
            )
            .group_by(
                RegistrationInterest.student_plan_id,
                RegistrationInterest.course_id,
            )
            .having(func.count() > 1)
            .count()
        )

        print(f"Duplicate student plans       : {duplicate_plans}")
        print(f"Duplicate course interests    : {duplicate_interests}")

        # -----------------------------------------
        # 4. Foreign key validation
        # -----------------------------------------

        print("\nFOREIGN KEY VALIDATION")
        print("-" * 50)

        fk_issues = db.execute(
            text("PRAGMA foreign_key_check")
        ).fetchall()

        print(f"Foreign key violations: {len(fk_issues)}")

        # -----------------------------------------
        # 5. Program-course relationship validation
        # -----------------------------------------

        print("\nPROGRAM AND COURSE VALIDATION")
        print("-" * 50)

        invalid_program_courses = (
            db.query(RegistrationInterest)
            .join(
                StudentPlan,
                RegistrationInterest.student_plan_id
                == StudentPlan.student_plan_id,
            )
            .join(
                Course,
                RegistrationInterest.course_id == Course.course_id,
            )
            .filter(
                StudentPlan.program_id != Course.program_id
            )
            .count()
        )

        print(
            "Interests linked to another program: "
            f"{invalid_program_courses}"
        )

        # -----------------------------------------
        # 6. Registration interest count per plan
        # -----------------------------------------

        print("\nINTEREST COUNT VALIDATION")
        print("-" * 50)

        interest_counts = (
            db.query(
                StudentPlan.student_plan_id,
                func.count(RegistrationInterest.interest_id),
            )
            .outerjoin(
                RegistrationInterest,
                StudentPlan.student_plan_id
                == RegistrationInterest.student_plan_id,
            )
            .group_by(StudentPlan.student_plan_id)
            .all()
        )

        plans_without_interests = sum(
            1 for _, count in interest_counts if count == 0
        )

        plans_with_invalid_interest_count = sum(
            1 for _, count in interest_counts
            if count < 3 or count > 6
        )

        print(f"Plans without interests: {plans_without_interests}")
        print(
            "Plans outside 3-6 interests: "
            f"{plans_with_invalid_interest_count}"
        )

        # -----------------------------------------
        # 7. Planned credits validation
        # -----------------------------------------

        print("\nPLANNED CREDITS VALIDATION")
        print("-" * 50)

        credit_results = (
            db.query(
                StudentPlan.student_plan_id,
                StudentPlan.planned_credits,
                func.coalesce(func.sum(Course.credits), 0),
            )
            .outerjoin(
                RegistrationInterest,
                StudentPlan.student_plan_id
                == RegistrationInterest.student_plan_id,
            )
            .outerjoin(
                Course,
                RegistrationInterest.course_id == Course.course_id,
            )
            .group_by(
                StudentPlan.student_plan_id,
                StudentPlan.planned_credits,
            )
            .all()
        )

        credit_mismatches = sum(
            1
            for _, planned, calculated in credit_results
            if planned != calculated
        )

        print(f"Planned credit mismatches: {credit_mismatches}")

        # -----------------------------------------
        # 8. Preference rank validation
        # -----------------------------------------

        print("\nPREFERENCE RANK VALIDATION")
        print("-" * 50)

        invalid_ranks = (
            db.query(RegistrationInterest)
            .filter(RegistrationInterest.preference_rank <= 0)
            .count()
        )

        print(f"Invalid preference ranks: {invalid_ranks}")

        # -----------------------------------------
        # 9. Semester validation
        # -----------------------------------------

        print("\nSEMESTER VALIDATION")
        print("-" * 50)

        invalid_semesters = (
            db.query(StudentPlan)
            .filter(~StudentPlan.semester.in_([1, 2]))
            .count()
        )

        print(f"Invalid semesters: {invalid_semesters}")

        # -----------------------------------------
        # 10. Final summary
        # -----------------------------------------

        total_issues = (
            count_errors
            + duplicate_plans
            + duplicate_interests
            + len(fk_issues)
            + invalid_program_courses
            + plans_without_interests
            + plans_with_invalid_interest_count
            + credit_mismatches
            + invalid_ranks
            + invalid_semesters
        )

        print("\nFINAL VALIDATION SUMMARY")
        print("=" * 50)

        if total_issues == 0:
            print("STATUS: ALL STUDENT DATA CHECKS PASSED")
        else:
            print(f"STATUS: {total_issues} ISSUE(S) FOUND")

    finally:
        db.close()


if __name__ == "__main__":
    validate_student_data()
