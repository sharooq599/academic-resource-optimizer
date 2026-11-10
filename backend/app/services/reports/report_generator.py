
from pathlib import Path
from datetime import datetime
from io import BytesIO
import json
import html

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = BASE_DIR / "data" / "output"


AVAILABLE_SECTIONS = {
    "forecast": {
        "title": "Demand Forecast",
        "file": "course_demand_forecast_2026.csv",
    },
    "allocations": {
        "title": "Resource Allocations",
        "file": "section_allocations.csv",
    },
    "unmet_demand": {
        "title": "Unmet Demand",
        "file": "unmet_demand.csv",
    },
    "decision_log": {
        "title": "Allocation Decision Log",
        "file": "allocation_decision_log.csv",
    },
    "anomalies": {
        "title": "Anomaly Detection",
        "file": "anomaly_detection_results.csv",
    },
    "feature_importance": {
        "title": "Forecast Feature Importance",
        "file": "feature_importance.csv",
    },
}


# -------------------------------------------------
# DATA LOADING
# -------------------------------------------------

def load_section(section_key):
    """Load one selected report section."""

    section = AVAILABLE_SECTIONS.get(section_key)

    if section is None:
        raise ValueError(
            f"Unknown report section: {section_key}"
        )

    file_path = OUTPUT_DIR / section["file"]

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Report source file not found: {section['file']}"
        )

    return pd.read_csv(file_path)


def get_project_summary():
    """Read existing project summary metrics."""

    result = {}

    files = {
        "allocation": "allocation_summary.json",
        "forecast": "forecast_metrics.json",
        "anomaly": "anomaly_detection_metrics.json",
    }

    for key, filename in files.items():
        path = OUTPUT_DIR / filename

        if path.is_file():
            with open(path, "r", encoding="utf-8") as file:
                result[key] = json.load(file)

    return result


def get_available_sections():
    """Return available report sections and file status."""

    result = []

    for key, section in AVAILABLE_SECTIONS.items():
        path = OUTPUT_DIR / section["file"]

        result.append({
            "key": key,
            "title": section["title"],
            "filename": section["file"],
            "available": path.is_file(),
        })

    return result


# -------------------------------------------------
# CSV REPORT GENERATOR
# -------------------------------------------------

def generate_csv_report(sections):
    """Combine selected sections into a downloadable CSV."""

    if not sections:
        raise ValueError(
            "Select at least one report section."
        )

    frames = []

    for section_key in sections:
        df = load_section(section_key)

        df.insert(0, "report_section", section_key)

        frames.append(df)

    combined = pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )

    buffer = BytesIO()

    combined.to_csv(
        buffer,
        index=False,
    )

    buffer.seek(0)

    return buffer


# -------------------------------------------------
# PDF HELPER FUNCTIONS
# -------------------------------------------------

def _format_value(value):
    """Format numeric values for report display."""

    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")

    return str(value)


def _summary_items(data, prefix=""):
    """Flatten nested metrics and avoid duplicate forecast aliases."""

    items = []

    if not isinstance(data, dict):
        return items

    for key, value in data.items():

        if key in {
            "mae",
            "rmse",
            "r2",
            "r2_score",
            "MAE",
            "RMSE",
            "R2",
        } and prefix == "Forecast":
            continue

        label = (
            f"{prefix} - {key.replace('_', ' ').title()}"
            if prefix
            else key.replace("_", " ").title()
        )

        if isinstance(value, dict):

            items.extend(
                _summary_items(value, label)
            )

        elif isinstance(value, list):
            continue

        elif isinstance(value, (str, int, float, bool)):

            items.append((
                label,
                _format_value(value),
            ))

    return items


# -------------------------------------------------
# IMPROVED PDF TABLE GENERATOR
# -------------------------------------------------

