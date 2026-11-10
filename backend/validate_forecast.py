
import json
import math
from pathlib import Path

import pandas as pd

from app.database.connection import SessionLocal
from app.models import Course


BASE_DIR = Path(__file__).resolve().parent

FORECAST_PATH = (
    BASE_DIR / "data" / "output"
    / "course_demand_forecast_2026.csv"
)

METRICS_PATH = (
    BASE_DIR / "data" / "output"
    / "forecast_metrics.json"
)


def validate_forecast():

    db = SessionLocal()

    try:
        print("\n2026 FORECAST VALIDATION")
        print("=" * 55)

        # -----------------------------------------
        # 1. Check files
        # -----------------------------------------

        if not FORECAST_PATH.exists():
            raise FileNotFoundError(
                f"Forecast file not found: {FORECAST_PATH}"
            )

        if not METRICS_PATH.exists():
            raise FileNotFoundError(
                f"Metrics file not found: {METRICS_PATH}"
            )

        df = pd.read_csv(FORECAST_PATH)

        with open(
            METRICS_PATH,
            "r",
            encoding="utf-8",
        ) as file:
            metrics = json.load(file)

        # -----------------------------------------
        # 2. Required columns
        # -----------------------------------------

        required_columns = [
            "course_id",
            "academic_year",
            "semester",
            "predicted_demand",
            "target_section_size",
            "predicted_sections_required",
            "source_type",
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        print("\nCOLUMN VALIDATION")
        print("-" * 55)

        print(f"Missing columns: {len(missing_columns)}")

        # -----------------------------------------
        # 3. Record count
        # -----------------------------------------

        print("\nRECORD VALIDATION")
        print("-" * 55)

        print(f"Total records: {len(df):,}")
        print(f"Unique courses: {df['course_id'].nunique():,}")

        count_pass = len(df) == 2000
        course_pass = df["course_id"].nunique() == 1000

        print(f"Expected 2,000 records: {'PASS' if count_pass else 'FAIL'}")
        print(f"Expected 1,000 courses: {'PASS' if course_pass else 'FAIL'}")

        # -----------------------------------------
        # 4. Semester and year validation
        # -----------------------------------------

        print("\nACADEMIC PERIOD VALIDATION")
        print("-" * 55)

        invalid_years = (
            df["academic_year"] != 2026
        ).sum()

        invalid_semesters = (
            ~df["semester"].isin([1, 2])
        ).sum()

        print(f"Invalid academic years: {invalid_years}")
        print(f"Invalid semesters: {invalid_semesters}")

        # -----------------------------------------
        # 5. Duplicate validation
        # -----------------------------------------

        print("\nDUPLICATE VALIDATION")
        print("-" * 55)

        duplicates = df.duplicated(
            subset=[
                "course_id",
                "academic_year",
                "semester",
            ]
        ).sum()

        print(f"Duplicate forecast records: {duplicates}")

        # -----------------------------------------
        # 6. Demand validation
        # -----------------------------------------

        print("\nDEMAND VALIDATION")
        print("-" * 55)

        invalid_demand = (
            df["predicted_demand"] < 0
        ).sum()

        invalid_capacity = (
            df["target_section_size"] <= 0
        ).sum()

        print(f"Negative demand values: {invalid_demand}")
        print(f"Invalid section sizes: {invalid_capacity}")

        # -----------------------------------------
        # 7. Section calculation validation
        # -----------------------------------------

        print("\nSECTION VALIDATION")
        print("-" * 55)

        expected_sections = df.apply(
            lambda row: math.ceil(
                row["predicted_demand"]
                / row["target_section_size"]
            ),
            axis=1,
        )

        section_mismatches = (
            expected_sections
            != df["predicted_sections_required"]
        ).sum()

        print(f"Section calculation mismatches: {section_mismatches}")

        # -----------------------------------------
        # 8. Course foreign key validation
        # -----------------------------------------

        print("\nCOURSE REFERENCE VALIDATION")
        print("-" * 55)

        valid_course_ids = {
            course_id
            for (course_id,) in db.query(Course.course_id).all()
        }

        invalid_course_ids = (
            ~df["course_id"].isin(valid_course_ids)
        ).sum()

        print(f"Invalid course references: {invalid_course_ids}")

        # -----------------------------------------
        # 9. Source validation
        # -----------------------------------------

        print("\nSOURCE VALIDATION")
        print("-" * 55)

        invalid_sources = (
            df["source_type"]
            != "SYNTHETIC_MODEL_FORECAST"
        ).sum()

        print(f"Incorrect source labels: {invalid_sources}")

        # -----------------------------------------
        # 10. Forecast summary
        # -----------------------------------------

        print("\nFORECAST SUMMARY")
        print("-" * 55)

        print(
            "Total predicted demand: "
            f"{df['predicted_demand'].sum():,}"
        )

        print(
            "Total predicted sections: "
            f"{df['predicted_sections_required'].sum():,}"
        )

        print(f"MAE: {metrics['mae']:.4f}")
        print(f"RMSE: {metrics['rmse']:.4f}")
        print(f"R2: {metrics['r2_score']:.4f}")

        # -----------------------------------------
        # 11. Final summary
        # -----------------------------------------

        issues = (
            len(missing_columns)
            + int(not count_pass)
            + int(not course_pass)
            + invalid_years
            + invalid_semesters
            + duplicates
            + invalid_demand
            + invalid_capacity
            + section_mismatches
            + invalid_course_ids
            + invalid_sources
        )

        print("\nFINAL VALIDATION SUMMARY")
        print("=" * 55)

        if issues == 0:
            print("STATUS: ALL FORECAST CHECKS PASSED")
        else:
            print(f"STATUS: {issues} ISSUE(S) FOUND")

    finally:
        db.close()


if __name__ == "__main__":
    validate_forecast()
