import { useEffect, useState } from "react";
import axios from "axios";
import { Link, useParams } from "react-router-dom";

const API_BASE_URL = "http://127.0.0.1:8000";

function InternshipDetailsPage() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [file, setFile] = useState(null);
  const [atsResult, setAtsResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchJob = async () => {
      try {
        setLoading(true);
        setError("");
        const response = await axios.get(`${API_BASE_URL}/internships/${id}`);
        setJob(response.data);
      } catch (err) {
        console.error(err);
        setError("Failed to load internship details.");
      } finally {
        setLoading(false);
      }
    };

    fetchJob();
  }, [id]);

  const handleAnalyze = async (e) => {
    e.preventDefault();

    if (!file) {
      setError("Please upload your CV first.");
      return;
    }

    try {
      setAnalyzing(true);
      setError("");
      setAtsResult(null);

      const formData = new FormData();
      formData.append("internship_id", id);
      formData.append("file", file);

      const response = await axios.post(`${API_BASE_URL}/ats/analyze`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setAtsResult(response.data);
    } catch (err) {
      console.error(err);
      setError(
        err?.response?.data?.detail || "Failed to analyze CV against this job."
      );
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <h2>Loading internship details...</h2>
      </div>
    );
  }

  if (error && !job) {
    return (
      <div className="page">
        <div className="error-box">{error}</div>
        <Link to="/">← Back to internships</Link>
      </div>
    );
  }

  return (
    <div className="page">
      <Link className="back-link" to="/">← Back to internships</Link>

      {job && (
        <>
          <section className="card details-card">
            <h1>{job.title}</h1>
            <p><strong>Company:</strong> {job.company_name}</p>
            <p><strong>Location:</strong> {job.location || "Not specified"}</p>
            <p><strong>Source:</strong> {job.source}</p>
            <p><strong>Skills:</strong> {job.skills_required?.join(", ") || "Not extracted yet"}</p>
            <p><strong>Apply:</strong> <a href={job.apply_url} target="_blank" rel="noreferrer">Open real job link</a></p>

            <div className="job-description">
              <h2>Job Description</h2>
              <p>{job.description || "No description available."}</p>
            </div>
          </section>

          <section className="card upload-card">
            <h2>Check your CV for this role</h2>
            <form onSubmit={handleAnalyze}>
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />

              <button className="primary-btn" type="submit" disabled={analyzing}>
                {analyzing ? "Analyzing..." : "Analyze CV"}
              </button>
            </form>

            {error && <div className="error-box mt-16">{error}</div>}
          </section>

          {atsResult && (
            <section className="card ats-card">
              <h2>ATS Analysis Result</h2>

              <div className="score-pill">
                ATS Score: {atsResult.ats_score}%
              </div>

              <div className="ats-grid">
                <div>
                  <h3>Matched Keywords</h3>
                  {atsResult.matched_keywords?.length ? (
                    <ul>
                      {atsResult.matched_keywords.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No strong matches found yet.</p>
                  )}
                </div>

                <div>
                  <h3>Missing Keywords</h3>
                  {atsResult.missing_keywords?.length ? (
                    <ul>
                      {atsResult.missing_keywords.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No major keyword gaps detected.</p>
                  )}
                </div>
              </div>

              <div className="suggestions-box">
                <h3>What to change in your CV</h3>
                <ul>
                  {atsResult.suggestions.map((suggestion, index) => (
                    <li key={index}>{suggestion}</li>
                  ))}
                </ul>
              </div>

              <div className="preview-box">
                <h3>Extracted Resume Preview</h3>
                <p>{atsResult.extracted_preview}</p>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

export default InternshipDetailsPage;