import React from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

function HeadingFields({ content, onChange }) {
  return (
    <input
      type="text"
      placeholder="Heading text"
      value={content.text ?? ""}
      onChange={(e) => onChange({ ...content, text: e.target.value })}
    />
  );
}

function TextFields({ content, onChange }) {
  return (
    <textarea
      rows={4}
      placeholder="Body text"
      value={content.body ?? ""}
      onChange={(e) => onChange({ ...content, body: e.target.value })}
    />
  );
}

function ImageFields({ content, onChange }) {
  return (
    <>
      <input
        type="text"
        placeholder="Image URL"
        value={content.url ?? ""}
        onChange={(e) => onChange({ ...content, url: e.target.value })}
      />
      <input
        type="text"
        placeholder="Caption (optional)"
        value={content.caption ?? ""}
        onChange={(e) => onChange({ ...content, caption: e.target.value })}
        style={{ marginTop: "0.5rem" }}
      />
    </>
  );
}

function SkillsFields({ content, onChange }) {
  const items = content.items ?? [];
  function updateItem(idx, value) {
    onChange({ ...content, items: items.map((it, i) => (i === idx ? value : it)) });
  }
  function removeItem(idx) {
    onChange({ ...content, items: items.filter((_, i) => i !== idx) });
  }
  function addItem() {
    onChange({ ...content, items: [...items, ""] });
  }
  return (
    <div>
      <div className="chip-input">
        {items.map((item, idx) => (
          <span className="chip" key={idx}>
            <input
              type="text"
              value={item}
              placeholder="Skill"
              onChange={(e) => updateItem(idx, e.target.value)}
            />
            <button type="button" className="chip-remove" onClick={() => removeItem(idx)}>
              &times;
            </button>
          </span>
        ))}
      </div>
      <button type="button" className="btn-link" onClick={addItem}>
        + Add skill
      </button>
    </div>
  );
}

function LinksFields({ content, onChange }) {
  const items = content.items ?? [];
  function updateItem(idx, field, value) {
    onChange({ ...content, items: items.map((it, i) => (i === idx ? { ...it, [field]: value } : it)) });
  }
  function removeItem(idx) {
    onChange({ ...content, items: items.filter((_, i) => i !== idx) });
  }
  function addItem() {
    onChange({ ...content, items: [...items, { label: "", url: "" }] });
  }
  return (
    <div>
      {items.map((item, idx) => (
        <div className="link-row" key={idx}>
          <input
            type="text"
            placeholder="Label"
            value={item.label ?? ""}
            onChange={(e) => updateItem(idx, "label", e.target.value)}
          />
          <input
            type="text"
            placeholder="URL"
            value={item.url ?? ""}
            onChange={(e) => updateItem(idx, "url", e.target.value)}
          />
          <button type="button" className="chip-remove" onClick={() => removeItem(idx)}>
            &times;
          </button>
        </div>
      ))}
      <button type="button" className="btn-link" onClick={addItem}>
        + Add link
      </button>
    </div>
  );
}

const FIELDS_BY_TYPE = {
  heading: HeadingFields,
  text: TextFields,
  image: ImageFields,
  skills: SkillsFields,
  links: LinksFields,
};

const LABEL_BY_TYPE = {
  heading: "Heading",
  text: "Text",
  image: "Image",
  skills: "Skills",
  links: "Links",
};

export default function BlockRenderer({ block, onChange, onDelete }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: block.id });
  const style = { transform: CSS.Transform.toString(transform), transition };

  const Fields = FIELDS_BY_TYPE[block.type];

  return (
    <div className="block-item" ref={setNodeRef} style={style}>
      <div className="block-item-header">
        <button type="button" className="block-drag-handle" {...attributes} {...listeners}>
          ⠿
        </button>
        <span className="block-type-label">{LABEL_BY_TYPE[block.type] ?? block.type}</span>
        <button type="button" className="block-delete" onClick={() => onDelete(block.id)}>
          Delete
        </button>
      </div>
      <div className="block-item-body">
        {Fields ? (
          <Fields content={block.content} onChange={(content) => onChange(block.id, content)} />
        ) : (
          <p className="muted">Unknown block type.</p>
        )}
      </div>
    </div>
  );
}
