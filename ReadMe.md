# ⚡ LeetCode AI Solver

A self-correcting AI that solves LeetCode problems automatically.
Built with LangGraph + Azure OpenAI + FastAPI + Chrome Extension.

## How It Works
Open LeetCode problem
↓
Click extension → Solve
↓
AI scrapes problem + examples
↓
Generates solution → runs tests
↓
Fails? → AI reads error → fixes → retries
↓
All tests pass → copy code

## Project Structure
project/
├── backend/
│   ├── main.py          → FastAPI server
│   ├── state.py         → shared memory
│   ├── nodes.py         → LangGraph nodes
│   ├── graph.py         → retry loop
│   ├── scraper.py       → LeetCode scraper
│   └── requirements.txt
│
└── extension/
├── manifest.json    → Chrome extension config
├── popup.html       → UI
├── popup.js         → button logic
└── content.js       → page interaction

## Setup — Backend

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/leetcode-ai-solver.git
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

### 4. Create `.env` file in backend/
```bash
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

### 5. Run the server
```bash
uvicorn main:app --reload --port 8000
```

## Setup — Chrome Extension

Open Chrome → chrome://extensions
Enable Developer Mode (top right)
Click Load unpacked
Select the extension/ folder
Go to any LeetCode problem
Click the extension icon


## Tech Stack

| Layer | Technology |
|---|---|
| AI Framework | LangGraph |
| LLM | Azure OpenAI GPT |
| Backend | FastAPI + Python |
| Extension | Chrome MV3 |
| Scraping | LeetCode GraphQL API |

## Contributing

1. Fork the repo
2. Create your branch `git checkout -b feature/your-feature`
3. Commit changes `git commit -m "add: your feature"`
4. Push `git push origin feature/your-feature`
5. Open a Pull Request

Step 3 — Create backend/requirements.txt
langgraph
langchain-openai
fastapi
uvicorn
requests
beautifulsoup4
python-dotenv
pytest

Step 4 — Create .env.example
bash# .env.example
# copy this to .env and fill in your values
# NEVER commit .env — only commit .env.example

AZURE_OPENAI_API_KEY=your-azure-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2025-01-01-preview

Step 5 — Initialize git and push
bash# go to root project folder
cd "Code Assisstance"

# initialize git
git init

# add all files
git add .

# first commit
git commit -m "init: LeetCode AI Solver — backend + chrome extension"

# go to github.com → New Repository
# name it: leetcode-ai-solver
# keep it public or private
# DO NOT add README (we already have one)
# copy the repo URL then:

git remote add origin https://github.com/yourusername/leetcode-ai-solver.git
git branch -M main
git push -u origin main

Step 6 — For your friend to contribute
bash# clone
git clone https://github.com/yourusername/leetcode-ai-solver.git

# setup venv
python -m venv .venv
.venv\Scripts\activate

# install deps
cd backend
pip install -r requirements.txt

# create their own .env
# copy .env.example → .env
# fill in their own API keys
