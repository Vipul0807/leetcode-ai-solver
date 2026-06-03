# ⚡ LeetCode AI Solver

A self-correcting AI that solves LeetCode problems automatically.  
Built with **LangGraph**, **Azure OpenAI**, **FastAPI**, and a **Chrome Extension**.

---

## 🧠 How It Works

1. **Open** a LeetCode problem in your browser.
2. **Click** the extension icon and hit **Solve**.
3. **Scrape:** The AI automatically scrapes the problem description and examples.
4. **Generate & Test:** The AI generates a solution and runs the initial tests.
5. **Self-Correct:** If a test fails, the AI reads the error output, fixes the code, and retries.
6. **Success:** Once all tests pass, the final working code is copied for you to use.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **AI Framework** | LangGraph |
| **LLM** | Azure OpenAI GPT |
| **Backend** | FastAPI + Python |
| **Extension** | Chrome Manifest V3 |
| **Scraping** | LeetCode GraphQL API |

---

## 📁 Project Structure

```text
leetcode-ai-solver/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── state.py             # Shared memory for LangGraph
│   ├── nodes.py             # LangGraph nodes (logic)
│   ├── graph.py             # Retry & self-correction loop
│   ├── scraper.py           # LeetCode data scraper
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Template for environment variables
│
└── extension/
    ├── manifest.json        # Chrome extension config
    ├── popup.html           # Extension UI
    ├── popup.js             # Button logic & API calls
    └── content.js           # Page interaction script
