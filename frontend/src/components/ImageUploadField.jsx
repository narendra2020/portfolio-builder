import React, { useState } from "react";
import client from "../api/client";

export default function ImageUploadField({ value, onChange, label }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  async function handleFileChange(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setError("");
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await client.post("/media/image", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onChange(res.data.url);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not upload image.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="image-upload-field">
      {label && <label>{label}</label>}

      {value ? (
        <div className="image-upload-preview">
          <img src={value} alt="" className="image-upload-thumb" />
          <button
            type="button"
            className="btn-link"
            onClick={() => onChange("")}
            disabled={uploading}
          >
            Remove
          </button>
        </div>
      ) : (
        <input type="file" accept="image/*" onChange={handleFileChange} disabled={uploading} />
      )}

      {uploading && <p className="muted small">Uploading...</p>}
      {error && <p className="error-text">{error}</p>}
    </div>
  );
}
