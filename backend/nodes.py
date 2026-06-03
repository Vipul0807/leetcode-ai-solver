# backend/nodes.py

import re
import subprocess
import tempfile
import os
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from scraper import fetch_problem
from state import AgentState, TestResult

load_dotenv()

# ── setup LLM ────────────────────────────────────
llm = AzureChatOpenAI(
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    azure_endpoint   = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key          = os.getenv("AZURE_OPENAI_API_KEY"),
    api_version      = os.getenv("AZURE_OPENAI_API_VERSION"),
)


# ════════════════════════════════════════════════
# HELPER — clean LLM markdown
# ════════════════════════════════════════════════
def clean_code(raw: str) -> str:
    lines   = raw.strip().split("\n")
    cleaned = []
    for line in lines:
        if line.strip().startswith("```"):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


# ════════════════════════════════════════════════
# HELPER — LLM based error classifier
# ════════════════════════════════════════════════
def classify_error(stderr: str) -> str:
    prompt = f"""
    You are a Python debugging expert.

    A Python script produced this error:
    {stderr}

    Respond in this exact format:
    ERROR TYPE: <one line error type>
    CAUSE: <one line what caused it>
    FIX: <one line how to fix it>
    RETRY: <yes or no — can LLM fix this by rewriting code?>
    """
    response = llm.invoke(prompt)
    return response.content.strip()


# ════════════════════════════════════════════════
# NODE 1 — Scrape Problem
# ════════════════════════════════════════════════
def scrape_problem(state: AgentState) -> AgentState:
    print(f"\n🔍 SCRAPE — {state['problem_url']}")

    try:
        data = fetch_problem(state["problem_url"])

        return {
            **state,
            "problem_slug"  : data["slug"],
            "problem_title" : data["title"],
            "description"   : data["description"],
            "examples"      : data["examples"],
        }

    except Exception as e:
        print(f"🔴 SCRAPE ERROR: {e}")
        return {
            **state,
            "error_message" : f"Failed to fetch problem: {str(e)}"
        }


# ════════════════════════════════════════════════
# HELPER — extract function signature from description
# ════════════════════════════════════════════════
def extract_signature(description: str, language: str) -> str:
    """
    Extract the actual function signature from problem description
    so LLM uses correct method name and params
    """
    # python signature pattern
    if language == "python":
        patterns = [
            r'def\s+\w+\s*\([^)]*\)\s*(?:->\s*\w+)?:',
            r'def\s+\w+\([^)]*\)',
        ]
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(0)

    # javascript signature pattern
    elif language == "javascript":
        patterns = [
            r'var\s+\w+\s*=\s*function\s*\([^)]*\)',
            r'function\s+\w+\s*\([^)]*\)',
        ]
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(0)

    # java signature pattern
    elif language == "java":
        patterns = [
            r'public\s+\w+\s+\w+\s*\([^)]*\)',
        ]
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(0)

    return ""  # not found — LLM will figure it out


# ════════════════════════════════════════════════
# NODE 2 — Generate Code (updated)
# ════════════════════════════════════════════════

# in generate_code — update first attempt prompt

def generate_code(state: AgentState) -> AgentState:
    print(f"\n🔵 GENERATE — attempt {state['attempt_count']} lang={state['language']}")

    lang      = state["language"]
    signature = extract_signature(state["description"], lang)
    sig_hint  = f"\nUSE THIS EXACT SIGNATURE: {signature}" if signature else ""

    format_hints = {
        "python": f"""
Format EXACTLY like this:
class Solution:
    def methodName(self, param1, param2):
        # your solution
{sig_hint}
""",
        "javascript": f"""
Format EXACTLY like this:
var methodName = function(param1, param2) {{
    // your solution
}};
{sig_hint}
""",
        "java": f"""
Format EXACTLY like this:
class Solution {{
    public returnType methodName(param1, param2) {{
        // your solution
    }}
}}
{sig_hint}
"""
    }

    hint = format_hints.get(lang, "")

    # ✅ check if user pasted an error from LeetCode
    user_error_context = ""
    if state.get("user_error", "").strip():
        user_error_context = f"""
IMPORTANT — User submitted this code to LeetCode and got this error:
{state["user_error"]}

Fix this specific error in your solution.
"""

    if state["attempt_count"] == 0:
        prompt = f"""
        You are an expert competitive programmer solving LeetCode problems.

        PROBLEM TITLE: {state["problem_title"]}

        PROBLEM DESCRIPTION:
        {state["description"]}

        LANGUAGE: {lang}

        {hint}

        {user_error_context}

        STRICT RULES:
        - ALWAYS wrap solution inside class Solution
        - Use the EXACT function signature shown above
        - Handle ALL edge cases
        - NO markdown, NO backticks, NO explanation
        - Return ONLY the code
        """

    else:
        failing = [t for t in state["test_results"] if not t["passed"]]
        failing_summary = "\n".join([
            f"Input    : {t['input']}\n"
            f"Expected : {t['expected']}\n"
            f"Got      : {t['got']}"
            for t in failing
        ])

        prompt = f"""
        You are an expert competitive programmer.

        PROBLEM: {state["problem_title"]}

        This {lang} solution is WRONG:
        {state["generated_code"]}

        FAILING TEST CASES:
        {failing_summary}

        {user_error_context}

        {hint}

        STRICT RULES:
        - ALWAYS wrap solution inside class Solution
        - Use the EXACT function signature shown above
        - Fix logic so ALL test cases pass
        - NO markdown, NO backticks, NO explanation
        - Return ONLY the corrected code
        """

    response = llm.invoke(prompt)
    cleaned  = clean_code(response.content)
    print(f"🔵 GENERATED:\n{cleaned[:200]}...")

    return {
        **state,
        "generated_code" : cleaned,
        "test_results"   : [],
        "all_tests_pass" : False,
    }


