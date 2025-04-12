import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  // Fetch metrics from the backend with optional date range
  const fetchMetrics = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await axios.get("http://localhost:5001/metrics", {
        params: { from: fromDate, to: toDate },
      });
      setMetrics(response.data);
    } catch (err) {
      setError("Failed to fetch metrics. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Refresh metrics by triggering the backend script
  const refreshMetrics = async () => {
    setLoading(true);
    setError("");
    try {
      // Pass the date range to the refresh endpoint
      await axios.post("http://localhost:5001/refresh", null, {
        params: { from: fromDate, to: toDate },
      });
      await fetchMetrics(); // Fetch updated metrics after refresh
    } catch (err) {
      setError("Failed to refresh metrics. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    //fetchMetrics();
  }, []);

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>GitHub Metrics</h1>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <div style={{ marginBottom: "20px" }}>
        <label>
          From:{" "}
          <input
            type="date"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
          />
        </label>
        <label style={{ marginLeft: "10px" }}>
          To:{" "}
          <input
            type="date"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
          />
        </label>
        <button
          onClick={fetchMetrics}
          disabled={loading}
          style={{ marginLeft: "10px" }}
        >
          Apply Date Range
        </button>
      </div>

      {/* Conditionally render the Refresh Metrics button */}
      {/* {fromDate && toDate && (
        <button
          onClick={refreshMetrics}
          disabled={loading}
          style={{ marginBottom: "20px" }}
        >
          Refresh Metrics
        </button>
      )} */}

      {/* Conditionally render the table or a friendly message */}
      {metrics.length > 0 ? (
        <table
          border="1"
          cellPadding="10"
          style={{ width: "100%", borderCollapse: "collapse" }}
        >
          <thead>
            <tr>
              <th>User</th>
              <th>Total Coding Days</th>
              <th>Total Commits</th>
              <th>Files Changed</th>
              <th>Lines Added</th>
              <th>Lines Removed</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((metric, index) => (
              <tr key={index}>
                <td>{metric.User}</td>
                <td>{metric["Total Coding Days"]}</td>
                <td>{metric["Total Commits"]}</td>
                <td>{metric["Files Changed"]}</td>
                <td>{metric["Lines Added"]}</td>
                <td>{metric["Lines Removed"]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        !loading && !error && (
          <p style={{ textAlign: "center", marginTop: "20px" }}>
            No records found. Please select a date range and try again.
          </p>
        )
      )}
    </div>
  );
}

export default App;