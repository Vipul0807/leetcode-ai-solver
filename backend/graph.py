# backend/graph.py

from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import (
    scrape_problem,
    generate_code,
    run_tests,
    check_tests
)


# ── Step 1: create graph ──────────────────────────
graph_builder = StateGraph(AgentState)


# ── Step 2: add nodes ────────────────────────────
graph_builder.add_node("scrape",   scrape_problem)
graph_builder.add_node("generate", generate_code)
graph_builder.add_node("test",     run_tests)


# ── Step 3: fixed edges ──────────────────────────
graph_builder.add_edge("scrape",   "generate")
graph_builder.add_edge("generate", "test")


# ── Step 4: conditional edge from test ───────────
graph_builder.add_conditional_edges(
    "test",         # from this node
    check_tests,    # call this to decide next step
    {
        "success"  : END,        # all tests pass → done
        "retry"    : "generate", # some fail → fix and retry
        "give_up"  : END,        # max attempts → stop
    }
)


# ── Step 5: entry point ──────────────────────────
graph_builder.set_entry_point("scrape")


# ── Step 6: compile ──────────────────────────────
graph = graph_builder.compile()


# ════════════════════════════════════════════════
# TEST — run directly to verify
# ════════════════════════════════════════════════
if __name__ == "__main__":
    from state import AgentState

    initial_state = AgentState(
        problem_url    = "https://leetcode.com/problems/two-sum/",
        language       = "python",
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

    print("\n🚀 Running graph...\n")
    final = graph.invoke(initial_state)

    print("\n══════════════════════════════════")
    print(f"Title    : {final['problem_title']}")
    print(f"Language : {final['language']}")
    print(f"Attempts : {final['attempt_count']}")
    print(f"All Pass : {final['all_tests_pass']}")

    print("\n── Test Results ──")
    for i, t in enumerate(final["test_results"]):
        icon = "✅" if t["passed"] else "❌"
        print(f"  {icon} Test {i+1}")
        print(f"     Input    : {t['input']}")
        print(f"     Expected : {t['expected']}")
        print(f"     Got      : {t['got']}")

    print("\n── Final Code ──")
    print(final["generated_code"])