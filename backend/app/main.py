
from pathlib import Path
import json

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field


# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "data" / "output"
GROUND_TRUTH_DIR = BASE_DIR / "data" / "ground_truth"

app = FastAPI(
    title="Academic Demand & Resource Optimizer",
    description=(
        "Course demand forecasting, academic resource "
        "allocation, anomaly detection and reporting API."
    ),
    version="1.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------
# REQUEST MODELS
# -------------------------------------------------

class ScenarioRequest(BaseModel):
    demand_change_pct: float = Field(
        default=0,
        ge=-30,
        le=50,
        description="Change in student demand percentage.",
    )

    faculty_availability_reduction_pct: float = Field(
        default=0,
        ge=0,
        le=50,
        description="Percentage of faculty made unavailable.",
    )

    room_capacity_change_pct: float = Field(
        default=0,
        ge=-30,
        le=30,
        description="Change in room capacity percentage.",
    )


class ManualAllocationRequest(BaseModel):
    section_id: str = Field(
        min_length=1,
        max_length=15,
    )

    faculty_id: str | None = Field(
        default=None,
        max_length=13,
    )

    room_id: str | None = Field(
        default=None,
        max_length=13,
    )


class CustomReportRequest(BaseModel):
    sections: list[str] = Field(
        min_length=1,
        description="Report section keys selected by the user.",
    )

    format: str = Field(
        default="pdf",
        pattern="^(pdf|csv)$",
        description="Report output format: pdf or csv.",
    )


# -------------------------------------------------
# EXPORT FILE REGISTRY
# -------------------------------------------------

EXPORT_FILES = {
    "forecast": (
        OUTPUT_DIR / "course_demand_forecast_2026.csv",
        "course_demand_forecast_2026.csv",
    ),
    "allocations": (
        OUTPUT_DIR / "section_allocations.csv",
        "section_allocations.csv",
    ),
    "unmet-demand": (
        OUTPUT_DIR / "unmet_demand.csv",
        "unmet_demand.csv",
    ),
    "decision-log": (
        OUTPUT_DIR / "allocation_decision_log.csv",
        "allocation_decision_log.csv",
    ),
    "anomaly-results": (
        OUTPUT_DIR / "anomaly_detection_results.csv",
        "anomaly_detection_results.csv",
    ),
    "anomaly-injections": (
        OUTPUT_DIR / "anomaly_injections.csv",
        "anomaly_injections.csv",
    ),
    "anomaly-ground-truth": (
        GROUND_TRUTH_DIR / "anomaly_ground_truth.csv",
        "anomaly_ground_truth.csv",
    ),
    "allocation-summary": (
        OUTPUT_DIR / "allocation_summary.json",
        "allocation_summary.json",
    ),
    "forecast-metrics": (
        OUTPUT_DIR / "forecast_metrics.json",
        "forecast_metrics.json",
    ),
    "anomaly-metrics": (
        OUTPUT_DIR / "anomaly_detection_metrics.json",
        "anomaly_detection_metrics.json",
    ),
    "feature-importance": (
        OUTPUT_DIR / "feature_importance.csv",
        "feature_importance.csv",
    ),
    "reproducibility-baseline": (
        OUTPUT_DIR / "reproducibility_baseline.json",
        "reproducibility_baseline.json",
    ),
}


# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------

def read_json(filename):
    path = OUTPUT_DIR / filename

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {filename}",
        )

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def read_csv(filename, limit=100, filters=None):
    path = OUTPUT_DIR / filename

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {filename}",
        )

    df = pd.read_csv(path)

    if filters:
        for column, value in filters.items():
            if value is not None:
                if column not in df.columns:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid filter column: {column}",
                    )

                df = df[df[column] == value]

    df = df.head(limit)
    df = df.astype(object).where(pd.notna(df), None)

    return df.to_dict(orient="records")


# -------------------------------------------------
# BASIC ENDPOINTS
# -------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Academic Demand & Resource Optimizer API",
        "status": "Running successfully",
        "version": "1.3.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Academic Optimizer API",
    }


# -------------------------------------------------
# DASHBOARD OVERVIEW
# -------------------------------------------------

