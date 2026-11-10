# 🎓 Academic Demand & Resource Optimizer

**An Intelligent, Machine Learning-Based Academic Planning and Resource Optimization Platform**

An end-to-end academic decision-support system that forecasts student demand, optimizes faculty and classroom allocation, detects resource constraints, generates explainable AI recommendations, and supports interactive academic planning through a modern dashboard.

Built using **Python, FastAPI, Machine Learning, React.js, and Vite**.

---

## 📌 Project Overview

Academic institutions face challenges in predicting course demand, assigning qualified faculty, managing classroom availability, and ensuring that student demand is adequately accommodated.

The **Academic Demand & Resource Optimizer** addresses these challenges through a data-driven approach that combines machine learning, constraint-based allocation, anomaly detection, explainable recommendations, and what-if scenario simulation.

The platform transforms historical academic data into actionable insights and provides an interactive dashboard for monitoring and managing academic resources.

## 🎯 Project Objectives

- Forecast future student demand for academic courses.
- Estimate the number of sections required for each course.
- Allocate qualified faculty members and suitable classrooms.
- Identify unmet demand and resource allocation constraints.
- Detect academic resource allocation anomalies.
- Generate explainable, priority-based recommendations.
- Simulate alternative academic planning scenarios.
- Provide allocation decision traceability and reproducibility.
- Generate downloadable PDF and CSV reports.

---

## ✨ Key Features

### 1. Machine Learning-Based Demand Forecasting

- Uses Random Forest Regression to predict future course demand.
- Trains using historical academic demand records.
- Uses academic year, semester, credits, course level, target section size, and previous demand as model features.
- Predicts demand for the 2026 academic year.
- Estimates the number of sections required.
- Evaluates model performance using MAE, RMSE, and R².
- Compares model performance against a previous-year baseline.

### 2. Intelligent Resource Allocation

A constraint-based allocation engine assigns faculty members and classrooms to planned academic sections.

**Allocation constraints include:**
- Faculty subject expertise and qualification.
- Faculty availability.
- Faculty workload limits.
- Classroom capacity.
- Classroom suitability.
- Faculty timetable conflicts.
- Classroom timetable conflicts.

**Allocation outcomes include:**
- Successfully allocated sections.
- Unallocated sections.
- Unmet student demand.
- Allocation decision reasons.

### 3. Interactive Manual Resource Allocation

Allows users to manually reassign faculty members and classrooms through the dashboard.

**Capabilities:**
- Select an existing allocated section.
- Choose replacement faculty members.
- Select replacement classrooms.
- Preview proposed allocation changes.
- Validate faculty skills and workload.
- Check resource availability and scheduling conflicts.
- Validate classroom capacity.
- Display validation errors and warnings.
- Apply successfully validated changes.
- View previously applied manual overrides.

### 4. Advanced Analytics Dashboard

Provides interactive academic demand and allocation analysis.

**Features:**
- Search courses using course name or course ID.
- Filter by semester.
- Filter by allocation status.
- Dynamically update KPI values.
- Compare predicted demand and unmet demand.
- Visualize the top 10 courses by predicted demand.
- Display detailed course-level analytics.

### 5. Unmet Demand Analysis

Identifies courses where predicted student demand has not been fully accommodated.

- Displays total unmet demand.
- Identifies courses requiring additional sections or resources.
- Highlights courses with higher unmet demand.
- Displays predicted demand, planned sections, and allocated sections.
- Helps prioritize academic resource planning.

### 6. Anomaly Detection

A rule-based anomaly detection engine identifies resource allocation issues.

The project includes five synthetic anomaly categories:

| Anomaly ID | Anomaly Type |
|---|---|
| ANM-001 | FACULTY_WORKLOAD_EXCEEDED |
| ANM-002 | FACULTY_SKILL_MISMATCH |
| ANM-003 | ROOM_CAPACITY_EXCEEDED |
| ANM-004 | FACULTY_TIMETABLE_CONFLICT |
| ANM-005 | ROOM_TIMETABLE_CONFLICT |

