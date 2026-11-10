# Data Dictionary — Academic Demand & Resource Optimizer

## 1. Overview

This document describes the generated datasets and output files used by the Academic Demand & Resource Optimizer.

The project uses synthetic academic data to forecast course demand, allocate faculty and classrooms, identify resource constraints, detect anomalies, and maintain allocation decision traceability.

**Reproducibility seed:** `20261022`

## 2. Dataset Summary

| Dataset | File | Description |
|---|---|---|
| Demand Forecast | `course_demand_forecast_2026.csv` | Predicted demand and section requirements |
| Section Allocations | `section_allocations.csv` | Faculty, room, and timetable assignments |
| Unmet Demand | `unmet_demand.csv` | Demand not covered by allocated sections |
| Decision Log | `allocation_decision_log.csv` | Traceability of allocation decisions |
| Anomaly Injections | `anomaly_injections.csv` | Synthetic anomaly scenarios |
| Anomaly Detection Results | `anomaly_detection_results.csv` | Detection outcomes and classifications |
| Anomaly Ground Truth | `anomaly_ground_truth.csv` | Expected anomaly labels |
| Feature Importance | `feature_importance.csv` | Forecasting model feature importance |

## 3. Demand Forecast Dataset

**File:** `course_demand_forecast_2026.csv`

Contains predicted course demand for the 2026 academic year.

| Column | Description |
|---|---|
| course_id | Unique course identifier |
| course_name | Name of the course |
| program_id | Program associated with the course |
| academic_year | Forecast academic year |
| semester | Semester identifier |
| credits | Course credit value |
| course_level | Academic level of the course |
| target_section_size | Target student capacity per section |
| lag_1 | Previous-period demand feature |
| predicted_demand | Model-predicted student demand |
| predicted_sections | Predicted number of sections |
| predicted_sections_required | Calculated section requirement |
| source_type | Origin or category of the forecast record |

## 4. Section Allocation Dataset

**File:** `section_allocations.csv`

Contains the output of the resource allocation engine.

| Column | Description |
|---|---|
| section_id | Unique section identifier |
| course_id | Associated course identifier |
| course_name | Course name |
| semester | Semester identifier |
| section_number | Section sequence number |
| section_capacity | Maximum capacity of the section |
| faculty_id | Assigned faculty identifier |
| faculty_name | Assigned faculty name |
| room_id | Assigned classroom identifier |
| room_name | Assigned room name |
| scheduled_day | Scheduled day |
| start_time | Class start time |
| end_time | Class end time |
| weekly_hours | Weekly teaching hours |
| allocation_status | Allocation outcome |
| failure_reason | Reason for unsuccessful allocation, if applicable |

## 5. Unmet Demand Dataset

**File:** `unmet_demand.csv`

Records course demand that cannot be accommodated by the allocated sections.

| Column | Description |
|---|---|
| course_id | Course identifier |
| course_name | Course name |
| semester | Semester identifier |
| predicted_demand | Forecast student demand |
| planned_sections | Planned number of sections |
| allocated_sections | Successfully allocated sections |
| unallocated_sections | Sections that could not be allocated |
| allocated_capacity | Total nominal capacity of allocated sections |
| unmet_demand | Remaining demand after allocated capacity |

## 6. Allocation Decision Log

**File:** `allocation_decision_log.csv`

Provides traceability between demand forecasts and final allocation outcomes.

| Column | Description |
|---|---|
| decision_id | Unique decision record identifier |
| section_id | Associated section identifier |
| course_id | Course identifier |
| course_name | Course name |
| academic_year | Academic year |
| semester | Semester identifier |
| predicted_demand | Forecast demand |
| predicted_sections | Predicted section count |
| predicted_sections_required | Calculated section requirement |
| faculty_id | Assigned faculty identifier |
| faculty_name | Assigned faculty name |
| room_id | Assigned room identifier |
| room_name | Assigned room name |
| scheduled_day | Scheduled day |
| start_time | Class start time |
| end_time | Class end time |
| weekly_hours | Weekly teaching hours |
| section_capacity | Section capacity |
| allocation_status | Allocation outcome |
| failure_reason | Allocation failure explanation, if any |
| decision_reason | Recorded explanation for the decision |
| source_type | Source record category |
| source_forecast | Reference to the forecast source |
| random_seed | Reproducibility seed |

