import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import client from "../../api/client";
import GapAnalysisList from "../../components/GapAnalysisList";
import ScoreBar from "../../components/ScoreBar";

const SCORE_LABELS = {
  technical: "Technical fit",
  keyword: "Keyword match",
  experience: "Experience fit",
  ats_readiness: "ATS readiness",
};

export default function ResumeJdTailor() {
  const { id } = useParams();
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    client.get(`/resumes/${id}`).then((res) => {
      if (res.data.tailoring_job_description) setJobDescription(res.data.tailoring_job_description);
      if (res.data.tailoring_match_scores) {
        setResult({
          match_scores: res.data.tailoring_match_scores,
          gap_analysis: res.data.tailoring_gap_analysis || [],
          suggested_bullet_rewrites: [],
        });
      }
    }).catch(() => {});
  }, [id]);

  async function analyze() {
    setError("");
    setLoading(true);
    try {
      const res = await client.post(`/resumes/${id}/analyze-job-description`, { job_description: jobDescription });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Job description analysis is temporarily unavailable. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="card">
        <h1>Tailor to a Job Description</h1>
        <p className="muted">Paste a job posting to see how well your resume matches, and where the gaps are.</p>
        <div className="field-group">
          <label>Job description</label>
          <textarea rows={8} value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} />
        </div>
        {error && <p className="error-text">{error}</p>}
        <div className="form-actions">
          <Link className="btn-link" to={`/resumes/${id}/edit`}>Back to editor</Link>
          <button className="btn btn-primary" disabled={loading || !jobDescription.trim()} onClick={analyze}>
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </div>

      {result && (
        <>
          <div className="card">
            <h2>Match Scores</h2>
            {Object.entries(result.match_scores || {}).map(([key, score]) => (
              <ScoreBar key={key} label={SCORE_LABELS[key] || key} score={score} />
            ))}
          </div>

          <div className="card">
            <h2>Gap Analysis</h2>
            <GapAnalysisList gaps={result.gap_analysis} />
          </div>

          {result.suggested_bullet_rewrites?.length > 0 && (
            <div className="card">
              <h2>Suggested Bullet Rewrites</h2>
              <p className="muted small">
                These are suggestions only — go to the editor to apply any you like.
              </p>
              <ul>
                {result.suggested_bullet_rewrites.map((s, idx) => (
                  <li key={idx}>{s.suggested_text}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
