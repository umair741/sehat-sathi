// Sehat Sathi — Chat Page Logic (Supabase auth + API-backed conversations)

const API_URL = "https://sehat-sathi-production-32ce.up.railway.app";
const SUPABASE_URL = "https://zmdcvaarifpvtunvuncc.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable__mbHS1RZ5BDr1C9hqvbEEw_hg6SNNha";

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");
const suggestionsEl = document.getElementById("suggestions");
const sessionListEl = document.getElementById("sessionList");
const newChatBtn = document.getElementById("newChatBtn");
const clearBtn = document.getElementById("clearBtn");
const userCard = document.getElementById("userCard");
const userName = document.getElementById("userName");
const userEmail = document.getElementById("userEmail");
const logoutBtn = document.getElementById("logoutBtn");

let accessToken = null;
let currentUser = null;
let currentConversationId = null;
let conversations = [];

// ================= Auth =================

async function initAuth() {
  const {
    data: { session },
    error,
  } = await supabase.auth.getSession();

  if (error || !session) {
    window.location.href = "auth.html";
    return;
  }

  accessToken = session.access_token;
  currentUser = session.user;

  // Display user info
  userCard.style.display = "flex";
  logoutBtn.style.display = "block";
  userName.textContent = currentUser.user_metadata?.full_name || currentUser.email?.split("@")[0] || "User";
  userEmail.textContent = currentUser.email || "";

  // Listen for auth changes
  supabase.auth.onAuthStateChange((event, session) => {
    if (event === "SIGNED_OUT" || !session) {
      window.location.href = "index.html";
    }
  });

  await loadConversations();
  startNewChat();
}

async function logout() {
  await supabase.auth.signOut();
  window.location.href = "auth.html";
}

logoutBtn.addEventListener("click", logout);

// ================= API Helpers =================

async function apiGet(path) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

// ================= Conversations =================

async function loadConversations() {
  try {
    conversations = await apiGet("/auth/conversations");
  } catch (err) {
    console.error("Failed to load conversations", err);
    conversations = [];
  }
  renderSessionList();
}

async function loadConversationMessages(conversationId) {
  currentConversationId = conversationId;
  renderSessionList();

  try {
    const messages = await apiGet(`/auth/conversations/${conversationId}/messages`);
    chatEl.innerHTML = "";
    suggestionsEl.style.display = "none";

    if (messages.length === 0) {
      renderWelcome();
    } else {
      messages.forEach((m) =>
        renderMessage({
          role: m.role,
          content: m.content,
          route: m.route,
          severity: m.severity,
        })
      );
    }

    scrollToBottom();
  } catch (err) {
    console.error("Failed to load messages", err);
    renderError("⚠️ Could not load conversation history.");
  }
}

function startNewChat() {
  currentConversationId = null;
  chatEl.innerHTML = "";
  suggestionsEl.style.display = "flex";
  renderWelcome();
  renderSessionList();
  inputEl.value = "";
  inputEl.focus();
}

// ================= Renderers =================

function renderWelcome() {
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
    alert.textContent = "📞 Foran 1122 (Rescue) par call karein!";
    div.appendChild(alert);
  }

  chatEl.appendChild(div);
}

