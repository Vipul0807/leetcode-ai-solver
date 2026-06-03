# backend/state.py

from typing import TypedDict, List, Optional


# ════════════════════════════════════════════════
# Test Case — one example from the problem
# ════════════════════════════════════════════════
class TestCase(TypedDict):
    input    : str    # "nums = [2,7,11,15], target = 9"
    expected : str    # "[0,1]"


# ════════════════════════════════════════════════
# Test Result — after running solution against one example
# ════════════════════════════════════════════════
class TestResult(TypedDict):
    input    : str    # what was passed in
    expected : str    # what LeetCode expects
    got      : str    # what our code returned
    passed   : bool   # True / False


# ════════════════════════════════════════════════
# Agent State — shared memory across all nodes
# ════════════════════════════════════════════════
class AgentState(TypedDict):

    # ── problem info ──────────────────────────
    problem_url   : str            # "https://leetcode.com/problems/two-sum/"
    problem_title : str            # "Two Sum"
    description   : str            # full problem statement
    examples      : List[TestCase] # structured test cases

    # ── solution ──────────────────────────────
    language       : str           # "python" / "javascript" / "java"
    generated_code : str           # solution LLM wrote

    # ── execution ─────────────────────────────
    test_results   : List[TestResult]  # per example pass/fail
    all_tests_pass : bool              # final verdict
    error_message  : str               # error if something failed
    attempt_count  : int               # retry counter
    max_attempts   : int               # stop at 3

    # ── meta ──────────────────────────────────
    problem_slug  : str            # "two-sum" extracted from URL

    user_error     : str    # ✅ new — error user pastes from LeetCode