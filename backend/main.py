# backend/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph import graph
from state import AgentState


# ── app setup ────────────────────────────────────
app = FastAPI(
    title       = "LeetCode AI Solver",
    description = "Self-correcting code assistant for LeetCode",
    version     = "1.0.0"
)


# ── CORS — allow Chrome extension to call API ────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],   # extension can call from any origin
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ════════════════════════════════════════════════
class SolveRequest(BaseModel):
    url      : str
    language : str = "python"   # default to python
    user_error : str = ""


class TestResultResponse(BaseModel):
    input    : str
    expected : str
    got      : str
    passed   : bool


class SolveResponse(BaseModel):
    title        : str
    difficulty   : str = ""
    language     : str
    code         : str
    test_results : list[TestResultResponse]
    all_pass     : bool
    attempts     : int
    error        : str = ""


# ════════════════════════════════════════════════
# ROUTES
# ════════════════════════════════════════════════

# ── health check ─────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "message": "LeetCode AI Solver is running"}


# ── main solve endpoint ───────────────────────────

@app.post("/solve", response_model=SolveResponse)
def solve(request: SolveRequest):
    print(f"\n📥 REQUEST — url={request.url} lang={request.language}")

    supported = ["python", "javascript", "java"]
    if request.language not in supported:
        raise HTTPException(
            status_code = 400,
            detail      = f"Language must be one of {supported}"
        )

    if "leetcode.com/problems" not in request.url:
        raise HTTPException(
            status_code = 400,
            detail      = "URL must be a valid LeetCode problem URL"
        )

    try:
        initial_state = AgentState(
            problem_url    = request.url,
            language       = request.language,
            user_error     = request.user_error,   # ✅ pass through
            problem_slug   = "",
            problem_title  = "",
            description    = "",
            examples       = [],
            generated_code = "",
            test_results   = [],
            all_tests_pass = False,
            error_message  = "",
            attempt_count  = 0,
            max_attempts   = 3,
        )

        final = graph.invoke(initial_state)

        if not final["problem_title"]:
            raise HTTPException(
                status_code = 404,
                detail      = f"Could not fetch problem: {final['error_message']}"
            )

        return SolveResponse(
            title        = final["problem_title"],
            language     = final["language"],
            code         = final["generated_code"],
            test_results = [
                TestResultResponse(
                    input    = t["input"],
                    expected = t["expected"],
                    got      = t["got"],
                    passed   = t["passed"]
                )
                for t in final["test_results"]
            ],
            all_pass     = final["all_tests_pass"],
            attempts     = final["attempt_count"],
            error        = final["error_message"]
        )

    except HTTPException:
        raise

    except Exception as e:
        print(f"🔴 SERVER ERROR: {e}")
        raise HTTPException(
            status_code = 500,
            detail      = f"Server error: {str(e)}"
        )

# ── get problem info only (no solve) ─────────────
@app.get("/problem")
def get_problem(url: str):
    """
    Just fetch problem info without solving
    Used by extension to show title + difficulty
    """
    if "leetcode.com/problems" not in url:
        raise HTTPException(
            status_code = 400,
            detail      = "URL must be a valid LeetCode problem URL"
        )

    try:
        from scraper import fetch_problem
        data = fetch_problem(url)

        return {
            "slug"       : data["slug"],
            "title"      : data["title"],
            "difficulty" : data["difficulty"],
            "examples"   : data["examples"]
        }

    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail      = f"Could not fetch problem: {str(e)}"
        )