**Note:** This log is reconstructed from the forecast and final allocation outputs. It is not a runtime log of every candidate assignment considered.

## 7. Anomaly Injection Dataset

**File:** `anomaly_injections.csv`

Contains deliberately generated anomaly scenarios for testing the detection system.

| Column | Description |
|---|---|
| anomaly_id | Unique anomaly identifier |
| anomaly_type | Type of injected anomaly |
| entity_type | Type of affected entity |
| entity_id | Identifier of the affected entity |
| source_section_id | Related section identifier |
| expected_condition | Expected valid condition |
| injected_condition | Deliberately introduced invalid condition |
| is_anomaly | Indicates whether the record represents an anomaly |
| injection_source | Source of the anomaly injection |
| seed | Random seed |
| course_id | Related course identifier |
| semester | Semester identifier |
| actual_weekly_workload | Original faculty workload |
| maximum_weekly_workload | Maximum permitted workload |
| injected_weekly_workload | Workload after injection |
| course_name | Related course name |
| skill_match_before_injection | Original faculty skill-match status |
| skill_match_after_injection | Skill-match status after injection |
| required_capacity | Required room or section capacity |
| actual_room_capacity | Original room capacity |
| injected_room_capacity | Room capacity used in the anomaly scenario |
| day | Simulated schedule day |
| start_time | Event start time |
| end_time | Event end time |
| simulated_event_id | Identifier of the simulated conflict event |

## 8. Anomaly Detection Results

**File:** `anomaly_detection_results.csv`

Contains injected anomaly information together with detection outcomes.

It includes the columns from `anomaly_injections.csv`, with these additional fields:

| Column | Description |
|---|---|
| detected_type | Anomaly type identified by the detector |
| detection_status | Detection outcome |
| anomaly_type_ground_truth | Expected anomaly classification |
| correct_detection | Indicates whether the detection matches the expected classification |

## 9. Anomaly Ground Truth Dataset

**File:** `ground_truth/anomaly_ground_truth.csv`

Contains the expected labels used to evaluate synthetic anomaly detection.

| Column | Description |
|---|---|
| anomaly_id | Unique anomaly identifier |
| anomaly_type | Expected anomaly category |
| entity_type | Affected entity category |
| entity_id | Affected entity identifier |
| source_section_id | Related section identifier |
| expected_condition | Expected valid condition |
| injected_condition | Injected invalid condition |
| is_anomaly | Ground-truth anomaly indicator |
| injection_source | Injection source |
| seed | Random seed |

Ground truth is maintained separately from the detection results to support evaluation.

## 10. Forecast Feature Importance

**File:** `feature_importance.csv`

Contains the importance scores of features used by the demand forecasting model.

| Column | Description |
|---|---|
| feature | Input feature name |
| importance | Feature importance score produced by the trained model |

## 11. JSON Output Files

| File | Description |
|---|---|
| `allocation_summary.json` | Summary statistics of resource allocation |
| `forecast_metrics.json` | Forecast model evaluation metrics |
| `anomaly_detection_metrics.json` | Anomaly detection evaluation metrics |
| `reproducibility_baseline.json` | Baseline file checksums and reproducibility metadata |

## 12. Data Relationships

The principal relationships between the generated outputs are:

1. `course_id` connects forecast records, section allocations, unmet demand, and decision logs.
2. `section_id` connects allocation records with their corresponding decision records and anomaly scenarios.
3. `faculty_id` identifies the faculty member assigned to an allocated section.
4. `room_id` identifies the classroom assigned to an allocated section.
5. `anomaly_id` connects anomaly injections, detection results, and ground-truth records.
6. `source_forecast` provides traceability from an allocation decision to its forecast source.

## 13. Data Validation and Reproducibility

The project includes validation for generated master data, resources, student data, historical demand, and final allocations.

The project uses a fixed seed:

`20261022`

A checksum-based reproducibility baseline tracks selected generated output files.

The baseline comparison checks whether the tracked files match the saved reference checksums.

## 14. Important Interpretation Notes

- The project uses synthetic academic datasets.
- Forecast metrics represent performance on synthetic held-out data.
- Allocated capacity represents nominal available section capacity, not confirmed student attendance.
- Anomaly detection results are evaluated against deliberately injected synthetic cases.
- The decision log is reconstructed from final output records rather than capturing every runtime allocation attempt.
- Column data types and constraints should be verified against the source schemas before treating this document as a formal database schema specification.