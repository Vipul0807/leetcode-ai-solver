// extension/popup.js

const API_BASE = "http://localhost:8000";

let currentCode  = "";
let selectedLang = "python";
let currentTab   = null;
let currentUrl   = "";


// ════════════════════════════════════════════════
// ON LOAD
// ════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", async () => {

  const [tab] = await chrome.tabs.query({
    active       : true,
    currentWindow: true
  });

  currentTab = tab;
  currentUrl = tab.url || "";

  if (!currentUrl.includes("leetcode.com/problems")) {
    document.getElementById("notLeetcode").style.display = "block";
    document.getElementById("mainContent").style.display = "none";
    return;
  }

  const saved = await chrome.storage.local.get("language");
  if (saved.language) {
    selectedLang = saved.language;
    updateLangButtons(selectedLang);
  }

  await restoreResults(currentUrl);
  await loadProblemInfo(currentUrl);
  setupListeners();
});


// ════════════════════════════════════════════════
// HELPERS — URL + SLUG
// ════════════════════════════════════════════════
function extractSlug(url) {
  try {
    url = url.replace(/\/$/, "");
    const afterProblems = url.split("/problems/")[1];
    if (!afterProblems) return "unknown";
    return afterProblems.split("/")[0] || "unknown";
  } catch (e) {
    return "unknown";
  }
}

function getCleanUrl(url) {
  const slug = extractSlug(url);
  return `https://leetcode.com/problems/${slug}/`;
}


// ════════════════════════════════════════════════
// SAVE RESULTS
// ════════════════════════════════════════════════
async function saveResults(url, data) {
  const cleanUrl = getCleanUrl(url);
  const key      = "result_" + btoa(cleanUrl).slice(0, 40);
  await chrome.storage.local.set({ [key]: data });
}


// ════════════════════════════════════════════════
// RESTORE RESULTS
// ════════════════════════════════════════════════
async function restoreResults(url) {
  try {
    const cleanUrl = getCleanUrl(url);
    const key      = "result_" + btoa(cleanUrl).slice(0, 40);
    const data     = await chrome.storage.local.get(key);
    if (data[key]) {
      currentCode = data[key].code;
      renderResults(data[key]);
      console.log("✅ Restored previous results");
    }
  } catch (e) {
    console.log("No saved results");
  }
}


// ════════════════════════════════════════════════
// LOAD PROBLEM INFO
// ════════════════════════════════════════════════
async function loadProblemInfo(url) {
  try {
    const info = await chrome.tabs.sendMessage(
      currentTab.id,
      { type: "GET_PROBLEM_INFO" }
    );

    if (info?.title) {
      document.getElementById("problemTitle").textContent = info.title;

      const diffBadge      = document.getElementById("diffBadge");
      diffBadge.textContent = info.difficulty || "Unknown";
      diffBadge.className   = `badge ${info.difficulty?.toLowerCase() || "easy"}`;

      if (info.language) {
        selectedLang = info.language;
        updateLangButtons(selectedLang);
        document.getElementById("langBadge").textContent =
          selectedLang.charAt(0).toUpperCase() + selectedLang.slice(1);
      }
    }

  } catch (e) {
    const slug  = extractSlug(url);
    const title = slug.split("-")
      .map(w => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
    document.getElementById("problemTitle").textContent = title || "Unknown";
  }
}


// ════════════════════════════════════════════════
// SETUP LISTENERS
// ════════════════════════════════════════════════
function setupListeners() {

  // language buttons
  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      selectedLang = btn.dataset.lang;
      updateLangButtons(selectedLang);
      const langBadge = document.getElementById("langBadge");
      if (langBadge) {
        langBadge.textContent =
          selectedLang.charAt(0).toUpperCase() + selectedLang.slice(1);
      }
      chrome.storage.local.set({ language: selectedLang });
    });
  });

  // error toggle
  const errorToggle = document.getElementById("errorToggle");
  if (errorToggle) {
    errorToggle.addEventListener("click", () => {
      const paste   = document.getElementById("errorPaste");
      const isShown = paste.classList.contains("show");
      paste.classList.toggle("show",         !isShown);
      errorToggle.classList.toggle("active", !isShown);
    });
  }

  // solve
  const solveBtn = document.getElementById("solveBtn");
  if (solveBtn) solveBtn.addEventListener("click", solve);

  // copy
  const copyBtn = document.getElementById("copyBtn");
  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      if (!currentCode) return;
      navigator.clipboard.writeText(currentCode);
      showToast("✅ Code copied!");
    });
  }

  // retry
  const retryBtn = document.getElementById("retryBtn");
  if (retryBtn) {
    retryBtn.addEventListener("click", () => {
      const cleanUrl = getCleanUrl(currentUrl);
      const key      = "result_" + btoa(cleanUrl).slice(0, 40);
      chrome.storage.local.remove(key);
      showResults(false);
      showError("");
      solve();
    });
  }

  // clear
  const clearBtn = document.getElementById("clearBtn");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      const cleanUrl = getCleanUrl(currentUrl);
      const key      = "result_" + btoa(cleanUrl).slice(0, 40);
      chrome.storage.local.remove(key);
      showResults(false);
      showError("");
      currentCode = "";
      const errorInput  = document.getElementById("errorInput");
      const errorPaste  = document.getElementById("errorPaste");
      const errorToggle = document.getElementById("errorToggle");
      if (errorInput)  errorInput.value = "";
      if (errorPaste)  errorPaste.classList.remove("show");
      if (errorToggle) errorToggle.classList.remove("active");
    });
  }

  // settings
  const settingsBtn = document.getElementById("settingsBtn");
  if (settingsBtn) {
    settingsBtn.addEventListener("click", () => {
      chrome.tabs.create({
        url: chrome.runtime.getURL("settings.html")
      });
    });
  }

  // push
  const pushBtn = document.getElementById("pushBtn");
  if (pushBtn) {
    pushBtn.addEventListener("click", pushToGitHub);
  }
}


