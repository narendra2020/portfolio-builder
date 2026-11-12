import React from "react";

export default function ScoreBar({ label, score, note }) {
  const pct = Math.min(100, Math.max(0, score ?? 0));
  const level = pct >= 80 ? "good" : pct >= 50 ? "fair" : "weak";

  return (
    <div className="score-bar">
      <div className="score-bar-header">
        <span className="score-bar-label">{label}</span>
        <span className={`score-bar-value score-bar-value-${level}`}>{pct}</span>
      </div>
      <div className="score-bar-track">
        <div className={`score-bar-fill score-bar-fill-${level}`} style={{ width: `${pct}%` }} />
      </div>
      {note && <p className="muted small score-bar-note">{note}</p>}
    </div>
  );
}
