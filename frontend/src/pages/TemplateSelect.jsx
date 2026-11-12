import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";
import UniversalTemplateThumbnail from "../components/UniversalTemplateThumbnail";
import StepProgress from "../components/StepProgress";

export default function TemplateSelect() {
  const { refreshOnboarding } = useAuth();
  const navigate = useNavigate();
  const [templates, setTemplates] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [onboardingStatus, setOnboardingStatus] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([client.get("/templates"), client.get("/profile")])
      .then(([templatesRes, profileRes]) => {
        const list = templatesRes.data || [];
        setTemplates(list);
        setOnboardingStatus(profileRes.data.onboarding_status);
        const current = list.find((t) => t.id === profileRes.data.template_id);
        setSelectedId((current || list[0])?.id ?? null);
      })
      .catch((err) => {
        setError(err.response?.data?.detail || "Could not load templates.");
      })
      .finally(() => setLoading(false));
  }, []);

  const isOnboardingStep = onboardingStatus === "template_pending";
  const selectedTemplate = templates.find((t) => t.id === selectedId) || null;

  async function confirm() {
    if (!selectedId) return;
    setError("");
    setSaving(true);
    try {
      await client.put("/profile/template", { template_id: selectedId });
      await refreshOnboarding();
      navigate(isOnboardingStep ? "/questionnaire" : "/publish");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not confirm your template.");
    } finally {
      setSaving(false);
    }
  }

  if (error && templates.length === 0) {
    return (
      <div className="card">
        <p className="error-text">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="card">
        <p className="muted">Loading templates...</p>
      </div>
    );
  }

  return (
    <div>
      {isOnboardingStep && (
        <StepProgress current={4} total={4} labels={["Resume", "Audience", "Profile", "Template"]} />
      )}
      <div className="card template-confirm-card">
        <h1>{isOnboardingStep ? "Choose your portfolio template" : "Template"}</h1>
        <p className="muted">
          {isOnboardingStep
            ? "Pick the layout your published portfolio will use. You can fine-tune sections later."
            : "This is the layout your published portfolio uses."}
        </p>
        {error && <p className="error-text">{error}</p>}

        <div className="template-picker-grid">
          {templates.map((template) => (
            <button
              type="button"
              key={template.id}
              className={`template-picker-card ${
                selectedId === template.id ? "template-picker-card-active" : ""
              }`}
              onClick={() => setSelectedId(template.id)}
            >
              {template.preview_image ? (
                <img className="template-picker-thumb-img" src={template.preview_image} alt={template.name} />
              ) : (
                <UniversalTemplateThumbnail />
              )}
              <div className="template-picker-body">
                <div className="template-picker-name">{template.name}</div>
                {template.description && (
                  <div className="template-picker-description">{template.description}</div>
                )}
              </div>
            </button>
          ))}
        </div>

        {selectedTemplate && (
          <>
            <div className="template-name">{selectedTemplate.name}</div>
            {selectedTemplate.description && (
              <div className="template-description">{selectedTemplate.description}</div>
            )}
          </>
        )}

        <div className="form-actions" style={{ justifyContent: isOnboardingStep ? "flex-end" : "space-between" }}>
          {!isOnboardingStep && (
            <button className="btn-link" onClick={() => navigate("/dashboard")}>
              Cancel
            </button>
          )}
          <button className="btn btn-primary" disabled={saving || !selectedId} onClick={confirm}>
            {saving ? "Saving..." : "Continue"}
          </button>
        </div>
      </div>
    </div>
  );
}