// ════════════════════════════════════════════════
// UPDATE LANG BUTTONS
// ════════════════════════════════════════════════
function updateLangButtons(lang) {
  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.lang === lang);
  });
}


// ════════════════════════════════════════════════
// SOLVE
// ════════════════════════════════════════════════
async function solve() {

  const [tab] = await chrome.tabs.query({
    active       : true,
    currentWindow: true
  });

  currentUrl     = tab.url || currentUrl;
  const slug     = extractSlug(currentUrl);
  const cleanUrl = `https://leetcode.com/problems/${slug}/`;

  showLoading(true);
  showResults(false);
  showError("");

  const steps = [
    "Fetching problem...",
    "Generating solution...",
    "Running test cases...",
    "Checking results...",
  ];

  let stepIndex      = 0;
  const stepInterval = setInterval(() => {
    stepIndex = (stepIndex + 1) % steps.length;
    document.getElementById("loadingStep").textContent = steps[stepIndex];
  }, 2000);

  try {
    const errorInput = document.getElementById("errorInput");
    const userError  = errorInput ? errorInput.value.trim() : "";

    const res = await fetch(`${API_BASE}/solve`, {
      method  : "POST",
      headers : { "Content-Type": "application/json" },
      body    : JSON.stringify({
        url        : cleanUrl,
        language   : selectedLang,
        user_error : userError
      })
    });

    clearInterval(stepInterval);

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Server error");
    }

    const data  = await res.json();
    currentCode = data.code;

    await saveResults(cleanUrl, data);

    showLoading(false);
    renderResults(data);

  } catch (e) {
    clearInterval(stepInterval);
    showLoading(false);
    showError(`❌ ${e.message}`);
  }
}


// ════════════════════════════════════════════════
// PUSH TO GITHUB
// ════════════════════════════════════════════════
async function pushToGitHub() {
  console.log("🐙 pushToGitHub called");

  const btn = document.getElementById("pushBtn");
  if (btn) {
    btn.textContent = "⏳ Pushing...";
    btn.disabled    = true;
  }

  try {
    const settings = await chrome.storage.local.get([
      "githubToken",
      "githubUsername"
    ]);

    if (!settings.githubToken || !settings.githubUsername) {
      showPushStatus("❌ Setup GitHub first — click ⚙ Settings", "err");
      if (btn) { btn.textContent = "🐙 Push to GitHub"; btn.disabled = false; }
      return;
    }

    const cleanUrl = getCleanUrl(currentUrl);
    const key      = "result_" + btoa(cleanUrl).slice(0, 40);
    const data     = await chrome.storage.local.get(key);
    const result   = data[key];

    if (!result) {
      showPushStatus("❌ No solution found — solve first", "err");
      if (btn) { btn.textContent = "🐙 Push to GitHub"; btn.disabled = false; }
      return;
    }

    const slug = extractSlug(currentUrl);

    let difficulty = "Unknown";
    try {
      const info = await chrome.tabs.sendMessage(
        currentTab.id,
        { type: "GET_PROBLEM_INFO" }
      );
      difficulty = info?.difficulty || "Unknown";
    } catch (e) {}

    const payload = {
      token       : settings.githubToken,
      username    : settings.githubUsername,
      slug        : slug,
      title       : result.title       || slug,
      difficulty  : difficulty,
      description : "",
      examples    : result.test_results || [],
      code        : result.code,
      language    : result.language     || "python",
      attempts    : result.attempts     || 0
    };

    const res = await fetch(`${API_BASE}/push`, {
      method  : "POST",
      headers : { "Content-Type": "application/json" },
      body    : JSON.stringify(payload)
    });

    const pushResult = await res.json();

    if (res.ok && pushResult.success) {
      showPushStatus(`✅ Pushed! → ${pushResult.url}`, "ok");
      if (btn) btn.textContent = "✅ Pushed!";
    } else {
      throw new Error(pushResult.detail || "Push failed");
    }

  } catch (e) {
    showPushStatus(`❌ ${e.message}`, "err");
    const btn = document.getElementById("pushBtn");
    if (btn) { btn.textContent = "🐙 Push to GitHub"; btn.disabled = false; }
  }
}


