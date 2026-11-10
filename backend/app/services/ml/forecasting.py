
from pathlib import Path
import json
import math

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.database.connection import SessionLocal
from app.models.course import Course
from app.models.historical_demand import HistoricalCourseDemand
from app.services.data.config import SEED


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[3]

MODEL_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "data" / "output"

MODEL_PATH = MODEL_DIR / "course_demand_forecaster.joblib"
FORECAST_PATH = OUTPUT_DIR / "course_demand_forecast_2026.csv"
METRICS_PATH = OUTPUT_DIR / "forecast_metrics.json"
IMPORTANCE_PATH = OUTPUT_DIR / "feature_importance.csv"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

TRAINING_YEAR = 2024
TESTING_YEAR = 2025
FORECAST_YEAR = 2026

FEATURE_COLUMNS = [
    "academic_year",
    "semester",
    "credits",
    "course_level_encoded",
    "target_section_size",
    "lag_1",
]


# ---------------------------------------------------------
# LOAD HISTORICAL DATA
# ---------------------------------------------------------

def load_historical_data():
    """Load historical demand records along with course details."""

    db = SessionLocal()

    try:
        results = (
            db.query(HistoricalCourseDemand, Course)
            .join(
                Course,
                HistoricalCourseDemand.course_id == Course.course_id
            )
            .order_by(
                HistoricalCourseDemand.course_id,
                HistoricalCourseDemand.semester,
                HistoricalCourseDemand.academic_year,
            )
            .all()
        )

        records = []

        for demand, course in results:
            records.append({
                "historical_demand_id": demand.historical_demand_id,
                "course_id": demand.course_id,
                "course_name": course.course_name,
                "program_id": course.program_id,
                "academic_year": demand.academic_year,
                "semester": demand.semester,
                "demand_count": demand.demand_count,
                "credits": course.credits,
                "course_level": course.course_level,
                "target_section_size": course.target_section_size,
            })

        return pd.DataFrame(records)

    finally:
        db.close()


# ---------------------------------------------------------
# PREPARE FEATURES
# ---------------------------------------------------------

def prepare_features(df):
    """
    Create a consistent previous-year demand feature.

    2024 demand uses 2023 demand as lag_1.
    2025 demand uses 2024 demand as lag_1.
    2026 forecast uses 2025 demand as lag_1.
    """

    df = df.copy()

    numeric_columns = [
        "academic_year",
        "semester",
        "demand_count",
        "credits",
        "target_section_size",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # Encode course levels.
    level_values = sorted(
        df["course_level"].fillna("UNKNOWN").astype(str).unique()
    )

    level_mapping = {
        level: index
        for index, level in enumerate(level_values)
    }

    df["course_level_encoded"] = (
        df["course_level"]
        .fillna("UNKNOWN")
        .astype(str)
        .map(level_mapping)
    )

    # Calculate previous year's demand for the same course
    # and semester.
    df = df.sort_values(
        ["course_id", "semester", "academic_year"]
    ).reset_index(drop=True)

    df["lag_1"] = (
        df.groupby(["course_id", "semester"])["demand_count"]
        .shift(1)
    )

    return df, level_mapping


# ---------------------------------------------------------
# EVALUATION HELPERS
# ---------------------------------------------------------

def calculate_metrics(actual, predicted):
    """Calculate regression evaluation metrics."""

    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(
            math.sqrt(mean_squared_error(actual, predicted))
        ),
        "r2": float(r2_score(actual, predicted)),
    }


# ---------------------------------------------------------
# MAIN FORECASTING PIPELINE
# ---------------------------------------------------------

