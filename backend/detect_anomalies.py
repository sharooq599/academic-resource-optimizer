
from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "data/output/anomaly_injections.csv"
GROUND_TRUTH_FILE = BASE_DIR / "data/ground_truth/anomaly_ground_truth.csv"

OUTPUT_FILE = BASE_DIR / "data/output/anomaly_detection_results.csv"
METRICS_FILE = BASE_DIR / "data/output/anomaly_detection_metrics.json"


def detect(row):
    """Detect synthetic anomaly scenarios using observable fields."""

    # Rule 1: Faculty workload exceeds maximum
    if pd.notna(row.get("injected_weekly_workload")):
        if row["injected_weekly_workload"] > row["maximum_weekly_workload"]:
            return "FACULTY_WORKLOAD_EXCEEDED"

    # Rule 2: Faculty lacks the required skill
    if pd.notna(row.get("skill_match_after_injection")):
        if str(row["skill_match_after_injection"]).lower() == "false":
            return "FACULTY_SKILL_MISMATCH"

    # Rule 3: Room capacity is insufficient
    if pd.notna(row.get("injected_room_capacity")):
        if row["injected_room_capacity"] < row["required_capacity"]:
            return "ROOM_CAPACITY_EXCEEDED"

    # Rule 4 and 5: Explicit synthetic overlapping booking events.
    # The generator represents these as simulated event records.
    event_id = row.get("simulated_event_id")

    if pd.notna(event_id) and str(event_id).strip():
        if row["entity_type"] == "FACULTY":
            return "FACULTY_TIMETABLE_CONFLICT"

        if row["entity_type"] == "ROOM":
            return "ROOM_TIMETABLE_CONFLICT"

    return "NO_ANOMALY_DETECTED"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    if not GROUND_TRUTH_FILE.exists():
        raise FileNotFoundError(GROUND_TRUTH_FILE)

    df = pd.read_csv(INPUT_FILE)
    ground_truth = pd.read_csv(GROUND_TRUTH_FILE)

    df["detected_type"] = df.apply(detect, axis=1)

    df["detection_status"] = df.apply(
        lambda row: (
            "DETECTED"
            if row["detected_type"] != "NO_ANOMALY_DETECTED"
            else "NOT_DETECTED"
        ),
        axis=1
    )

    results = df.merge(
        ground_truth[["anomaly_id", "anomaly_type"]],
        on="anomaly_id",
        how="left",
        suffixes=("", "_ground_truth")
    )

    results["correct_detection"] = (
        results["detected_type"] == results["anomaly_type_ground_truth"]
    )

    results.to_csv(OUTPUT_FILE, index=False)

    total = len(results)
    detected = int((results["detection_status"] == "DETECTED").sum())
    correct = int(results["correct_detection"].sum())

    metrics = {
        "total_synthetic_events": total,
        "detected_events": detected,
        "correctly_classified_events": correct,
        "missed_events": total - detected,
        "classification_accuracy": round(
            correct / total, 4
        ) if total else 0,
        "detection_method": "Rule-Based",
        "data_source": "SYNTHETIC_TEST_DATA"
    }

    with open(METRICS_FILE, "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=4)

    print("\nANOMALY DETECTION RESULTS")
    print("=" * 50)

    print(results[
        [
            "anomaly_id",
            "anomaly_type",
            "detected_type",
            "detection_status",
            "correct_detection"
        ]
    ].to_string(index=False))

    print("\nMETRICS")
    print("=" * 50)

    for key, value in metrics.items():
        print(f"{key}: {value}")

    print("\nOUTPUT FILES")
    print(OUTPUT_FILE)
    print(METRICS_FILE)


if __name__ == "__main__":
    main()
