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

export default function AiAssistantUpgrade() {
  const [limits, setLimits] = useState(null);
  const [billingStatus, setBillingStatus] = useState(null);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [screenshot, setScreenshot] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [pending, setPending] = useState(false);
  const [method, setMethod] = useState(null);
  const [razorpayBusy, setRazorpayBusy] = useState(false);
  const [enabled, setEnabled] = useState(false);

  function load() {
    Promise.all([client.get("/ai-assistant/limits"), client.get("/billing/status")])
      .then(([limitsRes, billingRes]) => {
        setLimits(limitsRes.data);
        setBillingStatus(billingRes.data);
        setMethod((prev) => prev || (billingRes.data.razorpay_enabled ? "razorpay" : "upi"));
      })
      .catch((err) => setError(err.response?.data?.detail || "Could not load upgrade details."));
  }

  useEffect(load, []);

  async function submitClaim(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const res = await client.post("/billing/payment-requests", {
        reference_note: note || null,
        product: "ai_assistant",
      });
      if (screenshot) {
        const form = new FormData();
        form.append("file", screenshot);
        await client.post(`/billing/payment-requests/${res.data.id}/screenshot`, form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      }
      setSubmitted(true);
      setPending(true);
      setNote("");
      setScreenshot(null);
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
      const { data: order } = await client.post("/billing/razorpay/order", { product: "ai_assistant" });
      const razorpay = new window.Razorpay({
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        order_id: order.order_id,
        name: "Portfolio Builder",
        description: "AI Assistant add-on",
        handler: async (response) => {
          try {
            await client.post("/billing/razorpay/verify", {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            });
            setEnabled(true);
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

  if (!limits || !billingStatus) {
    return (
      <div className="card">
        <p className="muted">Loading...</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h1>Upgrade — AI Assistant</h1>
      <p className="muted">
        Add an AI-powered chat widget to your published portfolio so visitors can ask questions about you
        and get instant answers.
      </p>
      {error && <p className="error-text">{error}</p>}

      <div className="field-group">
        <h2>AI Assistant add-on — ₹{limits.add_on_price_rupees}</h2>

        {enabled ? (
          <p className="success-text">AI Assistant is now enabled on your account.</p>
        ) : pending ? (
          <p className="muted">Your payment claim is pending admin review.</p>
        ) : (
          <>
            {billingStatus.upi_enabled && billingStatus.razorpay_enabled && (
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
                  Pay securely by card, UPI, netbanking, or wallet via Razorpay. The add-on is enabled
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
                {billingStatus.qr_image_url ? (
                  <img
                    src={billingStatus.qr_image_url}
                    alt="UPI QR code"
                    style={{ maxWidth: "220px", display: "block", margin: "0.5rem 0" }}
                  />
                ) : (
                  <p className="muted small">The admin hasn't uploaded a UPI QR code yet.</p>
                )}
                {billingStatus.upi_id && (
                  <p className="muted small">
                    UPI ID: <strong>{billingStatus.upi_id}</strong>
                  </p>
                )}
                <p className="muted small">
                  Scan the QR code or pay to the UPI ID above, then submit your payment details below for review.
                  An admin will manually verify and enable the AI Assistant add-on on your account.
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

      <div className="form-actions">
        <Link to="/ai-assistant" className="btn-link">
          Back to AI Assistant
        </Link>
      </div>
    </div>
  );
}
