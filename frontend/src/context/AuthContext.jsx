import React, { createContext, useContext, useState, useCallback } from "react";
import client from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("auth_user");
    return raw ? JSON.parse(raw) : null;
  });
  const [onboardingStatus, setOnboardingStatus] = useState(() =>
    localStorage.getItem("onboarding_status")
  );

  const signup = useCallback(async (fullName, mobileNumber, password) => {
    const { data } = await client.post("/auth/signup", {
      full_name: fullName,
      mobile_number: mobileNumber,
      password,
    });
    return data.transaction_id;
  }, []);

  const resendOtp = useCallback(async (transactionId) => {
    const { data } = await client.post("/auth/otp/resend", { transaction_id: transactionId });
    return data.transaction_id;
  }, []);

  const applySession = useCallback((data) => {
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    localStorage.setItem("auth_user", JSON.stringify(data.user));
    localStorage.setItem("onboarding_status", data.onboarding_status);
    setUser(data.user);
    setOnboardingStatus(data.onboarding_status);
  }, []);

  const verifyOtp = useCallback(
    async (transactionId, otp) => {
      const { data } = await client.post("/auth/otp/verify", { transaction_id: transactionId, otp });
      applySession(data);
      return data;
    },
    [applySession]
  );

  const login = useCallback(
    async (mobileNumber, password) => {
      const { data } = await client.post("/auth/login", { mobile_number: mobileNumber, password });
      applySession(data);
      return data;
    },
    [applySession]
  );

  const requestPasswordReset = useCallback(async (mobileNumber) => {
    const { data } = await client.post("/auth/password-reset/request", { mobile_number: mobileNumber });
    return data.transaction_id;
  }, []);

  const verifyPasswordReset = useCallback(
    async (transactionId, otp, newPassword) => {
      const { data } = await client.post("/auth/password-reset/verify", {
        transaction_id: transactionId,
        otp,
        new_password: newPassword,
      });
      applySession(data);
      return data;
    },
    [applySession]
  );

  const refreshOnboarding = useCallback(async () => {
    const { data } = await client.get("/auth/session");
    setUser(data.user);
    setOnboardingStatus(data.onboarding_status);
    localStorage.setItem("auth_user", JSON.stringify(data.user));
    localStorage.setItem("onboarding_status", data.onboarding_status);
    return data;
  }, []);

  const logout = useCallback(async () => {
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      try {
        await client.post("/auth/logout", { refresh_token: refreshToken });
      } catch (e) {
        // best-effort — proceed to clear local state regardless
      }
    }
    localStorage.clear();
    setUser(null);
    setOnboardingStatus(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        onboardingStatus,
        signup,
        resendOtp,
        verifyOtp,
        login,
        requestPasswordReset,
        verifyPasswordReset,
        refreshOnboarding,
        logout,
        isAdmin: user?.role === "admin" || user?.role === "super_admin",
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