def _make_table(data, available_width, styles, section_key=None):
    """
    Build readable PDF tables.

    Wide tables are split into horizontal groups.
    Identifier columns are repeated in every group.

    CSV exports retain every column and every row.
    """

    if data is None or data.empty:
        return []

    df = data.copy().fillna("")
    columns = list(df.columns)

    preferred_ids = {
        "forecast": [
            "course_id",
            "course_name",
            "program_id",
            "academic_year",
            "semester",
        ],

        "allocations": [
            "section_id",
            "course_id",
            "course_name",
            "semester",
        ],

        "unmet_demand": [
            "course_id",
            "course_name",
            "semester",
        ],

        "decision_log": [
            "decision_id",
            "section_id",
            "course_id",
            "course_name",
            "semester",
        ],

        "anomalies": [
            "anomaly_id",
            "anomaly_type",
            "entity_id",
            "source_section_id",
        ],

        "feature_importance": [
            "feature",
            "feature_name",
        ],
    }

    pinned = [
        column
        for column in preferred_ids.get(section_key, [])
        if column in columns
    ]

    # Improved column width estimation.
    def estimate_width(column):

        values = [
            str(column).replace("_", " ")
        ]

        values.extend(
            df[column].astype(str).head(30).tolist()
        )

        longest = min(
            max((len(value) for value in values), default=8),
            34,
        )

        width = max(
            55,
            min(125, 22 + longest * 2.5)
        )

        # Give identifier columns additional space.
        if "id" in str(column).lower():
            width = max(width, 85)

        return width

    widths_by_column = {
        column: estimate_width(column)
        for column in columns
    }

    # Allocate page width across groups.
    pinned_width = sum(
        widths_by_column[column]
        for column in pinned
    )

    remaining = [
        column
        for column in columns
        if column not in pinned
    ]

    groups = []

    current = list(pinned)
    current_width = pinned_width

    target_width = available_width - 8

    for column in remaining:

        width = widths_by_column[column]

        if (
            len(current) > len(pinned)
            and current_width + width > target_width
        ):

            groups.append(current)

            current = list(pinned)
            current_width = pinned_width

        current.append(column)
        current_width += width

    if current:
        groups.append(current)

    output = []

    header_style = ParagraphStyle(
        "ReportTableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        textColor=colors.white,
        wordWrap="CJK",
    )

    cell_style = ParagraphStyle(
        "ReportTableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.6,
        leading=8,
        wordWrap="CJK",
    )

    # Generate each horizontal group.
    for group_index, group in enumerate(groups):

        if group_index:

            output.append(
                Spacer(1, 7)
            )

            output.append(
                Paragraph(
                    (
                        f"Continued fields "
                        f"({group_index + 1} of {len(groups)}) "
                        "- record identifiers repeated"
                    ),
                    styles["Italic"],
                )
            )

        raw_widths = [
            widths_by_column[column]
            for column in group
        ]

        total_width = sum(raw_widths)

        scale = (
            min(1.0, target_width / total_width)
            if total_width
            else 1.0
        )

        col_widths = [
            width * scale
            for width in raw_widths
        ]

        table_data = [[
            Paragraph(
                html.escape(
                    str(column).replace("_", " ")
                ),
                header_style,
            )
            for column in group
        ]]

        for _, row in df[group].iterrows():

            table_data.append([
                Paragraph(
                    html.escape(str(row[column])),
                    cell_style,
                )
                for column in group
            ])

        table = Table(
            table_data,
            colWidths=col_widths,
            repeatRows=1,
            hAlign="LEFT",
            splitByRow=1,
        )

        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#4338CA"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor("#D1D5DB"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F3F4F6"),
                    ],
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ])
        )

        output.append(table)

    return output


# -------------------------------------------------
# PDF REPORT GENERATOR
# -------------------------------------------------

def generate_pdf_report(sections):
    """Generate a formatted A3 landscape PDF report."""

    if not sections:
        raise ValueError(
            "Select at least one report section."
        )

    buffer = BytesIO()

    # A3 landscape provides more space for wide tables.
    page_width, _ = landscape(A3)

    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A3),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#4338CA"),
        fontSize=21,
        leading=26,
        spaceAfter=10,
    )

    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#4338CA"),
        fontSize=13,
        spaceBefore=12,
        spaceAfter=8,
    )

    small_style = ParagraphStyle(
        "SmallText",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
    )

    story = []

    # Report heading.
    story.append(
        Paragraph(
            "Academic Demand &amp; Resource Optimizer",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Custom Project Report",
            styles["Heading2"],
        )
    )

    story.append(
        Paragraph(
            (
                "Generated on: "
                f"{datetime.now().strftime('%d %B %Y, %I:%M %p')}"
            ),
            small_style,
        )
    )

    story.append(
        Spacer(1, 15)
    )

    # Project summary.
    summary = get_project_summary()

    story.append(
        Paragraph(
            "Project Summary",
            section_style,
        )
    )

    for category, metrics in summary.items():

        story.append(
            Paragraph(
                category.title() + " Metrics",
                styles["Heading3"],
            )
        )

        for label, value in _summary_items(
            metrics,
            category.title(),
        ):

            story.append(
                Paragraph(
                    f"<b>{label}:</b> {html.escape(str(value))}",
                    small_style,
                )
            )

        story.append(
            Spacer(1, 8)
        )

    available_width = page_width - 24 * mm

    # Selected report sections.
    for section_key in sections:

        if section_key not in AVAILABLE_SECTIONS:
            raise ValueError(
                f"Unknown report section: {section_key}"
            )

        df = load_section(section_key)

        story.append(
            Spacer(1, 12)
        )

        story.append(
            Paragraph(
                AVAILABLE_SECTIONS[section_key]["title"],
                section_style,
            )
        )

        story.append(
            Paragraph(
                f"Total records: {len(df)}",
                small_style,
            )
        )

        if df.empty:

            story.append(
                Paragraph(
                    "No records available.",
                    small_style,
                )
            )

            continue

        # PDF preview: first 50 records.
        display_df = df.head(50)

        story.extend(
            _make_table(
                display_df,
                available_width,
                styles,
                section_key=section_key,
            )
        )

        if len(df) > 50:

            story.append(
                Spacer(1, 6)
            )

            story.append(
                Paragraph(
                    (
                        f"Showing first 50 of {len(df)} records. "
                        "Download the CSV report for complete data."
                    ),
                    styles["Italic"],
                )
            )

    # Build PDF.
    document.build(story)

    buffer.seek(0)

    return buffer
