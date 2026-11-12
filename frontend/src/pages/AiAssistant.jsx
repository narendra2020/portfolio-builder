import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import client from "../api/client";

const SPARKLE_AVATAR = (
  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2l1.8 4.6L18 8l-4.2 1.4L12 14l-1.8-4.6L6 8l4.2-1.4L12 2z" fill="#fff" />
    <path d="M19 14l.9 2.3L22 17l-2.1.7L19 20l-.9-2.3L16 17l2.1-.7L19 14z" fill="#fff" opacity="0.8" />
  </svg>
);

const PREVIEW_ANSWER =
  "Based on this portfolio, they've recently shipped a few **production features**, including work with " +
  "`React` and `Node.js` — ask me anything specific and I'll answer from their profile and Q&A.";

export default function AiAssistant() {
  const [status, setStatus] = useState(null);
  const [limits, setLimits] = useState(null);
  const [qaPairs, setQaPairs] = useState([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const [enabled, setEnabled] = useState(false);
  const [useProfileData, setUseProfileData] = useState(true);

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [adding, setAdding] = useState(false);

  const [publishStatus, setPublishStatus] = useState(null);
  const [republishing, setRepublishing] = useState(false);
  const [republishMessage, setRepublishMessage] = useState("");

  function load() {
    Promise.all([
      client.get("/ai-assistant/status"),
      client.get("/ai-assistant/limits"),
      client.get("/publish"),
    ])
      .then(([statusRes, limitsRes, publishRes]) => {
        setStatus(statusRes.data);
        setLimits(limitsRes.data);
        setEnabled(statusRes.data.config.enabled);
        setUseProfileData(statusRes.data.config.use_profile_data);
        setPublishStatus(publishRes.data);
        if (statusRes.data.entitled) {
          client.get("/ai-assistant/qa-pairs").then((res) => setQaPairs(res.data));
        }
      })
      .catch((err) => setError(err.response?.data?.detail || "Could not load AI Assistant."));
  }

  useEffect(load, []);

  async function republish() {
    setRepublishing(true);
    setRepublishMessage("");
    setError("");
    try {
      await client.post("/publish/unpublish", {});
      const res = await client.post("/publish", {});
      setPublishStatus(res.data);
      setRepublishMessage("Your portfolio has been republished with the AI Assistant.");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not republish your portfolio.");
    } finally {
      setRepublishing(false);
    }
  }

  async function saveConfig(nextEnabled, nextUseProfileData) {
    setSaving(true);
    setError("");
    try {
      const res = await client.put("/ai-assistant/config", {
        enabled: nextEnabled,
        use_profile_data: nextUseProfileData,
      });
      setEnabled(res.data.enabled);
      setUseProfileData(res.data.use_profile_data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save settings.");
    } finally {
      setSaving(false);
    }
  }

  async function addQaPair(e) {
    e.preventDefault();
    setError("");
    setAdding(true);
    try {
      const res = await client.post("/ai-assistant/qa-pairs", { question, answer });
      setQaPairs([...qaPairs, res.data]);
      setQuestion("");
      setAnswer("");
      setStatus((s) => ({ ...s, qa_pair_count: s.qa_pair_count + 1 }));
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add question/answer.");
    } finally {
      setAdding(false);
    }
  }

  async function removeQaPair(id) {
    setError("");
    try {
      await client.delete(`/ai-assistant/qa-pairs/${id}`);
      setQaPairs(qaPairs.filter((p) => p.id !== id));
      setStatus((s) => ({ ...s, qa_pair_count: s.qa_pair_count - 1 }));
    } catch (err) {
      setError(err.response?.data?.detail || "Could not remove question/answer.");
    }
  }

  if (!status || !limits) {
    return (
      <div className="card">
        <p className="muted">Loading AI Assistant...</p>
      </div>
    );
  }

  if (!status.entitled) {
    return (
      <div className="card">
        <h1>AI Assistant</h1>
        <p className="muted">
          AI Assistant isn't included in your plan.{" "}
          <Link to="/ai-assistant/upgrade">Upgrade to enable it</Link>.
        </p>
        <div className="form-actions">
          <Link to="/dashboard" className="btn-link">
            Back to dashboard
          </Link>
        </div>
      </div>
    );
  }

  const atQaPairCap = qaPairs.length >= limits.max_qa_pairs;
  const questionOverLimit = question.length > limits.question_max_length;
  const answerOverLimit = answer.length > limits.answer_max_length;

  return (
    <div className="card">
      <h1>AI Assistant</h1>
      {error && <p className="error-text">{error}</p>}

      <div className="chat-widget-preview">
        <div className="chat-widget-preview-header">
          <span className="chat-widget-avatar">{SPARKLE_AVATAR}</span>
          <div>
            AI Portfolio Assistant
            <div className="muted">Illustrative preview — not a live chat</div>
          </div>
        </div>

        <div className="chat-bubble-row chat-bubble-row-user">
          <div className="chat-bubble chat-bubble-user">What projects has this person shipped recently?</div>
        </div>

        <div className="chat-bubble-row chat-bubble-row-bot">
          <div className="chat-bubble chat-bubble-bot">
            <ReactMarkdown>{PREVIEW_ANSWER}</ReactMarkdown>
          </div>
        </div>

        <div className="chat-bubble-row chat-bubble-row-bot">
          <div className="chat-typing">
            <span />
            <span />
            <span />
          </div>
        </div>
      </div>

      <div className="field-group" style={{ marginTop: "1.5rem" }}>
        <h2>Settings</h2>
        <div className="choice-row">
          <input
            id="assistant-enabled"
            type="checkbox"
            checked={enabled}
            disabled={saving}
            onChange={(e) => saveConfig(e.target.checked, useProfileData)}
          />
          <label htmlFor="assistant-enabled">Show the AI Assistant widget on my published site</label>
        </div>
        <div className="choice-row">
          <input
            id="use-profile-data"
            type="checkbox"
            checked={useProfileData}
            disabled={saving}
            onChange={(e) => saveConfig(enabled, e.target.checked)}
          />
          <label htmlFor="use-profile-data">
            Use my profile, resume, and questionnaire answers as a knowledge source
          </label>
        </div>

        {publishStatus?.slug && (
          <div className="form-actions" style={{ marginTop: "1rem" }}>
            <button
              type="button"
              className="btn btn-primary"
              disabled={republishing}
              onClick={republish}
            >
              {republishing ? "Republishing..." : "Re-Publish with AI Assistant"}
            </button>
          </div>
        )}
        {republishMessage && <p className="muted small">{republishMessage}</p>}
      </div>

      <div className="field-group">
        <h2>Questions & answers ({qaPairs.length}/{limits.max_qa_pairs})</h2>
        <p className="muted small">
          Add specific questions and answers for the assistant to use when visitors ask about you.
        </p>

        <div className="qa-pair-list">
          {qaPairs.map((pair) => (
            <div className="qa-pair-item" key={pair.id}>
              <div className="qa-question">{pair.question}</div>
              <div className="qa-answer">{pair.answer}</div>
              <button
                type="button"
                className="repeater-remove"
                onClick={() => removeQaPair(pair.id)}
                style={{ marginTop: "0.5rem" }}
              >
                Remove
              </button>
            </div>
          ))}
        </div>

        {atQaPairCap ? (
          <p className="muted small" style={{ marginTop: "0.8rem" }}>
            You've reached the maximum of {limits.max_qa_pairs} question/answer pairs.
          </p>
        ) : (
          <form onSubmit={addQaPair} style={{ marginTop: "0.8rem" }}>
            <label htmlFor="qa-question">Question</label>
            <input
              id="qa-question"
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. What technologies do you work with?"
            />
            <div className={`char-counter ${questionOverLimit ? "char-counter-over" : ""}`}>
              {question.length}/{limits.question_max_length}
            </div>

            <label htmlFor="qa-answer">Answer</label>
            <textarea
              id="qa-answer"
              rows={3}
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="e.g. I mainly work with React, Python, and AWS."
            />
            <div className={`char-counter ${answerOverLimit ? "char-counter-over" : ""}`}>
              {answer.length}/{limits.answer_max_length}
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ marginTop: "0.6rem" }}
              disabled={
                adding ||
                !question.trim() ||
                !answer.trim() ||
                questionOverLimit ||
                answerOverLimit
              }
            >
              {adding ? "Adding..." : "Add question & answer"}
            </button>
          </form>
        )}
      </div>

      <div className="form-actions">
        <Link to="/dashboard" className="btn-link">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