function renderSessionList() {
  sessionListEl.innerHTML = "";

  conversations.forEach((c) => {
    const li = document.createElement("li");
    li.className = `session-item${c.id === currentConversationId ? " active" : ""}`;
    li.innerHTML = `<span class="session-dot"></span>${escapeHtml(c.title)}`;
    li.addEventListener("click", () => loadConversationMessages(c.id));
    sessionListEl.appendChild(li);
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function renderError(text) {
  renderMessage({ role: "bot", content: text, severity: null, route: null });
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

// ================= Booking Flow =================

function renderBookingMessage(booking) {
  // Render the text reply first (same as a normal bot message)
  renderMessage({
    role: "bot",
    content: booking.message,
    route: "booking",
    severity: null,
  });

  // Then attach interactive UI based on the booking stage
  if (booking.stage === "need_facility" && booking.facilities) {
    renderOptionCards(booking.facilities, "facility");
  } else if (booking.stage === "need_doctor" && booking.doctors) {
    renderOptionCards(booking.doctors, "doctor");
  } else if (booking.stage === "need_slot" && booking.slots) {
    renderSlotGrid(booking.slots);
  } else if (booking.stage === "booked" && booking.booking) {
    renderBookingSuccess(booking);
  }
}

function renderOptionCards(items, kind) {
  const wrapper = document.createElement("div");
  wrapper.className = "option-cards";

  items.forEach((item) => {
    const card = document.createElement("button");
    card.className = "option-card";

    if (kind === "facility") {
      card.innerHTML = `
        <span class="card-icon">🏥</span>
        <span class="card-body">
          <span class="card-title">${escapeHtml(item.name)}</span>
          <span class="card-sub">${escapeHtml(item.type)} · ${escapeHtml(item.address || item.district || "")}</span>
        </span>`;
    } else {
      card.innerHTML = `
        <span class="card-icon">👨\u200d⚕️</span>
        <span class="card-body">
          <span class="card-title">${escapeHtml(item.name)}</span>
          <span class="card-sub">${escapeHtml(item.specialty || "General Physician")} · ${escapeHtml(item.qualification || "")}</span>
        </span>`;
    }

    // Clicking a card = user typing that name as a chat message
    card.addEventListener("click", () => sendMessage(item.name));
    wrapper.appendChild(card);
  });

  chatEl.appendChild(wrapper);
  scrollToBottom();
}

function renderSlotGrid(slots) {
  const wrapper = document.createElement("div");
  wrapper.className = "slot-grid";

  slots.forEach((s) => {
    const btn = document.createElement("button");
    btn.className = "slot-btn";
    btn.textContent = s.time;
    btn.disabled = !s.available;
    if (!s.available) btn.classList.add("taken");

    // Clicking a slot = user typing that time as a chat message
    btn.addEventListener("click", () => sendMessage(s.time));
    wrapper.appendChild(btn);
  });

  chatEl.appendChild(wrapper);
  scrollToBottom();
}

function renderBookingSuccess(booking) {
  const b = booking.booking;
  const div = document.createElement("div");
  div.className = "booking-success";
  div.innerHTML = `
    <div class="success-icon">✅</div>
    <div class="success-title">Appointment Booked!</div>
    <div class="token-box">Token: <strong>${escapeHtml(b.token)}</strong></div>
    <div class="success-details">
      <div>🏥 ${escapeHtml(booking.facility?.name || "")}</div>
      <div>👨\u200d⚕️ ${escapeHtml(booking.doctor?.name || "")}</div>
      <div>📅 ${escapeHtml(booking.requested_date || "")} · 🕐 ${escapeHtml(booking.slot || "")}</div>
    </div>
    <button class="copy-token-btn" onclick="navigator.clipboard.writeText('${escapeHtml(b.token)}')">📋 Copy Token</button>
  `;
  chatEl.appendChild(div);
  scrollToBottom();
}

function disableOldOptionCards() {
  document.querySelectorAll(".option-card").forEach((btn) => {
    btn.disabled = true;
    btn.classList.add("disabled");
  });
  document.querySelectorAll(".slot-btn").forEach((btn) => {
    btn.disabled = true;
    btn.classList.add("disabled");
  });
}

// ================= Send Message =================

async function sendMessage(message) {
  const text = message.trim();
  if (!text) return;

  // Ensure we left the welcome state
  if (chatEl.children.length === 0) {
    renderWelcome();
  }

  // Booking cards are only valid until the next message
  disableOldOptionCards();

  // Show user message
  renderMessage({ role: "user", content: text });
  inputEl.value = "";
  inputEl.focus();
  suggestionsEl.style.display = "none";
  scrollToBottom();

  sendBtn.disabled = true;
  addTypingIndicator();

  try {
    const payload = { message: text };
    if (currentConversationId) {
      payload.session_id = currentConversationId;
    }

    const data = await apiPost("/chat", payload);
    removeTypingIndicator();

    if (data.route === "booking" && data.booking) {
      renderBookingMessage(data.booking);
    } else {
      renderMessage({
        role: "bot",
        content: data.response,
        route: data.route,
        severity: data.severity || null,
      });
    }

    // Update conversation id from backend
    if (data.session_id && !currentConversationId) {
      currentConversationId = data.session_id;
      // Optimistically add the new conversation so it appears instantly
      const newConversation = {
        id: data.session_id,
        title: text.length > 60 ? text.slice(0, 60) + "..." : text,
      };
      conversations = [newConversation, ...conversations.filter((c) => c.id !== data.session_id)];
      renderSessionList();
      await loadConversations();
    }
  } catch (err) {
    removeTypingIndicator();
    renderMessage({
      role: "bot",
      content:
        "⚠️ Oops! Kuch masla ho gaya.\n\n" +
        "Please check karein:\n" +
        "1. Kya aap ka internet chal raha hai?\n" +
        "2. Sehat Sathi service active hai?\n\n" +
        "Thori der baad dobara try karein.",
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

newChatBtn.addEventListener("click", startNewChat);

clearBtn.addEventListener("click", async () => {
  if (confirm("Saari chat history delete karein?")) {
    currentConversationId = null;
    await loadConversations();
    startNewChat();
  }
});

// ================= Init =================

initAuth();
