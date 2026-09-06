// Sehat Sathi — Auth Page (Login / Sign Up)

const SUPABASE_URL = "https://zmdcvaarifpvtunvuncc.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable__mbHS1RZ5BDr1C9hqvbEEw_hg6SNNha";

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const tabs = document.querySelectorAll(".auth-tab");
const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");
const authMessage = document.getElementById("authMessage");

const redirectTo =
  window.location.hostname === "localhost"
    ? "http://localhost:5500/chat.html"
    : "https://sehat-sathi-peach.vercel.app/chat.html";

// Redirect if already logged in
async function checkSession() {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (session) {
    window.location.href = redirectTo;
  }
}

checkSession();

// Tab switching
tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");

    const target = tab.dataset.tab;
    if (target === "login") {
      loginForm.style.display = "block";
      signupForm.style.display = "none";
    } else {
      loginForm.style.display = "none";
      signupForm.style.display = "block";
    }
    authMessage.textContent = "";
    authMessage.className = "auth-message";
  });
});

function showMessage(text, type = "error") {
  authMessage.textContent = text;
  authMessage.className = `auth-message ${type}`;
}

function setLoading(isLoading) {
  document.querySelectorAll(".auth-submit").forEach((btn) => {
    btn.disabled = isLoading;
  });
}

// Email/password login
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  setLoading(true);
  showMessage("");

  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;

  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  setLoading(false);

  if (error) {
    showMessage(error.message);
    return;
  }

  if (data.session) {
    window.location.href = redirectTo;
  }
});

// Email/password signup
signupForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  setLoading(true);
  showMessage("");

  const email = document.getElementById("signupEmail").value.trim();
  const password = document.getElementById("signupPassword").value;
  const confirm = document.getElementById("signupConfirm").value;

  if (password !== confirm) {
    showMessage("Passwords do not match.");
    setLoading(false);
    return;
  }

  if (password.length < 6) {
    showMessage("Password must be at least 6 characters.");
    setLoading(false);
    return;
  }

  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: { emailRedirectTo: redirectTo },
  });

  setLoading(false);

  if (error) {
    showMessage(error.message);
    return;
  }

  if (data.session) {
    // Auto-confirmed email
    window.location.href = redirectTo;
  } else {
    showMessage(
      "Account created! Please check your email to confirm your account.",
      "success"
    );
  }
});

// Google OAuth
async function signInWithGoogle() {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo },
  });

  if (error) {
    showMessage(error.message);
  }
}

document.getElementById("googleSignIn").addEventListener("click", signInWithGoogle);
document.getElementById("googleSignUp").addEventListener("click", signInWithGoogle);
