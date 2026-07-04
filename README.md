# ⚡ LeetCode AI Solver

A self-correcting AI that solves LeetCode problems automatically
and pushes accepted solutions to GitHub.
Built with **LangGraph**, **Azure OpenAI**, **FastAPI**, and a **Chrome Extension**.

---

## 🧠 How It Works

```
Open LeetCode problem
        ↓
Click extension → Select language → Click Solve
        ↓
AI scrapes problem description + examples
        ↓
AI generates solution → runs against examples
        ↓
All pass? → ✅ Show code → Push to GitHub
Any fail? → ❌ AI reads error → fixes → retries
        ↓
Max 3 attempts → give up with error explanation
```

---

## ✨ Features

- 🤖 **Self-correcting loop** — AI fixes its own errors automatically
- 🧪 **Auto test** — runs solution against LeetCode examples locally
- 📋 **Copy code** — one click to copy working solution
- 🔁 **Retry** — re-solve with fresh attempt
- ⚠️ **Error paste** — paste LeetCode errors for targeted fixes
- 🐙 **GitHub push** — auto pushes solution + README to your repo
- 💾 **Persistent results** — results saved across popup close/open
- 🌐 **Multi-language** — Python, JavaScript, Java

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **AI Framework** | LangGraph |
| **LLM** | Azure OpenAI GPT |
| **Backend** | FastAPI + Python |
| **Extension** | Chrome Manifest V3 |
| **Scraping** | LeetCode GraphQL API |
| **GitHub Integration** | GitHub REST API |

---

## 📁 Project Structure

```
leetcode-ai-solver/
│
├── backend/
│   ├── main.py              ← FastAPI server + API endpoints
│   ├── state.py             ← Shared memory (AgentState)
│   ├── nodes.py             ← LangGraph nodes (scrape, generate, test, check)
│   ├── graph.py             ← Self-correcting retry loop
│   ├── scraper.py           ← LeetCode GraphQL scraper
│   ├── github_pusher.py     ← GitHub API integration
│   ├── requirements.txt     ← Python dependencies
│   └── .env.example         ← Environment variable template
│
└── extension/
    ├── manifest.json        ← Chrome extension config
    ├── popup.html           ← Extension UI
    ├── popup.js             ← Button logic + API calls
    ├── content.js           ← LeetCode page interaction
    ├── settings.html        ← GitHub token setup UI
    ├── settings.js          ← Settings save + verify logic
    └── icons/               ← Extension icons
        ├── icon16.png
        ├── icon48.png
        └── icon128.png
```

---

## ⚙️ Setup — Backend

### 1. Clone the repo
```bash
git clone https://github.com/Vipul0807/leetcode-ai-solver.git
cd leetcode-ai-solver
```

### 2. Create virtual environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Create `.env` file
```bash
# copy from example
cp .env.example .env
```

Fill in your values:
```
AZURE_OPENAI_API_KEY=your-azure-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

### 5. Run the server
```bash
uvicorn main:app --reload --port 8000
```

Server runs at `http://localhost:8000`
Auto docs at `http://localhost:8000/docs`

---

## 🧩 Setup — Chrome Extension

```
1. Open Chrome → chrome://extensions
2. Enable Developer Mode (top right toggle)
3. Click "Load unpacked"
4. Select the extension/ folder
5. Pin the extension to toolbar
```

---

## 🐙 Setup — GitHub Integration

```
1. Go to github.com/settings/tokens
2. Click "Tokens (classic)"
3. Generate new token (classic)
4. Select scope: ✅ repo
5. Copy token

In extension:
6. Click ⚙ gear icon
7. Enter GitHub username + token
8. Click "Verify GitHub Connection"
9. Click "Save Settings"
```

After setup — solving a problem shows a **Push to GitHub** button.

Pushes to:
```
github.com/username/leetcode-problems/
  └── two-sum/
      ├── solution.py    ← solution with header comment
      └── README.md      ← problem info + examples + badges
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Server status check |
| GET | `/problem?url=` | Fetch problem info only |
| POST | `/solve` | Full solve with test results |
| POST | `/push` | Push solution to GitHub |
| POST | `/verify-github` | Verify GitHub token |

---

## 🔄 Self-Correcting Loop

```
[START]
    ↓
[scrape_problem]    → fetch title + description + examples
    ↓
[generate_code] ← ← ← ← ← ← ← ← ← ← ←
    ↓                                    ↑
[run_tests]                              ↑
    ↓                                    ↑
[check_tests]                            ↑
    ├── all pass  → [END] ✅             ↑
    ├── retry     → [generate_code] ─────↑
    └── give_up   → [END] ❌
```

---

## 🧪 Running Tests

```bash
cd backend

# run without API calls (fast)
pytest test_app.py::TestCleanCode -v
pytest test_app.py::TestClassifyError -v
pytest test_app.py::TestExecuteCode -v
pytest test_app.py::TestCheckResult -v

# full integration tests (uses Azure OpenAI tokens)
pytest test_app.py::TestFullGraph -v

# all at once
pytest test_app.py -v
```

---

## 🚧 Known Limitations

```
- Code injection into LeetCode editor not yet supported (use copy instead)
- Only supports LeetCode (HackerRank coming soon)
- Backend must run locally (not deployed to cloud yet)
- Java requires JDK installed locally
- JavaScript requires Node.js installed locally
```

---

## 🗺️ Roadmap

```
✅ Phase 1 — Core self-correcting loop
✅ Phase 2 — Chrome extension UI
✅ Phase 3 — GitHub auto-push
⏳ Phase 4 — Monaco editor injection
⏳ Phase 5 — HackerRank support
⏳ Phase 6 — Cloud deployment
⏳ Phase 7 — More languages (C++, TypeScript)
```

---

## 🤝 Contributing

```bash
# fork the repo then:
git clone https://github.com/your-username/leetcode-ai-solver.git

# create feature branch
git checkout -b feature/your-feature-name

# make changes then commit
git add .
git commit -m "add: your feature description"
git push origin feature/your-feature-name

# open Pull Request on GitHub
```

### Commit conventions
```
init:    first setup
add:     new feature
fix:     bug fix
update:  modify existing feature
remove:  delete something
docs:    readme or comments update
test:    add or update tests
```

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ using LangGraph + Azure OpenAI*