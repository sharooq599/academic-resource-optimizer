
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from app.services.data.config import SEED


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "output"
GROUND_TRUTH_DIR = BASE_DIR / "data" / "ground_truth"

BASELINE_FILE = OUTPUT_DIR / "reproducibility_baseline.json"

# Core generated outputs used for reproducibility comparison.
# allocation_summary.json is excluded because it contains generated_at.
TRACKED_FILES = [
    OUTPUT_DIR / "course_demand_forecast_2026.csv",
    OUTPUT_DIR / "feature_importance.csv",
    OUTPUT_DIR / "section_allocations.csv",
    OUTPUT_DIR / "unmet_demand.csv",
    OUTPUT_DIR / "anomaly_injections.csv",
    OUTPUT_DIR / "anomaly_detection_results.csv",
    OUTPUT_DIR / "forecast_metrics.json",
    OUTPUT_DIR / "anomaly_detection_metrics.json",
    GROUND_TRUTH_DIR / "anomaly_ground_truth.csv",
]


def calculate_sha256(file_path):
    """Calculate SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def collect_file_checksums():
    """Collect checksums for all tracked files."""
    results = {}

    for file_path in TRACKED_FILES:
        relative_path = str(file_path.relative_to(BASE_DIR))

        if not file_path.exists():
            results[relative_path] = {
                "status": "MISSING"
            }
            continue

        results[relative_path] = {
            "status": "PRESENT",
            "size_bytes": file_path.stat().st_size,
            "sha256": calculate_sha256(file_path),
        }

    return results


def create_baseline():
    """Save the current outputs as the reproducibility baseline."""
    checksums = collect_file_checksums()

    missing_files = [
        name
        for name, details in checksums.items()
        if details["status"] == "MISSING"
    ]

    if missing_files:
        print("\nCannot create baseline. Missing files:")
        for name in missing_files:
            print(f" - {name}")
        return

    baseline = {
        "project": "Academic Demand & Resource Optimizer",
        "random_seed": SEED,
        "created_at": datetime.now().isoformat(),
        "comparison_method": "SHA-256",
        "files": checksums,
    }

    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(BASELINE_FILE, "w", encoding="utf-8") as file:
        json.dump(baseline, file, indent=4)

    print("\nREPRODUCIBILITY BASELINE CREATED")
    print("--------------------------------")
    print(f"Random seed: {SEED}")
    print(f"Files recorded: {len(checksums)}")
    print(f"Baseline: {BASELINE_FILE}")

    for name in checksums:
        print(f"[RECORDED] {name}")


def compare_with_baseline():
    """Compare current generated files with the saved baseline."""
    if not BASELINE_FILE.exists():
        print("Baseline not found.")
        print("Run: python reproducibility_check.py --create-baseline")
        return

    with open(BASELINE_FILE, "r", encoding="utf-8") as file:
        baseline = json.load(file)

    current_checksums = collect_file_checksums()
    baseline_checksums = baseline["files"]

    print("\nREPRODUCIBILITY COMPARISON")
    print("--------------------------")
    print(f"Baseline seed: {baseline['random_seed']}")
    print(f"Current seed:  {SEED}")

    if baseline["random_seed"] != SEED:
        print("\nWARNING: Random seed has changed!")

    identical = []
    changed = []
    missing = []

    for name, old_details in baseline_checksums.items():
        new_details = current_checksums.get(name)

        if new_details is None or new_details["status"] == "MISSING":
            missing.append(name)
        elif old_details["status"] != "PRESENT":
            changed.append(name)
        elif old_details["sha256"] == new_details["sha256"]:
            identical.append(name)
        else:
            changed.append(name)

    for name in identical:
        print(f"[IDENTICAL] {name}")

    for name in changed:
        print(f"[CHANGED]   {name}")

    for name in missing:
        print(f"[MISSING]   {name}")

    print("\nSUMMARY")
    print("-------")
    print(f"Identical files: {len(identical)}")
    print(f"Changed files:   {len(changed)}")
    print(f"Missing files:   {len(missing)}")

    if not changed and not missing and baseline["random_seed"] == SEED:
        print("\nALL CHECKSUMS MATCH!")
    else:
        print("\nREPRODUCIBILITY CHECK NEEDS REVIEW.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify project output reproducibility."
    )

    parser.add_argument(
        "--create-baseline",
        action="store_true",
        help="Save checksums of current generated outputs."
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare current outputs with the saved baseline."
    )

    args = parser.parse_args()

    if args.create_baseline:
        create_baseline()
    elif args.compare:
        compare_with_baseline()
    else:
        parser.print_help()
