import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import StepProgress from "../../components/StepProgress";

const AI_STEPS = [
  "Extracting text from your file",
  "Identifying skills & experience",
  "Pre-filling your portfolio",
];
const AI_STEP_INTERVAL_MS = 1800;

export default function Resume() {
  const { refreshOnboarding } = useAuth();
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const stepTimer = useRef(null);

  useEffect(() => {
    if (!loading) {
      clearInterval(stepTimer.current);
      setActiveStep(0);
      return;
    }
    stepTimer.current = setInterval(() => {
      setActiveStep((s) => Math.min(s + 1, AI_STEPS.length - 1));
    }, AI_STEP_INTERVAL_MS);
    return () => clearInterval(stepTimer.current);
  }, [loading]);

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) return;
    setError("");
    setLoading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await client.post("/profile/resume", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      await refreshOnboarding();
      navigate(res.data.next_step);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not process your resume.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSkip() {
    setError("");
    setLoading(true);
    try {
      await client.post("/profile/resume/skip");
      await refreshOnboarding();
      navigate("/onboarding/audience");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not skip this step.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-container">
      <StepProgress current={1} total={4} labels={["Resume", "Audience", "Profile", "Template"]} />
      <div className="card" style={{ maxWidth: 480, margin: "0 auto" }}>
        <h1>Upload your resume</h1>
        <p className="muted">
          Optional — we'll read it and pre-fill your portfolio details so you have less
          typing to do. You can review and edit everything before it's saved.
        </p>

        <button
          type="button"
          className="btn btn-secondary btn-block"
          disabled={loading}
          onClick={() => navigate("/resumes")}
        >
          Create with AI Resume Builder
        </button>
        <p className="muted small" style={{ textAlign: "center", margin: "0.75rem 0" }}>
          — or —
        </p>

        <form onSubmit={handleUpload}>
          <label>Resume (PDF or DOCX)</label>
          <input
            type="file"
            accept=".pdf,.docx"
            disabled={loading}
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />

          {error && <p className="error-text">{error}</p>}

          {!loading && (
            <button type="submit" className="btn btn-primary btn-block" disabled={!file}>
              Upload & continue
            </button>
          )}
        </form>

        {loading && (
          <div className="ai-thinking">
            <div className="ai-orb" />
            <div className="ai-thinking-status">Reading {file?.name}…</div>
            <div className="ai-thinking-steps">
              {AI_STEPS.map((label, i) => (
                <div
                  key={label}
                  className={`ai-thinking-step ${i < activeStep ? "ai-thinking-step-done" : ""} ${
                    i === activeStep ? "ai-thinking-step-active" : ""
                  }`}
                >
                  <span className="dot" />
                  {label}
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="form-actions" style={{ justifyContent: "center" }}>
          <button type="button" className="btn-link" onClick={handleSkip} disabled={loading}>
            Skip for now
          </button>
        </div>
      </div>
    </div>
  );
}
