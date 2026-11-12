import React, { useEffect, useState } from "react";
import client from "../../api/client";

export default function AdminBilling() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [upi, setUpi] = useState({ upi_id: "", qr_image_url: null });
  const [upiInput, setUpiInput] = useState("");
  const [qrFile, setQrFile] = useState(null);
  const [savingUpi, setSavingUpi] = useState(false);
  const [upiEnabled, setUpiEnabled] = useState(true);
  const [razorpayEnabled, setRazorpayEnabled] = useState(false);
  const [savingPaymentSettings, setSavingPaymentSettings] = useState(false);
  const [paymentSettingsMessage, setPaymentSettingsMessage] = useState("");

  function loadRequests() {
    client
      .get("/admin/billing/payment-requests")
      .then(({ data }) => setRequests(data))
      .catch((err) => setError(err.response?.data?.detail || "Could not load payment requests."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadRequests();
    client
      .get("/admin/billing/upi-settings")
      .then(({ data }) => {
        setUpi(data);
        setUpiInput(data.upi_id || "");
        setUpiEnabled(data.upi_enabled);
        setRazorpayEnabled(data.razorpay_enabled);
      })
      .catch(() => {});
  }, []);

  async function savePaymentSettings(e) {
    e.preventDefault();
    setSavingPaymentSettings(true);
    setPaymentSettingsMessage("");
    const formData = new FormData();
    formData.append("upi_enabled", upiEnabled);
    formData.append("razorpay_enabled", razorpayEnabled);
    try {
      const { data } = await client.post("/admin/billing/payment-settings", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUpi(data);
      setPaymentSettingsMessage("Saved.");
    } catch (err) {
      setPaymentSettingsMessage(err.response?.data?.detail || "Could not save.");
    } finally {
      setSavingPaymentSettings(false);
    }
  }

  async function handleApprove(id) {
    setError("");
    try {
      await client.post(`/admin/billing/payment-requests/${id}/approve`);
      loadRequests();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not approve request.");
    }
  }

  async function handleReject(id) {
    setError("");
    try {
      await client.post(`/admin/billing/payment-requests/${id}/reject`);
      loadRequests();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not reject request.");
    }
  }

  async function handleSaveUpi(e) {
    e.preventDefault();
    setSavingUpi(true);
    setError("");
    try {
      const res = await client.put("/admin/billing/upi-settings", { upi_id: upiInput || null });
      setUpi(res.data);
      if (qrFile) {
        const form = new FormData();
        form.append("file", qrFile);
        const qrRes = await client.put("/admin/billing/upi-settings/qr-image", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setUpi(qrRes.data);
        setQrFile(null);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save UPI settings.");
    } finally {
      setSavingUpi(false);
    }
  }

  if (loading) return <div className="card">Loading payment requests...</div>;

  const pending = requests.filter((r) => r.status === "pending");
  const reviewed = requests.filter((r) => r.status !== "pending");

  return (
    <div className="card">
      <h1>Billing admin</h1>
      {error && <p className="error-text">{error}</p>}

      <h2>Payment methods</h2>
      <form onSubmit={savePaymentSettings} style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxWidth: "360px" }}>
        <label>
          <input type="checkbox" checked={upiEnabled} onChange={(e) => setUpiEnabled(e.target.checked)} />{" "}
          Enable UPI QR Code payments
        </label>
        <label>
          <input type="checkbox" checked={razorpayEnabled} onChange={(e) => setRazorpayEnabled(e.target.checked)} />{" "}
          Enable Razorpay payments
        </label>
        <p className="muted small">
          Razorpay Key ID/Secret are configured via server environment variables, not here. Enabling this
          toggle without those set will be rejected.
        </p>
        <button type="submit" className="btn btn-primary" disabled={savingPaymentSettings} style={{ alignSelf: "flex-start" }}>
          {savingPaymentSettings ? "Saving..." : "Save payment methods"}
        </button>
        {paymentSettingsMessage && <p className="muted small">{paymentSettingsMessage}</p>}
      </form>

      <h2 style={{ marginTop: "2rem" }}>UPI settings</h2>
      <form onSubmit={handleSaveUpi} style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxWidth: "360px" }}>
        <label htmlFor="upi-id">UPI ID</label>
        <input id="upi-id" type="text" value={upiInput} onChange={(e) => setUpiInput(e.target.value)} placeholder="e.g. business@upi" />
        <label htmlFor="qr-file">QR code image</label>
        {upi.qr_image_url && (
          <img src={upi.qr_image_url} alt="Current UPI QR code" style={{ maxWidth: "160px" }} />
        )}
        <input id="qr-file" type="file" accept="image/*" onChange={(e) => setQrFile(e.target.files?.[0] || null)} />
        <button type="submit" className="btn btn-primary" disabled={savingUpi} style={{ alignSelf: "flex-start" }}>
          {savingUpi ? "Saving..." : "Save UPI settings"}
        </button>
      </form>

      <h2 style={{ marginTop: "2rem" }}>Pending payment claims</h2>
      {pending.length === 0 ? (
        <p className="muted">No pending claims.</p>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Method</th>
              <th>Amount</th>
              <th>Reference</th>
              <th>Screenshot</th>
              <th>Submitted</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {pending.map((r) => (
              <tr key={r.id}>
                <td>{r.user_full_name}</td>
                <td>{r.method === "razorpay" ? "Razorpay" : "UPI"}</td>
                <td>₹{r.amount_rupees}</td>
                <td>{r.reference_note || "—"}</td>
                <td>
                  {r.screenshot_url ? (
                    <a href={r.screenshot_url} target="_blank" rel="noreferrer">
                      View
                    </a>
                  ) : (
                    "—"
                  )}
                </td>
                <td>{new Date(r.created_at).toLocaleString()}</td>
                <td style={{ display: "flex", gap: "0.5rem" }}>
                  <button type="button" className="btn-link" onClick={() => handleApprove(r.id)}>
                    Approve
                  </button>
                  <button type="button" className="btn-link" onClick={() => handleReject(r.id)}>
                    Reject
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2 style={{ marginTop: "2rem" }}>Reviewed claims</h2>
      {reviewed.length === 0 ? (
        <p className="muted">None yet.</p>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Reviewed</th>
            </tr>
          </thead>
          <tbody>
            {reviewed.map((r) => (
              <tr key={r.id}>
                <td>{r.user_full_name}</td>
                <td>₹{r.amount_rupees}</td>
                <td>{r.status}</td>
                <td>{r.reviewed_at ? new Date(r.reviewed_at).toLocaleString() : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
