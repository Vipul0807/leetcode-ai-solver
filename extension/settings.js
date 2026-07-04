// extension/settings.js

const API_BASE = "http://localhost:8000";


// ════════════════════════════════════════════════
// ON LOAD — restore saved settings
// ════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", async () => {

  const data = await chrome.storage.local.get([
    "githubUsername",
    "githubToken",
    "autoPush",
    "aiPassOnly",
    "githubVerified",
    "githubProfile"
  ]);

  if (data.githubUsername) {
    document.getElementById("githubUsername").value = data.githubUsername;
  }

  if (data.githubToken) {
    document.getElementById("githubToken").value = data.githubToken;
  }

  if (data.autoPush) {
    document.getElementById("autoPushToggle").checked = data.autoPush;
  }

  if (data.aiPassOnly !== undefined) {
    document.getElementById("aiPassToggle").checked = data.aiPassOnly;
  }

  // restore profile card if already verified
  if (data.githubVerified && data.githubProfile) {
    showProfileCard(data.githubProfile);
  }

  setupListeners();
});


// ════════════════════════════════════════════════
// SETUP LISTENERS
// ════════════════════════════════════════════════
function setupListeners() {

  // back button
  document.getElementById("backBtn").addEventListener("click", () => {
    window.close();
  });

  // verify button
  document.getElementById("verifyBtn").addEventListener("click", verifyGitHub);

  // save button
  document.getElementById("saveBtn").addEventListener("click", saveSettings);
}


// ════════════════════════════════════════════════
// VERIFY GITHUB
// ════════════════════════════════════════════════
async function verifyGitHub() {
  const token    = document.getElementById("githubToken").value.trim();
  const username = document.getElementById("githubUsername").value.trim();

  if (!token || !username) {
    showStatus("verifyStatus", "❌ Enter both username and token", "error");
    return;
  }

  showStatus("verifyStatus", "⏳ Verifying...", "success");

  try {
    const res = await fetch(`${API_BASE}/verify-github`, {
      method  : "POST",
      headers : { "Content-Type": "application/json" },
      body    : JSON.stringify({ token, username })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Verification failed");
    }

    const profile = await res.json();

    // save verified state
    await chrome.storage.local.set({
      githubVerified : true,
      githubProfile  : profile
    });

    showProfileCard(profile);
    showStatus("verifyStatus", "✅ GitHub connected successfully!", "success");

  } catch (e) {
    showStatus("verifyStatus", `❌ ${e.message}`, "error");
    await chrome.storage.local.set({ githubVerified: false });
  }
}


// ════════════════════════════════════════════════
// SHOW PROFILE CARD
// ════════════════════════════════════════════════
function showProfileCard(profile) {
  document.getElementById("profileCard").classList.add("show");
  document.getElementById("profileAvatar").src  = profile.avatar || "";
  document.getElementById("profileName").textContent = profile.name || profile.username;
  document.getElementById("profileUser").textContent = `@${profile.username}`;
}


// ════════════════════════════════════════════════
// SAVE SETTINGS
// ════════════════════════════════════════════════
async function saveSettings() {
  const username   = document.getElementById("githubUsername").value.trim();
  const token      = document.getElementById("githubToken").value.trim();
  const autoPush   = document.getElementById("autoPushToggle").checked;
  const aiPassOnly = document.getElementById("aiPassToggle").checked;

  if (!username || !token) {
    showStatus("saveStatus", "❌ Username and token are required", "error");
    return;
  }

  await chrome.storage.local.set({
    githubUsername : username,
    githubToken    : token,
    autoPush       : autoPush,
    aiPassOnly     : aiPassOnly
  });

  showStatus("saveStatus", "✅ Settings saved!", "success");

  setTimeout(() => {
    hideStatus("saveStatus");
  }, 2000);
}


// ════════════════════════════════════════════════
// UI HELPERS
// ════════════════════════════════════════════════
function showStatus(id, msg, type) {
  const el      = document.getElementById(id);
  el.textContent = msg;
  el.className   = `status show ${type}`;
}

function hideStatus(id) {
  document.getElementById(id).className = "status";
}