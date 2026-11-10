
import math
import random

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import SessionLocal

from app.models import (
    Course,
    StudentPlan,
    RegistrationInterest,
    HistoricalCourseDemand,
)

from app.services.data.config import (
    SEED,
    SEMESTERS,
)


def generate_historical_demand():
    rng = random.Random(SEED + 4)

    db: Session = SessionLocal()

    try:
        # ---------------------------------------------
        # 1. Prevent duplicate generation
        # ---------------------------------------------

        if db.query(HistoricalCourseDemand).first():
            print("Historical demand records already exist.")
            print("Skipping generation to prevent duplicates.")
            return

        # ---------------------------------------------
        # 2. Load courses
        # ---------------------------------------------

        courses = db.query(Course).order_by(
            Course.course_id
        ).all()

        if not courses:
            raise ValueError(
                "Courses must exist before generating historical demand."
            )

        if not db.query(RegistrationInterest).first():
            raise ValueError(
                "Registration interests must exist before generating "
                "historical demand."
            )

        # ---------------------------------------------
        # 3. Calculate current demand reference
        # ---------------------------------------------

        demand_rows = (
            db.query(
                RegistrationInterest.course_id,
                StudentPlan.semester,
                func.count(RegistrationInterest.interest_id),
            )
            .join(
                StudentPlan,
                RegistrationInterest.student_plan_id
                == StudentPlan.student_plan_id,
            )
            .group_by(
                RegistrationInterest.course_id,
                StudentPlan.semester,
            )
            .all()
        )

        current_demand = {
            (course_id, semester): count
            for course_id, semester, count in demand_rows
        }

        print("Loaded current registration demand.")
        print(f"Courses available: {len(courses)}")

        # ---------------------------------------------
        # 4. Historical year configuration
        # ---------------------------------------------

        historical_years = {
            2023: 0.75,
            2024: 0.85,
            2025: 0.95,
        }

        # The factors create a controlled upward trend.
        # Random variation prevents identical year patterns.

        # ---------------------------------------------
        # 5. Generate historical demand records
        # ---------------------------------------------

        records = []
        record_counter = 1

        for course in courses:

            target_size = max(
                1,
                course.target_section_size or 50,
            )

            for semester in SEMESTERS:

                reference_demand = current_demand.get(
                    (course.course_id, semester),
                    0,
                )

                # Give courses without current interests
                # a small synthetic baseline demand.
                if reference_demand == 0:
                    reference_demand = rng.randint(8, 25)

                for academic_year, growth_factor in (
                    historical_years.items()
                ):

                    variation = rng.uniform(0.90, 1.10)

                    demand_count = max(
                        0,
                        round(
                            reference_demand
                            * growth_factor
                            * variation
                        ),
                    )

                    # Estimate enrolled and waitlisted students.
                    enrollment_ratio = rng.uniform(0.88, 0.97)

                    enrolled_count = round(
                        demand_count * enrollment_ratio
                    )

                    if demand_count > 0:
                        enrolled_count = max(
                            1,
                            enrolled_count,
                        )

                    enrolled_count = min(
                        enrolled_count,
                        demand_count,
                    )

                    waitlisted_count = (
                        demand_count - enrolled_count
                    )

                    # Calculate sections offered.
                    sections_offered = (
                        math.ceil(enrolled_count / target_size)
                        if enrolled_count > 0
                        else 0
                    )

                    record = HistoricalCourseDemand(
                        historical_demand_id=(
                            f"HDM-{record_counter:09d}"
                        ),
                        course_id=course.course_id,
                        academic_year=academic_year,
                        semester=semester,
                        demand_count=demand_count,
                        enrolled_count=enrolled_count,
                        waitlisted_count=waitlisted_count,
                        sections_offered=sections_offered,
                        source_type="SYNTHETIC_HISTORICAL",
                    )

                    records.append(record)
                    record_counter += 1

        # ---------------------------------------------
        # 6. Save records
        # ---------------------------------------------

        db.add_all(records)
        db.commit()

        # ---------------------------------------------
        # 7. Generation summary
        # ---------------------------------------------

        print("\nHISTORICAL DEMAND GENERATION COMPLETED")
        print("=" * 50)

        print(f"Courses processed: {len(courses)}")
        print(f"Historical years: {list(historical_years.keys())}")
        print(f"Semesters: {SEMESTERS}")
        print(f"Total historical records: {len(records)}")
        print("Source: SYNTHETIC_HISTORICAL")
        print(f"Random seed: {SEED + 4}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    generate_historical_demand()
