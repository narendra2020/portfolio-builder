import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import client from "../../api/client";
import ScoreBar from "../../components/ScoreBar";

const CATEGORY_LABELS = {
  formatting_compatibility: "Formatting compatibility",
  keyword_relevance: "Keyword relevance",
  section_completeness: "Section completeness",
  quantifiable_impact: "Quantifiable impact",
  action_verb_usage: "Action verb usage",
  length_and_density: "Length & density",
  contact_and_links: "Contact & links",
};

export default function ResumeAtsAnalysis() {
  const { id } = useParams();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    client.get(`/resumes/${id}`).then((res) => {
      if (res.data.ats_analysis) {
        setResult({ categories: res.data.ats_analysis, overall_score: res.data.ats_score });
      }
    }).catch(() => {});
  }, [id]);

  async function analyze() {
    setError("");
    setLoading(true);
    try {
      const res = await client.post(`/resumes/${id}/analyze-ats`);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "ATS analysis is temporarily unavailable. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="card">
        <h1>ATS Score</h1>
        <p className="muted">See how well your resume would survive an Applicant Tracking System scan.</p>
        {error && <p className="error-text">{error}</p>}
        <div className="form-actions">
          <Link className="btn-link" to={`/resumes/${id}/edit`}>Back to editor</Link>
          <button className="btn btn-primary" disabled={loading} onClick={analyze}>
            {loading ? "Analyzing..." : result ? "Re-analyze" : "Analyze"}
          </button>
        </div>
      </div>

      {result && (
        <div className="card">
          <h2>Overall Score: {result.overall_score}</h2>
          {Object.entries(result.categories || {}).map(([key, cat]) => (
            <ScoreBar key={key} label={CATEGORY_LABELS[key] || key} score={cat.score} note={cat.note} />
          ))}
        </div>
      )}
    </div>
  );
}
