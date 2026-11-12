import React from "react";
import ImageUploadField from "./ImageUploadField";

export default function DynamicField({ question, value, onChange, idPrefix }) {
  const { key, label, type, options = [], required, placeholder } = question;
  const fieldId = idPrefix ? `${idPrefix}-${key}` : key;

  const commonLabel = (
    <label htmlFor={fieldId}>
      {label}
      {required && <span className="required-mark">*</span>}
    </label>
  );

  switch (type) {
    case "repeater": {
      const items = Array.isArray(value) ? value : [];
      const addItem = () => onChange(key, [...items, {}]);
      const removeItem = (idx) => onChange(key, items.filter((_, i) => i !== idx));
      const updateItem = (idx, k, v) =>
        onChange(key, items.map((it, i) => (i === idx ? { ...it, [k]: v } : it)));
      return (
        <div className="field-group repeater-field">
          {commonLabel}
          <div className="repeater-list">
            {items.map((item, idx) => (
              <div className="repeater-item" key={idx}>
                {question.fields.map((f) => (
                  <DynamicField
                    key={f.key}
                    question={f}
                    value={item[f.key]}
                    idPrefix={`${fieldId}-${idx}`}
                    onChange={(k, v) => updateItem(idx, k, v)}
                  />
                ))}
                <button
                  type="button"
                  className="btn-link repeater-remove"
                  onClick={() => removeItem(idx)}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
          <button type="button" className="btn-link repeater-add" onClick={addItem}>
            + Add {question.item_label || "item"}
          </button>
        </div>
      );
    }

    case "textarea":
      return (
        <div className="field-group">
          {commonLabel}
          <textarea
            id={fieldId}
            rows={4}
            placeholder={placeholder}
            value={value ?? ""}
            onChange={(e) => onChange(key, e.target.value)}
          />
        </div>
      );

    case "number":
      return (
        <div className="field-group">
          {commonLabel}
          <input
            id={fieldId}
            type="number"
            placeholder={placeholder}
            value={value ?? ""}
            onChange={(e) => onChange(key, e.target.value === "" ? "" : Number(e.target.value))}
          />
        </div>
      );

    case "email":
      return (
        <div className="field-group">
          {commonLabel}
          <input
            id={fieldId}
            type="email"
            placeholder={placeholder}
            value={value ?? ""}
            onChange={(e) => onChange(key, e.target.value)}
          />
        </div>
      );

    case "boolean":
      return (
        <div className="field-group choice-row">
          <input
            id={fieldId}
            type="checkbox"
            checked={!!value}
            onChange={(e) => onChange(key, e.target.checked)}
          />
          <label htmlFor={fieldId}>{label}</label>
        </div>
      );

    case "radio":
      return (
        <div className="field-group">
          {commonLabel}
          {options.map((opt) => (
            <div className="choice-row" key={opt}>
              <input
                id={`${fieldId}-${opt}`}
                type="radio"
                name={fieldId}
                checked={value === opt}
                onChange={() => onChange(key, opt)}
              />
              <label htmlFor={`${fieldId}-${opt}`}>{opt}</label>
            </div>
          ))}
        </div>
      );

    case "checkbox": {
      const selected = Array.isArray(value) ? value : [];
      return (
        <div className="field-group">
          {commonLabel}
          {options.map((opt) => (
            <div className="choice-row" key={opt}>
              <input
                id={`${fieldId}-${opt}`}
                type="checkbox"
                checked={selected.includes(opt)}
                onChange={(e) =>
                  onChange(key, e.target.checked ? [...selected, opt] : selected.filter((o) => o !== opt))
                }
              />
              <label htmlFor={`${fieldId}-${opt}`}>{opt}</label>
            </div>
          ))}
        </div>
      );
    }

    case "select":
      return (
        <div className="field-group">
          {commonLabel}
          <select id={fieldId} value={value ?? ""} onChange={(e) => onChange(key, e.target.value)}>
            <option value="" disabled>
              Select...
            </option>
            {options.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </div>
      );

    case "image":
      return (
        <div className="field-group">
          {commonLabel}
          <ImageUploadField value={value} onChange={(url) => onChange(key, url)} />
        </div>
      );

    case "color":
      return (
        <div className="field-group">
          {commonLabel}
          <input
            id={fieldId}
            type="color"
            value={value || "#4f46e5"}
            onChange={(e) => onChange(key, e.target.value)}
          />
        </div>
      );

    default:
      return (
        <div className="field-group">
          {commonLabel}
          <input
            id={fieldId}
            type="text"
            placeholder={placeholder}
            value={value ?? ""}
            onChange={(e) => onChange(key, e.target.value)}
          />
        </div>
      );
  }
}