def run_forecasting():

    print("\nCOURSE DEMAND FORECASTING")
    print("=" * 60)

    # 1. Load historical data.
    df = load_historical_data()

    if df.empty:
        raise ValueError("No historical demand records found.")

    print(f"Historical records loaded: {len(df):,}")

    # 2. Prepare features.
    df, level_mapping = prepare_features(df)

    # Remove records without previous-year demand.
    supervised_df = df.dropna(subset=["lag_1"]).copy()

    training_df = supervised_df[
        supervised_df["academic_year"] == TRAINING_YEAR
    ].copy()

    testing_df = supervised_df[
        supervised_df["academic_year"] == TESTING_YEAR
    ].copy()

    if training_df.empty or testing_df.empty:
        raise ValueError(
            "Training or testing data is empty. "
            "Check the historical academic years."
        )

    X_train = training_df[FEATURE_COLUMNS]
    y_train = training_df["demand_count"]

    X_test = testing_df[FEATURE_COLUMNS]
    y_test = testing_df["demand_count"]

    print(f"Training records: {len(training_df):,}")
    print(f"Testing records : {len(testing_df):,}")

    # 3. Train Random Forest model.
    print("\nTraining Random Forest Regression...")

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=2,
        random_state=SEED,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    # 4. Evaluate model on 2025 test data.
    model_predictions = model.predict(X_test)

    model_metrics = calculate_metrics(
        y_test,
        model_predictions
    )

    # 5. Compare against previous-year baseline.
    baseline_predictions = testing_df["lag_1"].to_numpy()

    baseline_metrics = calculate_metrics(
        y_test,
        baseline_predictions
    )

    print("\nMODEL EVALUATION — 2025 TEST DATA")
    print("-" * 60)

    print("Random Forest:")
    print(f"MAE : {model_metrics['mae']:.4f}")
    print(f"RMSE: {model_metrics['rmse']:.4f}")
    print(f"R2  : {model_metrics['r2']:.4f}")

    print("\nPrevious-year baseline:")
    print(f"MAE : {baseline_metrics['mae']:.4f}")
    print(f"RMSE: {baseline_metrics['rmse']:.4f}")
    print(f"R2  : {baseline_metrics['r2']:.4f}")

    # 6. Retrain using all supervised data through 2025.
    print("\nRetraining using 2024 and 2025 data...")

    final_model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=2,
        random_state=SEED,
        n_jobs=-1,
    )

    X_all = supervised_df[FEATURE_COLUMNS]
    y_all = supervised_df["demand_count"]

    final_model.fit(X_all, y_all)

    # 7. Prepare 2026 forecast inputs using 2025 demand.
    forecast_input = df[
        df["academic_year"] == TESTING_YEAR
    ].copy()

    if len(forecast_input) != 2000:
        raise ValueError(
            f"Expected 2,000 forecast inputs, "
            f"but found {len(forecast_input):,}."
        )

    forecast_input["academic_year"] = FORECAST_YEAR

    X_forecast = forecast_input[FEATURE_COLUMNS]

    # 8. Generate 2026 predictions.
    predictions = final_model.predict(X_forecast)

    forecast_input["predicted_demand"] = np.maximum(
        np.rint(predictions),
        0
    ).astype(int)

    # Calculate required sections.
    forecast_input["predicted_sections"] = np.ceil(
        forecast_input["predicted_demand"]
        / forecast_input["target_section_size"]
    ).astype(int)

    # Keep the validation script's expected column name too.
    forecast_input["predicted_sections_required"] = (
        forecast_input["predicted_sections"]
    )

    forecast_input["source_type"] = "SYNTHETIC_MODEL_FORECAST"

    # 9. Build final output.
    forecast_df = forecast_input[[
        "course_id",
        "course_name",
        "program_id",
        "academic_year",
        "semester",
        "credits",
        "course_level",
        "target_section_size",
        "lag_1",
        "predicted_demand",
        "predicted_sections",
        "predicted_sections_required",
        "source_type",
    ]].copy()

    forecast_df = forecast_df.sort_values(
        ["course_id", "semester"]
    ).reset_index(drop=True)

    # 10. Save forecast CSV.
    forecast_df.to_csv(FORECAST_PATH, index=False)

    # 11. Save trained model.
    joblib.dump(final_model, MODEL_PATH)

    # 12. Save evaluation metrics.
    metrics_output = {
        "training_year": TRAINING_YEAR,
        "testing_year": TESTING_YEAR,
        "forecast_year": FORECAST_YEAR,
        "training_records": int(len(training_df)),
        "testing_records": int(len(testing_df)),
        "forecast_records": int(len(forecast_df)),
        "feature_columns": FEATURE_COLUMNS,
        "model": "RandomForestRegressor",
        "model_metrics": model_metrics,
        "baseline_metrics": baseline_metrics,

        # Compatibility keys for the validation script.
        "mae": model_metrics["mae"],
        "rmse": model_metrics["rmse"],
        "r2": model_metrics["r2"],
        "r2_score": model_metrics["r2"],
        "MAE": model_metrics["mae"],
        "RMSE": model_metrics["rmse"],
        "R2": model_metrics["r2"],
    }

    with open(METRICS_PATH, "w", encoding="utf-8") as file:
        json.dump(metrics_output, file, indent=4)

    # 13. Save feature importance.
    importance_df = pd.DataFrame({
        "feature": FEATURE_COLUMNS,
        "importance": final_model.feature_importances_,
    }).sort_values(
        "importance",
        ascending=False
    )

    importance_df.to_csv(IMPORTANCE_PATH, index=False)

    # 14. Print summary.
    print("\nFORECAST GENERATION COMPLETED")
    print("=" * 60)

    print(f"2026 forecast records : {len(forecast_df):,}")

    print(
        "Total predicted demand : "
        f"{forecast_df['predicted_demand'].sum():,}"
    )

    print(
        "Total predicted sections: "
        f"{forecast_df['predicted_sections'].sum():,}"
    )

    print(f"\nModel saved: {MODEL_PATH}")
    print(f"Forecast saved: {FORECAST_PATH}")
    print(f"Metrics saved: {METRICS_PATH}")
    print(f"Feature importance saved: {IMPORTANCE_PATH}")


if __name__ == "__main__":
    run_forecasting()
