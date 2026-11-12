import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";

const RAZORPAY_SCRIPT_SRC = "https://checkout.razorpay.com/v1/checkout.js";

function loadRazorpayScript() {
  if (window.Razorpay) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${RAZORPAY_SCRIPT_SRC}"]`);
    if (existing) {
      existing.addEventListener("load", resolve);
      existing.addEventListener("error", reject);
      return;
    }
    const script = document.createElement("script");
    script.src = RAZORPAY_SCRIPT_SRC;
    script.onload = resolve;
    script.onerror = reject;
    document.body.appendChild(script);
  });
}

export default function Billing() {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [screenshot, setScreenshot] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [method, setMethod] = useState(null);
  const [razorpayBusy, setRazorpayBusy] = useState(false);

  function load() {
    client
      .get("/billing/status")
      .then((res) => {
        setStatus(res.data);
        setMethod((prev) => prev || (res.data.razorpay_enabled ? "razorpay" : "upi"));
      })
      .catch((err) => setError(err.response?.data?.detail || "Could not load billing status."));
  }

  useEffect(load, []);

  async function submitClaim(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const res = await client.post("/billing/payment-requests", { reference_note: note || null });
      if (screenshot) {
        const form = new FormData();
        form.append("file", screenshot);
        await client.post(`/billing/payment-requests/${res.data.id}/screenshot`, form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      }
      setSubmitted(true);
      setNote("");
      setScreenshot(null);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not submit payment claim.");
    } finally {
      setSubmitting(false);
    }
  }

  async function payWithRazorpay() {
    setRazorpayBusy(true);
    setError("");
    try {
      await loadRazorpayScript();
      const { data: order } = await client.post("/billing/razorpay/order", { product: "subscription" });
      const razorpay = new window.Razorpay({
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        order_id: order.order_id,
        name: "Portfolio Builder",
        description: "Upgrade — 1 year",
        handler: async (response) => {
          try {
            await client.post("/billing/razorpay/verify", {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            });
            load();
          } catch (err) {
            setError(err.response?.data?.detail || "Payment verification failed. Contact support if you were charged.");
          } finally {
            setRazorpayBusy(false);
          }
        },
        modal: {
          ondismiss: () => setRazorpayBusy(false),
        },
      });
      razorpay.open();
    } catch (err) {
      setError("Could not start Razorpay checkout. Please try again.");
      setRazorpayBusy(false);
    }
  }

  if (!status) {
    return (
      <div className="card">
        <p className="muted">Loading billing status...</p>
      </div>
    );
  }

  const isActive = status.subscription_status === "active";
  const isExpired = status.subscription_status === "expired";
  const isTrial = status.subscription_status === "trial";

  return (
    <div className="card">
      <h1>Billing & upgrade</h1>
      {error && <p className="error-text">{error}</p>}

      {isActive && (
        <p className="success-text">
          Your subscription is active until{" "}
          <strong>{new Date(status.paid_until).toLocaleDateString()}</strong>.
        </p>
      )}
      {isTrial && (
        <p className="muted">
          You're on a free trial with <strong>{status.days_remaining} day(s)</strong> remaining (ends{" "}
          {new Date(status.trial_ends_at).toLocaleDateString()}).
        </p>
      )}
      {isExpired && (
        <p className="error-text">
          Your free trial has ended and your published site has been taken down. Upgrade below to publish
          again.
        </p>
      )}

      {!isActive && (
        <div className="field-group">
          <h2>Upgrade for 1 year — ₹{status.amount_rupees}</h2>

          {status.pending_request ? (
            <p className="muted">Your payment claim is pending admin review.</p>
          ) : (
            <>
              {status.upi_enabled && status.razorpay_enabled && (
                <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
                  <button
                    type="button"
                    className={method === "razorpay" ? "btn btn-primary" : "btn btn-outline"}
                    onClick={() => setMethod("razorpay")}
                  >
                    Pay Online
                  </button>
                  <button
                    type="button"
                    className={method === "upi" ? "btn btn-primary" : "btn btn-outline"}
                    onClick={() => setMethod("upi")}
                  >
                    UPI QR Code
                  </button>
                </div>
              )}

              {method === "razorpay" ? (
                <div className="field-group">
                  <p className="muted small">
                    Pay securely by card, UPI, netbanking, or wallet via Razorpay. Your plan is upgraded
                    automatically as soon as payment succeeds — no admin review needed.
                  </p>
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ marginTop: "0.5rem" }}
                    disabled={razorpayBusy}
                    onClick={payWithRazorpay}
                  >
                    {razorpayBusy ? "Processing..." : "Pay Online"}
                  </button>
                </div>
              ) : (
                <>
                  {status.qr_image_url ? (
                    <img
                      src={status.qr_image_url}
                      alt="UPI QR code"
                      style={{ maxWidth: "220px", display: "block", margin: "0.5rem 0" }}
                    />
                  ) : (
                    <p className="muted small">The admin hasn't uploaded a UPI QR code yet.</p>
                  )}
                  {status.upi_id && (
                    <p className="muted small">
                      UPI ID: <strong>{status.upi_id}</strong>
                    </p>
                  )}
                  <p className="muted small">
                    Scan the QR code or pay to the UPI ID above, then submit your payment details below for
                    review. An admin will manually verify and activate your 1-year upgrade.
                  </p>

                  {submitted ? (
                    <p className="success-text">Payment claim submitted — awaiting admin review.</p>
                  ) : (
                    <form onSubmit={submitClaim} style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxWidth: "360px" }}>
                      <label htmlFor="ref-note">UTR / transaction reference (optional)</label>
                      <input
                        id="ref-note"
                        type="text"
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                        placeholder="e.g. UPI ref number"
                      />
                      <label htmlFor="screenshot">Payment screenshot (optional)</label>
                      <input
                        id="screenshot"
                        type="file"
                        accept="image/*"
                        onChange={(e) => setScreenshot(e.target.files?.[0] || null)}
                      />
                      <button type="submit" className="btn btn-primary" disabled={submitting}>
                        {submitting ? "Submitting..." : "I've paid — submit for review"}
                      </button>
                    </form>
                  )}
                </>
              )}
            </>
          )}
        </div>
      )}

      <div className="form-actions">
        <Link to="/dashboard" className="btn-link">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