The system detects and classifies intentionally injected synthetic anomaly events.

### 7. Explainable AI Recommendations

Generates actionable recommendations using forecast and allocation results.

**Features:**
- Identifies courses with significant unmet demand.
- Categorizes recommendations into HIGH, MEDIUM, and LOW priority.
- Provides supporting evidence.
- Suggests possible resource planning actions.
- Highlights allocation-related concerns.
- Displays recommendation summaries and detailed explanations.

The recommendation engine provides decision support without automatically modifying allocation records.

### 8. What-If Scenario Simulator

Allows users to explore alternative academic planning conditions.

**Adjustable parameters:**
- Student demand percentage.
- Faculty availability reduction.
- Classroom capacity changes.

**Simulation capabilities:**
- Run alternative allocation scenarios.
- Compare baseline and simulated results.
- Analyze predicted demand changes.
- Compare allocated and unallocated sections.
- Evaluate changes in unmet demand.
- Visualize simulation results.
- Identify courses with high simulated unmet demand.

The simulator operates in memory and does not overwrite baseline allocation outputs.

### 9. Custom PDF and CSV Report Generator

Provides flexible reporting directly from the dashboard.

**Features:**
- Select individual report sections.
- Select all or clear selected sections.
- Generate PDF reports.
- Generate CSV reports.
- Download generated reports directly.
- Export forecasting, allocation, unmet demand, decision logs, anomaly results, and feature importance.

### 10. Downloadable Project Outputs

Provides access to generated datasets and evaluation outputs through the dashboard.

Includes forecasting results, allocation results, unmet demand, anomaly reports, model metrics, feature importance, and other generated project files.

---

## 🌟 Additional Engineering Features

### 11. Allocation Constraint Validation

The allocation engine identifies why a section could not be assigned.

Allocation failure categories include:

- `NO_QUALIFIED_FACULTY`
- `NO_SUITABLE_ROOM`
- `NO_COMPATIBLE_FACULTY_ROOM_SLOT`

This helps distinguish allocation failures caused by faculty qualifications, room suitability, or combined resource constraints.

### 12. Allocation Decision Traceability

A decision log connects forecasted demand with final allocation outcomes.

**Features:**
- Connects allocation records with forecast records.
- Uses course ID and semester for matching.
- Generates deterministic decision IDs.
- Records allocation status.
- Stores source forecast information.
- Includes allocation decision reasons.

This improves transparency and makes allocation outcomes easier to investigate.

### 13. Reproducibility and Deterministic Validation

The project includes a reproducibility verification workflow.

**Features:**
- Uses a fixed random seed.
- Generates a baseline of selected output files.
- Calculates file hashes.
- Compares generated outputs against the saved baseline.
- Identifies identical, changed, and missing files.

The reproducibility check helps verify consistency across tracked project outputs.

### 14. Manual Allocation Safety and Validation

The manual allocation workflow includes additional safeguards:

- Prevents unchanged or no-op assignments.
- Validates faculty subject skills.
- Checks workload limits.
- Checks faculty availability.
- Validates timetable conflicts.
- Checks classroom capacity.
- Provides warnings for room suitability.
- Saves validated manual overrides.

### 15. Data Validation and Quality Checks

Validation is performed across important stages of the project:

- Academic program and course data.
- Faculty skills and availability.
- Classroom resources.
- Student academic plans.
- Historical demand records.
- Forecast outputs.
- Resource allocation results.
- Anomaly detection outputs.
- Reproducibility comparisons.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Languages | Python, JavaScript |
| Backend Framework | FastAPI |
| Frontend Framework | React.js |
| Frontend Build Tool | Vite |
| Machine Learning | Scikit-learn |
| ML Algorithm | Random Forest Regressor |
| Data Processing | Pandas, NumPy |
| Data Visualization | Recharts |
| UI Icons | Lucide React |
| PDF Generation | ReportLab |
| API Documentation | Swagger UI |
| Version Control | Git, GitHub |

