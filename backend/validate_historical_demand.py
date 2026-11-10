
from sqlalchemy import func, text
from sqlalchemy.orm import configure_mappers

from app.database.connection import SessionLocal

from app.models import (
    Course,
    HistoricalCourseDemand,
)

configure_mappers()


def validate_historical_demand():
    db = SessionLocal()

    try:
        print("\nHISTORICAL DEMAND VALIDATION")
        print("=" * 55)

        # -----------------------------------------
        # 1. Record counts
        # -----------------------------------------

        total_records = db.query(
            HistoricalCourseDemand
        ).count()

        total_courses = db.query(
            func.count(
                func.distinct(
                    HistoricalCourseDemand.course_id
                )
            )
        ).scalar()

        total_years = db.query(
            func.count(
                func.distinct(
                    HistoricalCourseDemand.academic_year
                )
            )
        ).scalar()

        print(f"Historical demand records : {total_records:,}")
        print(f"Unique courses            : {total_courses:,}")
        print(f"Academic years             : {total_years}")

        # -----------------------------------------
        # 2. Expected count validation
        # -----------------------------------------

        print("\nEXPECTED COUNT VALIDATION")
        print("-" * 55)

        count_checks = {
            "Historical records": total_records == 6000,
            "Unique courses": total_courses == 1000,
            "Academic years": total_years == 3,
        }

        count_errors = 0

        for label, passed in count_checks.items():
            print(f"{label:<30}: {'PASS' if passed else 'FAIL'}")

            if not passed:
                count_errors += 1

        # -----------------------------------------
        # 3. Academic year distribution
        # -----------------------------------------

        print("\nACADEMIC YEAR DISTRIBUTION")
        print("-" * 55)

        year_distribution = (
            db.query(
                HistoricalCourseDemand.academic_year,
                func.count(
                    HistoricalCourseDemand.historical_demand_id
                ),
            )
            .group_by(
                HistoricalCourseDemand.academic_year
            )
            .order_by(
                HistoricalCourseDemand.academic_year
            )
            .all()
        )

        for year, count in year_distribution:
            print(f"{year}: {count:,} records")

        # -----------------------------------------
        # 4. Duplicate validation
        # -----------------------------------------

        print("\nDUPLICATE VALIDATION")
        print("-" * 55)

        duplicate_records = (
            db.query(
                HistoricalCourseDemand.course_id,
                HistoricalCourseDemand.academic_year,
                HistoricalCourseDemand.semester,
            )
            .group_by(
                HistoricalCourseDemand.course_id,
                HistoricalCourseDemand.academic_year,
                HistoricalCourseDemand.semester,
            )
            .having(func.count() > 1)
            .count()
        )

        print(f"Duplicate demand records: {duplicate_records}")

        # -----------------------------------------
        # 5. Foreign key validation
        # -----------------------------------------

        print("\nFOREIGN KEY VALIDATION")
        print("-" * 55)

        fk_issues = db.execute(
            text("PRAGMA foreign_key_check")
        ).fetchall()

        print(f"Foreign key violations: {len(fk_issues)}")

        invalid_courses = (
            db.query(HistoricalCourseDemand)
            .outerjoin(
                Course,
                HistoricalCourseDemand.course_id
                == Course.course_id,
            )
            .filter(Course.course_id.is_(None))
            .count()
        )

        print(f"Invalid course references: {invalid_courses}")

        # -----------------------------------------
        # 6. Demand distribution validation
        # -----------------------------------------

        print("\nDEMAND DISTRIBUTION VALIDATION")
        print("-" * 55)

        invalid_distribution = (
            db.query(HistoricalCourseDemand)
            .filter(
                HistoricalCourseDemand.enrolled_count
                + HistoricalCourseDemand.waitlisted_count
                != HistoricalCourseDemand.demand_count
            )
            .count()
        )

        print(
            "Invalid demand distributions: "
            f"{invalid_distribution}"
        )

        # -----------------------------------------
        # 7. Negative value validation
        # -----------------------------------------

        print("\nNEGATIVE VALUE VALIDATION")
        print("-" * 55)

        negative_values = (
            db.query(HistoricalCourseDemand)
            .filter(
                (HistoricalCourseDemand.demand_count < 0)
                | (HistoricalCourseDemand.enrolled_count < 0)
                | (HistoricalCourseDemand.waitlisted_count < 0)
                | (HistoricalCourseDemand.sections_offered < 0)
            )
            .count()
        )

        print(f"Records with negative values: {negative_values}")

        # -----------------------------------------
        # 8. Source type validation
        # -----------------------------------------

        print("\nSOURCE VALIDATION")
        print("-" * 55)

        invalid_sources = (
            db.query(HistoricalCourseDemand)
            .filter(
                HistoricalCourseDemand.source_type
                != "SYNTHETIC_HISTORICAL"
            )
            .count()
        )

        print(f"Incorrect source labels: {invalid_sources}")

        # -----------------------------------------
        # 9. Records per course validation
        # -----------------------------------------

        print("\nCOURSE COVERAGE VALIDATION")
        print("-" * 55)

        course_coverage = (
            db.query(
                HistoricalCourseDemand.course_id,
                func.count(
                    HistoricalCourseDemand.historical_demand_id
                ),
            )
            .group_by(
                HistoricalCourseDemand.course_id
            )
            .all()
        )

        courses_with_incomplete_history = sum(
            1 for _, count in course_coverage
            if count != 6
        )

        print(
            "Courses without exactly 6 records: "
            f"{courses_with_incomplete_history}"
        )

        # -----------------------------------------
        # 10. Final summary
        # -----------------------------------------

        total_issues = (
            count_errors
            + duplicate_records
            + len(fk_issues)
            + invalid_courses
            + invalid_distribution
            + negative_values
            + invalid_sources
            + courses_with_incomplete_history
        )

        print("\nFINAL VALIDATION SUMMARY")
        print("=" * 55)

        if total_issues == 0:
            print("STATUS: ALL HISTORICAL DEMAND CHECKS PASSED")
        else:
            print(f"STATUS: {total_issues} ISSUE(S) FOUND")

    finally:
        db.close()


if __name__ == "__main__":
    validate_historical_demand()