# ════════════════════════════════════════════════
# NODE 3 — Run Tests
# ════════════════════════════════════════════════
def run_tests(state: AgentState) -> AgentState:
    print(f"\n🟡 RUN TESTS — {len(state['examples'])} examples")

    results      = []
    lang         = state["language"]
    solution     = state["generated_code"]

    for i, example in enumerate(state["examples"]):
        inp      = example["input"]
        expected = example["expected"].strip()

        # build test runner code based on language
        if lang == "python":
            test_code = build_python_test(solution, inp, expected)
            result    = run_python(test_code)

        elif lang == "javascript":
            test_code = build_js_test(solution, inp, expected)
            result    = run_javascript(test_code)

        elif lang == "java":
            test_code = build_java_test(solution, inp, expected)
            result    = run_java(test_code)

        else:
            result = {"passed": False, "got": "Unsupported language"}

        print(f"  Test {i+1}: {'✅' if result['passed'] else '❌'} "
              f"expected={expected} got={result['got']}")

        results.append(TestResult(
            input    = inp,
            expected = expected,
            got      = result["got"],
            passed   = result["passed"]
        ))

    all_pass = all(r["passed"] for r in results)

    return {
        **state,
        "test_results"   : results,
        "all_tests_pass" : all_pass,
        "attempt_count"  : state["attempt_count"] + (0 if all_pass else 1)
    }


# ════════════════════════════════════════════════
# NODE 4 — Check Tests (router)
# ════════════════════════════════════════════════
def check_tests(state: AgentState) -> str:
    print(f"\n⚪ CHECK — all_pass={state['all_tests_pass']} "
          f"attempt={state['attempt_count']}")

    if state["all_tests_pass"]:
        print("✅ All tests passed!")
        return "success"

    elif state["attempt_count"] >= state["max_attempts"]:
        print("❌ Max attempts reached")
        return "give_up"

    else:
        print("🔁 Retrying with failing test context")
        return "retry"


# ════════════════════════════════════════════════
# LANGUAGE RUNNERS
# ════════════════════════════════════════════════

# ── Python ───────────────────────────────────────
def build_python_test(solution: str, inp: str, expected: str) -> str:
    """
    Wraps the solution with a test runner that:
    - parses the input
    - calls the function
    - compares output to expected
    - prints PASS or FAIL
    """
    return f"""
{solution}

# ── test runner ──
import re

def normalize(val):
    \"\"\"normalize output for comparison\"\"\"
    return str(val).replace(" ", "").lower()

# parse input: "nums = [2,7,11,15], target = 9"
inp = "{inp}"
expected = "{expected}"

# extract variables from input string
local_vars = {{}}
try:
    # split by comma outside brackets
    parts = re.split(r',\\s*(?=[a-zA-Z])', inp)
    for part in parts:
        if '=' in part:
            key, val = part.split('=', 1)
            local_vars[key.strip()] = eval(val.strip())
except Exception as e:
    print(f"PARSE ERROR: {{e}}")
    exit(1)

# call function with parsed args
try:
    sol = Solution()
    # get function name dynamically
    import inspect
    methods = [m for m in dir(sol)
               if not m.startswith('_')]
    func = getattr(sol, methods[0])
    result = func(**local_vars)
    got = str(result).replace(" ", "")

    if normalize(got) == normalize(expected):
        print(f"PASS|{{got}}")
    else:
        print(f"FAIL|{{got}}")

except Exception as e:
    print(f"ERROR|{{e}}")
"""