@app.get("/api/overview")
def get_overview():
    allocation = read_json("allocation_summary.json")
    forecast = read_json("forecast_metrics.json")
    anomaly = read_json("anomaly_detection_metrics.json")

    return {
        "project": "Academic Demand & Resource Optimizer",
        "academic_year": allocation.get("academic_year"),
        "total_predicted_demand": allocation.get(
            "total_predicted_demand", 0
        ),
        "total_planned_sections": allocation.get(
            "total_planned_sections", 0
        ),
        "allocated_sections": allocation.get(
            "allocated_sections", 0
        ),
        "unallocated_sections": allocation.get(
            "unallocated_sections", 0
        ),
        "total_unmet_demand": allocation.get(
            "total_unmet_demand", 0
        ),
        "active_faculty": allocation.get("active_faculty", 0),
        "active_rooms": allocation.get("active_rooms", 0),
        "forecast_metrics": forecast,
        "anomaly_metrics": anomaly,
    }


# -------------------------------------------------
# FORECAST ENDPOINTS
# -------------------------------------------------

@app.get("/api/forecast")
def get_forecast(
    semester: int | None = Query(default=None, ge=1, le=2),
    limit: int = Query(default=100, ge=1, le=2000),
):
    return read_csv(
        "course_demand_forecast_2026.csv",
        limit=limit,
        filters={"semester": semester},
    )


@app.get("/api/forecast/metrics")
def get_forecast_metrics():
    return read_json("forecast_metrics.json")


# -------------------------------------------------
# ALLOCATION ENDPOINTS
# -------------------------------------------------

@app.get("/api/allocations")
def get_allocations(
    status: str | None = Query(default=None),
    semester: int | None = Query(default=None, ge=1, le=2),
    limit: int = Query(default=100, ge=1, le=3000),
):
    if status and status not in ["ALLOCATED", "UNALLOCATED"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be ALLOCATED or UNALLOCATED",
        )

    return read_csv(
        "section_allocations.csv",
        limit=limit,
        filters={
            "allocation_status": status,
            "semester": semester,
        },
    )


@app.get("/api/unmet-demand")
def get_unmet_demand(
    limit: int = Query(default=100, ge=1, le=2000),
):
    return read_csv(
        "unmet_demand.csv",
        limit=limit,
    )


@app.get("/api/allocation/summary")
def get_allocation_summary():
    return read_json("allocation_summary.json")


# -------------------------------------------------
# EXPLAINABLE AI RECOMMENDATIONS
# -------------------------------------------------

@app.get("/api/recommendations")
def get_recommendations():
    """Generate explainable recommendations from allocation results."""

    try:
        from app.services.recommendations.recommendation_engine import (
            generate_recommendations,
        )

        return generate_recommendations()

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation generation failed: {str(error)}",
        )


# -------------------------------------------------
# WHAT-IF SCENARIO SIMULATION
# -------------------------------------------------

@app.post("/api/simulation/run")
def run_scenario_simulation(request: ScenarioRequest):
    try:
        from app.services.simulation.scenario_simulator import run_scenario

        return run_scenario(
            demand_change_pct=request.demand_change_pct,
            faculty_availability_reduction_pct=(
                request.faculty_availability_reduction_pct
            ),
            room_capacity_change_pct=request.room_capacity_change_pct,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# -------------------------------------------------
# INTERACTIVE RESOURCE ALLOCATION
# -------------------------------------------------

@app.get("/api/manual-allocation/resources")
def manual_allocation_resources():
    """Return active faculty and rooms for manual reassignment."""

    try:
        from app.services.manual_allocation.override_service import (
            get_resources,
        )

        return get_resources()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load resources: {str(error)}",
        )


@app.get("/api/manual-allocation/overrides")
def manual_allocation_overrides():
    """Return all applied manual allocation overrides."""

    try:
        from app.services.manual_allocation.override_service import (
            get_overrides,
        )

        return get_overrides()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load overrides: {str(error)}",
        )


@app.post("/api/manual-allocation/preview")
def manual_allocation_preview(
    request: ManualAllocationRequest,
):
    """Validate and preview a proposed faculty or room reassignment."""

    try:
        from app.services.manual_allocation.override_service import (
            preview_override,
        )

        return preview_override(
            section_id=request.section_id,
            faculty_id=request.faculty_id,
            room_id=request.room_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Preview failed: {str(error)}",
        )


