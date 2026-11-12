import React from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Navbar from "./components/Navbar.jsx";
import PageTransition from "./components/PageTransition.jsx";
import Signup from "./pages/Signup.jsx";
import Login from "./pages/Login.jsx";
import VerifyOtp from "./pages/VerifyOtp.jsx";
import Resume from "./pages/onboarding/Resume.jsx";
import Audience from "./pages/onboarding/Audience.jsx";
import Profile from "./pages/onboarding/Profile.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Questionnaire from "./pages/Questionnaire.jsx";
import TemplateSelect from "./pages/TemplateSelect.jsx";
import LayoutEditor from "./pages/LayoutEditor.jsx";
import Publish from "./pages/Publish.jsx";
import Billing from "./pages/Billing.jsx";
import AiAssistant from "./pages/AiAssistant.jsx";
import AiAssistantUpgrade from "./pages/AiAssistantUpgrade.jsx";
import ResumeLanding from "./pages/resume/ResumeLanding.jsx";
import ResumeEditor from "./pages/resume/ResumeEditor.jsx";
import ResumeJdTailor from "./pages/resume/ResumeJdTailor.jsx";
import ResumeAtsAnalysis from "./pages/resume/ResumeAtsAnalysis.jsx";
import UserManagement from "./pages/admin/UserManagement.jsx";
import AdminBilling from "./pages/admin/AdminBilling.jsx";
import { useAuth } from "./context/AuthContext.jsx";

export default function App() {
  const { user } = useAuth();
  const location = useLocation();

  return (
    <>
      <Navbar />
      <AnimatePresence mode="wait" initial={false}>
        <Routes location={location} key={location.pathname}>
          <Route path="/signup" element={<PageTransition><Signup /></PageTransition>} />
          <Route path="/login" element={<PageTransition><Login /></PageTransition>} />
          <Route path="/verify-otp" element={<PageTransition><VerifyOtp /></PageTransition>} />

          <Route
            path="/onboarding/resume"
            element={<ProtectedRoute requireOnboarded={false}><PageTransition><Resume /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/onboarding/audience"
            element={<ProtectedRoute requireOnboarded={false}><PageTransition><Audience /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/onboarding/profile"
            element={<ProtectedRoute requireOnboarded={false}><PageTransition><Profile /></PageTransition></ProtectedRoute>}
          />

          <Route
            path="/dashboard"
            element={<ProtectedRoute><PageTransition className="page-container"><Dashboard /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/questionnaire"
            element={<ProtectedRoute><PageTransition className="page-container"><Questionnaire /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/template"
            element={<ProtectedRoute requireOnboarded={false}><PageTransition className="page-container"><TemplateSelect /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/editor"
            element={<ProtectedRoute><PageTransition className="page-container"><LayoutEditor /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/publish"
            element={<ProtectedRoute><PageTransition className="page-container"><Publish /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/billing"
            element={<ProtectedRoute><PageTransition className="page-container"><Billing /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/resumes"
            element={<ProtectedRoute requireOnboarded={false}><PageTransition className="page-container"><ResumeLanding /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/resumes/:id/edit"
            element={<ProtectedRoute requireOnboarded={false}><PageTransition className="page-container"><ResumeEditor /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/resumes/:id/tailor"
            element={<ProtectedRoute><PageTransition className="page-container"><ResumeJdTailor /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/resumes/:id/ats"
            element={<ProtectedRoute><PageTransition className="page-container"><ResumeAtsAnalysis /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/ai-assistant"
            element={<ProtectedRoute><PageTransition className="page-container"><AiAssistant /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/ai-assistant/upgrade"
            element={<ProtectedRoute><PageTransition className="page-container"><AiAssistantUpgrade /></PageTransition></ProtectedRoute>}
          />
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute superAdminOnly>
                <PageTransition className="page-container"><UserManagement /></PageTransition>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/billing"
            element={
              <ProtectedRoute superAdminOnly>
                <PageTransition className="page-container"><AdminBilling /></PageTransition>
              </ProtectedRoute>
            }
          />

          <Route path="/" element={<Navigate to={user ? "/dashboard" : "/signup"} replace />} />
          <Route path="*" element={<Navigate to={user ? "/dashboard" : "/signup"} replace />} />
        </Routes>
      </AnimatePresence>
    </>
  );
}
