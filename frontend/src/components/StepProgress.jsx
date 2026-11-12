import React from "react";
import { motion } from "framer-motion";

export default function StepProgress({ current, total, labels }) {
  const pct = Math.min(100, Math.max(0, (current / total) * 100));

  return (
    <div className="step-progress">
      <div className="step-progress-bar">
        <motion.div
          className="step-progress-fill"
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
        />
      </div>
      {labels && (
        <div className="step-progress-labels">
          {labels.map((label, idx) => (
            <span
              key={label}
              className={
                "step-progress-label" +
                (idx + 1 === current ? " step-progress-label-active" : "") +
                (idx + 1 < current ? " step-progress-label-done" : "")
              }
            >
              {label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