@app.post("/api/manual-allocation/apply")
def manual_allocation_apply(
    request: ManualAllocationRequest,
):
    """Apply a valid manual reassignment as a separate override."""

    try:
        from app.services.manual_allocation.override_service import (
            apply_override,
        )

        result = apply_override(
            section_id=request.section_id,
            faculty_id=request.faculty_id,
            room_id=request.room_id,
        )

        if not result.get("valid"):
            raise HTTPException(
                status_code=400,
                detail={
                    "message": result.get("message"),
                    "errors": result.get("errors", []),
                    "warnings": result.get("warnings", []),
                },
            )

        return result

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Applying override failed: {str(error)}",
        )


# -------------------------------------------------
# ANOMALY ENDPOINTS
# -------------------------------------------------

@app.get("/api/anomalies")
def get_anomalies(
    limit: int = Query(default=100, ge=1, le=1000),
):
    return read_csv(
        "anomaly_detection_results.csv",
        limit=limit,
    )


@app.get("/api/anomalies/metrics")
def get_anomaly_metrics():
    return read_json("anomaly_detection_metrics.json")


# -------------------------------------------------
# CUSTOM REPORT GENERATOR
# -------------------------------------------------

@app.get("/api/reports/sections")
def get_report_sections():
    """List report sections and indicate whether their source files exist."""

    try:
        from app.services.reports.report_generator import (
            get_available_sections,
        )

        sections = get_available_sections()

        return {
            "total_sections": len(sections),
            "available_sections": sum(
                section["available"] for section in sections
            ),
            "sections": sections,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load report sections: {str(error)}",
        )


@app.get("/api/reports/summary")
def get_report_summary():
    """Return the existing project metrics for report previews."""

    try:
        from app.services.reports.report_generator import (
            get_project_summary,
        )

        return get_project_summary()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load report summary: {str(error)}",
        )


@app.post("/api/reports/generate")
def generate_custom_report(request: CustomReportRequest):
    """Generate a custom PDF or CSV report from selected project outputs."""

    try:
        from app.services.reports.report_generator import (
            AVAILABLE_SECTIONS,
            generate_csv_report,
            generate_pdf_report,
        )

        # Validate selected section keys.
        invalid_sections = [
            section
            for section in request.sections
            if section not in AVAILABLE_SECTIONS
        ]

        if invalid_sections:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "One or more report sections are invalid.",
                    "invalid_sections": invalid_sections,
                    "valid_sections": list(AVAILABLE_SECTIONS.keys()),
                },
            )

        # Remove duplicate section selections.
        selected_sections = list(dict.fromkeys(request.sections))

        if request.format == "pdf":
            report_buffer = generate_pdf_report(selected_sections)
            filename = "academic_optimizer_custom_report.pdf"
            media_type = "application/pdf"

        else:
            report_buffer = generate_csv_report(selected_sections)
            filename = "academic_optimizer_custom_report.csv"
            media_type = "text/csv"

        return StreamingResponse(
            report_buffer,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )

    except HTTPException:
        raise

    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(
            status_code=400 if isinstance(error, ValueError) else 404,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(error)}",
        )


# -------------------------------------------------
# EXPORT ENDPOINTS
# -------------------------------------------------

@app.get("/api/exports")
def list_exports():
    """List all available downloadable project files."""

    available = []

    for export_name, (file_path, download_name) in EXPORT_FILES.items():
        available.append({
            "export_name": export_name,
            "filename": download_name,
            "available": file_path.is_file(),
            "download_url": (
                f"/api/exports/{export_name}"
                if file_path.is_file()
                else None
            ),
        })

    return {
        "total_exports": len(available),
        "available_exports": sum(
            item["available"] for item in available
        ),
        "exports": available,
    }


@app.get("/api/exports/{export_name}")
def download_export(export_name: str):
    """Download a specific CSV or JSON output."""

    export = EXPORT_FILES.get(export_name)

    if export is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown export name.",
        )

    file_path, download_name = export

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Export file not available: {download_name}",
        )

    suffix = file_path.suffix.lower()

    media_type = (
        "text/csv"
        if suffix == ".csv"
        else "application/json"
    )

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=download_name,
    )


# -------------------------------------------------
# RUN SERVER
# -------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
