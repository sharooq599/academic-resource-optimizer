import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  BookOpen,
  Building2,
  CheckCircle2,
  FileDown,
  GraduationCap,
  LayoutDashboard,
  RefreshCw,
  ShieldCheck,
  Users,
  Play,
  RotateCcw,
  SlidersHorizontal,
  Brain,
  Lightbulb,
  Search,
} from "lucide-react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";

import "./App.css";

const API = "http://127.0.0.1:8000";

const number = (value) =>
  Number(value || 0).toLocaleString("en-IN");

const formatPercent = (value) =>
  `${Number(value || 0).toFixed(1)}%`;

async function getData(endpoint) {
  const response = await fetch(`${API}${endpoint}`);

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${endpoint}`);
  }

  return response.json();
}

function StatCard({ title, value, subtitle, icon: Icon, color }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}>
        <Icon size={21} />
      </div>
      <div className="stat-content">
        <p>{title}</p>
        <h2>{value}</h2>
        <span>{subtitle}</span>
      </div>
      <ArrowUpRight className="stat-arrow" size={18} />
    </div>
  );
}

function SectionHeading({ title, description, action }) {
  return (
    <div className="section-heading">
      <div>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}

function ComparisonCard({
  title,
  baseline,
  simulated,
  change,
  suffix = "",
}) {
  const isNegative = Number(change) < 0;

  return (
    <div className="comparison-card">
      <span>{title}</span>
      <div className="comparison-values">
        <div>
          <small>Baseline</small>
          <strong>
            {number(baseline)}
            {suffix}
          </strong>
        </div>
        <div>
          <small>Simulated</small>
          <strong>
            {number(simulated)}
            {suffix}
          </strong>
        </div>
      </div>
      <div
        className={`comparison-change ${isNegative ? "negative" : "positive"
          }`}
      >
        Change: {isNegative ? "" : "+"}
        {number(change)}
        {suffix}
      </div>
    </div>
  );
}

function App() {
  const [overview, setOverview] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [allocations, setAllocations] = useState([]);
  const [unmet, setUnmet] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [exportsList, setExportsList] = useState([]);

  // Custom report generator
  const [reportSections, setReportSections] = useState([]);
  const [selectedReportSections, setSelectedReportSections] = useState([]);
  const [reportFormat, setReportFormat] = useState("pdf");
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState("");
  const [reportSuccess, setReportSuccess] = useState("");

  const [recommendationsData, setRecommendationsData] = useState({
    summary: {},
    recommendations: [],
  });

  const [recommendationsError, setRecommendationsError] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Scenario simulator state
  const [demandChange, setDemandChange] = useState(0);
  const [facultyReduction, setFacultyReduction] = useState(0);
  const [roomChange, setRoomChange] = useState(0);

  const [simulation, setSimulation] = useState(null);
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [simulationError, setSimulationError] = useState("");

  // Advanced Analytics filters
  const [analyticsSearch, setAnalyticsSearch] = useState("");
  const [analyticsSemester, setAnalyticsSemester] = useState("ALL");
  const [analyticsStatus, setAnalyticsStatus] = useState("ALL");

  // Interactive manual allocation state
  const [manualResources, setManualResources] = useState({
    faculty: [],
    rooms: [],
  });

  const [manualOverrides, setManualOverrides] = useState([]);
  const [selectedSectionId, setSelectedSectionId] = useState("");
  const [selectedFacultyId, setSelectedFacultyId] = useState("");
  const [selectedRoomId, setSelectedRoomId] = useState("");

  const [manualPreview, setManualPreview] = useState(null);
  const [manualLoading, setManualLoading] = useState(false);
  const [manualApplying, setManualApplying] = useState(false);
  const [manualError, setManualError] = useState("");
  const [manualSuccess, setManualSuccess] = useState("");

  // Load manual allocation resources and overrides
  const loadManualAllocationData = async () => {
    try {
      const [resources, overrideData] = await Promise.all([
        getData("/api/manual-allocation/resources"),
        getData("/api/manual-allocation/overrides"),
      ]);

      setManualResources({
        faculty: resources.faculty || [],
        rooms: resources.rooms || [],
      });

      setManualOverrides(
        overrideData.overrides || overrideData.items || []
      );

      setManualError("");
    } catch (err) {
      setManualError(
        err.message || "Unable to load manual allocation resources."
      );
    }
  };

  const getManualAllocationPayload = () => ({
    section_id: selectedSectionId,
    faculty_id: selectedFacultyId || null,
    room_id: selectedRoomId || null,
  });

  // Preview a manual reassignment
  const previewManualAllocation = async () => {
    if (!selectedSectionId) {
      setManualError("Please select a section.");
      return;
    }

    if (!selectedFacultyId && !selectedRoomId) {
      setManualError(
        "Select a replacement faculty member or room."
      );
      return;
    }

    setManualLoading(true);
    setManualError("");
    setManualSuccess("");
    setManualPreview(null);

    try {
      const response = await fetch(
        `${API}/api/manual-allocation/preview`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(getManualAllocationPayload()),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to preview reassignment."
        );
      }

      setManualPreview(data);
    } catch (err) {
      setManualError(err.message || "Preview failed.");
    } finally {
      setManualLoading(false);
    }
  };

  // Apply a successfully validated reassignment
  const applyManualAllocation = async () => {
    if (!manualPreview?.valid || !selectedSectionId) {
      setManualError(
        "Run a successful preview before applying."
      );
      return;
    }

    setManualApplying(true);
    setManualError("");
    setManualSuccess("");

    try {
      const response = await fetch(
        `${API}/api/manual-allocation/apply`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(getManualAllocationPayload()),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to apply reassignment."
        );
      }

      if (data.saved === false) {
        throw new Error(
          data.message || "Reassignment was not saved."
        );
      }

      setManualSuccess(
        data.message ||
        "Manual reassignment applied successfully."
      );

      setManualPreview(null);
      setSelectedFacultyId("");
      setSelectedRoomId("");

      await loadManualAllocationData();
    } catch (err) {
      setManualError(
        err.message || "Unable to apply reassignment."
      );
    } finally {
      setManualApplying(false);
    }
  };

  const resetManualAllocation = () => {
    setSelectedSectionId("");
    setSelectedFacultyId("");
    setSelectedRoomId("");
    setManualPreview(null);
    setManualError("");
    setManualSuccess("");
  };

  // Load dashboard data
  const loadDashboard = async () => {
    setLoading(true);
    setError("");

    try {
      const [
        overviewData,
        forecastData,
        allocationData,
        unmetData,
        anomalyData,
        exportData,
        recommendationsResult,
      ] = await Promise.all([
        getData("/api/overview"),
        getData("/api/forecast?limit=2000"),
        getData("/api/allocations?limit=3000"),
        getData("/api/unmet-demand?limit=2000"),
        getData("/api/anomalies?limit=100"),
        getData("/api/exports"),
        getData("/api/recommendations").catch((err) => {
          setRecommendationsError(
            err.message || "Unable to load recommendations."
          );
          return null;
        }),
      ]);

      setOverview(overviewData);
      setForecast(forecastData);
      setAllocations(allocationData);
      setUnmet(unmetData);
      setAnomalies(anomalyData);
      setExportsList(exportData.exports || []);

      if (recommendationsResult) {
        setRecommendationsData(recommendationsResult);
        setRecommendationsError("");
      }

      await loadManualAllocationData();
    } catch (err) {
      setError(err.message || "Unable to connect to the API.");
    } finally {
      setLoading(false);
    }
  };

  // Load report sections exposed by the backend
  const loadReportSections = async () => {
    try {
      const data = await getData("/api/reports/sections");
      const rawSections = Array.isArray(data)
        ? data
        : data.sections || data.available_sections || [];

      const normalized = rawSections.map((item) => {
        if (typeof item === "string") {
          return {
            key: item,
            label: item.replaceAll("_", " "),
            available: true,
          };
        }

        return {
          key: item.key || item.id || item.name,
          label:
            item.label ||
            item.title ||
            item.description ||
            item.key ||
            item.id ||
            item.name,
          available: item.available !== false,
          rowCount: item.row_count ?? item.records ?? item.count,
        };
      }).filter((item) => item.key);

      setReportSections(normalized);
      setSelectedReportSections(
        normalized.filter((item) => item.available).map((item) => item.key)
      );
      setReportError("");
    } catch (err) {
      setReportError(
        err.message || "Unable to load report sections. Please refresh."
      );
    }
  };

  const toggleReportSection = (sectionKey) => {
    setSelectedReportSections((current) =>
      current.includes(sectionKey)
        ? current.filter((key) => key !== sectionKey)
        : [...current, sectionKey]
    );
    setReportError("");
    setReportSuccess("");
  };

  const generateCustomReport = async () => {
    if (selectedReportSections.length === 0) {
      setReportError("Select at least one report section.");
      setReportSuccess("");
      return;
    }

    setReportLoading(true);
    setReportError("");
    setReportSuccess("");

    try {
      const response = await fetch(`${API}/api/reports/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: reportFormat === "pdf" ? "application/pdf" : "text/csv,*/*",
        },
        body: JSON.stringify({
          sections: selectedReportSections,
          format: reportFormat,
        }),
      });

      if (!response.ok) {
        let message = `Report generation failed (HTTP ${response.status}).`;
        try {
          const errorData = await response.json();
          message =
            typeof errorData.detail === "string"
              ? errorData.detail
              : JSON.stringify(errorData.detail || errorData);
        } catch {
          // Keep the HTTP error message when the response is not JSON.
        }
        throw new Error(message);
      }

      const blob = await response.blob();
      const disposition = response.headers.get("content-disposition") || "";
      const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
      const extension = reportFormat === "pdf" ? "pdf" : "csv";
      const filename =
        filenameMatch?.[1] || `academic_optimizer_custom_report.${extension}`;

      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setReportSuccess(
        `${filename} generated successfully. Your download should begin automatically.`
      );
    } catch (err) {
      setReportError(err.message || "Unable to generate the custom report.");
    } finally {
      setReportLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    loadReportSections();
  }, []);

  // Run what-if scenario
  const runSimulation = async () => {
    setSimulationLoading(true);
    setSimulationError("");
    setSimulation(null);

    try {
      const response = await fetch(`${API}/api/simulation/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          demand_change_pct: demandChange,
          faculty_availability_reduction_pct: facultyReduction,
          room_capacity_change_pct: roomChange,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to run the simulation."
        );
      }

      setSimulation(data);
    } catch (err) {
      setSimulationError(
        err.message || "Simulation failed. Please try again."
      );
    } finally {
      setSimulationLoading(false);
    }
  };

  const resetSimulation = () => {
    setDemandChange(0);
    setFacultyReduction(0);
    setRoomChange(0);
    setSimulation(null);
    setSimulationError("");
  };

  const semesterData = useMemo(() => {
    const grouped = {};

    forecast.forEach((item) => {
      const semester = Number(item.semester);
      const key = `Semester ${semester}`;

      if (!grouped[key]) {
        grouped[key] = {
          semester: key,
          demand: 0,
          sections: 0,
        };
      }

      grouped[key].demand += Number(
        item.predicted_demand || 0
      );

      grouped[key].sections += Number(
        item.planned_sections || 0
      );
    });

    return Object.values(grouped);
  }, [forecast]);

  const allocationStatusData = useMemo(() => {
    const allocated = allocations.filter(
      (item) => item.allocation_status === "ALLOCATED"
    ).length;

    const unallocated = allocations.filter(
      (item) => item.allocation_status !== "ALLOCATED"
    ).length;

    return [
      { name: "Allocated", value: allocated },
      { name: "Unallocated", value: unallocated },
    ];
  }, [allocations]);

  const topUnmetDemand = useMemo(() => {
    return [...unmet]
      .sort(
        (a, b) =>
          Number(b.unmet_demand || 0) -
          Number(a.unmet_demand || 0)
      )
      .slice(0, 10);
  }, [unmet]);

  const anomalySummary = useMemo(() => {
    const grouped = {};

    anomalies.forEach((item) => {
      const type =
        item.anomaly_type || item.anomaly_category || "Unknown";

      grouped[type] = (grouped[type] || 0) + 1;
    });

    return Object.entries(grouped).map(([name, value]) => ({
      name,
      value,
    }));
  }, [anomalies]);

  const recommendations = useMemo(() => {
    return recommendationsData?.recommendations || [];
  }, [recommendationsData]);

  const recommendationSummary = recommendationsData?.summary || {};

  // Advanced Analytics: combine forecast, allocation and unmet demand
  const analyticsRows = useMemo(() => {
    const allocationMap = {};
    const unmetMap = {};

    allocations.forEach((item) => {
      const key = `${item.course_id}-${item.semester}`;

      if (!allocationMap[key]) {
        allocationMap[key] = {
          allocated: 0,
          unallocated: 0,
        };
      }

      if (item.allocation_status === "ALLOCATED") {
        allocationMap[key].allocated += 1;
      } else {
        allocationMap[key].unallocated += 1;
      }
    });

    unmet.forEach((item) => {
      const key = `${item.course_id}-${item.semester}`;
      unmetMap[key] = Number(item.unmet_demand || 0);
    });

    return forecast.map((item) => {
      const key = `${item.course_id}-${item.semester}`;
      const allocation = allocationMap[key] || {
        allocated: 0,
        unallocated: 0,
      };

      return {
        course_id: item.course_id,
        course_name: item.course_name,
        semester: String(item.semester),
        predicted_demand: Number(item.predicted_demand || 0),
        planned_sections: Number(item.planned_sections || 0),
        allocated_sections: allocation.allocated,
        unallocated_sections: allocation.unallocated,
        unmet_demand: unmetMap[key] || 0,
      };
    });
  }, [forecast, allocations, unmet]);

  const filteredAnalytics = useMemo(() => {
    return analyticsRows.filter((item) => {
      const search = analyticsSearch.toLowerCase().trim();

      const matchesSearch =
        !search ||
        String(item.course_name || "").toLowerCase().includes(search) ||
        String(item.course_id || "").toLowerCase().includes(search);

      const matchesSemester =
        analyticsSemester === "ALL" ||
        item.semester === analyticsSemester;

      const matchesStatus =
        analyticsStatus === "ALL" ||
        (analyticsStatus === "ALLOCATED" &&
          item.allocated_sections > 0 &&
          item.unallocated_sections === 0) ||
        (analyticsStatus === "PARTIAL" &&
          item.allocated_sections > 0 &&
          item.unallocated_sections > 0) ||
        (analyticsStatus === "UNALLOCATED" &&
          item.allocated_sections === 0);

      return (
        matchesSearch &&
        matchesSemester &&
        matchesStatus
      );
    });
  }, [
    analyticsRows,
    analyticsSearch,
    analyticsSemester,
    analyticsStatus,
  ]);

  const analyticsSummary = useMemo(() => {
    return filteredAnalytics.reduce(
      (summary, item) => ({
        courses: summary.courses + 1,
        demand: summary.demand + item.predicted_demand,
        allocated: summary.allocated + item.allocated_sections,
        unmet: summary.unmet + item.unmet_demand,
      }),
      {
        courses: 0,
        demand: 0,
        allocated: 0,
        unmet: 0,
      }
    );
  }, [filteredAnalytics]);

  const analyticsChartData = useMemo(() => {
    return [...filteredAnalytics]
      .sort(
        (a, b) => b.predicted_demand - a.predicted_demand
      )
      .slice(0, 10);
  }, [filteredAnalytics]);

  const downloadFile = (exportName) => {
    window.open(
      `${API}/api/exports/${exportName}`,
      "_blank"
    );
  };

  const getPriorityClass = (priority) => {
    return String(priority || "LOW").toLowerCase();
  };

  const getPriorityIcon = (priority) => {
    if (priority === "HIGH") return <AlertTriangle size={17} />;
    if (priority === "MEDIUM") return <Lightbulb size={17} />;
    return <CheckCircle2 size={17} />;
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <RefreshCw className="loading-spinner" size={30} />
        <p>Loading Academic Resource Optimizer...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-screen">
        <AlertTriangle size={35} />
        <h2>Unable to load dashboard</h2>
        <p>{error}</p>
        <button onClick={loadDashboard}>
          <RefreshCw size={16} />
          Retry
        </button>
      </div>
    );
  }
    return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">
            <GraduationCap size={25} />
          </div>

          <div>
            <h2>Academic Optimizer</h2>
            <span>Resource Intelligence</span>
          </div>
        </div>

        <div className="sidebar-label">WORKSPACE</div>

        <nav className="sidebar-nav">
          <a href="#overview" className="nav-link active">
            <LayoutDashboard size={18} />
            <span>Overview</span>
          </a>

          <a href="#forecast" className="nav-link">
            <Activity size={18} />
            <span>Demand Forecast</span>
          </a>

          <a href="#analytics" className="nav-link">
            <Activity size={18} />
            <span>Advanced Analytics</span>
          </a>

          <a href="#allocation" className="nav-link">
            <Building2 size={18} />
            <span>Resource Allocation</span>
          </a>

          <a href="#manual-allocation" className="nav-link">
            <Users size={18} />
            <span>Manual Allocation</span>
          </a>

          <a href="#unmet" className="nav-link">
            <AlertTriangle size={18} />
            <span>Unmet Demand</span>
          </a>

          <a href="#anomalies" className="nav-link">
            <ShieldCheck size={18} />
            <span>Anomaly Detection</span>
          </a>

          <a href="#recommendations" className="nav-link">
            <Brain size={18} />
            <span>AI Recommendations</span>
          </a>

          <a href="#simulator" className="nav-link">
            <SlidersHorizontal size={18} />
            <span>Scenario Simulator</span>
          </a>

          <a href="#custom-reports" className="nav-link">
            <FileDown size={18} />
            <span>Custom Reports</span>
          </a>

          <a href="#downloads" className="nav-link">
            <FileDown size={18} />
            <span>Downloads</span>
          </a>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-footer-icon">
            <ShieldCheck size={18} />
          </div>
          <div>
            <strong>System Status</strong>
            <span>All systems operational</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Header */}
        <header className="topbar">
          <div>
            <h1>Academic Demand & Resource Optimizer</h1>
            <p>
              Intelligent academic planning, forecasting and resource
              management
            </p>
          </div>

          <button className="refresh-button" onClick={loadDashboard}>
            <RefreshCw size={16} />
            Refresh Data
          </button>
        </header>

        {/* Overview */}
        <section id="overview" className="dashboard-section">
          <SectionHeading
            title="Dashboard Overview"
            description="A real-time view of academic demand and resource utilization."
          />

          <div className="stats-grid">
            <StatCard
              title="Total Programs"
              value={number(overview?.total_programs)}
              subtitle="Academic programs"
              icon={GraduationCap}
              color="blue"
            />

            <StatCard
              title="Total Courses"
              value={number(overview?.total_courses)}
              subtitle="Available courses"
              icon={BookOpen}
              color="purple"
            />

            <StatCard
              title="Total Faculty"
              value={number(overview?.total_faculty)}
              subtitle="Faculty members"
              icon={Users}
              color="green"
            />

            <StatCard
              title="Total Rooms"
              value={number(overview?.total_rooms)}
              subtitle="Available classrooms"
              icon={Building2}
              color="orange"
            />
          </div>

          <div className="stats-grid secondary-stats">
            <StatCard
              title="Predicted Demand"
              value={number(overview?.total_predicted_demand)}
              subtitle="Expected student demand"
              icon={Activity}
              color="blue"
            />

            <StatCard
              title="Planned Sections"
              value={number(overview?.total_planned_sections)}
              subtitle="Sections required"
              icon={BookOpen}
              color="purple"
            />

            <StatCard
              title="Allocated Sections"
              value={number(overview?.allocated_sections)}
              subtitle="Successfully allocated"
              icon={CheckCircle2}
              color="green"
            />

            <StatCard
              title="Unmet Demand"
              value={number(overview?.total_unmet_demand)}
              subtitle="Demand not yet served"
              icon={AlertTriangle}
              color="orange"
            />
          </div>
        </section>

        {/* Forecast */}
        <section id="forecast" className="dashboard-section">
          <SectionHeading
            title="Demand Forecast"
            description="Predicted course demand and planned sections across semesters."
          />

          <div className="charts-grid">
            <div className="chart-card">
              <h4>Semester-wise Predicted Demand</h4>

              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={semesterData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                  />
                  <XAxis dataKey="semester" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar
                    dataKey="demand"
                    name="Predicted Demand"
                    fill="#6366f1"
                    radius={[6, 6, 0, 0]}
                  />
                  <Bar
                    dataKey="sections"
                    name="Planned Sections"
                    fill="#14b8a6"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h4>Forecast Information</h4>

              <div className="forecast-info">
                <div>
                  <span>Forecast Records</span>
                  <strong>{number(forecast.length)}</strong>
                </div>

                <div>
                  <span>Forecast Year</span>
                  <strong>2026</strong>
                </div>

                <div>
                  <span>Model</span>
                  <strong>Random Forest</strong>
                </div>

                <div>
                  <span>Forecasting Status</span>
                  <strong className="status-success">
                    <CheckCircle2 size={15} />
                    Completed
                  </strong>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Advanced Analytics */}
        <section id="analytics" className="dashboard-section">
          <SectionHeading
            title="Advanced Analytics & Filters"
            description="Explore course demand, allocation performance and unmet demand using interactive filters."
          />

          <div className="analytics-filter-panel">
            <div className="analytics-search">
              <Search size={17} />
              <input
                type="text"
                placeholder="Search by course name or ID..."
                value={analyticsSearch}
                onChange={(event) =>
                  setAnalyticsSearch(event.target.value)
                }
              />
            </div>

            <select
              value={analyticsSemester}
              onChange={(event) =>
                setAnalyticsSemester(event.target.value)
              }
            >
              <option value="ALL">All Semesters</option>
              <option value="1">Semester 1</option>
              <option value="2">Semester 2</option>
            </select>

            <select
              value={analyticsStatus}
              onChange={(event) =>
                setAnalyticsStatus(event.target.value)
              }
            >
              <option value="ALL">All Allocation Statuses</option>
              <option value="ALLOCATED">Allocated</option>
              <option value="PARTIAL">Partially Allocated</option>
              <option value="UNALLOCATED">Unallocated</option>
            </select>

            <button
              className="secondary-button"
              onClick={() => {
                setAnalyticsSearch("");
                setAnalyticsSemester("ALL");
                setAnalyticsStatus("ALL");
              }}
            >
              <RotateCcw size={15} />
              Reset Filters
            </button>
          </div>

          <div className="analytics-kpi-grid">
            <div className="analytics-kpi-card">
              <span>Filtered Courses</span>
              <strong>{number(analyticsSummary.courses)}</strong>
            </div>

            <div className="analytics-kpi-card">
              <span>Predicted Demand</span>
              <strong>{number(analyticsSummary.demand)}</strong>
            </div>

            <div className="analytics-kpi-card">
              <span>Allocated Sections</span>
              <strong>{number(analyticsSummary.allocated)}</strong>
            </div>

            <div className="analytics-kpi-card">
              <span>Unmet Demand</span>
              <strong className="danger-text">
                {number(analyticsSummary.unmet)}
              </strong>
            </div>
          </div>

          <div className="chart-card analytics-chart-card">
            <h4>Top 10 Courses by Predicted Demand</h4>

            <ResponsiveContainer width="100%" height={330}>
              <BarChart
                data={analyticsChartData}
                margin={{
                  top: 10,
                  right: 15,
                  left: 5,
                  bottom: 55,
                }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />

                <XAxis
                  dataKey="course_id"
                  angle={-35}
                  textAnchor="end"
                  interval={0}
                  height={70}
                  tick={{ fontSize: 10 }}
                />

                <YAxis />
                <Tooltip />
                <Legend />

                <Bar
                  dataKey="predicted_demand"
                  name="Predicted Demand"
                  fill="#6366f1"
                  radius={[5, 5, 0, 0]}
                />

                <Bar
                  dataKey="unmet_demand"
                  name="Unmet Demand"
                  fill="#f97316"
                  radius={[5, 5, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="table-card">
            <div className="table-header">
              <h4>Course Analytics Details</h4>
              <span>{filteredAnalytics.length} courses</span>
            </div>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Course</th>
                    <th>Semester</th>
                    <th>Predicted Demand</th>
                    <th>Planned Sections</th>
                    <th>Allocated Sections</th>
                    <th>Unmet Demand</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredAnalytics.map((item) => {
                    let status = "UNALLOCATED";

                    if (
                      item.allocated_sections > 0 &&
                      item.unallocated_sections > 0
                    ) {
                      status = "PARTIAL";
                    } else if (item.allocated_sections > 0) {
                      status = "ALLOCATED";
                    }

                    return (
                      <tr
                        key={`${item.course_id}-${item.semester}`}
                      >
                        <td>
                          <strong>{item.course_name}</strong>
                          <small>{item.course_id}</small>
                        </td>

                        <td>{item.semester}</td>
                        <td>{number(item.predicted_demand)}</td>
                        <td>{number(item.planned_sections)}</td>
                        <td>{number(item.allocated_sections)}</td>

                        <td className="danger-text">
                          {number(item.unmet_demand)}
                        </td>

                        <td>
                          <span
                            className={`analytics-status ${status.toLowerCase()}`}
                          >
                            {status === "PARTIAL"
                              ? "Partially Allocated"
                              : status === "ALLOCATED"
                                ? "Allocated"
                                : "Unallocated"}
                          </span>
                        </td>
                      </tr>
                    );
                  })}

                  {filteredAnalytics.length === 0 && (
                    <tr>
                      <td colSpan="7" className="empty-state">
                        No courses match the selected filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Resource Allocation */}
        <section id="allocation" className="dashboard-section">
          <SectionHeading
            title="Resource Allocation"
            description="Overview of faculty and classroom allocation results."
          />

          <div className="charts-grid">
            <div className="chart-card">
              <h4>Allocation Status Distribution</h4>

              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={allocationStatusData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    label
                  >
                    {allocationStatusData.map((entry, index) => (
                      <Cell
                        key={`allocation-cell-${index}`}
                        fill={
                          index === 0 ? "#10b981" : "#f97316"
                        }
                      />
                    ))}
                  </Pie>

                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h4>Allocation Summary</h4>

              <div className="forecast-info">
                <div>
                  <span>Total Sections</span>
                  <strong>{number(allocations.length)}</strong>
                </div>

                <div>
                  <span>Allocated</span>
                  <strong className="status-success">
                    {number(allocationStatusData[0]?.value)}
                  </strong>
                </div>

                <div>
                  <span>Unallocated</span>
                  <strong className="danger-text">
                    {number(allocationStatusData[1]?.value)}
                  </strong>
                </div>

                <div>
                  <span>Allocation Success Rate</span>
                  <strong>
                    {formatPercent(
                      allocations.length
                        ? (allocationStatusData[0]?.value /
                          allocations.length) *
                        100
                        : 0
                    )}
                  </strong>
                </div>
              </div>
            </div>
          </div>

          <div className="table-card">
            <div className="table-header">
              <h4>Recent Allocation Records</h4>
              <span>{allocations.length} records</span>
            </div>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Course</th>
                    <th>Semester</th>
                    <th>Faculty</th>
                    <th>Room</th>
                    <th>Day</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {allocations.slice(0, 15).map((item, index) => (
                    <tr key={item.section_id || index}>
                      <td>
                        <strong>{item.course_name}</strong>
                        <small>{item.course_id}</small>
                      </td>

                      <td>{item.semester}</td>
                      <td>{item.faculty_name || "—"}</td>
                      <td>{item.room_name || "—"}</td>
                      <td>{item.scheduled_day || "—"}</td>

                      <td>
                        <span
                          className={`status-badge ${item.allocation_status === "ALLOCATED"
                              ? "success"
                              : "warning"
                            }`}
                        >
                          {item.allocation_status}
                        </span>
                      </td>
                    </tr>
                  ))}

                  {allocations.length === 0 && (
                    <tr>
                      <td colSpan="6" className="empty-state">
                        No allocation records available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
                    {/* Interactive Manual Resource Allocation */}
          <div id="manual-allocation" className="manual-allocation-panel">
            <SectionHeading
              title="Interactive Resource Allocation"
              description="Select a section, choose replacement resources, validate the change, and apply it."
            />

            <div className="manual-allocation-form">
              <div className="manual-form-group">
                <label htmlFor="manual-section">
                  Select Section
                </label>

                <select
                  id="manual-section"
                  value={selectedSectionId}
                  onChange={(event) => {
                    setSelectedSectionId(event.target.value);
                    setSelectedFacultyId("");
                    setSelectedRoomId("");
                    setManualPreview(null);
                    setManualError("");
                    setManualSuccess("");
                  }}
                >
                  <option value="">Choose an allocated section</option>

                  {allocations
                    .filter(
                      (item) =>
                        item.allocation_status === "ALLOCATED"
                    )
                    .map((item) => (
                      <option
                        key={item.section_id}
                        value={item.section_id}
                      >
                        {item.section_id} - {item.course_name}
                        {" (Semester "}
                        {item.semester}
                        {")"}
                      </option>
                    ))}
                </select>
              </div>

              <div className="manual-form-group">
                <label htmlFor="manual-faculty">
                  Replacement Faculty
                </label>

                <select
                  id="manual-faculty"
                  value={selectedFacultyId}
                  onChange={(event) => {
                    setSelectedFacultyId(event.target.value);
                    setManualPreview(null);
                    setManualError("");
                  }}
                >
                  <option value="">Keep existing faculty</option>

                  {manualResources.faculty.map((item) => (
                    <option
                      key={item.faculty_id}
                      value={item.faculty_id}
                    >
                      {item.faculty_name || item.name || item.faculty_id}
                      {" ("}
                      {item.faculty_id}
                      {")"}
                    </option>
                  ))}
                </select>
              </div>

              <div className="manual-form-group">
                <label htmlFor="manual-room">
                  Replacement Room
                </label>

                <select
                  id="manual-room"
                  value={selectedRoomId}
                  onChange={(event) => {
                    setSelectedRoomId(event.target.value);
                    setManualPreview(null);
                    setManualError("");
                  }}
                >
                  <option value="">Keep existing room</option>

                  {manualResources.rooms.map((item) => (
                    <option
                      key={item.room_id}
                      value={item.room_id}
                    >
                      {item.room_name || item.name || item.room_id}
                      {" ("}
                      {item.room_id}
                      {") - Capacity "}
                      {item.capacity}
                      {" - "}
                      {item.room_type}
                    </option>
                  ))}
                </select>
              </div>

              <div className="manual-form-actions">
                <button
                  className="primary-button"
                  onClick={previewManualAllocation}
                  disabled={manualLoading || manualApplying}
                >
                  {manualLoading ? (
                    <RefreshCw
                      size={16}
                      className="loading-spinner"
                    />
                  ) : (
                    <Search size={16} />
                  )}

                  {manualLoading
                    ? "Validating..."
                    : "Preview Changes"}
                </button>

                <button
                  className="secondary-button"
                  onClick={resetManualAllocation}
                  disabled={manualLoading || manualApplying}
                >
                  <RotateCcw size={15} />
                  Reset
                </button>
              </div>
            </div>

            {manualError && (
              <div className="error-notice">
                <AlertTriangle size={17} />
                <span>{manualError}</span>
              </div>
            )}

            {manualSuccess && (
              <div className="manual-success-notice">
                <CheckCircle2 size={18} />
                <span>{manualSuccess}</span>
              </div>
            )}

            {manualPreview && (
              <div className="manual-preview-card">
                <div className="manual-preview-header">
                  <div>
                    <h4>Reassignment Preview</h4>
                    <p>
                      Section:{" "}
                      {manualPreview.section?.section_id ||
                        selectedSectionId}
                      {manualPreview.section?.course_name
                        ? ` · ${manualPreview.section.course_name}`
                        : ""}
                    </p>
                  </div>

                  <span
                    className={`manual-validation-badge ${
                      manualPreview.valid ? "valid" : "invalid"
                    }`}
                  >
                    {manualPreview.valid
                      ? "Validation Passed"
                      : "Validation Failed"}
                  </span>
                </div>

                <div className="manual-assignment-comparison">
                  <div>
                    <span>Original Faculty</span>
                    <strong>
                      {manualPreview.original_assignment?.faculty_name ||
                        manualPreview.original_assignment?.faculty_id ||
                        "—"}
                    </strong>

                    <span>Original Room</span>
                    <strong>
                      {manualPreview.original_assignment?.room_name ||
                        manualPreview.original_assignment?.room_id ||
                        "—"}
                    </strong>
                  </div>

                  <div>
                    <span>Proposed Faculty</span>
                    <strong>
                      {manualPreview.proposed_assignment?.faculty_name ||
                        manualPreview.proposed_assignment?.faculty_id ||
                        "Unchanged"}
                    </strong>

                    <span>Proposed Room</span>
                    <strong>
                      {manualPreview.proposed_assignment?.room_name ||
                        manualPreview.proposed_assignment?.room_id ||
                        "Unchanged"}
                    </strong>
                  </div>
                </div>

                {manualPreview.errors?.length > 0 && (
                  <div className="manual-validation-errors">
                    <strong>
                      <AlertTriangle size={16} />
                      Validation Errors
                    </strong>

                    {manualPreview.errors.map((item, index) => (
                      <p key={index}>
                        {typeof item === "string"
                          ? item
                          : JSON.stringify(item)}
                      </p>
                    ))}
                  </div>
                )}

                {manualPreview.warnings?.length > 0 && (
                  <div className="manual-validation-warnings">
                    <strong>Warnings</strong>

                    {manualPreview.warnings.map((item, index) => (
                      <p key={index}>
                        {typeof item === "string"
                          ? item
                          : JSON.stringify(item)}
                      </p>
                    ))}
                  </div>
                )}

                {manualPreview.valid && (
                  <div className="manual-valid-notice">
                    <CheckCircle2 size={17} />
                    All validation checks passed. You can apply this
                    reassignment.
                  </div>
                )}

                <button
                  className="primary-button manual-apply-button"
                  onClick={applyManualAllocation}
                  disabled={
                    !manualPreview.valid ||
                    manualApplying ||
                    manualLoading
                  }
                >
                  {manualApplying ? (
                    <RefreshCw
                      size={16}
                      className="loading-spinner"
                    />
                  ) : (
                    <CheckCircle2 size={16} />
                  )}

                  {manualApplying
                    ? "Applying..."
                    : "Apply Reassignment"}
                </button>
              </div>
            )}
          </div>

          {/* Applied Manual Overrides */}
          <div className="table-card manual-overrides-card">
            <div className="table-header">
              <h4>Applied Manual Overrides</h4>
              <span>{manualOverrides.length} overrides</span>
            </div>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Section</th>
                    <th>Course</th>
                    <th>Faculty</th>
                    <th>Room</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {manualOverrides.map((item, index) => (
                    <tr key={item.section_id || index}>
                      <td>{item.section_id || "—"}</td>
                      <td>{item.course_name || "—"}</td>
                      <td>
                        {item.faculty_name || item.faculty_id || "—"}
                      </td>
                      <td>
                        {item.room_name || item.room_id || "—"}
                      </td>
                      <td>
                        <span className="status-badge success">
                          {item.status || "APPLIED"}
                        </span>
                      </td>
                    </tr>
                  ))}

                  {manualOverrides.length === 0 && (
                    <tr>
                      <td colSpan="5" className="empty-state">
                        No manual overrides have been applied yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Unmet Demand */}
        <section id="unmet" className="dashboard-section">
          <SectionHeading
            title="Unmet Demand Analysis"
            description="Courses where predicted student demand has not been fully served."
          />

          <div className="stats-grid unmet-stats">
            <StatCard
              title="Courses with Unmet Demand"
              value={number(
                unmet.filter(
                  (item) => Number(item.unmet_demand || 0) > 0
                ).length
              )}
              subtitle="Courses requiring attention"
              icon={AlertTriangle}
              color="orange"
            />

            <StatCard
              title="Total Unmet Demand"
              value={number(
                unmet.reduce(
                  (sum, item) =>
                    sum + Number(item.unmet_demand || 0),
                  0
                )
              )}
              subtitle="Students not accommodated"
              icon={Users}
              color="purple"
            />
          </div>

          <div className="table-card">
            <div className="table-header">
              <h4>Top Courses with Unmet Demand</h4>
              <span>Top 10</span>
            </div>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Course</th>
                    <th>Semester</th>
                    <th>Predicted Demand</th>
                    <th>Planned Sections</th>
                    <th>Allocated Sections</th>
                    <th>Unmet Demand</th>
                  </tr>
                </thead>

                <tbody>
                  {topUnmetDemand.map((item, index) => (
                    <tr key={`${item.course_id}-${item.semester}-${index}`}>
                      <td>
                        <strong>{item.course_name}</strong>
                        <small>{item.course_id}</small>
                      </td>

                      <td>{item.semester}</td>
                      <td>{number(item.predicted_demand)}</td>
                      <td>{number(item.planned_sections)}</td>
                      <td>{number(item.allocated_sections)}</td>

                      <td className="danger-text">
                        <strong>{number(item.unmet_demand)}</strong>
                      </td>
                    </tr>
                  ))}

                  {topUnmetDemand.length === 0 && (
                    <tr>
                      <td colSpan="6" className="empty-state">
                        No unmet demand records available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Anomaly Detection */}
        <section id="anomalies" className="dashboard-section">
          <SectionHeading
            title="Anomaly Detection"
            description="Detected synthetic resource allocation anomalies and their classifications."
          />

          <div className="stats-grid">
            <StatCard
              title="Detected Anomalies"
              value={number(anomalies.length)}
              subtitle="Anomaly events"
              icon={AlertTriangle}
              color="orange"
            />

            <StatCard
              title="Anomaly Categories"
              value={number(anomalySummary.length)}
              subtitle="Different anomaly types"
              icon={ShieldCheck}
              color="purple"
            />
          </div>

          <div className="chart-card">
            <h4>Anomalies by Category</h4>

            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={anomalySummary}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />

                <XAxis
                  dataKey="name"
                  interval={0}
                  angle={-15}
                  textAnchor="end"
                  height={70}
                  tick={{ fontSize: 10 }}
                />

                <YAxis allowDecimals={false} />
                <Tooltip />

                <Bar
                  dataKey="value"
                  name="Detected Events"
                  fill="#f97316"
                  radius={[5, 5, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="table-card">
            <div className="table-header">
              <h4>Detected Anomaly Records</h4>
              <span>{anomalies.length} records</span>
            </div>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Anomaly ID</th>
                    <th>Anomaly Type</th>
                    <th>Description</th>
                    <th>Detection Status</th>
                  </tr>
                </thead>

                <tbody>
                  {anomalies.map((item, index) => (
                    <tr key={item.anomaly_id || index}>
                      <td>
                        {item.anomaly_id || item.event_id || "—"}
                      </td>

                      <td>
                        <strong>
                          {item.anomaly_type ||
                            item.anomaly_category ||
                            "Unknown"}
                        </strong>
                      </td>

                      <td>
                        {item.description ||
                          item.details ||
                          item.reason ||
                          "Synthetic anomaly event"}
                      </td>

                      <td>
                        <span className="status-badge warning">
                          Detected
                        </span>
                      </td>
                    </tr>
                  ))}

                  {anomalies.length === 0 && (
                    <tr>
                      <td colSpan="4" className="empty-state">
                        No anomaly records available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="info-notice">
            <ShieldCheck size={18} />
            <p>
              Anomaly detection is evaluated against the five
              intentionally injected synthetic anomaly events.
              Results should not be interpreted as real-world
              detection accuracy.
            </p>
          </div>
        </section>

        {/* AI Recommendations */}
        <section
          id="recommendations"
          className="dashboard-section"
        >
          <SectionHeading
            title="Explainable AI Recommendations"
            description="Actionable suggestions based on course demand and allocation constraints."
          />

          {recommendationsError && (
            <div className="error-notice">
              <AlertTriangle size={17} />
              <span>{recommendationsError}</span>
            </div>
          )}

          <div className="recommendation-summary-grid">
            <div className="recommendation-summary-card">
              <span>Total Recommendations</span>
              <strong>
                {number(recommendationSummary.total_recommendations)}
              </strong>
            </div>

            <div className="recommendation-summary-card high">
              <span>High Priority</span>
              <strong>
                {number(recommendationSummary.high_priority)}
              </strong>
            </div>

            <div className="recommendation-summary-card medium">
              <span>Medium Priority</span>
              <strong>
                {number(recommendationSummary.medium_priority)}
              </strong>
            </div>

            <div className="recommendation-summary-card low">
              <span>Low Priority</span>
              <strong>
                {number(recommendationSummary.low_priority)}
              </strong>
            </div>
          </div>

          <div className="recommendation-list">
            {recommendations.map((item, index) => {
              const priority =
                item.priority || item.priority_level || "LOW";

              return (
                <div
                  className="recommendation-card"
                  key={
                    item.course_id ||
                    item.recommendation_id ||
                    index
                  }
                >
                  <div className="recommendation-card-header">
                    <div>
                      <span
                        className={`priority-badge ${getPriorityClass(
                          priority
                        )}`}
                      >
                        {getPriorityIcon(priority)}
                        {priority} PRIORITY
                      </span>

                      <h4>{item.course_name || "Course"}</h4>

                      <small>
                        {item.course_id || "—"} · Semester{" "}
                        {item.semester || "—"}
                      </small>
                    </div>

                    <div className="recommendation-unmet">
                      <span>Unmet Demand</span>
                      <strong>
                        {number(item.unmet_demand)}
                      </strong>
                    </div>
                  </div>

                  <div className="recommendation-details">
                    <div>
                      <strong>Explanation</strong>
                      <p>
                        {item.explanation ||
                          item.reason ||
                          "Review the course allocation and demand."}
                      </p>
                    </div>

                    <div>
                      <strong>Recommended Action</strong>
                      <p>
                        {item.recommended_action ||
                          item.action ||
                          "Review available academic resources."}
                      </p>
                    </div>

                    {item.failure_reasons && (
                      <div>
                        <strong>Allocation Failure Reasons</strong>
                        <p>
                          {Array.isArray(item.failure_reasons)
                            ? item.failure_reasons.join(", ")
                            : item.failure_reasons}
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="recommendation-card-footer">
                    <span>
                      Evidence:{" "}
                      {item.evidence_level || "DATA_BASED"}
                    </span>

                    <span>
                      Planned Sections:{" "}
                      {number(item.planned_sections)}
                    </span>
                  </div>
                </div>
              );
            })}

            {recommendations.length === 0 &&
              !recommendationsError && (
                <div className="empty-card">
                  <Lightbulb size={25} />
                  <p>No recommendations available.</p>
                </div>
              )}
          </div>

          <div className="info-notice">
            <ShieldCheck size={18} />
            <p>
              Recommendations are generated from existing forecast
              and allocation results. They are decision-support
              suggestions and do not automatically modify
              allocations or database records.
            </p>
          </div>
        </section>
                {/* Scenario Simulator */}
        <section id="simulator" className="dashboard-section">
          <SectionHeading
            title="What-If Scenario Simulator"
            description="Explore how changes in academic demand and resource availability may affect allocation outcomes."
          />

          <div className="simulator-layout">
            <div className="simulator-controls">
              <div className="simulator-control">
                <div className="simulator-control-heading">
                  <label htmlFor="demand-slider">
                    Demand Change
                  </label>

                  <strong>
                    {demandChange > 0 ? "+" : ""}
                    {demandChange}%
                  </strong>
                </div>

                <input
                  id="demand-slider"
                  type="range"
                  min="-30"
                  max="50"
                  step="5"
                  value={demandChange}
                  onChange={(event) =>
                    setDemandChange(Number(event.target.value))
                  }
                />

                <div className="slider-labels">
                  <span>-30%</span>
                  <span>+50%</span>
                </div>
              </div>

              <div className="simulator-control">
                <div className="simulator-control-heading">
                  <label htmlFor="faculty-slider">
                    Faculty Availability Reduction
                  </label>

                  <strong>{facultyReduction}%</strong>
                </div>

                <input
                  id="faculty-slider"
                  type="range"
                  min="0"
                  max="50"
                  step="5"
                  value={facultyReduction}
                  onChange={(event) =>
                    setFacultyReduction(
                      Number(event.target.value)
                    )
                  }
                />

                <div className="slider-labels">
                  <span>0%</span>
                  <span>50%</span>
                </div>
              </div>

              <div className="simulator-control">
                <div className="simulator-control-heading">
                  <label htmlFor="room-slider">
                    Room Capacity Change
                  </label>

                  <strong>
                    {roomChange > 0 ? "+" : ""}
                    {roomChange}%
                  </strong>
                </div>

                <input
                  id="room-slider"
                  type="range"
                  min="-30"
                  max="30"
                  step="5"
                  value={roomChange}
                  onChange={(event) =>
                    setRoomChange(Number(event.target.value))
                  }
                />

                <div className="slider-labels">
                  <span>-30%</span>
                  <span>+30%</span>
                </div>
              </div>

              <div className="simulator-actions">
                <button
                  className="primary-button"
                  onClick={runSimulation}
                  disabled={simulationLoading}
                >
                  {simulationLoading ? (
                    <RefreshCw
                      size={16}
                      className="loading-spinner"
                    />
                  ) : (
                    <Play size={16} />
                  )}

                  {simulationLoading
                    ? "Running Simulation..."
                    : "Run Simulation"}
                </button>

                <button
                  className="secondary-button"
                  onClick={resetSimulation}
                >
                  <RotateCcw size={15} />
                  Reset
                </button>
              </div>

              {simulationError && (
                <div className="error-notice">
                  <AlertTriangle size={17} />
                  <span>{simulationError}</span>
                </div>
              )}
            </div>

            <div className="simulator-information">
              <div className="simulator-info-icon">
                <SlidersHorizontal size={23} />
              </div>

              <h4>Scenario Planning</h4>

              <p>
                Adjust the input parameters to explore alternative
                academic planning conditions.
              </p>

              <ul>
                <li>Change predicted student demand.</li>
                <li>Reduce the available faculty pool.</li>
                <li>Increase or decrease room capacity.</li>
                <li>Compare simulated outcomes with the baseline.</li>
              </ul>

              <div className="simulator-safe-note">
                <ShieldCheck size={17} />
                <span>
                  Simulation runs in memory and does not modify
                  the original database or output files.
                </span>
              </div>
            </div>
          </div>

          {simulation && (
            <div className="simulation-results">
              <SectionHeading
                title="Simulation Results"
                description="Baseline versus simulated allocation outcomes."
              />

              <div className="simulation-kpi-grid">
                <ComparisonCard
                  title="Predicted Demand"
                  baseline={simulation.baseline?.total_demand}
                  simulated={simulation.simulated?.total_demand}
                  change={simulation.changes?.demand}
                />

                <ComparisonCard
                  title="Planned Sections"
                  baseline={simulation.baseline?.planned_sections}
                  simulated={simulation.simulated?.planned_sections}
                  change={simulation.changes?.planned_sections}
                />

                <ComparisonCard
                  title="Allocated Sections"
                  baseline={simulation.baseline?.allocated_sections}
                  simulated={simulation.simulated?.allocated_sections}
                  change={simulation.changes?.allocated_sections}
                />

                <ComparisonCard
                  title="Unmet Demand"
                  baseline={simulation.baseline?.unmet_demand}
                  simulated={simulation.simulated?.unmet_demand}
                  change={simulation.changes?.unmet_demand}
                />
              </div>

              <div className="chart-card">
                <h4>Baseline vs Simulated Allocation</h4>

                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={[
                      {
                        metric: "Allocated",
                        baseline:
                          simulation.baseline?.allocated_sections || 0,
                        simulated:
                          simulation.simulated?.allocated_sections || 0,
                      },
                      {
                        metric: "Unallocated",
                        baseline:
                          simulation.baseline?.unallocated_sections || 0,
                        simulated:
                          simulation.simulated?.unallocated_sections || 0,
                      },
                    ]}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                    />

                    <XAxis dataKey="metric" />
                    <YAxis />
                    <Tooltip />
                    <Legend />

                    <Bar
                      dataKey="baseline"
                      name="Baseline"
                      fill="#6366f1"
                      radius={[5, 5, 0, 0]}
                    />

                    <Bar
                      dataKey="simulated"
                      name="Simulated"
                      fill="#14b8a6"
                      radius={[5, 5, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {simulation.top_unmet_demand?.length > 0 && (
                <div className="table-card">
                  <div className="table-header">
                    <h4>Top Simulated Unmet Demand</h4>
                  </div>

                  <div className="table-wrapper">
                    <table>
                      <thead>
                        <tr>
                          <th>Course</th>
                          <th>Semester</th>
                          <th>Unmet Demand</th>
                        </tr>
                      </thead>

                      <tbody>
                        {simulation.top_unmet_demand
                          .slice(0, 10)
                          .map((item, index) => (
                            <tr
                              key={
                                item.course_id ||
                                `simulation-${index}`
                              }
                            >
                              <td>
                                <strong>{item.course_name}</strong>
                                <small>{item.course_id}</small>
                              </td>

                              <td>{item.semester}</td>

                              <td className="danger-text">
                                {number(item.unmet_demand)}
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="info-notice">
                <ShieldCheck size={18} />
                <p>
                  This is a what-if simulation using the existing
                  forecast and allocation logic. It does not
                  retrain the forecasting model or modify
                  persisted allocation results.
                </p>
              </div>
            </div>
          )}
        </section>

        {/* Custom Report Generator */}
        <section id="custom-reports" className="dashboard-section">
          <SectionHeading
            title="Custom Report Generator"
            description="Choose the project outputs you want to include and generate a downloadable PDF or CSV report."
          />

          <div className="chart-card" style={{ padding: "24px" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "12px",
                flexWrap: "wrap",
                marginBottom: "18px",
              }}
            >
              <div>
                <h4 style={{ margin: 0 }}>Select Report Sections</h4>
                <p style={{ margin: "6px 0 0", color: "#64748b", fontSize: "13px" }}>
                  {selectedReportSections.length} of {reportSections.length} sections selected
                </p>
              </div>

              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    setSelectedReportSections(
                      reportSections.filter((item) => item.available).map((item) => item.key)
                    );
                    setReportError("");
                    setReportSuccess("");
                  }}
                  disabled={reportSections.filter((item) => item.available).length === 0}
                >
                  Select All
                </button>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    setSelectedReportSections([]);
                    setReportError("");
                    setReportSuccess("");
                  }}
                >
                  Clear All
                </button>
              </div>
            </div>

            {reportSections.length === 0 ? (
              <div className="empty-state">
                {reportError
                  ? "Report sections could not be loaded."
                  : "Loading available report sections..."}
              </div>
            ) : (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                  gap: "12px",
                  marginBottom: "24px",
                }}
              >
                {reportSections.map((item) => (
                  <label
                    key={item.key}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "10px",
                      padding: "14px",
                      border: "1px solid #e2e8f0",
                      borderRadius: "10px",
                      background: selectedReportSections.includes(item.key)
                        ? "#f8fafc"
                        : "#ffffff",
                      opacity: item.available ? 1 : 0.55,
                      cursor: item.available ? "pointer" : "not-allowed",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedReportSections.includes(item.key)}
                      disabled={!item.available}
                      onChange={() => toggleReportSection(item.key)}
                      style={{ marginTop: "3px" }}
                    />
                    <span>
                      <strong style={{ display: "block", textTransform: "capitalize" }}>
                        {String(item.label).replaceAll("_", " ")}
                      </strong>
                      <small style={{ color: "#64748b" }}>
                        {item.available
                          ? item.rowCount != null
                            ? `${number(item.rowCount)} records`
                            : "Available"
                          : "Not available"}
                      </small>
                    </span>
                  </label>
                ))}
              </div>
            )}

            <div
              style={{
                display: "flex",
                alignItems: "end",
                gap: "16px",
                flexWrap: "wrap",
              }}
            >
              <div className="manual-form-group" style={{ minWidth: "180px" }}>
                <label htmlFor="custom-report-format">Report Format</label>
                <select
                  id="custom-report-format"
                  value={reportFormat}
                  onChange={(event) => {
                    setReportFormat(event.target.value);
                    setReportError("");
                    setReportSuccess("");
                  }}
                >
                  <option value="pdf">PDF Document</option>
                  <option value="csv">CSV Spreadsheet</option>
                </select>
              </div>

              <button
                type="button"
                className="primary-button"
                onClick={generateCustomReport}
                disabled={reportLoading || selectedReportSections.length === 0}
              >
                {reportLoading ? (
                  <RefreshCw size={16} className="loading-spinner" />
                ) : (
                  <FileDown size={16} />
                )}
                {reportLoading ? "Generating Report..." : "Generate Report"}
              </button>
            </div>

            {reportError && (
              <div className="error-notice" style={{ marginTop: "18px" }}>
                <AlertTriangle size={17} />
                <span>{reportError}</span>
              </div>
            )}

            {reportSuccess && (
              <div className="manual-success-notice" style={{ marginTop: "18px" }}>
                <CheckCircle2 size={18} />
                <span>{reportSuccess}</span>
              </div>
            )}

            <div className="info-notice" style={{ marginTop: "18px" }}>
              <FileDown size={18} />
              <p>
                PDF reports provide a formatted preview of selected sections.
                CSV reports include the complete selected records for further analysis.
              </p>
            </div>
          </div>
        </section>

        {/* Downloads */}
        <section id="downloads" className="dashboard-section">
          <SectionHeading
            title="Downloads & Reports"
            description="Download generated datasets, metrics, allocation results and validation reports."
          />

          <div className="downloads-grid">
            {exportsList.map((item, index) => {
              const exportName =
                typeof item === "string"
                  ? item
                  : item.name || item.export_name;

              const displayName =
                typeof item === "string"
                  ? item
                    .replaceAll("-", " ")
                    .replaceAll("_", " ")
                    .replace(/\b\w/g, (char) =>
                      char.toUpperCase()
                    )
                  : item.label ||
                  item.description ||
                  exportName;

              return (
                <div
                  className="download-card"
                  key={exportName || index}
                >
                  <div className="download-icon">
                    <FileDown size={20} />
                  </div>

                  <div className="download-details">
                    <strong>{displayName}</strong>
                    <span>Generated project output</span>
                  </div>

                  <button
                    className="download-button"
                    onClick={() => downloadFile(exportName)}
                    disabled={!exportName}
                    title="Download file"
                  >
                    <FileDown size={17} />
                  </button>
                </div>
              );
            })}

            {exportsList.length === 0 && (
              <div className="empty-card">
                <FileDown size={25} />
                <p>No export files available.</p>
              </div>
            )}
          </div>
        </section>

        {/* Footer */}
        <footer className="dashboard-footer">
          <div>
            <strong>Academic Demand & Resource Optimizer</strong>
            <span>
              Intelligent Academic Planning and Resource Management
            </span>
          </div>

          <span>Version 1.3.0</span>
        </footer>
      </main>
    </div>
  );
}

export default App;