// extension/content.js

// ════════════════════════════════════════════════
// LISTEN — messages from popup.js
// ════════════════════════════════════════════════
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

  if (message.type === "GET_PROBLEM_INFO") {
    sendResponse(getProblemInfo());
  }

  else if (message.type === "GET_LANGUAGE") {
    sendResponse({ language: getSelectedLanguage() });
  }

  return true;
});


// ════════════════════════════════════════════════
// GET PROBLEM INFO
// ════════════════════════════════════════════════
function getProblemInfo() {
  try {
    const titleEl = document.querySelector(
      "[data-cy='question-title'], " +
      ".text-title-large a, "        +
      "h4.mr-2"
    );
    const title = titleEl?.textContent?.trim() || "Unknown";

    const diffEl = document.querySelector(
      ".text-difficulty-easy, "   +
      ".text-difficulty-medium, " +
      ".text-difficulty-hard"
    );

    let difficulty = "Unknown";
    if (diffEl) {
      const cls = diffEl.className || "";
      if (cls.includes("easy"))   difficulty = "Easy";
      if (cls.includes("medium")) difficulty = "Medium";
      if (cls.includes("hard"))   difficulty = "Hard";
      if (difficulty === "Unknown") {
        difficulty = diffEl.textContent?.trim() || "Unknown";
      }
    }

    return {
      title,
      difficulty,
      url      : window.location.href,
      language : getSelectedLanguage()
    }

  } catch (e) {
    return {
      title      : "Unknown",
      difficulty : "Unknown",
      url        : window.location.href
    }
  }
}


// ════════════════════════════════════════════════
// GET SELECTED LANGUAGE
// ════════════════════════════════════════════════
function getSelectedLanguage() {
  try {
    const langEl = document.querySelector(
      "[data-cy='lang-select'] button, " +
      ".ant-select-selection-item, "     +
      "button.rounded.items-center"
    );

    if (!langEl) return "python";

    const text = langEl.textContent?.trim().toLowerCase() || "";

    if (text.includes("python"))     return "python";
    if (text.includes("javascript")) return "javascript";
    if (text.includes("java"))       return "java";

    return "python";

  } catch (e) {
    return "python";
  }
}


// ════════════════════════════════════════════════
// WATCH LANGUAGE CHANGE
// ════════════════════════════════════════════════
function watchLanguageChange() {
  const observer = new MutationObserver(() => {
    const lang = getSelectedLanguage();
    chrome.runtime.sendMessage({
      type     : "LANGUAGE_CHANGED",
      language : lang
    }).catch(() => {});
  });

  const langSelector = document.querySelector(
    "[data-cy='lang-select'], " +
    ".ant-select-selector"
  );

  if (langSelector) {
    observer.observe(langSelector, {
      childList  : true,
      subtree    : true,
      attributes : true
    });
  }
}

watchLanguageChange();

// watch SPA navigation
let lastUrl = window.location.href;
new MutationObserver(() => {
  if (window.location.href !== lastUrl) {
    lastUrl = window.location.href;
    watchLanguageChange();
  }
}).observe(document.body, { childList: true, subtree: true });

console.log("✅ Content script loaded");