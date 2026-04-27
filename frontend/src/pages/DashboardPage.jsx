import { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";

const API_BASE_URL = "http://127.0.0.1:8000";

function DashboardPage() {
  const [internships, setInternships] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const fetchInternships = async () => {
    try {
      setLoading(true);
      setError("");
      const response = await axios.get(`${API_BASE_URL}/internships`);
      setInternships(response.data);
    } catch (err) {
      console.error(err);
      setError("Failed to load internships.");
    } finally {
      setLoading(false);
    }
  };

  const refreshJobs = async () => {
    try {
      setRefreshing(true);
      setError("");
      await axios.post(`${API_BASE_URL}/refresh-jobs`);
      await fetchInternships();
    } catch (err) {
      console.error(err);
      setError("Failed to refresh live jobs.");
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchInternships();
  }, []);

  const filteredInternships = internships.filter((job) => {
    const combined = `${job.title} ${job.company_name} ${job.location} ${job.description}`.toLowerCase();
    return combined.includes(search.toLowerCase());
  });

  if (loading) {
    return (
      <div className="page">
        <h2>Loading live internships...</h2>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="hero">
        <div>
          <h1>InternPilot</h1>
          <p>Live internships from your target companies</p>
        </div>

        <div className="hero-actions">
          <input
            className="search-input"
            type="text"
            placeholder="Search by title, company, location..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button className="primary-btn" onClick={refreshJobs} disabled={refreshing}>
            {refreshing ? "Refreshing..." : "Refresh Jobs"}
          </button>
        </div>
      </header>

      {error && <div className="error-box">{error}</div>}

      <section className="stats-grid">
        <div className="card stat-card">
          <h2>{internships.length}</h2>
          <p>Live Internships</p>
        </div>
        <div className="card stat-card">
          <h2>{filteredInternships.length}</h2>
          <p>Visible Results</p>
        </div>
      </section>

      <section className="section">
        <h2>Internship Feed</h2>
        {filteredInternships.length === 0 ? (
          <div className="card">
            <p>No internships found yet. Try refreshing jobs.</p>
          </div>
        ) : (
          <div className="grid">
            {filteredInternships.map((job) => (
              <div className="card" key={job.id}>
                <h3>{job.title}</h3>
                <p><strong>Company:</strong> {job.company_name}</p>
                <p><strong>Location:</strong> {job.location || "Not specified"}</p>
                <p><strong>Source:</strong> {job.source}</p>
                <p><strong>Skills:</strong> {job.skills_required?.join(", ") || "Not extracted yet"}</p>
                <p className="description-preview">
                  {job.description
                    ? `${job.description.slice(0, 180)}${job.description.length > 180 ? "..." : ""}`
                    : "No description available."}
                </p>

                <div className="card-actions">
                  <Link className="secondary-link" to={`/internships/${job.id}`}>
                    View Details
                  </Link>
                  <a href={job.apply_url} target="_blank" rel="noreferrer">
                    Apply Link
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default DashboardPage;