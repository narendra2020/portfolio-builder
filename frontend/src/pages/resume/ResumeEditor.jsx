import React, { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import client from "../../api/client";
import FieldAiActionsMenu from "../../components/FieldAiActionsMenu";
import SkillGroupCard from "../../components/SkillGroupCard";
import ResumePreview from "./ResumePreview";
import {
  newExperience, newBullet, newProject, newEducation,
  newCertification, newAchievement, newAdditionalSection, newSkillGroup,
} from "./resumeContent";

const ICON_PERSON = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="8" r="3.5" /><path d="M5 20c0-3.5 3-6 7-6s7 2.5 7 6" /></svg>
);
const ICON_DOC = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M7 3h7l4 4v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" /><path d="M14 3v4h4" /></svg>
);
const ICON_BRIEFCASE = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="8" width="18" height="12" rx="2" /><path d="M8 8V6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></svg>
);
const ICON_FOLDER = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /></svg>
);
const ICON_LAYERS = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 3l9 5-9 5-9-5 9-5z" /><path d="M3 13l9 5 9-5" /></svg>
);
const ICON_GRAD = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 4 2 9l10 5 10-5-10-5z" /><path d="M6 11.5V17c0 1.5 3 3 6 3s6-1.5 6-3v-5.5" /></svg>
);
const ICON_AWARD = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="8" r="5" /><path d="M8.5 12.5 7 21l5-2.5L17 21l-1.5-8.5" /></svg>
);
const ICON_STAR = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 3l2.6 5.7 6.2.6-4.7 4.1 1.4 6.1L12 16.6 6.5 19.5l1.4-6.1-4.7-4.1 6.2-.6z" /></svg>
);
const ICON_GRID = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="3" width="7" height="7" rx="1.3" /><rect x="14" y="3" width="7" height="7" rx="1.3" /><rect x="3" y="14" width="7" height="7" rx="1.3" /><rect x="14" y="14" width="7" height="7" rx="1.3" /></svg>
);
const ICON_TARGET = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="4" /><circle cx="12" cy="12" r="0.6" fill="currentColor" /></svg>
);
const ICON_BARCHART = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M5 20V11M12 20V4M19 20v-7" /></svg>
);
const ICON_DOWNLOAD = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 3v12M7 10l5 5 5-5" /><path d="M5 20h14" /></svg>
);
const ICON_CHECK = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 13l4 4L19 7" /></svg>
);

const SECTIONS = [
  { key: "personal", label: "Personal", subtitle: "Basic information", icon: ICON_PERSON },
  { key: "summary", label: "Summary", subtitle: "Professional overview", icon: ICON_DOC },
  { key: "experience", label: "Experience", subtitle: "Work history", icon: ICON_BRIEFCASE },
  { key: "projects", label: "Projects", subtitle: "Key projects", icon: ICON_FOLDER },
  { key: "skills", label: "Skills", subtitle: "Technical & soft skills", icon: ICON_LAYERS },
  { key: "education", label: "Education", subtitle: "Academic details", icon: ICON_GRAD },
  { key: "certifications", label: "Certifications", subtitle: "Courses & certifications", icon: ICON_AWARD },
  { key: "achievements", label: "Achievements", subtitle: "Awards & recognition", icon: ICON_STAR },
  { key: "additional_sections", label: "Additional", subtitle: "Languages, interests, etc.", icon: ICON_GRID },
];

const AUTOSAVE_DELAY_MS = 2000;

