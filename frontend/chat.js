// Sehat Sathi — Chat Page Logic (with per-user memory in localStorage)

const API_URL = "http://127.0.0.1:8000";

const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");
const suggestionsEl = document.getElementById("suggestions");
const sessionListEl = document.getElementById("sessionList");
const newChatBtn = document.getElementById("newChatBtn");
const clearBtn = document.getElementById("clearBtn");

// ================= Memory Layer (localStorage) =================

const MEMORY_KEY = "sehat_sessions";
const CURRENT_KEY = "sehat_current_session";

function loadSessions() {
  try {
    return JSON.parse(localStorage.getItem(MEMORY_KEY)) || [];
  } catch {
    return [];
  }
}

function saveSessions(sessions) {
  localStorage.setItem(MEMORY_KEY, JSON.stringify(sessions));
}

function currentSessionId() {
  return localStorage.getItem(CURRENT_KEY);
}

function setCurrentSessionId(id) {
  localStorage.setItem(CURRENT_KEY, id);
}

function getCurrentSession(sessions) {
  const id = currentSessionId();
  return sessions.find((s) => s.id === id) || null;
}

function createSession(text) {
  const sessions = loadSessions();
  const session = {
    id: crypto.randomUUID(),
    title: text.slice(0, 40) || "New Chat",
    created: Date.now(),
    messages: [],
  };
  sessions.unshift(session);
  saveSessions(sessions);
  setCurrentSessionId(session.id);
  return session;
}

function addMessageToMemory(role, content, route, severity) {
  const sessions = loadSessions();
  const session = getCurrentSession(sessions);
  if (!session) return;

  session.messages.push({
    role,
    content,
    route: route || null,
    severity: severity || null,
    ts: Date.now(),
  });

  // Update title from first user message
  if (role === "user" && session.messages.filter((m) => m.role === "user").length === 1) {
    session.title = content.slice(0, 40);
  }

  saveSessions(sessions);
}

// ================= Renderers =================

function scrollToBottom() {
  chatEl.scrollTop = chatEl.scrollHeight;
}

function renderMessage(msg) {
  if (msg.role === "user") {
    const div = document.createElement("div");
    div.className = "msg user";
    div.textContent = msg.content;
    chatEl.appendChild(div);
    return;
  }

  const div = document.createElement("div");
  div.className = `msg bot ${msg.severity || ""}`;

  if (msg.route) {
    const badge = document.createElement("span");
    badge.className = `badge ${msg.route}`;
    badge.textContent = {
      triage: "🧭 Triage",
      health_info: "💊 Health Info",
      booking: "📅 Booking",
      general: "💬 General",
    }[msg.route] || msg.route;
    div.appendChild(badge);
    div.appendChild(document.createElement("br"));
  }

  div.appendChild(document.createTextNode(msg.content));

  if (msg.severity === "emergency") {
    const alert = document.createElement("div");
    alert.className = "emergency-box";
    alert.textContent = "📞 Call 1122 (Rescue) immediately!";
    div.appendChild(alert);
  }

  chatEl.appendChild(div);
}

function renderSession(sessions) {
  const current = currentSessionId();
  chatEl.innerHTML = "";

  const session = getCurrentSession(sessions);
  if (session && session.messages.length > 0) {
    session.messages.forEach(renderMessage);
    suggestionsEl.style.display = "none";
  } else {
    renderMessage({
      role: "bot",
      route: "general",
      content:
        "Assalam o Alaikum! 👋\n\n" +
        "Main Sehat Sathi hoon — aap ka apna health assistant.\n\n" +
        "Aap mujhse kuch bhi pooch sakte hain:\n" +
        "• Apni bimari ki alamat batayein\n" +
        "• Kisi bhi health sawal ka jawab paayein\n" +
        "• Emergency guidance lein\n\n" +
        "Neeche kuch suggestions hain, ya apna sawal type karein 👇",
      severity: null,
    });
    suggestionsEl.style.display = "flex";
  }

  scrollToBottom();
  renderSessionList(sessions, current);
}

function renderSessionList(sessions, currentId) {
  sessionListEl.innerHTML = "";
  sessions.forEach((s) => {
    const li = document.createElement("li");
    li.className = `session-item${s.id === currentId ? " active" : ""}`;
    li.innerHTML = `<span class="session-dot"></span>${escapeHtml(s.title)}`;
    li.addEventListener("click", () => {
      setCurrentSessionId(s.id);
      renderSession(loadSessions());
    });
    sessionListEl.appendChild(li);
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ================= Typing / Error =================

function addTypingIndicator() {
  const div = document.createElement("div");
  div.className = "typing";
  div.id = "typing";
  div.innerHTML = "<span></span><span></span><span></span>";
  chatEl.appendChild(div);
  scrollToBottom();
}

function removeTypingIndicator() {
  const typing = document.getElementById("typing");
  if (typing) typing.remove();
}

// ================= Send Message =================

async function sendMessage(message) {
  const text = message.trim();
  if (!text) return;

  // Ensure a session exists
  let sessions = loadSessions();
  if (!getCurrentSession(sessions)) createSession(text);
  sessions = loadSessions();

  // Show + persist user message
  renderMessage({ role: "user", content: text });
  addMessageToMemory("user", text);
  inputEl.value = "";
  inputEl.focus();
  suggestionsEl.style.display = "none";
  scrollToBottom();

  sendBtn.disabled = true;
  addTypingIndicator();

  try {
    const session = getCurrentSession(loadSessions());
    const res = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: session.id }),
    });

    if (!res.ok) throw new Error(`Server error (${res.status})`);

    const data = await res.json();
    removeTypingIndicator();

    renderMessage({
      role: "bot",
      content: data.response,
      route: data.route,
      severity: data.severity || null,
    });
    addMessageToMemory("bot", data.response, data.route, data.severity || null);
    renderSessionList(loadSessions(), currentSessionId());
  } catch (err) {
    removeTypingIndicator();
    renderMessage({
      role: "bot",
      content:
        "⚠️ Oops! Kuch masla ho gaya.\n\n" +
        "Please check karein:\n" +
        "1. Kya aap ka internet chal raha hai?\n" +
        "2. Sehat Sathi service active hai?\n\n" +
        "Thori der baad dobara try karein. Agar masla hal na ho, to baad mein aayein.",
    });
  } finally {
    sendBtn.disabled = false;
  }
}

// ================= Events =================

sendBtn.addEventListener("click", () => sendMessage(inputEl.value));

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage(inputEl.value);
});

suggestionsEl.addEventListener("click", (e) => {
  const btn = e.target.closest(".suggestion");
  if (btn) sendMessage(btn.dataset.msg);
});

newChatBtn.addEventListener("click", () => {
  const session = createSession("New Chat");
  renderSession(loadSessions());
  inputEl.focus();
});

clearBtn.addEventListener("click", () => {
  if (confirm("Saari chat history delete karein?")) {
    localStorage.removeItem(MEMORY_KEY);
    localStorage.removeItem(CURRENT_KEY);
    renderSession([]);
    suggestionsEl.style.display = "flex";
  }
});

// ================= Init =================

renderSession(loadSessions());
