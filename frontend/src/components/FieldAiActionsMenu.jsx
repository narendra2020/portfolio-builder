import React, { useState, useRef, useEffect } from "react";
import { IMPROVE_FIELD_ACTIONS } from "../pages/resume/resumeContent";

// Dropdown of AI rewrite actions for a single text field. Calls onAction(actionKey)
// and lets the caller handle the API call + accept/undo; this component is just the menu.
export default function FieldAiActionsMenu({ onAction, disabled, busy }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function onDocClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  return (
    <div className="field-ai-menu" ref={ref}>
      <button
        type="button"
        className="field-ai-menu-trigger"
        disabled={disabled || busy}
        onClick={() => setOpen((v) => !v)}
        title="AI actions"
      >
        {busy ? "..." : "✦"}
      </button>
      {open && (
        <div className="field-ai-menu-list">
          {IMPROVE_FIELD_ACTIONS.map((action) => (
            <button
              key={action.key}
              type="button"
              className="field-ai-menu-item"
              onClick={() => {
                setOpen(false);
                onAction(action.key);
              }}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