def run_python(test_code: str) -> dict:
    tmp_path = None
    try:
        # ✅ safety net — auto wrap if class Solution missing
        if "class Solution" not in test_code:
            lines = test_code.strip().split("\n")
            # find where the test runner starts (after solution code)
            solution_lines = []
            runner_lines   = []
            in_runner      = False

            for line in lines:
                if "# ── test runner ──" in line:
                    in_runner = True
                if in_runner:
                    runner_lines.append(line)
                else:
                    solution_lines.append(line)

            # indent solution and wrap in class
            indented = "\n".join(
                "    " + l if l.strip() else l
                for l in solution_lines
            )
            wrapped = f"class Solution:\n{indented}\n\n" + "\n".join(runner_lines)
            test_code = wrapped

        with tempfile.NamedTemporaryFile(
            mode     = "w",
            suffix   = ".py",
            delete   = False,
            encoding = "utf-8"
        ) as tmp:
            tmp.write(test_code)
            tmp_path = tmp.name

        result = subprocess.run(
            ["python", tmp_path],
            capture_output = True,
            text           = True,
            timeout        = 10,
            encoding       = "utf-8"
        )

        output = result.stdout.strip()

        if output.startswith("PASS"):
            got = output.split("|")[1] if "|" in output else output
            return {"passed": True,  "got": got}
        elif output.startswith("FAIL"):
            got = output.split("|")[1] if "|" in output else output
            return {"passed": False, "got": got}
        else:
            error = result.stderr.strip() or output
            return {"passed": False, "got": f"ERROR: {error[:100]}"}

    except subprocess.TimeoutExpired:
        return {"passed": False, "got": "Timed out"}

    except Exception as e:
        return {"passed": False, "got": f"Runner error: {str(e)[:100]}"}

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# ── JavaScript ───────────────────────────────────
def build_js_test(solution: str, inp: str, expected: str) -> str:
    return f"""
{solution}

// test runner
const inp = `{inp}`;
const expected = `{expected}`.trim();

try {{
    // parse input variables
    const vars = {{}};
    inp.split(/,\\s*(?=[a-zA-Z])/).forEach(part => {{
        const [key, val] = part.split('=').map(s => s.trim());
        vars[key] = JSON.parse(val);
    }});

    // call solution
    const result = JSON.stringify(twoSum(...Object.values(vars)));
    const exp    = JSON.stringify(JSON.parse(expected));

    if (result === exp) {{
        console.log(`PASS|${{result}}`);
    }} else {{
        console.log(`FAIL|${{result}}`);
    }}
}} catch(e) {{
    console.log(`ERROR|${{e.message}}`);
}}
"""


def run_javascript(test_code: str) -> dict:
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False
        ) as tmp:
            tmp.write(test_code)
            tmp_path = tmp.name

        result = subprocess.run(
            ["node", tmp_path],
            capture_output = True,
            text           = True,
            timeout        = 10
        )

        output = result.stdout.strip()

        if output.startswith("PASS"):
            got = output.split("|")[1] if "|" in output else output
            return {"passed": True,  "got": got}
        elif output.startswith("FAIL"):
            got = output.split("|")[1] if "|" in output else output
            return {"passed": False, "got": got}
        else:
            return {"passed": False, "got": f"ERROR: {result.stderr[:100]}"}

    except subprocess.TimeoutExpired:
        return {"passed": False, "got": "Timed out"}

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── Java ─────────────────────────────────────────
def build_java_test(solution: str, inp: str, expected: str) -> str:
    return f"""
import java.util.*;

public class Solution {{
    {solution}

    public static void main(String[] args) {{
        Solution sol = new Solution();
        String expected = "{expected}".trim();

        try {{
            // basic test runner
            String result = String.valueOf(sol.twoSum(
                new int[]{{2,7,11,15}}, 9
            ));

            if (result.equals(expected)) {{
                System.out.println("PASS|" + result);
            }} else {{
                System.out.println("FAIL|" + result);
            }}
        }} catch(Exception e) {{
            System.out.println("ERROR|" + e.getMessage());
        }}
    }}
}}
"""


def run_java(test_code: str) -> dict:
    tmp_path = None      # ✅
    try:
        with tempfile.NamedTemporaryFile(
            mode     = "w",
            suffix   = ".java",
            prefix   = "Solution",
            delete   = False,
            encoding = "utf-8"   # ✅
        ) as tmp:
            tmp.write(test_code)
            tmp_path = tmp.name

        compile_result = subprocess.run(
            ["javac", tmp_path],
            capture_output = True,
            text           = True,
            timeout        = 15,
            encoding       = "utf-8"   # ✅
        )

        if compile_result.returncode != 0:
            return {
                "passed" : False,
                "got"    : f"Compile error: {compile_result.stderr[:100]}"
            }

        run_result = subprocess.run(
            ["java", "-cp", os.path.dirname(tmp_path), "Solution"],
            capture_output = True,
            text           = True,
            timeout        = 10,
            encoding       = "utf-8"   # ✅
        )

        output = run_result.stdout.strip()

        if output.startswith("PASS"):
            got = output.split("|")[1] if "|" in output else output
            return {"passed": True,  "got": got}
        else:
            got = output.split("|")[1] if "|" in output else output
            return {"passed": False, "got": got}

    except subprocess.TimeoutExpired:
        return {"passed": False, "got": "Timed out"}

    except Exception as e:
        return {"passed": False, "got": f"Runner error: {str(e)[:100]}"}

    finally:
        if tmp_path and os.path.exists(tmp_path):   # ✅
            os.remove(tmp_path)