import React, { useState } from "react";

const DRAG_ICON = (
  <svg viewBox="0 0 24 24" fill="currentColor"><circle cx="9" cy="6" r="1.4" /><circle cx="15" cy="6" r="1.4" /><circle cx="9" cy="12" r="1.4" /><circle cx="15" cy="12" r="1.4" /><circle cx="9" cy="18" r="1.4" /><circle cx="15" cy="18" r="1.4" /></svg>
);
const COPY_ICON = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="8" y="8" width="12" height="12" rx="2" /><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" /></svg>
);
const TRASH_ICON = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2m-9 0 1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13" /></svg>
);
const CHEVRON_ICON = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M18 15l-6-6-6 6" /></svg>
);

export default function SkillGroupCard({
  group, index, total, onChange, onRemove, onDuplicate, onMoveUp, onMoveDown, dragProps,
}) {
  const [collapsed, setCollapsed] = useState(false);
  const [draft, setDraft] = useState("");

  function addSkill(text) {
    const value = text.trim();
    if (!value) return;
    onChange({ skills: [...(group.skills || []), value] });
    setDraft("");
  }
  function removeSkill(idx) {
    onChange({ skills: group.skills.filter((_, i) => i !== idx) });
  }

  return (
    <div className="skill-group-card" {...dragProps}>
      <div className="skill-group-card-header">
        <button
          type="button"
          className="skill-group-drag-handle"
          title="Drag to reorder"
          draggable
          onDragStart={dragProps?.onDragStart}
        >
          {DRAG_ICON}
        </button>
        <input
          type="text"
          className="skill-group-title-input"
          placeholder="Group title"
          value={group.title}
          onChange={(e) => onChange({ title: e.target.value })}
        />
        <div className="skill-group-card-actions">
          <button type="button" className="icon-btn-sm" title="Move up" disabled={index === 0} onClick={onMoveUp}>↑</button>
          <button type="button" className="icon-btn-sm" title="Move down" disabled={index === total - 1} onClick={onMoveDown}>↓</button>
          <button type="button" className="icon-btn-sm" title="Duplicate group" onClick={onDuplicate}>{COPY_ICON}</button>
          <button type="button" className="icon-btn-sm icon-btn-sm-danger" title="Delete group" onClick={onRemove}>{TRASH_ICON}</button>
          <button
            type="button"
            className={"icon-btn-sm skill-group-collapse-toggle" + (collapsed ? " skill-group-collapse-toggle-collapsed" : "")}
            title={collapsed ? "Expand" : "Collapse"}
            onClick={() => setCollapsed((v) => !v)}
          >
            {CHEVRON_ICON}
          </button>
        </div>
      </div>

      {!collapsed && (
        <div className="skill-group-card-body">
          <label>Skills (comma separated or add individually)</label>
          <div className="skill-tag-input-row">
            <input
              type="text"
              placeholder="Type a skill and press Enter"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  draft.split(",").forEach((part) => addSkill(part));
                }
              }}
            />
            <button type="button" className="btn btn-primary skill-tag-add-btn" onClick={() => draft.split(",").forEach((part) => addSkill(part))}>
              + Add
            </button>
          </div>
          <div className="skill-pill-row">
            {(group.skills || []).map((s, idx) => (
              <span className="skill-pill" key={`${s}-${idx}`}>
                {s}
                <button type="button" className="skill-pill-remove" onClick={() => removeSkill(idx)}>✕</button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
