
import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models import (
    Program,
    Course,
    StudentPlan,
    RegistrationInterest,
)

from app.services.data.config import (
    SEED,
    NUM_STUDENT_PLANS,
    ACADEMIC_YEAR,
    SEMESTERS,
    ACADEMIC_START_DATE,
    ACADEMIC_END_DATE,
)


def generate_student_data():
    rng = random.Random(SEED + 3)

    start_date = date.fromisoformat(ACADEMIC_START_DATE)
    end_date = date.fromisoformat(ACADEMIC_END_DATE)

    db: Session = SessionLocal()

    try:
        # ---------------------------------------------
        # 1. Prevent duplicate generation
        # ---------------------------------------------

        if (
            db.query(StudentPlan).first()
            or db.query(RegistrationInterest).first()
        ):
            print("Student plans or registration interests already exist.")
            print("Skipping generation to prevent duplicates.")
            return

        # ---------------------------------------------
        # 2. Load programs and courses
        # ---------------------------------------------

        programs = db.query(Program).order_by(
            Program.program_id
        ).all()

        courses = db.query(Course).order_by(
            Course.course_id
        ).all()

        if not programs or not courses:
            raise ValueError(
                "Programs and courses must exist before "
                "generating student data."
            )

        # Group courses by their program.
        courses_by_program = {}

        for course in courses:
            courses_by_program.setdefault(
                course.program_id,
                [],
            ).append(course)

        eligible_programs = [
            program
            for program in programs
            if courses_by_program.get(program.program_id)
        ]

        if not eligible_programs:
            raise ValueError(
                "No programs have courses available."
            )

        if not SEMESTERS:
            raise ValueError(
                "SEMESTERS configuration cannot be empty."
            )

        # ---------------------------------------------
        # 3. Generate student plans and interests
        # ---------------------------------------------

        total_plans = 0
        total_interests = 0
        interest_counter = 1

        batch_size = 1000

        plan_batch = []
        interest_batch = []

        print("\nSTARTING STUDENT DATA GENERATION")
        print("=" * 45)

        for i in range(1, NUM_STUDENT_PLANS + 1):

            # Distribute students across programs.
            program = rng.choice(eligible_programs)

            program_courses = courses_by_program[
                program.program_id
            ]

            # Each student gets 3-6 course interests,
            # depending on the number of available courses.
            number_of_interests = min(
                len(program_courses),
                rng.randint(3, 6),
            )

            selected_courses = rng.sample(
                program_courses,
                number_of_interests,
            )

            student_id = f"STU-{i:08d}"
            plan_id = f"PLN-{i:08d}"

            semester = rng.choice(SEMESTERS)

            # Keep study level within the program duration.
            duration = getattr(program, "duration_years", 4) or 4
            study_level = rng.randint(
                1,
                max(1, min(int(duration), 4)),
            )

            # Calculate planned credits from selected courses.
            planned_credits = sum(
                course.credits for course in selected_courses
            )

            # Generate a valid date inside the academic period.
            date_range = (end_date - start_date).days

            effective_date = start_date + timedelta(
                days=rng.randint(0, max(0, date_range))
            )

            student_plan = StudentPlan(
                student_plan_id=plan_id,
                student_id=student_id,
                program_id=program.program_id,
                academic_year=ACADEMIC_YEAR,
                semester=semester,
                study_level=study_level,
                planned_credits=planned_credits,
                effective_date=effective_date,
                status="ACTIVE",
            )

            plan_batch.append(student_plan)

            # -----------------------------------------
            # Generate course registration interests
            # -----------------------------------------

            for preference_rank, course in enumerate(
                selected_courses,
                start=1,
            ):

                interest_date = effective_date

                interest = RegistrationInterest(
                    interest_id=f"INT-{interest_counter:09d}",
                    student_plan_id=plan_id,
                    course_id=course.course_id,
                    preference_rank=preference_rank,
                    interest_date=interest_date,
                    status="REQUESTED",
                )

                interest_batch.append(interest)

                interest_counter += 1
                total_interests += 1

            total_plans += 1

            # -----------------------------------------
            # Save data in batches
            # -----------------------------------------

            if len(plan_batch) >= batch_size:
                db.add_all(plan_batch)

                # Insert parent plans before their interests.
                db.flush()

                db.add_all(interest_batch)
                db.commit()

                print(
                    f"Generated {total_plans:,} / "
                    f"{NUM_STUDENT_PLANS:,} student plans"
                )

                plan_batch.clear()
                interest_batch.clear()

        # Save remaining records.
        if plan_batch:
            db.add_all(plan_batch)
            db.flush()

            db.add_all(interest_batch)
            db.commit()

        # ---------------------------------------------
        # 4. Final generation summary
        # ---------------------------------------------

        print("\nSTUDENT DATA GENERATION COMPLETED")
        print("=" * 45)

        print(f"Student plans: {total_plans:,}")
        print(f"Registration interests: {total_interests:,}")
        print(f"Academic year: {ACADEMIC_YEAR}")
        print(f"Semesters: {SEMESTERS}")
        print(f"Random seed: {SEED + 3}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    generate_student_data()