---

## 🏗️ System Architecture

```text
                 Academic Resource Optimizer
                            |
                            v
              Synthetic Academic Dataset
                            |
                            v
                  Data Processing Layer
                            |
                            v
                  Demand Forecasting
                  (Random Forest ML)
                            |
                            v
                 Predicted Course Demand
                            |
                            v
              Constraint-Based Allocation
                            |
                  +---------+---------+
                  |                   |
                  v                   v
            Allocated Sections   Unallocated Sections
                  |                   |
                  +---------+---------+
                            |
                            v
                   Unmet Demand Analysis
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
          Anomaly       Explainable    Decision
         Detection      Recommendations Log
              |             |             |
              +-------------+-------------+
                            |
                            v
                  What-If Scenario Engine
                            |
                            v
                     FastAPI Backend
                            |
                            v
                    React Dashboard
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
          Analytics    Manual Allocation  Reports
                            |
                            v
                      PDF / CSV
```

---

## 📊 Dataset Overview

The project uses synthetic academic datasets to simulate a university-level academic planning environment.

| Dataset | Records |
|---|---:|
| Academic Programs | 100 |
| Courses | 1,000 |
| Course Prerequisites | 399 |
| Faculty Members | 500 |
| Faculty Skill Records | 1,735 |
| Faculty Availability Records | 5,025 |
| Classrooms | 150 |
| Student Academic Plans | 20,000 |
| Registration Interests | 90,141 |
| Historical Demand Records | 6,000 |

Historical demand covers three academic years: 2023, 2024, and 2025.

---

## 📈 Model Performance and Project Results

The following results were obtained during project evaluation using synthetic academic data.

### Demand Forecasting Results

| Metric | Result |
|---|---:|
| Forecast Records | 2,000 |
| Forecasted Student Demand | 85,653 |
| Planned Sections | 2,745 |
| MAE | 3.0180 |
| RMSE | 3.7777 |
| R² Score | 0.6999 |
| Baseline MAE | 4.7065 |
| Baseline RMSE | 5.6229 |
| Baseline R² | 0.3351 |

### Resource Allocation Results

| Metric | Result |
|---|---:|
| Planned Sections | 2,745 |
| Allocated Sections | 2,680 |
| Unallocated Sections | 65 |
| Allocation Success Rate | 97.63% |
| Unmet Demand | 2,112 |

### Anomaly Detection Results

| Metric | Result |
|---|---:|
| Synthetic Anomaly Events Injected | 5 |
| Events Detected and Classified | 5 |
| Missed Injected Events | 0 |

### Decision Traceability

| Metric | Result |
|---|---:|
| Decision Log Records | 2,745 |
| Allocated Records | 2,680 |
| Unallocated Records | 65 |

### Reproducibility Results

| Metric | Result |
|---|---:|
| Tracked Output Files | 9 |
| Identical Files | 9 |
| Changed Files | 0 |
| Missing Files | 0 |

**Evaluation Notes:**

- Forecasting metrics are based on synthetic held-out data.
- Anomaly detection results are based on five intentionally injected synthetic events, not a representative real-world anomaly dataset.
- Allocation success rate represents allocated sections divided by planned sections.
- The reproducibility result represents comparison against the saved output baseline; it does not independently establish a fresh end-to-end pipeline rerun.

---

## 📁 Project Structure

```text
academic-resource-optimizer/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── services/
│   │       ├── allocation/
│   │       │   └── allocator.py
│   │       ├── ml/
│   │       │   └── forecasting.py
│   │       ├── simulation/
│   │       │   └── scenario_simulator.py
│   │       ├── recommendations/
│   │       │   └── recommendation_engine.py
│   │       └── reports/
│   │           └── report_generator.py
│   │
│   ├── data/
│   │   └── output/
│   ├── models/
│   ├── requirements.txt
│   ├── generate_anomalies.py
│   ├── detect_anomalies.py
│   ├── generate_decision_log.py
│   └── reproducibility_check.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── index.html
│   └── package.json
│
├── README.md
└── .gitignore
```

