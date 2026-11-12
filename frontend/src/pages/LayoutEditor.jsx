import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { SortableContext, arrayMove, verticalListSortingStrategy } from "@dnd-kit/sortable";
import client from "../api/client";
import BlockRenderer from "../components/blocks/BlockRenderer";

const DEFAULT_CONTENT = {
  heading: { text: "" },
  text: { body: "" },
  image: { url: "", caption: "" },
  skills: { items: [] },
  links: { items: [] },
};

const BLOCK_TYPES = [
  { type: "heading", label: "Heading" },
  { type: "text", label: "Text" },
  { type: "image", label: "Image" },
  { type: "skills", label: "Skills" },
  { type: "links", label: "Links" },
];

export default function LayoutEditor() {
  const navigate = useNavigate();
  const [blocks, setBlocks] = useState(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState(null);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  useEffect(() => {
    client
      .get("/layout")
      .then((res) => setBlocks(res.data.blocks))
      .catch((err) => setError(err.response?.data?.detail || "Could not load your layout."));
  }, []);

  function addBlock(type) {
    setBlocks((prev) => [
      ...prev,
      { id: crypto.randomUUID(), type, content: { ...DEFAULT_CONTENT[type] } },
    ]);
  }

  function updateBlockContent(id, content) {
    setBlocks((prev) => prev.map((b) => (b.id === id ? { ...b, content } : b)));
  }

  function deleteBlock(id) {
    setBlocks((prev) => prev.filter((b) => b.id !== id));
  }

  function handleDragEnd(event) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    setBlocks((prev) => {
      const oldIndex = prev.findIndex((b) => b.id === active.id);
      const newIndex = prev.findIndex((b) => b.id === over.id);
      return arrayMove(prev, oldIndex, newIndex);
    });
  }

  async function save() {
    setError("");
    setSaving(true);
    try {
      await client.put("/layout", { blocks });
      setSavedAt(new Date());
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save your layout.");
    } finally {
      setSaving(false);
    }
  }

  if (error && !blocks) {
    return (
      <div className="card">
        <p className="error-text">{error}</p>
      </div>
    );
  }

  if (!blocks) {
    return (
      <div className="card">
        <p className="muted">Loading your layout...</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h1>Edit your layout</h1>
      <p className="muted">Add blocks, drag to reorder, and edit their content.</p>
      {error && <p className="error-text">{error}</p>}

      <div className="block-palette">
        {BLOCK_TYPES.map((bt) => (
          <button key={bt.type} type="button" className="btn-link" onClick={() => addBlock(bt.type)}>
            + {bt.label}
          </button>
        ))}
      </div>

      {blocks.length === 0 ? (
        <p className="muted" style={{ marginTop: "1rem" }}>
          No blocks yet — add one above.
        </p>
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={blocks.map((b) => b.id)} strategy={verticalListSortingStrategy}>
            <div className="block-list">
              {blocks.map((block) => (
                <BlockRenderer
                  key={block.id}
                  block={block}
                  onChange={updateBlockContent}
                  onDelete={deleteBlock}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}

      <div className="form-actions">
        <button className="btn-link" onClick={() => navigate("/dashboard")}>
          Back to dashboard
        </button>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {savedAt && <span className="muted small">Saved</span>}
          <button className="btn btn-primary" disabled={saving} onClick={save}>
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
