import React from "react";

export default function UniversalTemplateThumbnail() {
  return (
    <div className="tpl-thumb" aria-hidden="true">
      <div className="tpl-thumb-hero">
        <span className="tpl-thumb-bar tpl-thumb-bar-eyebrow" />
        <span className="tpl-thumb-bar tpl-thumb-bar-headline" />
        <span className="tpl-thumb-bar tpl-thumb-bar-headline-short" />
        <div className="tpl-thumb-ctas">
          <span className="tpl-thumb-pill tpl-thumb-pill-solid" />
          <span className="tpl-thumb-pill" />
        </div>
      </div>
      <div className="tpl-thumb-section">
        <span className="tpl-thumb-bar tpl-thumb-bar-heading" />
        <span className="tpl-thumb-bar tpl-thumb-bar-body" />
        <span className="tpl-thumb-bar tpl-thumb-bar-body tpl-thumb-bar-short" />
      </div>
      <div className="tpl-thumb-section tpl-thumb-grid">
        <span className="tpl-thumb-tile" />
        <span className="tpl-thumb-tile" />
        <span className="tpl-thumb-tile" />
      </div>
    </div>
  );
}