---

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.10 or above.
- Node.js and npm.
- Git.

### 1. Clone the Repository

```bash
git clone https://github.com/sharooq599/academic-resource-optimizer.git

cd academic-resource-optimizer
```

### 2. Backend Setup

Navigate to the backend directory:

```powershell
cd backend
```

Create and activate a virtual environment:

```powershell
python -m venv venv

venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the FastAPI server:

```powershell
uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Frontend Setup

Open a separate terminal and navigate to the frontend directory:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Start the development server:

```powershell
npm run dev
```

Open the URL displayed by Vite, typically:

```text
http://localhost:5173
```

### 4. Production Build

To generate the production frontend build:

```powershell
cd frontend

npm run build
```

---

## 🔌 Main API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/overview` | Dashboard overview |
| GET | `/api/forecast` | Demand forecasting results |
| GET | `/api/allocations` | Resource allocation records |
| GET | `/api/unmet-demand` | Unmet demand records |
| GET | `/api/anomalies` | Detected anomalies |
| GET | `/api/recommendations` | Explainable AI recommendations |
| POST | `/api/simulation/run` | Run what-if simulation |
| GET | `/api/manual-allocation/resources` | Retrieve faculty and room resources |
| GET | `/api/manual-allocation/overrides` | Retrieve manual overrides |
| POST | `/api/manual-allocation/preview` | Preview manual allocation changes |
| POST | `/api/manual-allocation/apply` | Apply validated allocation changes |
| GET | `/api/reports/sections` | Retrieve available report sections |
| GET | `/api/reports/summary` | Retrieve report summary |
| POST | `/api/reports/generate` | Generate custom PDF or CSV reports |

---

## 🧪 Testing and Validation

The project includes testing and validation workflows for:

- Synthetic dataset generation.
- Data quality validation.
- Embedding and model-independent pipeline checks where applicable.
- Forecasting model evaluation.
- Resource allocation constraint validation.
- Manual allocation preview and application.
- Synthetic anomaly detection.
- Scenario simulator baseline comparison.
- Decision log generation.
- Reproducibility comparison.
- Custom PDF and CSV report generation.

---

## ⚠️ Project Limitations

- The current implementation uses synthetic academic datasets.
- Forecasting results should be validated against real institutional data before production deployment.
- Scenario simulation uses heuristic allocation logic rather than retraining the forecasting model.
- Faculty availability and leave handling use simplified assumptions.
- Anomaly detection evaluation is based on intentionally injected synthetic events.
- Decision logs are reconstructed from final allocation and forecast outputs rather than recording every candidate decision during allocation.
- The system is currently a decision-support prototype and does not replace institutional approval workflows.

---

## 🔮 Future Enhancements

- Integration with real university management systems.
- Role-based authentication and authorization.
- Advanced optimization algorithms for resource allocation.
- Improved timetable conflict resolution.
- Real-time academic data integration.
- Advanced forecasting model comparisons.
- Cloud deployment and monitoring.
- Automated notification and approval workflows.
- Enhanced reporting and interactive visualizations.

---

## 💡 What Makes This Project Different?

Unlike a basic demand forecasting application, this project integrates the complete academic planning workflow:

1. Machine learning-based student demand forecasting.
2. Constraint-based faculty and classroom allocation.
3. Interactive manual resource reassignment.
4. Allocation constraint validation.
5. Unmet demand analysis.
6. Synthetic anomaly detection.
7. Explainable AI recommendations.
8. What-if scenario simulation.
9. Allocation decision traceability.
10. Reproducibility verification.
11. Interactive analytics dashboard.
12. Custom PDF and CSV report generation.

The platform combines predictive analytics with operational decision support, helping academic institutions make more informed resource planning decisions.

---



**Academic Demand & Resource Optimizer — Making Academic Planning Smarter Through Data and AI.**