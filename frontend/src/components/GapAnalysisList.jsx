import React from "react";

// Renders JD-vs-resume skill gaps. Backend guarantees the literal wording
// "Not found in current resume" for anything not confirmed in the resume —
// never implies the user has an unverified skill, so we render status as-is.
export default function GapAnalysisList({ gaps }) {
  if (!gaps || gaps.length === 0) {
    return <p className="muted small">No gaps identified.</p>;
  }

  return (
    <ul className="gap-analysis-list">
      {gaps.map((gap, idx) => {
        const isGap = gap.status === "Not found in current resume";
        return (
          <li key={idx} className={isGap ? "gap-analysis-item gap-analysis-item-missing" : "gap-analysis-item"}>
            <span className="gap-analysis-skill">{gap.skill}</span>
            <span className={isGap ? "gap-analysis-status error-text" : "gap-analysis-status success-text"}>
              {gap.status}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
