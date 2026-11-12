/*
 * Floating AI Assistant chat widget, injected into published portfolio
 * sites via <script src="/api/ai-assistant-widget.js" data-slug="...">.
 * Vanilla JS, no build step, scoped under #ai-assistant-widget-root so it
 * cannot clash with the host template's styles. Ships its own dark glass
 * UI, a typing indicator while a chat call is in flight, and a tiny
 * markdown renderer (bold/italic/inline code/bullet lists) for answers.
 */
(function () {
  var scriptTag = document.currentScript;
  var slug = scriptTag.getAttribute("data-slug");
  if (!slug) return;

  var AVATAR_SVG =
    '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">' +
    '<path d="M12 2l1.8 4.6L18 8l-4.2 1.4L12 14l-1.8-4.6L6 8l4.2-1.4L12 2z" fill="#fff"/>' +
    '<path d="M19 14l.9 2.3L22 17l-2.1.7L19 20l-.9-2.3L16 17l2.1-.7L19 14z" fill="#fff" opacity=".8"/>' +
    "</svg>";

  var STYLE = [
    "#ai-assistant-widget-root{position:fixed;bottom:20px;right:20px;z-index:999999;",
    "font-family:'Plus Jakarta Sans',ui-sans-serif,system-ui,-apple-system,sans-serif;}",

    /* ---- collapsed launcher ---- */
    "#ai-assistant-widget-root .aaw-launcher{display:flex;align-items:center;gap:10px;",
    "background:#1c1829;border:1px solid rgba(255,255,255,0.09);color:#efecf9;",
    "padding:10px 18px 10px 8px;border-radius:999px;cursor:pointer;font-weight:600;",
    "font-size:14px;box-shadow:0 20px 50px -16px rgba(0,0,0,0.55);",
    "transition:transform .18s ease;border:none;}",
    "#ai-assistant-widget-root .aaw-launcher:hover{transform:translateY(-2px);}",
    "#ai-assistant-widget-root .aaw-badge{width:34px;height:34px;border-radius:50%;",
    "background:linear-gradient(135deg,#7c6af0,#9c7bf3);display:flex;align-items:center;",
    "justify-content:center;flex-shrink:0;}",
    "#ai-assistant-widget-root .aaw-badge svg{width:16px;height:16px;}",

    /* ---- panel shell ---- */
    "#ai-assistant-widget-root .aaw-panel{display:none;flex-direction:column;",
    "width:min(380px,calc(100vw - 32px));max-height:min(580px,calc(100vh - 100px));",
    "background:#15121f;border:1px solid rgba(255,255,255,0.09);border-radius:20px;",
    "box-shadow:0 30px 70px -20px rgba(0,0,0,0.55);position:absolute;bottom:0;right:0;",
    "overflow:hidden;color:#efecf9;}",
    "#ai-assistant-widget-root .aaw-panel.aaw-open{display:flex;}",

    /* ---- header ---- */
    "#ai-assistant-widget-root .aaw-head{display:flex;align-items:center;gap:10px;",
    "padding:14px 14px;border-bottom:1px solid rgba(255,255,255,0.09);",
    "background:linear-gradient(180deg,#221d33,#1c1829);flex-shrink:0;}",
    "#ai-assistant-widget-root .aaw-avatar{width:36px;height:36px;border-radius:11px;",
    "background:linear-gradient(135deg,#7c6af0,#9c7bf3);display:flex;align-items:center;",
    "justify-content:center;flex-shrink:0;}",
    "#ai-assistant-widget-root .aaw-avatar svg{width:17px;height:17px;}",
    "#ai-assistant-widget-root .aaw-id{flex:1;min-width:0;}",
    "#ai-assistant-widget-root .aaw-id strong{display:block;font-size:14.5px;font-weight:700;",
    "letter-spacing:-0.005em;color:#efecf9;overflow:hidden;text-overflow:ellipsis;",
    "white-space:nowrap;}",
    "#ai-assistant-widget-root .aaw-id span{display:flex;align-items:center;gap:6px;",
    "color:#938dac;font-size:11.5px;margin-top:2px;}",
    "#ai-assistant-widget-root .aaw-live-dot{width:6px;height:6px;border-radius:50%;",
    "background:#5fe6a3;box-shadow:0 0 0 0 rgba(95,230,163,.6);",
    "animation:aaw-pulse 2.2s infinite;flex-shrink:0;}",
    "@keyframes aaw-pulse{0%{box-shadow:0 0 0 0 rgba(95,230,163,.55);}",
    "70%{box-shadow:0 0 0 6px rgba(95,230,163,0);}100%{box-shadow:0 0 0 0 rgba(95,230,163,0);}}",
    "#ai-assistant-widget-root .aaw-close{appearance:none;border:none;background:transparent;",
    "color:#938dac;width:28px;height:28px;border-radius:8px;display:flex;align-items:center;",
    "justify-content:center;cursor:pointer;flex-shrink:0;}",
    "#ai-assistant-widget-root .aaw-close:hover{background:rgba(255,255,255,0.09);color:#efecf9;}",

    /* ---- messages ---- */
    "#ai-assistant-widget-root .aaw-messages{flex:1;overflow-y:auto;padding:14px;",
    "display:flex;flex-direction:column;gap:12px;min-height:120px;}",
    "#ai-assistant-widget-root .aaw-row{display:flex;flex-direction:column;max-width:86%;}",
    "#ai-assistant-widget-root .aaw-row.aaw-user{align-self:flex-end;align-items:flex-end;}",
    "#ai-assistant-widget-root .aaw-row.aaw-bot{align-self:flex-start;align-items:flex-start;}",
    "#ai-assistant-widget-root .aaw-meta{display:flex;align-items:center;gap:6px;",
    "font-size:10.5px;color:#938dac;margin-bottom:4px;font-weight:600;letter-spacing:0.01em;}",
    "#ai-assistant-widget-root .aaw-meta .aaw-ava{width:16px;height:16px;border-radius:50%;",
    "display:flex;align-items:center;justify-content:center;flex-shrink:0;}",
    "#ai-assistant-widget-root .aaw-meta .aaw-ava svg{width:9px;height:9px;}",
    "#ai-assistant-widget-root .aaw-row.aaw-bot .aaw-ava{background:linear-gradient(135deg,#7c6af0,#9c7bf3);}",
    "#ai-assistant-widget-root .aaw-row.aaw-user .aaw-ava{background:#4b4560;",
    "font-family:ui-monospace,monospace;font-size:8px;color:#fff;}",
    "#ai-assistant-widget-root .aaw-bubble{padding:9px 12px;border-radius:14px;",
    "font-size:13.5px;line-height:1.5;}",
    "#ai-assistant-widget-root .aaw-row.aaw-user .aaw-bubble{",
    "background:linear-gradient(135deg,#7c6af0,#9c7bf3);color:#fff;",
    "border-radius:14px 14px 4px 14px;}",
    "#ai-assistant-widget-root .aaw-row.aaw-bot .aaw-bubble{background:#262233;color:#efecf9;",
    "border:1px solid rgba(255,255,255,0.09);border-radius:14px 14px 14px 4px;}",
    "#ai-assistant-widget-root .aaw-bubble p{margin:0 0 8px;}",
    "#ai-assistant-widget-root .aaw-bubble p:last-child{margin-bottom:0;}",
    "#ai-assistant-widget-root .aaw-bubble strong{color:#d9d4f7;font-weight:700;}",
    "#ai-assistant-widget-root .aaw-row.aaw-user .aaw-bubble strong{color:#fff;}",
    "#ai-assistant-widget-root .aaw-bubble code{background:rgba(255,255,255,0.1);",
    "padding:1.5px 5px;border-radius:5px;font-family:ui-monospace,monospace;font-size:12px;}",
    "#ai-assistant-widget-root .aaw-bubble ul{margin:4px 0 8px;padding-left:18px;}",
    "#ai-assistant-widget-root .aaw-bubble li{margin-bottom:4px;}",
    "#ai-assistant-widget-root .aaw-bubble li::marker{color:#8172f2;}",

    /* ---- typing indicator ---- */
    "#ai-assistant-widget-root .aaw-typing{display:inline-flex;gap:4px;padding:11px 13px;",
    "background:#262233;border:1px solid rgba(255,255,255,0.09);border-radius:14px 14px 14px 4px;}",
    "#ai-assistant-widget-root .aaw-typing span{width:6px;height:6px;border-radius:50%;",
    "background:#938dac;animation:aaw-bounce 1.1s infinite ease-in-out;}",
    "#ai-assistant-widget-root .aaw-typing span:nth-child(2){animation-delay:.15s;}",
    "#ai-assistant-widget-root .aaw-typing span:nth-child(3){animation-delay:.3s;}",
    "@keyframes aaw-bounce{0%,60%,100%{transform:translateY(0);opacity:.55;}",
    "30%{transform:translateY(-4px);opacity:1;}}",

    /* ---- suggestions ---- */
    "#ai-assistant-widget-root .aaw-suggestions{display:flex;flex-wrap:wrap;gap:6px;",
    "padding:0 14px 12px;flex-shrink:0;}",
    "#ai-assistant-widget-root .aaw-chip{font-size:12px;color:#efecf9;background:#1c1829;",
    "border:1px solid rgba(255,255,255,0.09);border-radius:999px;padding:6px 11px;",
    "cursor:pointer;font-family:inherit;}",
    "#ai-assistant-widget-root .aaw-chip:hover{border-color:#8172f2;}",

    /* ---- footer / input ---- */
    "#ai-assistant-widget-root .aaw-foot{border-top:1px solid rgba(255,255,255,0.09);",
    "padding:12px 13px 11px;background:#1c1829;flex-shrink:0;}",
    "#ai-assistant-widget-root .aaw-input-row{display:flex;align-items:center;gap:8px;",
    "background:#15121f;border:1px solid rgba(255,255,255,0.09);border-radius:13px;",
    "padding:5px 5px 5px 13px;}",
    "#ai-assistant-widget-root .aaw-input{flex:1;background:transparent;border:none;",
    "outline:none;color:#efecf9;font-size:13.5px;font-family:inherit;min-width:0;}",
    "#ai-assistant-widget-root .aaw-input::placeholder{color:#938dac;}",
    "#ai-assistant-widget-root .aaw-send{width:32px;height:32px;border-radius:9px;border:none;",
    "background:linear-gradient(135deg,#7c6af0,#9c7bf3);color:#fff;display:flex;",
    "align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;}",
    "#ai-assistant-widget-root .aaw-send:disabled{opacity:.5;cursor:default;}",
    "#ai-assistant-widget-root .aaw-send svg{width:14px;height:14px;}",
    "#ai-assistant-widget-root .aaw-foot-row{display:flex;align-items:center;",
    "justify-content:flex-end;margin-top:8px;padding:0 1px;}",
    "#ai-assistant-widget-root .aaw-foot-tag{font-family:ui-monospace,monospace;font-size:9.5px;",
    "color:#938dac;letter-spacing:0.03em;}",

    /* ---- mobile: full-screen panel ---- */
    "@media (max-width:640px){",
    "#ai-assistant-widget-root{bottom:16px;right:16px;}",
    "#ai-assistant-widget-root .aaw-panel{position:fixed;inset:0;top:0;left:0;right:0;bottom:0;",
    "width:100%;height:100%;max-width:none;max-height:none;border-radius:0;border:none;}",
    "#ai-assistant-widget-root .aaw-panel.aaw-open{display:flex;}",
    "#ai-assistant-widget-root .aaw-head{padding-top:max(14px,env(safe-area-inset-top));}",
    "#ai-assistant-widget-root .aaw-messages{min-height:0;}",
    "#ai-assistant-widget-root .aaw-foot{padding-bottom:max(11px,env(safe-area-inset-bottom));}",
    "#ai-assistant-widget-root .aaw-panel.aaw-open ~ .aaw-launcher{display:none;}",
    "}",
  ].join("");

  var styleEl = document.createElement("style");
  styleEl.textContent = STYLE;
  document.head.appendChild(styleEl);

  var SEND_SVG =
    '<svg viewBox="0 0 20 20" fill="none"><path d="M3 10h13M11 4l6 6-6 6" ' +
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var CLOSE_SVG =
    '<svg viewBox="0 0 20 20" width="14" height="14" fill="none"><path d="M5 5l10 10M15 5L5 15" ' +
    'stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>';

  var root = document.createElement("div");
  root.id = "ai-assistant-widget-root";
  root.innerHTML =
    '<div class="aaw-panel" id="aaw-panel">' +
    '<div class="aaw-head">' +
    '<span class="aaw-avatar">' + AVATAR_SVG + "</span>" +
    '<div class="aaw-id">' +
    '<strong id="aaw-title">AI Portfolio Assistant</strong>' +
    '<span><span class="aaw-live-dot"></span><span id="aaw-subtitle">Connecting…</span></span>' +
    "</div>" +
    '<button class="aaw-close" id="aaw-close" aria-label="Close">' + CLOSE_SVG + "</button>" +
    "</div>" +
    '<div class="aaw-messages" id="aaw-messages"></div>' +
    '<div class="aaw-suggestions" id="aaw-suggestions"></div>' +
    '<div class="aaw-foot">' +
    '<form class="aaw-input-row" id="aaw-form">' +
    '<input class="aaw-input" id="aaw-input" type="text" placeholder="Ask about projects, skills or experience…" autocomplete="off" />' +
    '<button class="aaw-send" id="aaw-send" type="submit" aria-label="Send">' + SEND_SVG + "</button>" +
    "</form>" +
    '<div class="aaw-foot-row"><span class="aaw-foot-tag">AI ASSISTANT</span></div>' +
    "</div>" +
    "</div>" +
    '<button class="aaw-launcher" id="aaw-launcher" aria-label="Open AI Assistant">' +
    '<span class="aaw-badge">' + AVATAR_SVG + "</span>" +
    '<span id="aaw-launcher-label">Chat with AI assistant</span>' +
    "</button>";
  document.body.appendChild(root);

  var panel = root.querySelector("#aaw-panel");
  var title = root.querySelector("#aaw-title");
  var subtitle = root.querySelector("#aaw-subtitle");
  var launcherLabel = root.querySelector("#aaw-launcher-label");
  var messages = root.querySelector("#aaw-messages");
  var suggestions = root.querySelector("#aaw-suggestions");
  var form = root.querySelector("#aaw-form");
  var input = root.querySelector("#aaw-input");
  var sendBtn = root.querySelector("#aaw-send");
  var launcher = root.querySelector("#aaw-launcher");
  var closeBtn = root.querySelector("#aaw-close");

  var apiBase = "/api/public/ai-assistant/" + encodeURIComponent(slug);
  var available = false;
  var ownerName = "";
  var greeted = false;

  // ---- tiny markdown renderer: bold, italic, inline code, bullet lists ----
  function escapeHtml(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }
  function inlineMarkdown(s) {
    s = escapeHtml(s);
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    return s;
  }
  function renderMarkdown(src) {
    var lines = src.split("\n");
    var html = "";
    var inList = false;
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i].trim();
      if (/^[-*]\s+/.test(line)) {
        if (!inList) {
          html += "<ul>";
          inList = true;
        }
        html += "<li>" + inlineMarkdown(line.replace(/^[-*]\s+/, "")) + "</li>";
      } else {
        if (inList) {
          html += "</ul>";
          inList = false;
        }
        if (line.length) html += "<p>" + inlineMarkdown(line) + "</p>";
      }
    }
    if (inList) html += "</ul>";
    return html;
  }

  function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  function addUserBubble(text) {
    var row = document.createElement("div");
    row.className = "aaw-row aaw-user";
    row.innerHTML =
      '<span class="aaw-meta">You<span class="aaw-ava">YOU</span></span>' +
      '<div class="aaw-bubble">' + escapeHtml(text) + "</div>";
    messages.appendChild(row);
    scrollToBottom();
  }

  function addBotBubble(markdown) {
    var row = document.createElement("div");
    row.className = "aaw-row aaw-bot";
    row.innerHTML =
      '<span class="aaw-meta"><span class="aaw-ava">' + AVATAR_SVG + "</span>Assistant</span>" +
      '<div class="aaw-bubble">' + renderMarkdown(markdown) + "</div>";
    messages.appendChild(row);
    scrollToBottom();
  }

  function showTyping() {
    var row = document.createElement("div");
    row.className = "aaw-row aaw-bot";
    row.id = "aaw-typing-row";
    row.innerHTML =
      '<span class="aaw-meta"><span class="aaw-ava">' + AVATAR_SVG + "</span>Assistant</span>" +
      '<div class="aaw-typing"><span></span><span></span><span></span></div>';
    messages.appendChild(row);
    scrollToBottom();
  }

  function hideTyping() {
    var row = root.querySelector("#aaw-typing-row");
    if (row) row.remove();
  }

  function renderSuggestions() {
    var starters = [
      "What has " + ownerName + " built recently?",
      "What skills does " + ownerName + " have?",
      "Is " + ownerName + " open to new roles?",
    ];
    suggestions.innerHTML = "";
    starters.forEach(function (text) {
      var chip = document.createElement("button");
      chip.type = "button";
      chip.className = "aaw-chip";
      chip.textContent = text;
      chip.addEventListener("click", function () {
        suggestions.innerHTML = "";
        sendMessage(text);
      });
      suggestions.appendChild(chip);
    });
  }

  function openPanel() {
    panel.classList.add("aaw-open");
    if (available && !greeted) {
      greeted = true;
      addBotBubble(
        "Hi, I'm " + ownerName + "'s AI assistant 👋 Ask me about **projects**, **skills**, or **experience** " +
          "— I only answer from " + ownerName + "'s real profile."
      );
      renderSuggestions();
    }
    input.focus();
  }

  fetch(apiBase + "/info")
    .then(function (res) {
      if (!res.ok) throw new Error("not available");
      return res.json();
    })
    .then(function (data) {
      available = true;
      ownerName = data.owner_name;
      title.textContent = ownerName + "'s Portfolio Assistant";
      subtitle.textContent = "Answers from " + ownerName + "'s real profile";
      launcherLabel.textContent = "Chat with " + ownerName + "'s assistant";
    })
    .catch(function () {
      root.style.display = "none";
    });

  launcher.addEventListener("click", openPanel);
  closeBtn.addEventListener("click", function () {
    panel.classList.remove("aaw-open");
  });

  function sendMessage(question) {
    if (!question || !available) return;
    addUserBubble(question);
    input.value = "";
    sendBtn.disabled = true;
    showTyping();

    fetch(apiBase + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: question }),
    })
      .then(function (res) {
        if (!res.ok) throw new Error("chat failed");
        return res.json();
      })
      .then(function (data) {
        hideTyping();
        addBotBubble(data.answer);
      })
      .catch(function () {
        hideTyping();
        addBotBubble("Sorry, I couldn't answer that right now. Please try again later.");
      })
      .finally(function () {
        sendBtn.disabled = false;
        input.focus();
      });
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    sendMessage(input.value.trim());
  });
})();
