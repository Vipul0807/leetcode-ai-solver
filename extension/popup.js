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

  // load saved language
  const saved = await chrome.storage.local.get("language");
  if (saved.language) {
    selectedLang = saved.language;
    updateLangButtons(selectedLang);
  }

  // ✅ restore previous results — don't lose on close
  await restoreResults(currentUrl);

  // load problem info
  await loadProblemInfo(currentUrl);

  setupListeners();
});


// ════════════════════════════════════════════════
// SAVE RESULTS
// ════════════════════════════════════════════════
async function saveResults(url, data) {
  const key = "result_" + btoa(url).slice(0, 40);
  await chrome.storage.local.set({ [key]: data });
}


// ════════════════════════════════════════════════
// RESTORE RESULTS
// ════════════════════════════════════════════════
async function restoreResults(url) {
  try {
    const key  = "result_" + btoa(url).slice(0, 40);
    const data = await chrome.storage.local.get(key);
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

      const diffBadge       = document.getElementById("diffBadge");
      diffBadge.textContent  = info.difficulty || "Unknown";
      diffBadge.className    = `badge ${info.difficulty?.toLowerCase() || "easy"}`;

      if (info.language) {
        selectedLang = info.language;
        updateLangButtons(selectedLang);
        document.getElementById("langBadge").textContent =
          selectedLang.charAt(0).toUpperCase() + selectedLang.slice(1);
      }
    }

  } catch (e) {
    const slug  = url.split("/problems/")[1]?.replace(/\/$/, "") || "";
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
      document.getElementById("langBadge").textContent =
        selectedLang.charAt(0).toUpperCase() + selectedLang.slice(1);
      chrome.storage.local.set({ language: selectedLang });
    });
  });

  // ✅ error toggle
  document.getElementById("errorToggle").addEventListener("click", () => {
    const paste   = document.getElementById("errorPaste");
    const toggle  = document.getElementById("errorToggle");
    const isShown = paste.classList.contains("show");
    paste.classList.toggle("show",  !isShown);
    toggle.classList.toggle("active", !isShown);
  });

  // solve
  document.getElementById("solveBtn").addEventListener("click", solve);

  // copy
  document.getElementById("copyBtn").addEventListener("click", () => {
    if (!currentCode) return;
    navigator.clipboard.writeText(currentCode);
    showToast("✅ Code copied!");
  });

  // ✅ retry — keeps error input, resolves again
  document.getElementById("retryBtn").addEventListener("click", () => {
    const key = "result_" + btoa(currentUrl).slice(0, 40);
    chrome.storage.local.remove(key);
    showResults(false);
    showError("");
    solve();
  });

  // ✅ clear — full reset
  document.getElementById("clearBtn").addEventListener("click", () => {
    const key = "result_" + btoa(currentUrl).slice(0, 40);
    chrome.storage.local.remove(key);
    showResults(false);
    showError("");
    currentCode = "";
    document.getElementById("errorInput").value = "";
    document.getElementById("errorPaste").classList.remove("show");
    document.getElementById("errorToggle").classList.remove("active");
  });
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

    // ✅ read pasted error if any
    const userError = document.getElementById("errorInput").value.trim();

    const res = await fetch(`${API_BASE}/solve`, {
      method  : "POST",
      headers : { "Content-Type": "application/json" },
      body    : JSON.stringify({
        url        : currentUrl,
        language   : selectedLang,
        user_error : userError       // ✅ send to backend
      })
    });

    clearInterval(stepInterval);

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Server error");
    }

    const data  = await res.json();
    currentCode = data.code;

    // ✅ save so popup close doesn't lose results
    await saveResults(currentUrl, data);

    showLoading(false);
    renderResults(data);

  } catch (e) {
    clearInterval(stepInterval);
    showLoading(false);
    showError(`❌ ${e.message}`);
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
}


// ════════════════════════════════════════════════
// UI HELPERS
// ════════════════════════════════════════════════
function showLoading(show) {
  document.getElementById("loading").classList.toggle("show", show);
  document.getElementById("solveBtn").disabled = show;
}

function showResults(show) {
  document.getElementById("results").classList.toggle("show", show);
}

function showError(msg) {
  const box       = document.getElementById("errorBox");
  box.textContent = msg;
  box.classList.toggle("show", !!msg);
}

function showToast(msg) {
  const toast       = document.getElementById("toast");
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2000);
}

function truncate(str, max) {
  return str.length > max ? str.slice(0, max) + "..." : str;
}