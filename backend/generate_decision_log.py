
from pathlib import Path
import pandas as pd

from app.services.data.config import SEED


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "output"

FORECAST_PATH = OUTPUT_DIR / "course_demand_forecast_2026.csv"
ALLOCATION_PATH = OUTPUT_DIR / "section_allocations.csv"
OUTPUT_PATH = OUTPUT_DIR / "allocation_decision_log.csv"


def generate_decision_log():

    print("\nGENERATING ALLOCATION DECISION LOG")
    print("----------------------------------")

    if not FORECAST_PATH.exists():
        raise FileNotFoundError(FORECAST_PATH)

    if not ALLOCATION_PATH.exists():
        raise FileNotFoundError(ALLOCATION_PATH)

    forecast_df = pd.read_csv(FORECAST_PATH)
    allocation_df = pd.read_csv(ALLOCATION_PATH)

    print(f"Forecast records: {len(forecast_df)}")
    print(f"Allocation records: {len(allocation_df)}")

    required_forecast = [
        "course_id",
        "semester",
        "academic_year",
        "predicted_demand",
        "predicted_sections",
        "predicted_sections_required",
        "source_type",
    ]

    required_allocation = [
        "section_id",
        "course_id",
        "course_name",
        "semester",
        "section_number",
        "section_capacity",
        "faculty_id",
        "faculty_name",
        "room_id",
        "room_name",
        "scheduled_day",
        "start_time",
        "end_time",
        "weekly_hours",
        "allocation_status",
        "failure_reason",
    ]

    missing_forecast = set(required_forecast) - set(forecast_df.columns)
    missing_allocation = set(required_allocation) - set(allocation_df.columns)

    if missing_forecast:
        raise ValueError(
            f"Missing forecast columns: {sorted(missing_forecast)}"
        )

    if missing_allocation:
        raise ValueError(
            f"Missing allocation columns: {sorted(missing_allocation)}"
        )

    if forecast_df.duplicated(
        subset=["course_id", "semester"]
    ).any():
        raise ValueError("Duplicate forecast keys found.")

    forecast_reference = forecast_df[required_forecast].copy()

    decision_df = allocation_df.merge(
        forecast_reference,
        on=["course_id", "semester"],
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    unmatched = decision_df[decision_df["_merge"] != "both"]

    if not unmatched.empty:
        raise ValueError(
            f"{len(unmatched)} allocation records have no matching forecast."
        )

    decision_df = decision_df.drop(columns=["_merge"])

    decision_df["decision_id"] = (
        "DEC-" + decision_df["section_id"].str.replace(
            "SEC-", "", regex=False
        )
    )

    decision_df["source_forecast"] = (
        "course_demand_forecast_2026.csv:"
        + decision_df["course_id"]
        + ":SEM-"
        + decision_df["semester"].astype(int).astype(str)
    )

    def explain_decision(row):

        if row["allocation_status"] == "ALLOCATED":
            return (
                "SUCCESS: Faculty, room and timetable were assigned "
                "by the constraint-based allocator."
            )

        reason = row["failure_reason"]

        if pd.isna(reason) or not str(reason).strip():
            reason = "Allocation failure reason not specified."

        return f"UNSUCCESSFUL: {reason}"

    decision_df["decision_reason"] = decision_df.apply(
        explain_decision,
        axis=1,
    )

    decision_df["random_seed"] = SEED

    final_columns = [
        "decision_id",
        "section_id",
        "course_id",
        "course_name",
        "academic_year",
        "semester",
        "predicted_demand",
        "predicted_sections",
        "predicted_sections_required",
        "faculty_id",
        "faculty_name",
        "room_id",
        "room_name",
        "scheduled_day",
        "start_time",
        "end_time",
        "weekly_hours",
        "section_capacity",
        "allocation_status",
        "failure_reason",
        "decision_reason",
        "source_type",
        "source_forecast",
        "random_seed",
    ]

    decision_df = decision_df[final_columns]

    if decision_df["decision_id"].duplicated().any():
        raise ValueError("Duplicate decision IDs found.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    decision_df.to_csv(OUTPUT_PATH, index=False)

    allocated = (
        decision_df["allocation_status"] == "ALLOCATED"
    ).sum()

    unallocated = (
        decision_df["allocation_status"] != "ALLOCATED"
    ).sum()

    print("\nDECISION LOG GENERATED SUCCESSFULLY")
    print("-----------------------------------")
    print(f"Total decisions: {len(decision_df)}")
    print(f"Allocated decisions: {allocated}")
    print(f"Unallocated decisions: {unallocated}")
    print(f"Unique decision IDs: {decision_df['decision_id'].nunique()}")
    print(f"Random seed: {SEED}")
    print(f"Output: {OUTPUT_PATH}")

    print("\nSample records:")
    print(decision_df.head(5).to_string(index=False))


if __name__ == "__main__":
    generate_decision_log()