// ════════════════════════════════════════════════
// SHOW PUSH STATUS
// ════════════════════════════════════════════════
function showPushStatus(msg, type) {
  const el = document.getElementById("pushStatus");
  if (!el) return;

  el.textContent   = msg;
  el.style.display = "block";
  el.style.padding = "6px 10px";
  el.style.marginTop = "6px";

  if (type === "ok") {
    el.style.background = "rgba(52,211,153,0.08)";
    el.style.border     = "1px solid rgba(52,211,153,0.3)";
    el.style.color      = "#34d399";
  } else {
    el.style.background = "rgba(248,113,113,0.08)";
    el.style.border     = "1px solid rgba(248,113,113,0.3)";
    el.style.color      = "#f87171";
  }
}


// ════════════════════════════════════════════════
// CHECK GITHUB SETUP
// ════════════════════════════════════════════════
async function checkGithubSetup() {
  const data = await chrome.storage.local.get([
    "githubVerified",
    "githubUsername",
    "githubToken"
  ]);

  const githubSection = document.getElementById("githubSection");
  if (!githubSection) return;

  if (data.githubVerified && data.githubUsername && data.githubToken) {
    githubSection.style.display = "block";
  } else {
    githubSection.style.display = "none";
  }
}


// ════════════════════════════════════════════════
// RENDER RESULTS
// ════════════════════════════════════════════════
function renderResults(data) {

  const statusEl = document.getElementById("resultStatus");
  if (data.all_pass) {
    statusEl.textContent = "✅ All tests passed!";
    statusEl.className   = "result-status pass";
  } else {
    const passed = data.test_results.filter(t => t.passed).length;
    const total  = data.test_results.length;
    statusEl.textContent = `❌ ${passed}/${total} tests passed`;
    statusEl.className   = "result-status fail";
  }

  document.getElementById("attemptsBadge").textContent =
    `ATTEMPTS: ${data.attempts}`;

  const testsList     = document.getElementById("testsList");
  testsList.innerHTML = "";

  data.test_results.forEach((t, i) => {
    const div     = document.createElement("div");
    div.className = `test-item ${t.passed ? "pass" : "fail"}`;
    div.innerHTML = `
      <div class="test-icon">${t.passed ? "✅" : "❌"}</div>
      <div class="test-detail">
        <div class="inp">Test ${i + 1}: ${truncate(t.input, 40)}</div>
        <div class="exp">Expected : ${t.expected}</div>
        ${!t.passed
          ? `<div class="got">Got : ${t.got}</div>`
          : ""
        }
      </div>
    `;
    testsList.appendChild(div);
  });

  document.getElementById("codeBlock").textContent = data.code;

  showResults(true);
  checkGithubSetup();
}


// ════════════════════════════════════════════════
// UI HELPERS
// ════════════════════════════════════════════════
function showLoading(show) {
  const loading  = document.getElementById("loading");
  const solveBtn = document.getElementById("solveBtn");
  if (loading)  loading.classList.toggle("show", show);
  if (solveBtn) solveBtn.disabled = show;
}

function showResults(show) {
  const results = document.getElementById("results");
  if (results) results.classList.toggle("show", show);
}

function showError(msg) {
  const box = document.getElementById("errorBox");
  if (!box) return;
  box.textContent = msg;
  box.classList.toggle("show", !!msg);
}

function showToast(msg) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2000);
}

function truncate(str, max) {
  return str.length > max ? str.slice(0, max) + "..." : str;
}