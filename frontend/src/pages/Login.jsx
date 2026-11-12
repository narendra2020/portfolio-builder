import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NEXT_STEP = {
  mobile_verified: "/onboarding/resume",
  resume_pending: "/onboarding/resume",
  profile_pending: "/onboarding/profile",
  template_pending: "/template",
  onboarding_complete: "/dashboard",
};

export default function Login() {
  const { login, requestPasswordReset, verifyPasswordReset } = useAuth();
  const navigate = useNavigate();
  const [mobileNumber, setMobileNumber] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState("login");
  const [resetStep, setResetStep] = useState("request");
  const [resetTransactionId, setResetTransactionId] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);

  const mobileValid = /^\d{10}$/.test(mobileNumber);
  const otpValid = /^\d{6}$/.test(otp);
  const newPasswordValid = newPassword.length >= 8;
  const isLoginMode = mode === "login";
  const isResetVerify = resetStep === "verify";
  const canSubmit = isLoginMode
    ? mobileValid && password && !loading
    : resetStep === "request"
        ? mobileValid && !loading
        : mobileValid && otpValid && newPasswordValid && resetTransactionId && !loading;

  const primaryLabel = isLoginMode
    ? loading ? "Logging in..." : "Log in"
    : resetStep === "request"
        ? loading ? "Sending OTP..." : "Send OTP"
        : loading ? "Resetting password..." : "Reset password";

  function handleMobileChange(e) {
    setMobileNumber(e.target.value.replace(/\D/g, "").slice(0, 10));
    if (!isLoginMode) {
      setError("");
      setInfo("");
      if (resetStep === "verify") {
        setResetStep("request");
        setResetTransactionId("");
        setOtp("");
        setNewPassword("");
      }
    }
  }

  function handleOtpChange(e) {
    setOtp(e.target.value.replace(/\D/g, "").slice(0, 6));
  }

  function switchToReset() {
    setMode("reset");
    setResetStep("request");
    setResetTransactionId("");
    setOtp("");
    setNewPassword("");
    setPassword("");
    setError("");
    setInfo("");
  }

  function switchToLogin() {
    setMode("login");
    setResetStep("request");
    setResetTransactionId("");
    setOtp("");
    setNewPassword("");
    setError("");
    setInfo("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!canSubmit) return;
    setInfo("");
    setError("");
    setLoading(true);
    try {
      if (isLoginMode) {
        const data = await login(mobileNumber, password);
        navigate(NEXT_STEP[data.onboarding_status] || "/dashboard");
      } else if (resetStep === "request") {
        const transactionId = await requestPasswordReset(mobileNumber);
        setResetTransactionId(transactionId);
        setResetStep("verify");
        setInfo("We sent a 6-digit OTP to your WhatsApp number.");
      } else {
        const data = await verifyPasswordReset(resetTransactionId, otp, newPassword);
        navigate(NEXT_STEP[data.onboarding_status] || "/dashboard");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-card">
      <h1>{isLoginMode ? "Welcome back" : "Reset your password"}</h1>
      <p className="muted">
        {isLoginMode
          ? "Log in with your mobile number and password."
          : resetStep === "request"
              ? "Enter your registered mobile number to receive an OTP on WhatsApp."
              : "Enter the OTP you received on WhatsApp and choose a new password."}
      </p>
      <form onSubmit={handleSubmit}>
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
        {isLoginMode ? (
          <>
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </>
        ) : (
          <>
            {isResetVerify && (
              <>
                <label>OTP</label>
                <input
                  type="tel"
                  inputMode="numeric"
                  maxLength={6}
                  value={otp}
                  onChange={handleOtpChange}
                  placeholder="6-digit code"
                  required
                />
              </>
            )}

            {isResetVerify && (
              <>
                <label>New password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  required
                />
              </>
            )}
          </>
        )}

        {error && <p className="error-text">{error}</p>}
        {info && <p className="success-text">{info}</p>}

        <button type="submit" className="btn btn-primary btn-block" disabled={!canSubmit}>
          {primaryLabel}
        </button>
      </form>

      {isLoginMode ? (
        <>
          <p className="auth-switch">
            <button type="button" className="btn-link" onClick={switchToReset}>
              Forgot password? Reset using WhatsApp OTP
            </button>
          </p>
          <p className="auth-switch">
            Don't have an account? <Link to="/signup">Sign up</Link>
          </p>
        </>
      ) : (
        <>
          {resetStep === "verify" && (
            <p className="muted small">Didn't receive a code? Wait a few seconds and request again.</p>
          )}
          <p className="auth-switch">
            <button type="button" className="btn-link" onClick={switchToLogin}>
              Back to login
            </button>
          </p>
        </>
      )}
    </div>
  );
}
