import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import PasswordStrengthMeter from "../components/PasswordStrengthMeter";

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [mobileNumber, setMobileNumber] = useState("");
  const [password, setPassword] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const mobileValid = /^\d{10}$/.test(mobileNumber);
  const passwordValid = password.length >= 8;
  const canSubmit = fullName.trim() && mobileValid && passwordValid && agreed && !loading;

  function handleMobileChange(e) {
    setMobileNumber(e.target.value.replace(/\D/g, "").slice(0, 10));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!canSubmit) return;
    setError("");
    setLoading(true);
    try {
      const transactionId = await signup(fullName.trim(), mobileNumber, password);
      navigate("/verify-otp", { state: { transactionId, mobileNumber } });
    } catch (err) {
      setError(err.response?.data?.detail || "Could not sign you up. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-card">
      <h1>Create your account</h1>
      <p className="muted">We'll send a one-time code to your WhatsApp number to verify it.</p>
      <form onSubmit={handleSubmit}>
        <label>Full name</label>
        <input
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
        />

        <label>Mobile number</label>
        <div className="mobile-input-group">
          <span className="mobile-input-prefix">+91</span>
          <input
            type="tel"
            inputMode="numeric"
            placeholder="9876543210"
            maxLength={10}
            value={mobileNumber}
            onChange={handleMobileChange}
            required
          />
        </div>

        <label>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={8}
          required
        />
        <PasswordStrengthMeter password={password} />
        <p className="muted small" style={{ marginTop: "0.3rem" }}>Minimum 8 characters.</p>

        <label className="checkbox-inline" style={{ display: "flex", marginTop: "0.9rem" }}>
          <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} required />
          &nbsp;I agree to the Terms of Service
        </label>

        {error && <p className="error-text">{error}</p>}

        <button type="submit" className="btn btn-primary btn-block" disabled={!canSubmit}>
          {loading ? "Signing up..." : "Sign Up"}
        </button>
      </form>

      <p className="auth-switch">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}
