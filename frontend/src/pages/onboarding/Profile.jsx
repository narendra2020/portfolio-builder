import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import StepProgress from "../../components/StepProgress";
import ImageUploadField from "../../components/ImageUploadField";

export default function Profile() {
  const { refreshOnboarding } = useAuth();
  const navigate = useNavigate();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("");
  const [profileImage, setProfileImage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    client.get("/profile").then(({ data: profile }) => {
      if (profile.profile_image) setProfileImage(profile.profile_image);
      const suggested = profile.resume_suggestions?.profile;
      if (!suggested) return;
      if (suggested.display_name) setDisplayName(suggested.display_name);
      if (suggested.email) setEmail(suggested.email);
      if (suggested.city) setCity(suggested.city);
      if (suggested.country) setCountry(suggested.country);
    });
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await client.put("/profile", {
        display_name: displayName,
        email,
        city,
        country,
        profile_image: profileImage,
      });
      await refreshOnboarding();
      navigate("/template");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save your profile.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-container">
      <StepProgress current={3} total={4} labels={["Resume", "Audience", "Profile", "Template"]} />
      <div className="card" style={{ maxWidth: 480, margin: "0 auto" }}>
        <h1>Tell us about you</h1>
        <p className="muted">This helps us personalize your portfolio.</p>
        <form onSubmit={handleSubmit}>
          <label>Full name</label>
          <input type="text" value={displayName} onChange={(e) => setDisplayName(e.target.value)} required />

          <label>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />

          <label>City</label>
          <input type="text" value={city} onChange={(e) => setCity(e.target.value)} />

          <label>Country</label>
          <input type="text" value={country} onChange={(e) => setCountry(e.target.value)} />

          <ImageUploadField label="Profile photo" value={profileImage} onChange={setProfileImage} />

          {error && <p className="error-text">{error}</p>}

          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? "Saving..." : "Continue"}
          </button>
        </form>
      </div>
    </div>
  );
}
