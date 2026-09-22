import { useEffect, useMemo, useState } from "react";
import axios from "axios";
const tableHeaderStyle = {
  textAlign: "left",
  padding: "12px",
  borderBottom: "1px solid #555",
};

const tableCellStyle = {
  padding: "12px",
  borderBottom: "1px solid #333",
};

const parseUtcDate = (value) => {
  if (!value) {
    return null;
  }

  // Backend timestamps are UTC but currently
  // arrive without "Z" or timezone offset.
  const hasTimezone =
    value.endsWith("Z") ||
    /[+-]\d{2}:\d{2}$/.test(value);

  return new Date(
    hasTimezone ? value : `${value}Z`
  );
};

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

function App() {
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState({
    total_jobs: 0,
    matching_jobs: 0,
    companies_monitored: 0,
    last_scan: null,
  });

  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
const [refreshing, setRefreshing] = useState(false);
const [lastScanResult, setLastScanResult] = useState(null);

  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [locationFilter, setLocationFilter] = useState("all");
const [companies, setCompanies] = useState([]);
const [activeTab, setActiveTab] = useState("jobs");
const [applications, setApplications] = useState([]);
const [applicationStats, setApplicationStats] = useState({
  total_applications: 0,
  applied: 0,
  assessment: 0,
  interview: 0,
  final_interview: 0,
  offer: 0,
  rejected: 0,
  withdrawn: 0,
  no_response: 0,
  interview_rate: 0,
  offer_rate: 0,
});

const fetchApplications = async () => {
  try {
    const response = await axios.get(
      `${API_URL}/applications`
    );

    setApplications(response.data);
  } catch (error) {
    console.error(
      "Failed to fetch applications:",
      error
    );
  }
};

const fetchApplicationStats = async () => {
  try {
    const response = await axios.get(
      `${API_URL}/applications/stats`
    );

    setApplicationStats(response.data);
  } catch (error) {
    console.error(
      "Failed to fetch application stats:",
      error
    );
  }
};

const fetchCompanies = async () => {
  try {
    const response = await axios.get(
      `${API_URL}/companies`
    );

    setCompanies(response.data);
  } catch (error) {
    console.error(
      "Failed to fetch companies:",
      error
    );
  }
};

  const fetchJobs = async () => {
    try {
      const response = await axios.get(
        `${API_URL}/jobs/matches`
      );

      setJobs(response.data);
    } catch (error) {
      console.error("Failed to fetch jobs:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(
        `${API_URL}/stats`
      );

      setStats(response.data);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  const refreshAll = async () => {
  try {
    setRefreshing(true);

    await Promise.all([
      fetchJobs(),
      fetchStats(),
      fetchCompanies(),
      fetchApplications(),
      fetchApplicationStats(),
    ]);
  } finally {
    setRefreshing(false);
  }
};

const scanNow = async () => {
  if (scanning) {
    return;
  }

  try {
    setScanning(true);

    const response = await axios.post(
      `${API_URL}/scan/all`
    );

    setLastScanResult(response.data);

    await Promise.all([
      fetchJobs(),
      fetchStats(),
      fetchCompanies(),
    ]);
  } catch (error) {
    console.error(
      "Manual scan failed:",
      error
    );

    alert(
      "Scan failed. Check the backend terminal."
    );
  } finally {
    setScanning(false);
  }
};

  useEffect(() => {
    refreshAll();

    const interval = setInterval(() => {
      refreshAll();
    }, 60000);

    return () => clearInterval(interval);
  }, []);

const filteredJobs = useMemo(() => {
  return jobs
    .filter((job) => {
      // Hide jobs that are already applied
      const alreadyApplied = applications.some(
        (application) =>
          application.job_id === job.id
      );

      if (alreadyApplied) {
        return false;
      }

      const searchableText =
        `${job.title} ${job.company}`.toLowerCase();

      const searchMatch =
        searchableText.includes(
          search.toLowerCase()
        );

      const roleMatch =
        roleFilter === "all" ||
        job.role_category === roleFilter;

      const location = (
        job.location || ""
      ).toLowerCase();

      let locationMatch = true;

      if (locationFilter === "bangalore") {
        locationMatch =
          location.includes("bangalore") ||
          location.includes("bengaluru");
      }

      if (locationFilter === "chennai") {
        locationMatch =
          location.includes("chennai");
      }

      if (locationFilter === "remote") {
        locationMatch =
          location.includes("remote");
      }

      return (
        searchMatch &&
        roleMatch &&
        locationMatch
      );
    })
    .sort(
      (a, b) =>
        new Date(b.first_seen_at) -
        new Date(a.first_seen_at)
    );
}, [
  jobs,
  applications,
  search,
  roleFilter,
  locationFilter,
]);

  const roleOptions = [
    ...new Set(
      jobs
        .map((job) => job.role_category)
        .filter(Boolean)
    ),
  ].sort();

  const formatExperience = (job) => {
    if (
      job.experience_min === null &&
      job.experience_max === null
    ) {
      return "Not specified";
    }

    if (
      job.experience_min !== null &&
      job.experience_max === null
    ) {
      return `${job.experience_min}+ years`;
    }

    if (
      job.experience_min === null &&
      job.experience_max !== null
    ) {
      return `Up to ${job.experience_max} years`;
    }

    return `${job.experience_min} - ${job.experience_max} years`;
  };

  const isNewJob = (job) => {
    if (!job.first_seen_at) {
      return false;
    }

  const firstSeen = parseUtcDate(
  job.first_seen_at
);
    const now = new Date();

    const hoursOld =
      (now - firstSeen) /
      (1000 * 60 * 60);

    return hoursOld <= 24;
  };

  const formatRole = (role) => {
    if (!role) {
      return "Unknown";
    }

    return role
      .split("_")
      .map(
        (word) =>
          word.charAt(0).toUpperCase() +
          word.slice(1)
      )
      .join(" ");
  };

  if (loading) {
    return (
      <div
        style={{
          padding: "30px",
          fontFamily: "Arial, sans-serif",
        }}
      >
        <h2>Loading jobs...</h2>
      </div>
    );
  }

  const markAsApplied = async (jobId) => {
  try {
    await axios.post(
      `${API_URL}/jobs/${jobId}/apply`
    );

    await Promise.all([
      fetchApplications(),
      fetchApplicationStats(),
    ]);

    alert("Job marked as applied.");
  } catch (error) {
    console.error(
      "Failed to mark job as applied:",
      error
    );

    alert("Could not mark job as applied.");
  }
};

const isApplied = (jobId) => {
  return applications.some(
    (application) =>
      application.job_id === jobId
  );
};

const availableJobs = filteredJobs.length;

const updateApplication = async (
  applicationId,
  status,
  result,
  notes
) => {
  try {
    await axios.put(
      `${API_URL}/applications/${applicationId}`,
      null,
      {
        params: {
          status,
          result,
          notes,
        },
      }
    );

    await Promise.all([
      fetchApplications(),
      fetchApplicationStats(),
    ]);
  } catch (error) {
    console.error(
      "Failed to update application:",
      error
    );

    alert("Could not update application.");
  }
};

const updateResult = async (
  application,
  newResult
) => {
  await updateApplication(
    application.id,
    application.status,
    newResult,
    application.notes
  );
};

const updateNotes = async (
  application,
  newNotes
) => {
  await updateApplication(
    application.id,
    application.status,
    application.result,
    newNotes
  );
};

const removeApplication = async (applicationId) => {
  const confirmed = window.confirm(
    "Remove this application?"
  );

  if (!confirmed) {
    return;
  }

  try {
    await axios.delete(
      `${API_URL}/applications/${applicationId}`
    );

    await Promise.all([
      fetchApplications(),
      fetchApplicationStats(),
      fetchJobs(),
    ]);
  } catch (error) {
    console.error(
      "Failed to remove application:",
      error
    );

    alert("Could not remove application.");
  }
};


return (
  <div
    style={{
      maxWidth: "1100px",
      margin: "0 auto",
      padding: "30px",
      fontFamily: "Arial, sans-serif",
    }}
  >
    <h1
      style={{
        fontSize: "54px",
        textAlign: "center",
        marginBottom: "30px",
      }}
    >
      Job Radar
    </h1>

    {/* TABS */}
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        gap: "12px",
        marginBottom: "30px",
      }}
    >
      <button
        onClick={() => setActiveTab("jobs")}
        style={{
          padding: "12px 24px",
          fontWeight: "bold",
          cursor: "pointer",
          borderRadius: "8px",
          border:
            activeTab === "jobs"
              ? "2px solid #777"
              : "1px solid #555",
        }}
      >
        Jobs
      </button>

      <button
        onClick={() =>
          setActiveTab("applications")
        }
        style={{
          padding: "12px 24px",
          fontWeight: "bold",
          cursor: "pointer",
          borderRadius: "8px",
          border:
            activeTab === "applications"
              ? "2px solid #777"
              : "1px solid #555",
        }}
      >
        Applications
      </button>
    </div>

    {/* ============================= */}
    {/* JOBS TAB */}
    {/* ============================= */}

    {activeTab === "jobs" && (
      <>
        {/* SUMMARY CARDS */}

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "14px",
            marginBottom: "35px",
          }}
        >
          <div
            style={{
              border: "1px solid #444",
              borderRadius: "12px",
              padding: "20px",
              textAlign: "center",
            }}
          >
            <div>
              Available Jobs
            </div>

            <strong
              style={{
                fontSize: "30px",
                display: "block",
                marginTop: "8px",
              }}
            >
              {availableJobs}
            </strong>
          </div>

          <div
            style={{
              border: "1px solid #444",
              borderRadius: "12px",
              padding: "20px",
              textAlign: "center",
            }}
          >
            <div>
              Total Matches
            </div>

            <strong
              style={{
                fontSize: "30px",
                display: "block",
                marginTop: "8px",
              }}
            >
              {stats.matching_jobs}
            </strong>
          </div>

          <div
            style={{
              border: "1px solid #444",
              borderRadius: "12px",
              padding: "20px",
              textAlign: "center",
            }}
          >
            <div>
              Companies Monitored
            </div>

            <strong
              style={{
                fontSize: "30px",
                display: "block",
                marginTop: "8px",
              }}
            >
              {stats.companies_monitored}
            </strong>
          </div>

          <div
            style={{
              border: "1px solid #444",
              borderRadius: "12px",
              padding: "20px",
              textAlign: "center",
            }}
          >
            <div>
              Total Jobs Scanned
            </div>

            <strong
              style={{
                fontSize: "30px",
                display: "block",
                marginTop: "8px",
              }}
            >
              {stats.total_jobs}
            </strong>
          </div>

          <div
            style={{
              border: "1px solid #444",
              borderRadius: "12px",
              padding: "20px",
              textAlign: "center",
            }}
          >
            <div>
              Last Scan
            </div>

            <strong
              style={{
                display: "block",
                marginTop: "8px",
              }}
            >
              {stats.last_scan
                ? parseUtcDate(
                  stats.last_scan
                ).toLocaleString()
                : "Not scanned yet"}
            </strong>
          </div>
        </div>

        {/* FILTER RESULT COUNT */}

        <p
          style={{
            textAlign: "center",
            fontSize: "18px",
            marginBottom: "10px",
          }}
        >
          Showing{" "}
          <strong>
            {filteredJobs.length}
          </strong>{" "}
          of{" "}
          <strong>
            {stats.matching_jobs}
          </strong>{" "}
          matching jobs
        </p>

        {/* FILTERS */}

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "2fr 1.5fr 1fr auto",
            gap: "12px",
            marginBottom: "30px",
          }}
        >
          <input
            type="text"
            placeholder="Search role or company..."
            value={search}
            onChange={(e) =>
              setSearch(e.target.value)
            }
            style={{
              padding: "12px",
              borderRadius: "6px",
              border:
                "1px solid #666",
              fontSize: "16px",
            }}
          />

          <select
            value={roleFilter}
            onChange={(e) =>
              setRoleFilter(
                e.target.value
              )
            }
            style={{
              padding: "12px",
              borderRadius: "6px",
              fontSize: "16px",
            }}
          >
            <option value="all">
              All Roles
            </option>

            {roleOptions.map(
              (role) => (
                <option
                  key={role}
                  value={role}
                >
                  {formatRole(role)}
                </option>
              )
            )}
          </select>

          <select
            value={locationFilter}
            onChange={(e) =>
              setLocationFilter(
                e.target.value
              )
            }
            style={{
              padding: "12px",
              borderRadius: "6px",
              fontSize: "16px",
            }}
          >
            <option value="all">
              All Locations
            </option>

            <option value="bangalore">
              Bangalore
            </option>

            <option value="chennai">
              Chennai
            </option>

            <option value="remote">
              Remote India
            </option>
          </select>

          <div
            style={{
              display: "flex",
              gap: "8px",
            }}
          >
            <button
              onClick={refreshAll}
              disabled={refreshing}
              style={{
                padding:
                  "12px 18px",
                cursor: refreshing
                  ? "not-allowed"
                  : "pointer",
                borderRadius:
                  "6px",
                border:
                  "1px solid #666",
                fontSize:
                  "16px",
              }}
            >
              {refreshing
                ? "Refreshing..."
                : "Refresh"}
            </button>

            <button
              onClick={scanNow}
              disabled={scanning}
              style={{
                padding:
                  "12px 18px",
                cursor: scanning
                  ? "not-allowed"
                  : "pointer",
                borderRadius:
                  "6px",
                border:
                  "1px solid #666",
                fontSize:
                  "16px",
                fontWeight:
                  "bold",
              }}
            >
              {scanning
                ? "Scanning..."
                : "Scan Now"}
            </button>
          </div>
        </div>

        {/* LAST MANUAL SCAN */}

        {lastScanResult && (
          <div
            style={{
              border:
                "1px solid #444",
              borderRadius:
                "10px",
              padding: "14px",
              marginBottom:
                "22px",
            }}
          >
            <strong>
              Last Manual Scan
            </strong>

            <div
              style={{
                marginTop:
                  "8px",
                display:
                  "flex",
                gap: "20px",
                flexWrap:
                  "wrap",
              }}
            >
              <span>
                Companies:{" "}
                {
                  lastScanResult.companies_scanned
                }
              </span>

              <span>
                New Jobs:{" "}
                {
                  lastScanResult.new_jobs
                }
              </span>

              <span>
                New Matches:{" "}
                {
                  lastScanResult.new_matches
                }
              </span>

              <span>
                Time:{" "}
                {
                  lastScanResult.duration_seconds
                }
                s
              </span>
            </div>
          </div>
        )}

        {/* COMPANIES MONITORED */}

        <div
          style={{
            border:
              "1px solid #444",
            borderRadius:
              "12px",
            padding: "20px",
            marginBottom:
              "30px",
          }}
        >
          <h2
            style={{
              marginTop: 0,
            }}
          >
            Companies Monitored
          </h2>

          <div
            style={{
              overflowX:
                "auto",
            }}
          >
            <table
              style={{
                width: "100%",
                borderCollapse:
                  "collapse",
              }}
            >
              <thead>
                <tr>
                  <th
                    style={
                      tableHeaderStyle
                    }
                  >
                    Company
                  </th>

                  <th
                    style={
                      tableHeaderStyle
                    }
                  >
                    ATS
                  </th>

                  <th
                    style={
                      tableHeaderStyle
                    }
                  >
                    Status
                  </th>

                  <th
                    style={
                      tableHeaderStyle
                    }
                  >
                    Last Scan
                  </th>
                </tr>
              </thead>

              <tbody>
                {companies.map(
                  (company) => (
                    <tr
                      key={
                        company.id
                      }
                    >
                      <td
                        style={
                          tableCellStyle
                        }
                      >
                        {
                          company.name
                        }
                      </td>

                      <td
                        style={
                          tableCellStyle
                        }
                      >
                        {
                          company.ats_type
                        }
                      </td>

                      <td
                        style={
                          tableCellStyle
                        }
                      >
                        {company.enabled
                          ? "Active"
                          : "Disabled"}
                      </td>

                      <td
                        style={
                          tableCellStyle
                        }
                      >
                        {company.last_scanned_at
                          ? parseUtcDate(
                            company.last_scanned_at
                          ).toLocaleString()
                          : "Never"}
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* JOB LIST */}

        {filteredJobs.length === 0 ? (
          <div
            style={{
              textAlign:
                "center",
              padding:
                "50px",
              border:
                "1px solid #444",
              borderRadius:
                "12px",
            }}
          >
            <h3>
              No matching jobs found.
            </h3>

            <p>
              Try changing your search
              or filters.
            </p>
          </div>
        ) : (
          filteredJobs.map(
            (job) => (
              <div
                key={job.id}
                style={{
                  border:
                    "1px solid #777",
                  borderRadius:
                    "14px",
                  padding:
                    "24px",
                  marginBottom:
                    "18px",
                  boxShadow:
                    "0 2px 8px rgba(0,0,0,0.08)",
                }}
              >
                {/* TITLE */}

                <div
                  style={{
                    display:
                      "flex",
                    alignItems:
                      "center",
                    gap:
                      "12px",
                    flexWrap:
                      "wrap",
                    marginBottom:
                      "18px",
                  }}
                >
                  <h2
                    style={{
                      margin: 0,
                    }}
                  >
                    {job.title}
                  </h2>

                  {isNewJob(job) && (
                    <span
                      style={{
                        padding:
                          "5px 9px",
                        borderRadius:
                          "6px",
                        background:
                          "#e8f5e9",
                        color:
                          "#222",
                        fontSize:
                          "12px",
                        fontWeight:
                          "bold",
                      }}
                    >
                      NEW
                    </span>
                  )}
                </div>

                {/* DETAILS */}

                <div
                  style={{
                    lineHeight:
                      "1.6",
                    fontSize:
                      "17px",
                  }}
                >
                  <p>
                    <strong>
                      Company:
                    </strong>{" "}
                    {job.company}
                  </p>

                  <p>
                    <strong>
                      Location:
                    </strong>{" "}
                    {job.location}
                  </p>

                  <p>
                    <strong>
                      Experience:
                    </strong>{" "}
                    {formatExperience(
                      job
                    )}
                  </p>

                  <p>
                    <strong>
                      Role:
                    </strong>{" "}
                    {formatRole(
                      job.role_category
                    )}
                  </p>

                  <p>
                    <strong>
                      Source:
                    </strong>{" "}
                    {job.source}
                  </p>

                  <p>
                    <strong>
                      Detected:
                    </strong>{" "}
                    {job.first_seen_at
                      ? parseUtcDate(
                        job.first_seen_at
                      ).toLocaleString()
                      : "Unknown"}
                  </p>
                </div>

                {/* APPLY BUTTON */}

                <div
                  style={{
                    display: "flex",
                    gap: "10px",
                    flexWrap: "wrap",
                    marginTop: "10px",
                  }}
                >
                  <a
                    href={job.career_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      display: "inline-block",
                      padding: "10px 18px",
                      border: "1px solid #777",
                      borderRadius: "7px",
                      textDecoration: "none",
                      fontWeight: "bold",
                    }}
                  >
                    Apply Now
                  </a>

                  <button
                    onClick={() => markAsApplied(job.id)}
                    disabled={isApplied(job.id)}
                    style={{
                      padding: "10px 18px",
                      border: "1px solid #777",
                      borderRadius: "7px",
                      fontWeight: "bold",
                      cursor: isApplied(job.id)
                        ? "not-allowed"
                        : "pointer",
                      opacity: isApplied(job.id)
                        ? 0.6
                        : 1,
                    }}
                  >
                    {isApplied(job.id)
                      ? "Applied ✓"
                      : "Mark as Applied"}
                  </button>
                </div>
              </div>
            )
          )
        )}
      </>
    )}

    {/* ============================= */}
    {/* APPLICATIONS TAB */}
    {/* ============================= */}

    {activeTab ===
      "applications" && (
      <>
        <h2
          style={{
            textAlign: "center",
            marginBottom: "25px",
          }}
        >
          Applications Dashboard
        </h2>

        {/* APPLICATION STATS */}

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "12px",
            marginBottom:
              "30px",
          }}
        >
          <div
            style={{
              border:
                "1px solid #444",
              borderRadius:
                "10px",
              padding:
                "18px",
              textAlign:
                "center",
            }}
          >
            <strong>
              Total Applied
            </strong>

            <h2>
              {
                applicationStats.total_applications
              }
            </h2>
          </div>

          <div
            style={{
              border:
                "1px solid #444",
              borderRadius:
                "10px",
              padding:
                "18px",
              textAlign:
                "center",
            }}
          >
            <strong>
              Interviews
            </strong>

            <h2>
              {applicationStats.interview +
                applicationStats.final_interview}
            </h2>
          </div>

          <div
            style={{
              border:
                "1px solid #444",
              borderRadius:
                "10px",
              padding:
                "18px",
              textAlign:
                "center",
            }}
          >
            <strong>
              Offers
            </strong>

            <h2>
              {
                applicationStats.offer
              }
            </h2>
          </div>

          <div
            style={{
              border:
                "1px solid #444",
              borderRadius:
                "10px",
              padding:
                "18px",
              textAlign:
                "center",
            }}
          >
            <strong>
              Rejected
            </strong>

            <h2>
              {
                applicationStats.rejected
              }
            </h2>
          </div>

          <div
            style={{
              border:
                "1px solid #444",
              borderRadius:
                "10px",
              padding:
                "18px",
              textAlign:
                "center",
            }}
          >
            <strong>
              Interview Rate
            </strong>

            <h2>
              {
                applicationStats.interview_rate
              }
              %
            </h2>
          </div>

          <div
            style={{
              border:
                "1px solid #444",
              borderRadius:
                "10px",
              padding:
                "18px",
              textAlign:
                "center",
            }}
          >
            <strong>
              Offer Rate
            </strong>

            <h2>
              {
                applicationStats.offer_rate
              }
              %
            </h2>
          </div>
        </div>

        {/* APPLICATION TABLE */}

        <div
          style={{
            border:
              "1px solid #444",
            borderRadius:
              "12px",
            padding:
              "20px",
            overflowX:
              "auto",
          }}
        >
          {applications.length ===
          0 ? (
            <div
              style={{
                textAlign:
                  "center",
                padding:
                  "30px",
              }}
            >
              No applications tracked yet.
            </div>
          ) : (
            <table
              style={{
                width:
                  "100%",
                borderCollapse:
                  "collapse",
              }}
            >
              <thead>
                <tr>
                  <th style={tableHeaderStyle}>Company</th>
                  <th style={tableHeaderStyle}>Role</th>
                  <th style={tableHeaderStyle}>Applied</th>
                  <th style={tableHeaderStyle}>Stage</th>
                  <th style={tableHeaderStyle}>Result</th>
                  <th style={tableHeaderStyle}>Notes</th>
                  <th style={tableHeaderStyle}>Actions</th>
                </tr>
              </thead>

              <tbody>
                {applications.map(
                  (
                    application
                  ) => (
                    <tr
                      key={
                        application.id
                      }
                    >
                      <td
                        style={
                          tableCellStyle
                        }
                      >
                        {
                          application.company
                        }
                      </td>

                      <td
                        style={
                          tableCellStyle
                        }
                      >
                        {
                          application.title
                        }
                      </td>

                      <td
                        style={
                          tableCellStyle
                        }
                      >
                        {application.applied_at
                          ?parseUtcDate(
                            application.applied_at
                          ).toLocaleDateString()
                          : "-"}
                      </td>

                      <td style={tableCellStyle}>
                        <select
                          value={application.status}
                          onChange={(e) =>
                            updateApplication(
                              application.id,
                              e.target.value,
                              application.result,
                              application.notes
                            )
                          }
                          style={{
                            padding: "8px",
                            borderRadius: "6px",
                          }}
                        >
                          <option value="applied">
                            Applied
                          </option>

                          <option value="assessment">
                            Assessment
                          </option>

                          <option value="interview">
                            Interview
                          </option>

                          <option value="final_interview">
                            Final Interview
                          </option>

                          <option value="offer">
                            Offer
                          </option>

                          <option value="rejected">
                            Rejected
                          </option>

                          <option value="withdrawn">
                            Withdrawn
                          </option>

                          <option value="no_response">
                            No Response
                          </option>
                        </select>
                      </td>

                      <td style={tableCellStyle}>
                        <input
                          type="text"
                          defaultValue={application.result || ""}
                          placeholder="Result"
                          onBlur={(e) =>
                            updateResult(
                              application,
                              e.target.value
                            )
                          }
                          style={{
                            padding: "8px",
                            borderRadius: "6px",
                            border: "1px solid #666",
                            width: "180px",
                          }}
                        />
                      </td>

                      <td style={tableCellStyle}>
                        <input
                          type="text"
                          defaultValue={application.notes || ""}
                          placeholder="Notes"
                          onBlur={(e) =>
                            updateNotes(
                              application,
                              e.target.value
                            )
                          }
                          style={{
                            padding: "8px",
                            borderRadius: "6px",
                            border: "1px solid #666",
                            width: "220px",
                          }}
                        />
                      </td>
                      <td style={tableCellStyle}>
                        <div
                          style={{
                            display: "flex",
                            gap: "8px",
                            flexWrap: "wrap",
                          }}
                        >
                          <a
                            href={application.career_url}
                            target="_blank"
                            rel="noreferrer"
                            style={{
                              padding: "8px 12px",
                              border: "1px solid #666",
                              borderRadius: "6px",
                              textDecoration: "none",
                            }}
                          >
                            View Job
                          </a>

                          <button
                            onClick={() =>
                              removeApplication(application.id)
                            }
                            style={{
                              padding: "8px 12px",
                              border: "1px solid #666",
                              borderRadius: "6px",
                              cursor: "pointer",
                            }}
                          >
                            Remove
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          )}
        </div>
      </>
    )}
  </div>
);
}

export default App;