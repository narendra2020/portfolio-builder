import React, { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import client from "../api/client";

const SLUG_RE = /^[a-z0-9-]{3,63}$/;

export default function Publish() {
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [slugInput, setSlugInput] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [availability, setAvailability] = useState(null);
  const [checking, setChecking] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    client
      .get("/publish")
      .then((res) => {
        setStatus(res.data);
        setSlugInput(res.data.slug || "");
      })
      .catch((err) => setError(err.response?.data?.detail || "Could not load publish status."));
  }, []);

  const slugLocked = Boolean(status?.slug);

  useEffect(() => {
    if (slugLocked) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!slugInput) {
      setAvailability(null);
      setChecking(false);
      return;
    }
    if (!SLUG_RE.test(slugInput)) {
      setAvailability({ available: false, reason: "format" });
      setChecking(false);
      return;
    }
    setChecking(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await client.get("/publish/slug-availability", { params: { slug: slugInput } });
        setAvailability(res.data);
      } catch {
        setAvailability(null);
      } finally {
        setChecking(false);
      }
    }, 400);
    return () => clearTimeout(debounceRef.current);
  }, [slugInput, slugLocked]);

  async function choosePublish() {
    setError("");
    setSaving(true);
    try {
      const slugRes = await client.put("/publish/slug", { slug: slugInput });
      const publishRes = await client.post("/publish", {});
      setStatus(publishRes.data);
    } catch (err) {
      if (err.response?.status === 402) {
        setError(err.response?.data?.detail || "Your free trial has ended.");
      } else {
        setError(err.response?.data?.detail || "Could not choose subdomain and publish.");
      }
      client.get("/publish").then((res) => setStatus(res.data));
    } finally {
      setSaving(false);
    }
  }

  async function doPublish() {
    setError("");
    setSaving(true);
    try {
      const res = await client.post("/publish", {});
      setStatus(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not publish.");
    } finally {
      setSaving(false);
    }
  }

  async function doUnpublish() {
    setError("");
    setSaving(true);
    try {
      const res = await client.post("/publish/unpublish", {});
      setStatus(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not unpublish.");
    } finally {
      setSaving(false);
    }
  }

  if (!status) {
    return (
      <div className="card">
        <p className="muted">Loading publish status...</p>
      </div>
    );
  }

  const isPublished = status.status === "published";
  const baseDomain = status.base_domain;
  const trialExpired = error && error.toLowerCase().includes("trial");

  let availabilityText = null;
  if (checking) {
    availabilityText = <span className="muted small">Checking...</span>;
  } else if (availability) {
    if (availability.available) {
      availabilityText = <span className="success-text small">✓ Available</span>;
    } else if (availability.reason === "taken") {
      availabilityText = <span className="error-text small">✗ Already taken</span>;
    } else if (availability.reason === "format") {
      availabilityText = (
        <span className="error-text small">✗ 3-63 characters: lowercase letters, digits, hyphens only</span>
      );
    }
  }

  return (
    <div className="card">
      <h1>Publish your portfolio</h1>
      <p className="muted">Choose a subdomain, then publish your portfolio for anyone to view.</p>
      {error && (
        <p className="error-text">
          {error}
          {trialExpired && (
            <>
              {" "}
              <Link to="/billing">Upgrade now</Link>
            </>
          )}
        </p>
      )}

      <div className="field-group">
        <label htmlFor="subdomain">Subdomain</label>
        {slugLocked ? (
          <p className="subdomain-input-row">
            <strong>
              {status.slug}.{baseDomain}
            </strong>
          </p>
        ) : (
          <>
            <div className="subdomain-input-row">
              <input
                id="subdomain"
                type="text"
                value={slugInput}
                placeholder="e.g. narendr"
                onChange={(e) => setSlugInput(e.target.value.toLowerCase())}
              />
              <span className="subdomain-suffix">.{baseDomain}</span>
            </div>
            {availabilityText}
            <p className="muted small">
              Your portfolio will be live at{" "}
              <strong>
                {slugInput || "..."}.{baseDomain}
              </strong>
              . You can only choose this once, so pick carefully.
            </p>
          </>
        )}
      </div>

      {isPublished && status.url && (
        <p className="success-text">
          Live at{" "}
          <a href={status.url} target="_blank" rel="noreferrer">
            {status.url}
          </a>
        </p>
      )}

      <div className="form-actions">
        <button className="btn-link" onClick={() => navigate("/dashboard")}>
          Back to dashboard
        </button>
        {isPublished ? (
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
            <button
              className="btn btn-primary"
              disabled={saving || !status.can_republish}
              onClick={doPublish}
            >
              {status.can_republish ? "Re-publish" : "Up to date"}
            </button>
            <button className="btn-link" disabled={saving} onClick={doUnpublish}>
              Unpublish
            </button>
          </div>
        ) : slugLocked ? (
          <button className="btn btn-primary" disabled={saving || !status.can_republish} onClick={doPublish}>
            {status.can_republish ? "Publish" : "Up to date"}
          </button>
        ) : (
          <button
            className="btn btn-primary"
            disabled={saving || !slugInput || !availability?.available}
            onClick={choosePublish}
          >
            Choose & Publish
          </button>
        )}
      </div>
    </div>
  );
}
