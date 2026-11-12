import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NEXT_STEP = {
  mobile_verified: "/onboarding/resume",
  resume_pending: "/onboarding/resume",
  profile_pending: "/onboarding/profile",
  template_pending: "/template",
  onboarding_complete: "/dashboard",
};

const RESEND_COOLDOWN_SECONDS = 120;

export default function VerifyOtp() {
  const { verifyOtp, resendOtp } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [transactionId, setTransactionId] = useState(location.state?.transactionId || "");
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(RESEND_COOLDOWN_SECONDS);

  useEffect(() => {
    const timer = setInterval(() => setSecondsLeft((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(timer);
  }, []);

  if (!transactionId) {
    navigate("/signup", { replace: true });
    return null;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await verifyOtp(transactionId, otp);
      navigate(NEXT_STEP[data.onboarding_status] || "/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid or expired code.");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    setError("");
    setResending(true);
    try {
      const newTransactionId = await resendOtp(transactionId);
      setTransactionId(newTransactionId);
      setSecondsLeft(RESEND_COOLDOWN_SECONDS);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not resend the code.");
    } finally {
      setResending(false);
    }
  }

  const mm = String(Math.floor(secondsLeft / 60)).padStart(2, "0");
  const ss = String(secondsLeft % 60).padStart(2, "0");

  return (
    <div className="auth-card">
      <h1>Enter your code</h1>
      <p className="muted">
        We sent a 6-digit code on WhatsApp to +91 {location.state?.mobileNumber || "your number"}. It's valid for 10
        minutes.
      </p>
      <form onSubmit={handleSubmit}>
        <label>One-time code</label>
        <input
          type="text"
          inputMode="numeric"
          maxLength={6}
          value={otp}
          onChange={(e) => setOtp(e.target.value)}
          required
        />

        {error && <p className="error-text">{error}</p>}

        <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
          {loading ? "Verifying..." : "Verify"}
        </button>

        {secondsLeft > 0 ? (
          <p className="muted small" style={{ marginTop: "0.8rem", textAlign: "center" }}>
            Resend code in {mm}:{ss}
          </p>
        ) : (
          <button
            type="button"
            className="btn-link"
            style={{ marginTop: "0.8rem", display: "block", margin: "0.8rem auto 0" }}
            onClick={handleResend}
            disabled={resending}
          >
            {resending ? "Resending..." : "Resend code"}
          </button>
        )}
      </form>

      {import.meta.env.VITE_OTP_MODE === "dev_fixed" && (
        <p className="dev-otp-hint">Dev mode: use code 123456</p>
      )}
    </div>
  );
}
