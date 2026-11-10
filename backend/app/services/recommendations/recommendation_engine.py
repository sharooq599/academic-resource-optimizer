from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = BASE_DIR / "data" / "output"

UNMET_DEMAND_FILE = OUTPUT_DIR / "unmet_demand.csv"
ALLOCATIONS_FILE = OUTPUT_DIR / "section_allocations.csv"


def load_data():
    """Load existing allocation results without modifying them."""

    if not UNMET_DEMAND_FILE.exists():
        raise FileNotFoundError(
            f"Unmet demand file not found: {UNMET_DEMAND_FILE}"
        )

    if not ALLOCATIONS_FILE.exists():
        raise FileNotFoundError(
            f"Allocation file not found: {ALLOCATIONS_FILE}"
        )

    unmet_df = pd.read_csv(UNMET_DEMAND_FILE)
    allocations_df = pd.read_csv(ALLOCATIONS_FILE)

    return unmet_df, allocations_df


def get_priority(unmet_demand, unallocated_sections):
    """Assign recommendation priority using existing evidence."""

    if unmet_demand >= 40 or unallocated_sections >= 2:
        return "HIGH"

    if unmet_demand > 0 or unallocated_sections > 0:
        return "MEDIUM"

    return "LOW"


def generate_recommendations():
    """Generate explainable recommendations from allocation results."""

    unmet_df, allocations_df = load_data()

    recommendations = []

    # Group allocation failure reasons by course and semester.
    failure_df = allocations_df[
        allocations_df["allocation_status"] == "UNALLOCATED"
    ].copy()

    if not failure_df.empty:
        failure_summary = (
            failure_df.groupby(["course_id", "semester"])
            .agg(
                unallocated_sections_count=("section_id", "count"),
                failure_reasons=("failure_reason", "unique"),
            )
            .reset_index()
        )
    else:
        failure_summary = pd.DataFrame(
            columns=[
                "course_id",
                "semester",
                "unallocated_sections_count",
                "failure_reasons",
            ]
        )

    # Generate one recommendation for each course with unmet demand.
    for _, row in unmet_df.iterrows():

        unmet_demand = int(row["unmet_demand"])
        unallocated_sections = int(row["unallocated_sections"])

        if unmet_demand <= 0 and unallocated_sections <= 0:
            continue

        course_id = row["course_id"]
        semester = int(row["semester"])

        matching_failure = failure_summary[
            (failure_summary["course_id"] == course_id)
            & (failure_summary["semester"] == semester)
        ]

        failure_reasons = []

        if not matching_failure.empty:
            failure_reasons = [
                str(reason)
                for reason in matching_failure.iloc[0]["failure_reasons"]
                if pd.notna(reason)
            ]

        priority = get_priority(
            unmet_demand,
            unallocated_sections,
        )

        if unallocated_sections > 0:
            explanation = (
                f"{unallocated_sections} section(s) remain unallocated "
                f"for this course, with {unmet_demand} students of "
                f"unmet demand."
            )

            action = (
                "Review qualified faculty, faculty availability, "
                "room suitability, and timetable compatibility. "
                "Then reassess the unallocated sections."
            )

            evidence_level = "CONFIRMED"

        else:
            explanation = (
                f"This course has {unmet_demand} students of unmet "
                f"demand based on the existing allocation results."
            )

            action = (
                "Review section capacity and consider whether "
                "additional sections are needed."
            )

            evidence_level = "CONFIRMED"

        recommendations.append(
            {
                "course_id": course_id,
                "course_name": row["course_name"],
                "semester": semester,
                "priority": priority,
                "predicted_demand": int(row["predicted_demand"]),
                "allocated_sections": int(row["allocated_sections"]),
                "unallocated_sections": unallocated_sections,
                "unmet_demand": unmet_demand,
                "failure_reasons": failure_reasons,
                "evidence_level": evidence_level,
                "explanation": explanation,
                "recommended_action": action,
            }
        )

    # Show highest-priority and highest-unmet-demand courses first.
    priority_order = {
        "HIGH": 0,
        "MEDIUM": 1,
        "LOW": 2,
    }

    recommendations.sort(
        key=lambda item: (
            priority_order[item["priority"]],
            -item["unmet_demand"],
        )
    )

    summary = {
        "total_recommendations": len(recommendations),
        "high_priority": sum(
            item["priority"] == "HIGH"
            for item in recommendations
        ),
        "medium_priority": sum(
            item["priority"] == "MEDIUM"
            for item in recommendations
        ),
        "low_priority": sum(
            item["priority"] == "LOW"
            for item in recommendations
        ),
    }

    return {
        "summary": summary,
        "recommendations": recommendations,
        "safety": {
            "database_modified": False,
            "output_files_modified": False,
        },
    }