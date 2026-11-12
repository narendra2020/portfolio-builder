import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { user } = useAuth();
  const [templateName, setTemplateName] = useState(null);
  const [publishStatus, setPublishStatus] = useState(null);
  const [billingStatus, setBillingStatus] = useState(null);

  useEffect(() => {
    Promise.all([client.get("/profile"), client.get("/templates"), client.get("/publish"), client.get("/billing/status")])
      .then(([profileRes, templatesRes, publishRes, billingRes]) => {
        const tpl = templatesRes.data.find((t) => t.id === profileRes.data.template_id);
        setTemplateName(tpl ? tpl.name : null);
        setPublishStatus(publishRes.data);
        setBillingStatus(billingRes.data);
      })
      .catch(() => {});
  }, []);

  const showUpgradeBanner =
    billingStatus &&
    (billingStatus.subscription_status === "expired" ||
      (billingStatus.subscription_status === "trial" && billingStatus.days_remaining <= 7));

  return (
    <div className="card">
      <h1>Welcome</h1>
      <p className="muted">
        Your account (role: <strong>{user?.role}</strong>) is onboarded. Tell us about yourself so we can
        start building your portfolio.
      </p>
      {showUpgradeBanner && (
        <p className={billingStatus.subscription_status === "expired" ? "error-text" : "muted"}>
          {billingStatus.subscription_status === "expired"
            ? "Your free trial has ended and your site is unpublished."
            : `Your free trial ends in ${billingStatus.days_remaining} day(s).`}{" "}
          <Link to="/billing">Upgrade now</Link>
        </p>
      )}
      <div className="menu-grid">
        <Link to="/questionnaire" className="menu-item menu-item-primary">
          <span className="menu-item-icon">✎</span>
          <strong>Fill out your questionnaire</strong>
          <span className="muted small">Tell us about your work</span>
        </Link>
        <Link to="/template" className="menu-item">
          <span className="menu-item-icon">🎨</span>
          <strong>{templateName ? `Template: ${templateName}` : "Choose a template"}</strong>
          <span className="muted small">Pick your layout &amp; style</span>
        </Link>
        <Link to="/publish" className="menu-item">
          <span className="menu-item-icon">🚀</span>
          <strong>{publishStatus?.status === "published" ? "Manage publishing" : "Publish your portfolio"}</strong>
          <span className="muted small">
            {publishStatus?.status === "published" ? "Live and shareable" : "Not published yet"}
          </span>
        </Link>
        <Link to="/billing" className="menu-item">
          <span className="menu-item-icon">💳</span>
          <strong>Billing</strong>
          <span className="muted small">Manage your plan</span>
        </Link>
        <Link to="/resumes" className="menu-item">
          <span className="menu-item-icon">📄</span>
          <strong>Resume Builder</strong>
          <span className="muted small">Create a new resume or improve an existing one</span>
        </Link>
        <Link to="/ai-assistant" className="menu-item">
          <span className="menu-item-icon">✦</span>
          <strong>AI Assistant</strong>
          <span className="muted small">Chat widget for visitors</span>
        </Link>
        {user?.role === "super_admin" && (
          <>
            <Link to="/admin/users" className="menu-item">
              <span className="menu-item-icon">👥</span>
              <strong>Manage users</strong>
              <span className="muted small">Admin tools</span>
            </Link>
            <Link to="/admin/billing" className="menu-item">
              <span className="menu-item-icon">🧾</span>
              <strong>Billing admin</strong>
              <span className="muted small">Review payment claims</span>
            </Link>
          </>
        )}
      </div>
      {publishStatus?.status === "published" && publishStatus.url && (
        <p className="muted small" style={{ marginTop: "1rem" }}>
          Live at{" "}
          <a href={publishStatus.url} target="_blank" rel="noreferrer">
            {publishStatus.url}
          </a>
        </p>
      )}
    </div>
  );
}