function timeAgo(timestamp) {
  if (!timestamp) return "";
  const seconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000));
  if (seconds < 10) return "a few seconds ago";
  if (seconds < 60) return `${seconds} seconds ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return minutes === 1 ? "a minute ago" : `${minutes} minutes ago`;
  const hours = Math.floor(minutes / 60);
  return hours === 1 ? "an hour ago" : `${hours} hours ago`;
}

export default function ResumeEditor() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [resume, setResume] = useState(null);
  const [content, setContent] = useState(null);
  const [sectionKey, setSectionKey] = useState("personal");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [saveState, setSaveState] = useState("idle"); // idle | pending | saving | saved
  const [generating, setGenerating] = useState(false);
  const [targetRole, setTargetRole] = useState("");
  const [busyFieldKey, setBusyFieldKey] = useState(null);
  const [undoStack, setUndoStack] = useState({});
  const [exporting, setExporting] = useState(false);
  const [lastSavedAt, setLastSavedAt] = useState(null);
  const [previewWidth, setPreviewWidth] = useState("single"); // single | two — cosmetic only
  const [menuOpen, setMenuOpen] = useState(false);
  const [, forceTick] = useState(0);

  const saveTimer = useRef(null);
  const dirty = useRef(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const interval = setInterval(() => forceTick((n) => n + 1), 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function onDocClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  useEffect(() => {
    client
      .get(`/resumes/${id}`)
      .then((res) => {
        setResume(res.data);
        setContent(res.data.content);
        setTargetRole(res.data.target_role || "");
      })
      .catch((err) => setError(err.response?.data?.detail || "Could not load this resume."));

    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  function scheduleSave(nextContent) {
    dirty.current = true;
    setSaveState("pending");
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => doSave(nextContent), AUTOSAVE_DELAY_MS);
  }

  async function doSave(nextContent) {
    setSaveState("saving");
    try {
      await client.put(`/resumes/${id}`, { content: nextContent ?? content });
      dirty.current = false;
      setSaveState("saved");
      setLastSavedAt(Date.now());
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save your changes.");
      setSaveState("idle");
    }
  }

  function updateContent(updater) {
    setContent((prev) => {
      const next = updater(prev);
      scheduleSave(next);
      return next;
    });
  }

  async function flushSave() {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    if (dirty.current) await doSave(content);
  }

  async function handleGenerate() {
    await flushSave();
    setError("");
    setGenerating(true);
    try {
      const res = await client.post(`/resumes/${id}/generate`, {
        target_role: targetRole || undefined,
      });
      setContent(res.data.resume.content);
      setResume(res.data.resume);
      setNotice("Resume regenerated. Review the changes below.");
    } catch (err) {
      setError(err.response?.data?.detail || "Resume generation is temporarily unavailable. Please try again.");
    } finally {
      setGenerating(false);
    }
  }

  async function improveField(fieldKey, currentText, action, context, onApply) {
    setBusyFieldKey(fieldKey);
    setError("");
    try {
      const res = await client.post(`/resumes/${id}/improve-field`, {
        current_text: currentText, action, context,
      });
      setUndoStack((prev) => ({ ...prev, [fieldKey]: currentText }));
      onApply(res.data.revised_text);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not improve this text right now. Please try again.");
    } finally {
      setBusyFieldKey(null);
    }
  }

  function undoField(fieldKey, onApply) {
    const prevText = undoStack[fieldKey];
    if (prevText === undefined) return;
    onApply(prevText);
    setUndoStack((prev) => {
      const next = { ...prev };
      delete next[fieldKey];
      return next;
    });
  }

  async function handleExport() {
    setError("");
    setExporting(true);
    try {
      const res = await client.get(`/resumes/${id}/export`, { responseType: "blob" });
      const disposition = res.headers["content-disposition"] || "";
      const match = disposition.match(/filename="?([^"]+)"?/);
      const filename = match ? match[1] : "Resume.pdf";
      const url = window.URL.createObjectURL(res.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError("Could not export your resume right now. Please try again.");
    } finally {
      setExporting(false);
    }
  }

  if (error && !content) {
    return (
      <div className="card">
        <p className="error-text">{error}</p>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="card">
        <p className="muted">Loading resume...</p>
      </div>
    );
  }

  return (
    <div>
      <button type="button" className="btn-link resume-back-link" onClick={() => navigate("/dashboard")}>
        ← Back to Dashboard
      </button>

      <div className="resume-page-header">
        <div>
          <h1>Build your resume</h1>
          <p className="muted">Create a professional resume with the help of AI. Add your details, customize and download.</p>
        </div>
        <div className="resume-save-pill">
          {saveState === "saved" && lastSavedAt && (
            <>
              <span className="resume-save-pill-badge">{ICON_CHECK} All changes saved</span>
              <span className="muted small">Last saved {timeAgo(lastSavedAt)}</span>
            </>
          )}
          {saveState === "saving" && <span className="muted small">Saving...</span>}
          {saveState === "pending" && <span className="muted small">Unsaved changes</span>}
        </div>
      </div>

      <div className="card resume-editor-toolbar-row2">
        <input
          type="text"
          placeholder="Target role / Job title"
          value={targetRole}
          onChange={(e) => setTargetRole(e.target.value)}
          className="resume-target-role-input"
        />
        <div className="resume-editor-toolbar-actions">
          <button className="btn btn-primary" disabled={generating} onClick={handleGenerate}>
            {generating ? "Generating..." : "✦ Generate with AI"}
          </button>
          <Link className="resume-toolbar-btn" to={`/resumes/${id}/tailor`}>{ICON_TARGET} Tailor to job</Link>
          <Link className="resume-toolbar-btn" to={`/resumes/${id}/ats`}>{ICON_BARCHART} ATS score</Link>
          <button type="button" className="resume-toolbar-btn" disabled={exporting} onClick={handleExport}>
            {ICON_DOWNLOAD} {exporting ? "Exporting..." : "Export PDF"}
          </button>
          <div className="resume-overflow-menu" ref={menuRef}>
            <button type="button" className="icon-btn resume-overflow-trigger" onClick={() => setMenuOpen((v) => !v)} title="More actions">
              ⋮
            </button>
            {menuOpen && (
              <div className="resume-overflow-list">
                <button type="button" className="resume-overflow-item" onClick={() => navigate("/resumes")}>
                  All resumes
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {error && <p className="error-text">{error}</p>}
      {notice && <p className="success-text">{notice}</p>}

      <div className="resume-editor-grid">
        <div className="resume-editor-nav resume-nav-numbered">
          {SECTIONS.map((s, idx) => (
            <button
              key={s.key}
              className={"resume-nav-item" + (sectionKey === s.key ? " resume-nav-item-active" : "")}
              onClick={() => setSectionKey(s.key)}
            >
              <span className="resume-nav-item-number">{idx + 1}</span>
              <span className="resume-nav-item-icon">{s.icon}</span>
              <span className="resume-nav-item-text">
                <strong>{s.label}</strong>
                <span className="resume-nav-item-subtitle">{s.subtitle}</span>
              </span>
            </button>
          ))}
        </div>

        <div className="card resume-editor-fields">
          {sectionKey === "personal" && (
            <PersonalSection content={content} updateContent={updateContent} />
          )}
          {sectionKey === "summary" && (
            <SummarySection
              content={content} updateContent={updateContent}
              busyFieldKey={busyFieldKey} undoStack={undoStack}
              improveField={improveField} undoField={undoField}
            />
          )}
          {sectionKey === "experience" && (
            <ExperienceSection
              content={content} updateContent={updateContent}
              busyFieldKey={busyFieldKey} undoStack={undoStack}
              improveField={improveField} undoField={undoField}
            />
          )}
          {sectionKey === "projects" && (
            <ProjectsSection
              content={content} updateContent={updateContent}
              busyFieldKey={busyFieldKey} undoStack={undoStack}
              improveField={improveField} undoField={undoField}
            />
          )}
          {sectionKey === "skills" && (
            <SkillsSection content={content} updateContent={updateContent} />
          )}
          {sectionKey === "education" && (
            <EducationSection content={content} updateContent={updateContent} />
          )}
          {sectionKey === "certifications" && (
            <CertificationsSection content={content} updateContent={updateContent} />
          )}
          {sectionKey === "achievements" && (
            <AchievementsSection
              content={content} updateContent={updateContent}
              busyFieldKey={busyFieldKey} undoStack={undoStack}
              improveField={improveField} undoField={undoField}
            />
          )}
          {sectionKey === "additional_sections" && (
            <AdditionalSectionsSection content={content} updateContent={updateContent} />
          )}
        </div>

        <div className={"resume-editor-preview-pane" + (previewWidth === "two" ? " resume-preview-pane-two" : "")}>
          <div className="resume-preview-pane-header">
            <div>
              <strong>Live preview</strong>
              <p className="muted small">This is how your resume will look. Changes are updated in real-time.</p>
            </div>
            <div className="resume-preview-toggle">
              <button
                type="button"
                className={previewWidth === "single" ? "resume-preview-toggle-active" : ""}
                onClick={() => setPreviewWidth("single")}
              >
                Single page
              </button>
              <button
                type="button"
                className={previewWidth === "two" ? "resume-preview-toggle-active" : ""}
                onClick={() => setPreviewWidth("two")}
              >
                Two page
              </button>
            </div>
          </div>
          <ResumePreview content={content} />
        </div>
      </div>
    </div>
  );
}

function TextFieldWithAi({ fieldKey, label, value, onChange, context, busyFieldKey, undoStack, improveField, undoField, multiline }) {
  const Tag = multiline ? "textarea" : "input";
  return (
    <div className="field-group resume-field-with-ai">
      {label && <label>{label}</label>}
      <div className="resume-field-with-ai-row">
        <Tag
          type={multiline ? undefined : "text"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
        <FieldAiActionsMenu
          busy={busyFieldKey === fieldKey}
          disabled={!value}
          onAction={(action) => improveField(fieldKey, value, action, context, onChange)}
        />
        {undoStack[fieldKey] !== undefined && (
          <button type="button" className="btn-link" onClick={() => undoField(fieldKey, onChange)}>
            Undo
          </button>
        )}
      </div>
    </div>
  );
}

function PersonalSection({ content, updateContent }) {
  const p = content.personal || {};
  function set(key, value) {
    updateContent((prev) => ({ ...prev, personal: { ...prev.personal, [key]: value } }));
  }
  const fields = [
    ["full_name", "Full name"], ["email", "Email"], ["phone", "Phone"],
    ["city", "City"], ["country", "Country"],
    ["linkedin_url", "LinkedIn URL"], ["portfolio_url", "Portfolio URL"], ["github_url", "GitHub URL"],
  ];
  return (
    <div>
      <h2>Personal</h2>
      {fields.map(([key, label]) => (
        <div className="field-group" key={key}>
          <label>{label}</label>
          <input type="text" value={p[key] || ""} onChange={(e) => set(key, e.target.value)} />
        </div>
      ))}
    </div>
  );
}

function SummarySection({ content, updateContent, busyFieldKey, undoStack, improveField, undoField }) {
  const text = content.summary?.text || "";
  function set(value) {
    updateContent((prev) => ({ ...prev, summary: { ...prev.summary, text: value, source: "user_edited" } }));
  }
  return (
    <div>
      <h2>Summary</h2>
      <TextFieldWithAi
        fieldKey="summary"
        value={text}
        onChange={set}
        multiline
        busyFieldKey={busyFieldKey}
        undoStack={undoStack}
        improveField={improveField}
        undoField={undoField}
      />
    </div>
  );
}

function ExperienceSection({ content, updateContent, busyFieldKey, undoStack, improveField, undoField }) {
  const items = content.experience || [];

  function updateItem(idx, patch) {
    updateContent((prev) => {
      const next = [...prev.experience];
      next[idx] = { ...next[idx], ...patch };
      return { ...prev, experience: next };
    });
  }
  function removeItem(idx) {
    updateContent((prev) => ({ ...prev, experience: prev.experience.filter((_, i) => i !== idx) }));
  }
  function addItem() {
    updateContent((prev) => ({ ...prev, experience: [...prev.experience, newExperience()] }));
  }
  function addBullet(idx) {
    updateContent((prev) => {
      const next = [...prev.experience];
      next[idx] = { ...next[idx], bullets: [...(next[idx].bullets || []), newBullet()] };
      return { ...prev, experience: next };
    });
  }
  function updateBullet(idx, bulletIdx, text) {
    updateContent((prev) => {
      const next = [...prev.experience];
      const bullets = [...(next[idx].bullets || [])];
      bullets[bulletIdx] = { ...bullets[bulletIdx], text, source: "user_edited" };
      next[idx] = { ...next[idx], bullets };
      return { ...prev, experience: next };
    });
  }
  function removeBullet(idx, bulletIdx) {
    updateContent((prev) => {
      const next = [...prev.experience];
      next[idx] = { ...next[idx], bullets: next[idx].bullets.filter((_, i) => i !== bulletIdx) };
      return { ...prev, experience: next };
    });
  }

  return (
    <div>
      <h2>Experience</h2>
      <div className="repeater-list">
        {items.map((exp, idx) => (
          <div className="repeater-item" key={exp.id}>
            <div className="field-group">
              <label>Title</label>
              <input type="text" value={exp.title} onChange={(e) => updateItem(idx, { title: e.target.value })} />
            </div>
            <div className="field-group">
              <label>Employer</label>
              <input type="text" value={exp.employer} onChange={(e) => updateItem(idx, { employer: e.target.value })} />
            </div>
            <div className="field-group">
              <label>Location</label>
              <input type="text" value={exp.location} onChange={(e) => updateItem(idx, { location: e.target.value })} />
            </div>
            <div className="field-group">
              <label>Dates</label>
              <input
                type="text" placeholder="e.g. 2019 — 2023" value={exp.date_range}
                onChange={(e) => updateItem(idx, { date_range: e.target.value })}
              />
            </div>
            <label>Bullets</label>
            {(exp.bullets || []).map((b, bIdx) => (
              <div key={b.id} style={{ display: "flex", gap: "0.4rem", alignItems: "flex-start" }}>
                <div style={{ flex: 1 }}>
                  <TextFieldWithAi
                    fieldKey={`exp-${exp.id}-bullet-${b.id}`}
                    value={b.text}
                    onChange={(v) => updateBullet(idx, bIdx, v)}
                    context={`${exp.title} at ${exp.employer}`}
                    multiline
                    busyFieldKey={busyFieldKey}
                    undoStack={undoStack}
                    improveField={improveField}
                    undoField={undoField}
                  />
                </div>
                <button type="button" className="repeater-remove" onClick={() => removeBullet(idx, bIdx)}>✕</button>
              </div>
            ))}
            <button type="button" className="repeater-add btn-link" onClick={() => addBullet(idx)}>+ Add bullet</button>
            <div className="form-actions">
              <button type="button" className="repeater-remove btn-link" onClick={() => removeItem(idx)}>Remove entry</button>
            </div>
          </div>
        ))}
      </div>
      <button type="button" className="repeater-add btn-link" onClick={addItem}>+ Add experience</button>
    </div>
  );
}

function ProjectsSection({ content, updateContent, busyFieldKey, undoStack, improveField, undoField }) {
  const items = content.projects || [];

  function updateItem(idx, patch) {
    updateContent((prev) => {
      const next = [...prev.projects];
      next[idx] = { ...next[idx], ...patch };
      return { ...prev, projects: next };
    });
  }
  function removeItem(idx) {
    updateContent((prev) => ({ ...prev, projects: prev.projects.filter((_, i) => i !== idx) }));
  }
  function addItem() {
    updateContent((prev) => ({ ...prev, projects: [...prev.projects, newProject()] }));
  }
  function addBullet(idx) {
    updateContent((prev) => {
      const next = [...prev.projects];
      next[idx] = { ...next[idx], description_bullets: [...(next[idx].description_bullets || []), newBullet()] };
      return { ...prev, projects: next };
    });
  }
  function updateBullet(idx, bulletIdx, text) {
    updateContent((prev) => {
      const next = [...prev.projects];
      const bullets = [...(next[idx].description_bullets || [])];
      bullets[bulletIdx] = { ...bullets[bulletIdx], text, source: "user_edited" };
      next[idx] = { ...next[idx], description_bullets: bullets };
      return { ...prev, projects: next };
    });
  }
  function removeBullet(idx, bulletIdx) {
    updateContent((prev) => {
      const next = [...prev.projects];
      next[idx] = { ...next[idx], description_bullets: next[idx].description_bullets.filter((_, i) => i !== bulletIdx) };
      return { ...prev, projects: next };
    });
  }
  function updateTags(idx, tagsStr) {
    updateItem(idx, { tags: tagsStr.split(",").map((t) => t.trim()).filter(Boolean) });
  }

  return (
    <div>
      <h2>Projects</h2>
      <div className="repeater-list">
        {items.map((proj, idx) => (
          <div className="repeater-item" key={proj.id}>
            <div className="field-group">
              <label>Title</label>
              <input type="text" value={proj.title} onChange={(e) => updateItem(idx, { title: e.target.value })} />
            </div>
            <div className="field-group">
              <label>Link</label>
              <input type="text" value={proj.link_url || ""} onChange={(e) => updateItem(idx, { link_url: e.target.value })} />
            </div>
            <div className="field-group">
              <label>Tags (comma separated)</label>
              <input type="text" value={(proj.tags || []).join(", ")} onChange={(e) => updateTags(idx, e.target.value)} />
            </div>
            <label>Description bullets</label>
            {(proj.description_bullets || []).map((b, bIdx) => (
              <div key={b.id} style={{ display: "flex", gap: "0.4rem", alignItems: "flex-start" }}>
                <div style={{ flex: 1 }}>
                  <TextFieldWithAi
                    fieldKey={`proj-${proj.id}-bullet-${b.id}`}
                    value={b.text}
                    onChange={(v) => updateBullet(idx, bIdx, v)}
                    context={proj.title}
                    multiline
                    busyFieldKey={busyFieldKey}
                    undoStack={undoStack}
                    improveField={improveField}
                    undoField={undoField}
                  />
                </div>
                <button type="button" className="repeater-remove" onClick={() => removeBullet(idx, bIdx)}>✕</button>
              </div>
            ))}
            <button type="button" className="repeater-add btn-link" onClick={() => addBullet(idx)}>+ Add bullet</button>
            <div className="form-actions">
              <button type="button" className="repeater-remove btn-link" onClick={() => removeItem(idx)}>Remove project</button>
            </div>
          </div>
        ))}
      </div>
      <button type="button" className="repeater-add btn-link" onClick={addItem}>+ Add project</button>
    </div>
  );
}

function SkillsSection({ content, updateContent }) {
  const groups = content.skills?.groups || [];
  const dragIndexRef = useRef(null);

  function setGroups(next) {
    updateContent((prev) => ({ ...prev, skills: { ...prev.skills, groups: next, source: "user_edited" } }));
  }
  function updateGroup(idx, patch) {
    const next = [...groups];
    next[idx] = { ...next[idx], ...patch };
    setGroups(next);
  }
  function removeGroup(idx) {
    setGroups(groups.filter((_, i) => i !== idx));
  }
  function duplicateGroup(idx) {
    const next = [...groups];
    next.splice(idx + 1, 0, { ...groups[idx], skills: [...(groups[idx].skills || [])] });
    setGroups(next);
  }
  function moveGroup(from, to) {
    if (to < 0 || to >= groups.length) return;
    const next = [...groups];
    const [moved] = next.splice(from, 1);
    next.splice(to, 0, moved);
    setGroups(next);
  }
  function addGroup() {
    setGroups([...groups, newSkillGroup()]);
  }

  return (
    <div>
      <h2>Skills</h2>
      <div className="skill-group-list">
        {groups.map((g, idx) => (
          <SkillGroupCard
            key={idx}
            group={g}
            index={idx}
            total={groups.length}
            onChange={(patch) => updateGroup(idx, patch)}
            onRemove={() => removeGroup(idx)}
            onDuplicate={() => duplicateGroup(idx)}
            onMoveUp={() => moveGroup(idx, idx - 1)}
            onMoveDown={() => moveGroup(idx, idx + 1)}
            dragProps={{
              onDragStart: () => {
                dragIndexRef.current = idx;
              },
              onDragOver: (e) => e.preventDefault(),
              onDrop: (e) => {
                e.preventDefault();
                const from = dragIndexRef.current;
                if (from === null || from === idx) return;
                moveGroup(from, idx);
                dragIndexRef.current = null;
              },
            }}
          />
        ))}
      </div>
      <button type="button" className="repeater-add btn-link" onClick={addGroup}>+ Add skill group</button>
    </div>
  );
}

function EducationSection({ content, updateContent }) {
  const items = content.education || [];

  function updateItem(idx, patch) {
    updateContent((prev) => {
      const next = [...prev.education];
      next[idx] = { ...next[idx], ...patch };
      return { ...prev, education: next };
    });
  }
  function removeItem(idx) {
    updateContent((prev) => ({ ...prev, education: prev.education.filter((_, i) => i !== idx) }));
  }
  function addItem() {
    updateContent((prev) => ({ ...prev, education: [...prev.education, newEducation()] }));
  }

  return (
    <div>
      <h2>Education</h2>
      <div className="repeater-list">
        {items.map((ed, idx) => (
          <div className="repeater-item" key={ed.id}>
            <div className="field-group">
              <label>Institution</label>
              <input type="text" value={ed.institution} onChange={(e) => updateItem(idx, { institution: e.target.value })} />
            </div>
            <div className="field-group">
              <label>Degree</label>
              <input type="text" value={ed.degree} onChange={(e) => updateItem(idx, { degree: e.target.value })} />
            </div>
            <div className="field-group">
              <label>Field</label>
              <input type="text" value={ed.field} onChange={(e) => updateItem(idx, { field: e.target.value })} />
            </div>
            <div className="field-group">
              <label>Dates</label>
              <input type="text" value={ed.date_range} onChange={(e) => updateItem(idx, { date_range: e.target.value })} />
            </div>
            <button type="button" className="repeater-remove btn-link" onClick={() => removeItem(idx)}>Remove</button>
          </div>
        ))}
      </div>
      <button type="button" className="repeater-add btn-link" onClick={addItem}>+ Add education</button>
    </div>
  );
}

function CertificationsSection({ content, updateContent }) {
  const items = content.certifications || [];

  function updateItem(idx, patch) {
    updateContent((prev) => {
      const next = [...prev.certifications];
      next[idx] = { ...next[idx], ...patch };
      return { ...prev, certifications: next };
    });
  }
  function removeItem(idx) {
    updateContent((prev) => ({ ...prev, certifications: prev.certifications.filter((_, i) => i !== idx) }));
  }
  function addItem() {
    updateContent((prev) => ({ ...prev, certifications: [...prev.certifications, newCertification()] }));
  }

  return (
    <div>
      <h2>Certifications</h2>
      <div className="repeater-list">
        {items.map((c, idx) => (
          <div className="repeater-item" key={c.id || idx}>
            <div className="field-group">
              <label>Name</label>
              <input type="text" value={c.name} onChange={(e) => updateItem(idx, { name: e.target.value })} />
            </div>
            <div className="field-group">
              <label>Issuer</label>
              <input type="text" value={c.issuer || ""} onChange={(e) => updateItem(idx, { issuer: e.target.value })} />
            </div>
            <div className="field-group">
              <label>Date</label>
              <input type="text" value={c.date || ""} onChange={(e) => updateItem(idx, { date: e.target.value })} />
            </div>
            <button type="button" className="repeater-remove btn-link" onClick={() => removeItem(idx)}>Remove</button>
          </div>
        ))}
      </div>
      <button type="button" className="repeater-add btn-link" onClick={addItem}>+ Add certification</button>
    </div>
  );
}

function AchievementsSection({ content, updateContent, busyFieldKey, undoStack, improveField, undoField }) {
  const items = content.achievements || [];

  function updateItem(idx, text) {
    updateContent((prev) => {
      const next = [...prev.achievements];
      next[idx] = { ...next[idx], text, source: "user_edited" };
      return { ...prev, achievements: next };
    });
  }
  function removeItem(idx) {
    updateContent((prev) => ({ ...prev, achievements: prev.achievements.filter((_, i) => i !== idx) }));
  }
  function addItem() {
    updateContent((prev) => ({ ...prev, achievements: [...prev.achievements, newAchievement()] }));
  }

  return (
    <div>
      <h2>Achievements</h2>
      <div className="repeater-list">
        {items.map((a, idx) => (
          <div className="repeater-item" key={a.id || idx}>
            <div style={{ display: "flex", gap: "0.4rem", alignItems: "flex-start" }}>
              <div style={{ flex: 1 }}>
                <TextFieldWithAi
                  fieldKey={`achievement-${a.id || idx}`}
                  value={a.text}
                  onChange={(v) => updateItem(idx, v)}
                  multiline
                  busyFieldKey={busyFieldKey}
                  undoStack={undoStack}
                  improveField={improveField}
                  undoField={undoField}
                />
              </div>
              <button type="button" className="repeater-remove" onClick={() => removeItem(idx)}>✕</button>
            </div>
          </div>
        ))}
      </div>
      <button type="button" className="repeater-add btn-link" onClick={addItem}>+ Add achievement</button>
    </div>
  );
}

function AdditionalSectionsSection({ content, updateContent }) {
  const items = content.additional_sections || [];

  function updateItem(idx, patch) {
    updateContent((prev) => {
      const next = [...prev.additional_sections];
      next[idx] = { ...next[idx], ...patch };
      return { ...prev, additional_sections: next };
    });
  }
  function removeItem(idx) {
    updateContent((prev) => ({ ...prev, additional_sections: prev.additional_sections.filter((_, i) => i !== idx) }));
  }
  function addItem() {
    updateContent((prev) => ({ ...prev, additional_sections: [...prev.additional_sections, newAdditionalSection()] }));
  }

  return (
    <div>
      <h2>Additional Sections</h2>
      <div className="repeater-list">
        {items.map((sec, idx) => (
          <div className="repeater-item" key={sec.id}>
            <div className="field-group">
              <label>Heading</label>
              <input type="text" value={sec.heading} onChange={(e) => updateItem(idx, { heading: e.target.value })} />
            </div>
            <div className="field-group">
              <label>Items (one per line)</label>
              <textarea
                value={(sec.items || []).join("\n")}
                onChange={(e) => updateItem(idx, { items: e.target.value.split("\n") })}
              />
            </div>
            <button type="button" className="repeater-remove btn-link" onClick={() => removeItem(idx)}>Remove section</button>
          </div>
        ))}
      </div>
      <button type="button" className="repeater-add btn-link" onClick={addItem}>+ Add section</button>
    </div>
  );
}
