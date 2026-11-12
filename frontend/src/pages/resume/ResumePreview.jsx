import React from "react";

// Lightweight live preview — approximates the PDF templates' content/order,
// not pixel parity with WeasyPrint output (that's the real export).
export default function ResumePreview({ content }) {
  const p = content.personal || {};
  const links = [p.linkedin_url, p.portfolio_url, p.github_url].filter(Boolean);

  return (
    <div className="resume-preview">
      <div className="resume-preview-header">
        <h2>{p.full_name || "Your Name"}</h2>
        <p className="muted small">
          {[p.email, p.phone, p.city, p.country].filter(Boolean).join(" · ") || "Contact details"}
        </p>
        {links.length > 0 && <p className="muted small">{links.join(" · ")}</p>}
      </div>

      {content.summary?.text && (
        <div className="resume-preview-section">
          <h3>Summary</h3>
          <p>{content.summary.text}</p>
        </div>
      )}

      {content.experience?.length > 0 && (
        <div className="resume-preview-section">
          <h3>Experience</h3>
          {content.experience.map((exp) => (
            <div key={exp.id} className="resume-preview-entry">
              <div className="resume-preview-entry-head">
                <strong>{exp.title || "Title"}{exp.employer ? ` — ${exp.employer}` : ""}</strong>
                <span className="muted small">{exp.date_range || [exp.start_date, exp.end_date].filter(Boolean).join(" – ")}</span>
              </div>
              {exp.location && <p className="muted small">{exp.location}</p>}
              <ul>
                {(exp.bullets || []).map((b) => <li key={b.id}>{b.text}</li>)}
              </ul>
            </div>
          ))}
        </div>
      )}

      {content.projects?.length > 0 && (
        <div className="resume-preview-section">
          <h3>Projects</h3>
          {content.projects.map((proj) => (
            <div key={proj.id} className="resume-preview-entry">
              <strong>{proj.title || "Project"}</strong>
              <ul>
                {(proj.description_bullets || []).map((b) => <li key={b.id}>{b.text}</li>)}
              </ul>
              {proj.tags?.length > 0 && <p className="muted small">{proj.tags.join(", ")}</p>}
            </div>
          ))}
        </div>
      )}

      {content.skills?.groups?.length > 0 && (
        <div className="resume-preview-section">
          <h3>Skills</h3>
          {content.skills.groups.map((g, idx) => (
            <p key={idx}><strong>{g.title}:</strong> {g.skills.join(", ")}</p>
          ))}
        </div>
      )}

      {content.education?.length > 0 && (
        <div className="resume-preview-section">
          <h3>Education</h3>
          {content.education.map((ed) => (
            <div key={ed.id} className="resume-preview-entry">
              <div className="resume-preview-entry-head">
                <strong>{ed.institution || "Institution"}</strong>
                <span className="muted small">{ed.date_range || [ed.start_date, ed.end_date].filter(Boolean).join(" – ")}</span>
              </div>
              <p className="muted small">{[ed.degree, ed.field].filter(Boolean).join(", ")}</p>
            </div>
          ))}
        </div>
      )}

      {content.certifications?.length > 0 && (
        <div className="resume-preview-section">
          <h3>Certifications</h3>
          <ul>
            {content.certifications.map((c) => (
              <li key={c.id || c.name}>{[c.name, c.issuer, c.date].filter(Boolean).join(" — ")}</li>
            ))}
          </ul>
        </div>
      )}

      {content.achievements?.length > 0 && (
        <div className="resume-preview-section">
          <h3>Achievements</h3>
          <ul>
            {content.achievements.map((a, idx) => <li key={a.id || idx}>{a.text}</li>)}
          </ul>
        </div>
      )}

      {content.additional_sections?.length > 0 && content.additional_sections.map((sec) => (
        <div key={sec.id} className="resume-preview-section">
          <h3>{sec.heading || "Additional"}</h3>
          <ul>
            {(sec.items || []).map((item, idx) => <li key={idx}>{item}</li>)}
          </ul>
        </div>
      ))}
    </div>
  );
}
