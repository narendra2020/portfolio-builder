import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../../api/client";

export default function ResumeLanding() {
  const navigate = useNavigate();
  const [resumes, setResumes] = useState(null);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    client
      .get("/resumes")
      .then((res) => setResumes(res.data))
      .catch((err) => setError(err.response?.data?.detail || "Could not load your resumes."));
  }, []);

  async function createResume(source) {
    setError("");
    setCreating(true);
    try {
      const res = await client.post("/resumes", {
        title: source === "mepage_import" ? "My Resume" : "Untitled Resume",
        source,
        template_key: "ats_professional",
      });
      navigate(`/resumes/${res.data.id}/edit`);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create a new resume.");
      setCreating(false);
    }
  }

  async function handleUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError("");
    setCreating(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await client.post("/resumes/import", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      navigate(`/resumes/${res.data.id}/edit`);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not import this file.");
      setCreating(false);
    } finally {
      e.target.value = "";
    }
  }

  if (error && !resumes) {
    return (
      <div className="card">
        <p className="error-text">{error}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <h1>Resume Builder</h1>
        <p className="muted">Create, tailor, and export an ATS-friendly resume with AI assistance.</p>
        {error && <p className="error-text">{error}</p>}
        <div className="menu-grid">
          <button className="menu-item menu-item-primary" disabled={creating} onClick={() => createResume("mepage_import")}>
            <span className="menu-item-icon">📥</span>
            <strong>Start from my MePage profile</strong>
            <span className="muted small">Pre-fill using your existing profile</span>
          </button>
          <label className="menu-item" style={{ cursor: creating ? "default" : "pointer" }}>
            <span className="menu-item-icon">📄</span>
            <strong>Upload a resume</strong>
            <span className="muted small">PDF or DOCX</span>
            <input
              type="file"
              accept=".pdf,.docx"
              style={{ display: "none" }}
              disabled={creating}
              onChange={handleUpload}
            />
          </label>
          <button className="menu-item" disabled={creating} onClick={() => createResume("scratch")}>
            <span className="menu-item-icon">✎</span>
            <strong>Start from scratch</strong>
            <span className="muted small">Build it up section by section</span>
          </button>
        </div>
      </div>

      <div className="card">
        <h2>My Resumes</h2>
        {resumes === null && <p className="muted">Loading...</p>}
        {resumes && resumes.length === 0 && <p className="muted">You haven't created a resume yet.</p>}
        {resumes && resumes.length > 0 && (
          <div className="resume-list">
            {resumes.map((r) => (
              <div key={r.id} className="resume-list-item" onClick={() => navigate(`/resumes/${r.id}/edit`)}>
                <div className="resume-list-item-main">
                  <strong>{r.title}</strong>
                  <span className="muted small">
                    {r.target_role ? r.target_role : "No target role set"} · Updated{" "}
                    {new Date(r.updated_at).toLocaleDateString()}
                  </span>
                </div>
                {typeof r.ats_score === "number" && (
                  <span className="resume-list-item-score">ATS {r.ats_score}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
