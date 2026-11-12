import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Mirrors app/services/onboarding.py's next_step_for() on the backend.
const NEXT_STEP = {
  mobile_verified: "/onboarding/resume",
  resume_pending: "/onboarding/resume",
  audience_pending: "/onboarding/audience",
  profile_pending: "/onboarding/profile",
  template_pending: "/template",
};

export default function ProtectedRoute({
  children,
  adminOnly = false,
  superAdminOnly = false,
  requireOnboarded = true,
}) {
  const { user, onboardingStatus, isAdmin } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && !isAdmin) return <Navigate to="/dashboard" replace />;
  if (superAdminOnly && user.role !== "super_admin") return <Navigate to="/dashboard" replace />;
  if (requireOnboarded && NEXT_STEP[onboardingStatus]) {
    return <Navigate to={NEXT_STEP[onboardingStatus]} replace />;
  }
  return children;
}
