import React, { useEffect, useState } from "react";
import client from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import PasswordStrengthMeter from "../../components/PasswordStrengthMeter";

export default function UserManagement() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [createSuccess, setCreateSuccess] = useState("");
  const [createFullName, setCreateFullName] = useState("");
  const [createMobile, setCreateMobile] = useState("");
  const [createPassword, setCreatePassword] = useState("");
  const [createRole, setCreateRole] = useState("registered_user");
  const [createActive, setCreateActive] = useState(true);
  const [resetTargetId, setResetTargetId] = useState(null);
  const [newPassword, setNewPassword] = useState("");
  const [resetError, setResetError] = useState("");
  const [resetSuccess, setResetSuccess] = useState("");
  const [resetting, setResetting] = useState(false);
  const [detailTargetId, setDetailTargetId] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [aiAssistantSaving, setAiAssistantSaving] = useState(false);
  const [aiAssistantError, setAiAssistantError] = useState("");

  useEffect(() => {
    client
      .get("/admin/users")
      .then(({ data }) => setUsers(data))
      .catch((err) => setError(err.response?.data?.detail || "Could not load users."))
      .finally(() => setLoading(false));
  }, []);

  function openReset(userId) {
    setResetTargetId(userId);
    setNewPassword("");
    setResetError("");
    setResetSuccess("");
  }

  async function handleResetSubmit(e) {
    e.preventDefault();
    setResetError("");
    setResetSuccess("");
    setResetting(true);
    try {
      await client.put(`/admin/users/${resetTargetId}/password`, { new_password: newPassword });
      setResetSuccess("Password updated.");
      setNewPassword("");
    } catch (err) {
      setResetError(err.response?.data?.detail || "Could not reset password.");
    } finally {
      setResetting(false);
    }
  }

  async function handleDelete(userId) {
    if (!window.confirm("Delete this user? This cannot be undone.")) return;
    setError("");
    try {
      await client.delete(`/admin/users/${userId}`);
      setUsers((prev) => prev.filter((u) => u.id !== userId));
    } catch (err) {
      setError(err.response?.data?.detail || "Could not delete user.");
    }
  }

  async function handleCreateSubmit(e) {
    e.preventDefault();
    setCreateError("");
    setCreateSuccess("");
    setCreating(true);
    try {
      const { data } = await client.post("/admin/users", {
        full_name: createFullName,
        mobile_number: createMobile,
        password: createPassword,
        role: createRole,
        is_active: createActive,
      });
      setUsers((prev) => [data, ...prev]);
      setCreateSuccess("User created.");
      setCreateFullName("");
      setCreateMobile("");
      setCreatePassword("");
      setCreateRole("registered_user");
      setCreateActive(true);
    } catch (err) {
      setCreateError(err.response?.data?.detail || "Could not create user.");
    } finally {
      setCreating(false);
    }
  }

  async function openDetails(userId) {
    if (detailTargetId === userId) {
      setDetailTargetId(null);
      return;
    }
    setDetailTargetId(userId);
    setDetailData(null);
    setDetailError("");
    setAiAssistantError("");
    setAiAssistantSaving(false);
    setDetailLoading(true);
    try {
      const { data } = await client.get(`/admin/users/${userId}`);
      setDetailData(data);
    } catch (err) {
      setDetailError(err.response?.data?.detail || "Could not load user details.");
    } finally {
      setDetailLoading(false);
    }
  }

  async function toggleAiAssistant(userId, enabled) {
    setAiAssistantError("");
    setAiAssistantSaving(true);
    try {
      const { data } = await client.put(`/admin/users/${userId}/ai-assistant`, { enabled });
      setDetailData(data);
    } catch (err) {
      setAiAssistantError(err.response?.data?.detail || "Could not update AI Assistant status.");
    } finally {
      setAiAssistantSaving(false);
    }
  }

  async function handleSlugReset(userId) {
    if (!window.confirm("Reset this user's subdomain? Their site will be unpublished and they'll be able to choose a new subdomain.")) return;
    setError("");
    try {
      await client.put(`/admin/users/${userId}/publish/slug-reset`);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not reset subdomain.");
    }
  }

  if (loading) return <div className="card">Loading users...</div>;

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}>
        <h1 style={{ margin: 0 }}>Manage users</h1>
        <button type="button" className="btn btn-primary" onClick={() => { setCreateOpen((prev) => !prev); setCreateError(""); setCreateSuccess(""); }}>
          {createOpen ? "Close" : "Add user"}
        </button>
      </div>
      {error && <p className="error-text">{error}</p>}

      {createOpen && (
        <form onSubmit={handleCreateSubmit} style={{ marginTop: "1.5rem", marginBottom: "2rem", display: "grid", gap: "1rem", maxWidth: "420px" }}>
          <div>
            <label>Full name</label>
            <input type="text" value={createFullName} onChange={(e) => setCreateFullName(e.target.value)} required />
          </div>
          <div>
            <label>Mobile number</label>
            <input type="text" value={createMobile} onChange={(e) => setCreateMobile(e.target.value)} placeholder="e.g. 9876543210" required />
          </div>
          <div>
            <label>Password</label>
            <input type="password" value={createPassword} onChange={(e) => setCreatePassword(e.target.value)} minLength={8} required />
            <PasswordStrengthMeter password={createPassword} />
          </div>
          <div>
            <label>Role</label>
            <select value={createRole} onChange={(e) => setCreateRole(e.target.value)}>
              <option value="registered_user">Registered user</option>
              <option value="support_user">Support user</option>
              <option value="content_manager">Content manager</option>
              <option value="template_manager">Template manager</option>
              <option value="admin">Admin</option>
              <option value="super_admin">Super admin</option>
            </select>
          </div>
          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <input type="checkbox" checked={createActive} onChange={(e) => setCreateActive(e.target.checked)} /> Active account
          </label>
          {createError && <p className="error-text" style={{ margin: 0 }}>{createError}</p>}
          {createSuccess && <p className="muted small" style={{ margin: 0 }}>{createSuccess}</p>}
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <button type="submit" className="btn btn-primary" disabled={creating || createPassword.length < 8}>
              {creating ? "Creating..." : "Create user"}
            </button>
            <button type="button" className="btn-link" onClick={() => { setCreateOpen(false); setCreateError(""); setCreateSuccess(""); }}>
              Cancel
            </button>
          </div>
        </form>
      )}

      <table className="admin-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Mobile</th>
            <th>Role</th>
            <th>Status</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <React.Fragment key={u.id}>
              <tr>
                <td>{u.full_name}</td>
                <td>{u.mobile_number}</td>
                <td>{u.role}</td>
                <td>{u.is_active ? "Active" : "Inactive"}</td>
                <td>{new Date(u.created_at).toLocaleDateString()}</td>
                <td style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                  <button type="button" className="btn-link" onClick={() => openDetails(u.id)}>
                    View details
                  </button>
                  <button type="button" className="btn-link" onClick={() => openReset(u.id)}>
                    Reset password
                  </button>
                  <button type="button" className="btn-link" onClick={() => handleSlugReset(u.id)}>
                    Reset subdomain
                  </button>
                  {u.id !== currentUser?.id && (
                    <button type="button" className="btn-link" onClick={() => handleDelete(u.id)}>
                      Delete
                    </button>
                  )}
                </td>
              </tr>
              {resetTargetId === u.id && (
                <tr>
                  <td colSpan={6}>
                    <form onSubmit={handleResetSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxWidth: "320px" }}>
                      <label>New password for {u.full_name}</label>
                      <input
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        minLength={8}
                        required
                      />
                      <PasswordStrengthMeter password={newPassword} />
                      {resetError && <p className="error-text">{resetError}</p>}
                      {resetSuccess && <p className="muted small">{resetSuccess}</p>}
                      <div style={{ display: "flex", gap: "0.5rem" }}>
                        <button type="submit" className="btn btn-primary" disabled={resetting || newPassword.length < 8}>
                          {resetting ? "Saving..." : "Save password"}
                        </button>
                        <button type="button" className="btn-link" onClick={() => setResetTargetId(null)}>
                          Cancel
                        </button>
                      </div>
                    </form>
                  </td>
                </tr>
              )}
              {detailTargetId === u.id && (
                <tr>
                  <td colSpan={6}>
                    {detailLoading && <p className="muted small">Loading details...</p>}
                    {detailError && <p className="error-text">{detailError}</p>}
                    {detailData && (
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem", maxWidth: "480px" }}>
                        {detailData.profile_image && (
                          <img
                            src={detailData.profile_image}
                            alt=""
                            style={{ width: "64px", height: "64px", borderRadius: "50%", objectFit: "cover" }}
                          />
                        )}
                        <p><strong>Name:</strong> {detailData.display_name || detailData.full_name}</p>
                        <p><strong>Mobile:</strong> {detailData.mobile_number}</p>
                        <p><strong>Email:</strong> {detailData.email || "—"}</p>
                        <p><strong>Location:</strong> {[detailData.city, detailData.country].filter(Boolean).join(", ") || "—"}</p>
                        <p><strong>Role:</strong> {detailData.role}</p>
                        <p><strong>Status:</strong> {detailData.is_active ? "Active" : "Inactive"}</p>
                        <p><strong>Created:</strong> {new Date(detailData.created_at).toLocaleDateString()}</p>
                        <p>
                          <strong>Portfolio:</strong>{" "}
                          {detailData.published_url ? (
                            <a href={detailData.published_url} target="_blank" rel="noreferrer">
                              {detailData.published_url}
                            </a>
                          ) : (
                            "Not published"
                          )}
                        </p>
                        <div style={{ marginTop: "0.5rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                          <p style={{ margin: 0 }}>
                            <strong>AI Assistant:</strong> {detailData.ai_assistant_enabled ? "Enabled" : "Disabled"}{" "}
                            <span className="muted" style={{ fontSize: "0.85rem" }}>
                              (Widget {detailData.ai_assistant_config_enabled ? "active" : "inactive"})
                            </span>
                          </p>
                          {aiAssistantError && <p className="error-text" style={{ margin: 0 }}>{aiAssistantError}</p>}
                          <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap" }}>
                            <button
                              type="button"
                              className="btn btn-primary"
                              disabled={aiAssistantSaving}
                              onClick={() => toggleAiAssistant(u.id, !detailData.ai_assistant_enabled)}
                            >
                              {aiAssistantSaving
                                ? "Saving..."
                                : detailData.ai_assistant_enabled
                                  ? "Disable AI Assistant"
                                  : "Enable AI Assistant"}
                            </button>
                          </div>
                        </div>
                        <button type="button" className="btn-link" onClick={() => setDetailTargetId(null)}>
                          Close
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
