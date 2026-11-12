import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import StepProgress from "../../components/StepProgress";

export default function Audience() {
  const { refreshOnboarding } = useAuth();
  const navigate = useNavigate();
  const [audienceTypes, setAudienceTypes] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([client.get("/taxonomy/audience-types"), client.get("/profile")])
      .then(([audienceRes, profileRes]) => {
        const types = audienceRes.data;
        setAudienceTypes(types);
        const suggestedSlug = profileRes.data.resume_suggestions?.profile?.audience_slug;
        const suggested = types.find((t) => t.slug === suggestedSlug);
        const fallback = types.find((t) => t.slug === "professional");
        setSelectedId((suggested || fallback || types[0])?.id ?? null);
      })
      .catch((err) => {
        setError(err.response?.data?.detail || "Could not load audience types.");
      })
      .finally(() => setLoading(false));
  }, []);

  async function handleContinue() {
    if (!selectedId) return;
    setError("");
    setSaving(true);
    try {
      await client.put("/profile/audience", { audience_type_id: selectedId });
      await refreshOnboarding();
      navigate("/onboarding/profile");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save your selection.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page-container">
      <StepProgress current={2} total={4} labels={["Resume", "Audience", "Profile", "Template"]} />
      <div className="card" style={{ maxWidth: 640, margin: "0 auto" }}>
        <h1>Which best describes you?</h1>
        <p className="muted">This helps us tailor your portfolio questions.</p>

        {loading && <p className="muted">Loading options...</p>}
        {error && <p className="error-text">{error}</p>}

        {!loading && audienceTypes.length > 0 && (
          <div className="audience-grid">
            {audienceTypes.map((type) => (
              <button
                type="button"
                key={type.id}
                className={`audience-card ${selectedId === type.id ? "audience-card-active" : ""}`}
                onClick={() => setSelectedId(type.id)}
              >
                {type.name}
              </button>
            ))}
          </div>
        )}

        <div className="form-actions" style={{ justifyContent: "flex-end" }}>
          <button
            type="button"
            className="btn btn-primary"
            disabled={saving || !selectedId}
            onClick={handleContinue}
          >
            {saving ? "Saving..." : "Continue"}
          </button>
        </div>
      </div>
    </div>
  );
}
