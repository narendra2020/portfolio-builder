import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import client from "../api/client";
import DynamicField from "../components/DynamicField";
import StepProgress from "../components/StepProgress";

export default function Questionnaire() {
  const navigate = useNavigate();
  const [sections, setSections] = useState(null);
  const [answersBySection, setAnswersBySection] = useState({});
  const [sectionIndex, setSectionIndex] = useState(0);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [savedKeys, setSavedKeys] = useState(new Set());

  useEffect(() => {
    Promise.all([
      client.get("/questionnaire/schema"),
      client.get("/questionnaire/responses"),
      client.get("/profile"),
    ])
      .then(([schemaRes, responsesRes, profileRes]) => {
        setSections(schemaRes.data);
        const bySection = {};
        const suggestedAnswers = profileRes.data.resume_suggestions?.answers || {};
        for (const section of schemaRes.data) {
          if (suggestedAnswers[section.section_key]) {
            bySection[section.section_key] = suggestedAnswers[section.section_key];
          }
        }
        for (const response of responsesRes.data) {
          bySection[response.section_key] = response.answers;
        }
        setAnswersBySection(bySection);
        setSavedKeys(new Set(responsesRes.data.map((r) => r.section_key)));
      })
      .catch((err) => {
        setError(err.response?.data?.detail || "Could not load the questionnaire.");
      });
  }, []);

  if (error) {
    return (
      <div className="card">
        <p className="error-text">{error}</p>
      </div>
    );
  }

  if (!sections) {
    return (
      <div className="card">
        <p className="muted">Loading questionnaire...</p>
      </div>
    );
  }

  if (sections.length === 0) {
    return (
      <div className="card">
        <h1>Questionnaire</h1>
        <p className="muted">No questionnaire is available for your profession yet. Check back soon.</p>
      </div>
    );
  }

  const currentSection = sections[sectionIndex];
  const currentAnswers = answersBySection[currentSection.section_key] || {};

  function updateField(key, value) {
    setAnswersBySection((prev) => ({
      ...prev,
      [currentSection.section_key]: { ...(prev[currentSection.section_key] || {}), [key]: value },
    }));
  }

  async function saveCurrentSection() {
    setError("");
    setSaving(true);
    try {
      await client.put("/questionnaire/responses", {
        section_key: currentSection.section_key,
        answers: currentAnswers,
      });
      setSavedKeys((prev) => new Set(prev).add(currentSection.section_key));
      return true;
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save your answers.");
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function handleNext() {
    const ok = await saveCurrentSection();
    if (!ok) return;
    if (sectionIndex < sections.length - 1) {
      setSectionIndex(sectionIndex + 1);
    } else {
      navigate("/publish");
    }
  }

  function handleBack() {
    if (sectionIndex > 0) setSectionIndex(sectionIndex - 1);
  }

  return (
    <div>
      <StepProgress
        current={sectionIndex + 1}
        total={sections.length}
        labels={sections.map((s) => s.section_title)}
      />

      <AnimatePresence mode="wait">
        <motion.div
          key={currentSection.section_key}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
          className="card"
        >
          <h1>{currentSection.section_title}</h1>
          {error && <p className="error-text">{error}</p>}
          {currentSection.questions.map((question) => (
            <DynamicField
              key={question.key}
              question={question}
              value={currentAnswers[question.key]}
              onChange={updateField}
            />
          ))}
          <div className="form-actions">
            <button className="btn-link" disabled={sectionIndex === 0 || saving} onClick={handleBack}>
              Back
            </button>
            <button className="btn btn-primary" disabled={saving} onClick={handleNext}>
              {sectionIndex < sections.length - 1 ? "Save & Next" : "Save & Finish"}
            </button>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
