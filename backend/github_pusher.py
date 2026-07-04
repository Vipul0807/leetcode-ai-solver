# backend/github_pusher.py

import base64
import requests
from datetime import datetime


# ════════════════════════════════════════════════
# GITHUB API BASE
# ════════════════════════════════════════════════
GITHUB_API = "https://api.github.com"
REPO_NAME  = "leetcode-problems"


# ════════════════════════════════════════════════
# HELPER — get or create repo
# ════════════════════════════════════════════════
def ensure_repo_exists(token: str, username: str) -> bool:
    """
    Check if leetcode-problems repo exists
    If not → create it automatically
    """
    headers = {
        "Authorization" : f"token {token}",
        "Accept"        : "application/vnd.github.v3+json"
    }

    # check if repo exists
    res = requests.get(
        f"{GITHUB_API}/repos/{username}/{REPO_NAME}",
        headers = headers
    )

    if res.status_code == 200:
        print(f"✅ Repo exists: {username}/{REPO_NAME}")
        return True

    # create repo if not found
    if res.status_code == 404:
        print(f"📁 Creating repo: {REPO_NAME}")
        create_res = requests.post(
            f"{GITHUB_API}/user/repos",
            headers = headers,
            json    = {
                "name"        : REPO_NAME,
                "description" : "My LeetCode solutions — auto pushed by AI Solver",
                "private"     : False,
                "auto_init"   : True   # creates main branch with README
            }
        )

        if create_res.status_code == 201:
            print(f"✅ Repo created: {username}/{REPO_NAME}")
            return True
        else:
            print(f"❌ Repo creation failed: {create_res.json()}")
            return False

    return False


# ════════════════════════════════════════════════
# HELPER — get file SHA (needed for update)
# ════════════════════════════════════════════════
def get_file_sha(
    token    : str,
    username : str,
    path     : str
) -> str | None:
    """
    GitHub API needs SHA of existing file to update it
    Returns None if file does not exist yet
    """
    headers = {
        "Authorization" : f"token {token}",
        "Accept"        : "application/vnd.github.v3+json"
    }

    res = requests.get(
        f"{GITHUB_API}/repos/{username}/{REPO_NAME}/contents/{path}",
        headers = headers
    )

    if res.status_code == 200:
        return res.json().get("sha")

    return None


# ════════════════════════════════════════════════
# HELPER — push one file to GitHub
# ════════════════════════════════════════════════
def push_file(
    token    : str,
    username : str,
    path     : str,
    content  : str,
    message  : str
) -> bool:
    """
    Create or update a file in the GitHub repo
    """
    headers = {
        "Authorization" : f"token {token}",
        "Accept"        : "application/vnd.github.v3+json"
    }

    # encode content to base64
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    # check if file already exists
    sha = get_file_sha(token, username, path)

    body = {
        "message" : message,
        "content" : encoded,
    }

    # if file exists → include sha for update
    if sha:
        body["sha"] = sha

    res = requests.put(
        f"{GITHUB_API}/repos/{username}/{REPO_NAME}/contents/{path}",
        headers = headers,
        json    = body
    )

    if res.status_code in [200, 201]:
        print(f"✅ Pushed: {path}")
        return True
    else:
        print(f"❌ Push failed: {path} → {res.json()}")
        return False


# ════════════════════════════════════════════════
# HELPER — build README for problem folder
# ════════════════════════════════════════════════

# def build_readme(
#     title       : str,
#     difficulty  : str,
#     description : str,
#     examples    : list,
#     language    : str,
#     attempts    : int
# ) -> str:
#     """
#     Build a clean README.md for the problem folder
#     """
#     # format examples
#     examples_md = ""
#     for i, ex in enumerate(examples):
#         examples_md += f"""
# ### Example {i + 1}
# """

#     # language badge
#     lang_badge = {
#         "python"     : "🐍 Python",
#         "javascript" : "🟨 JavaScript",
#         "java"       : "☕ Java"
#     }.get(language, language)

#     date = datetime.now().strftime("%Y-%m-%d")

#     return f"""# {title}

# ![Difficulty](https://img.shields.io/badge/Difficulty-{difficulty}-{'green' if difficulty == 'Easy' else 'orange' if difficulty == 'Medium' else 'red'})
# ![Language](https://img.shields.io/badge/Language-{language}-blue)
# ![Status](https://img.shields.io/badge/Status-Accepted-brightgreen)

# ## Problem

# {description[:500]}...

# ## Examples
# {examples_md}

# ## Solution

# Language : {lang_badge}
# Attempts : {attempts}
# Solved   : {date}
# Pushed by: [LeetCode AI Solver](https://github.com/Vipul0807/leetcode-ai-solver)
# """


def build_readme(
    title       : str,
    difficulty  : str,
    description : str,
    examples    : list,
    language    : str,
    attempts    : int,
    username    : str = ""     # ✅ add username param
) -> str:

    # ✅ handle both TestCase and TestResult formats
    examples_md = ""
    for i, ex in enumerate(examples):
        if isinstance(ex, dict):
            # TestResult format → has input/expected/got/passed
            inp = ex.get("input",    "") or ex.get("inp", "")
            exp = ex.get("expected", "") or ex.get("exp", "")
        else:
            inp = str(ex)
            exp = ""

        if inp or exp:
            examples_md += f"""
    ### Example {i + 1}
    Input    : {inp}
    Expected : {exp}

    """

    lang_badge = {
        "python"     : "🐍 Python",
        "javascript" : "🟨 JavaScript",
        "java"       : "☕ Java"
    }.get(language, language)

    color = {
        "Easy"   : "green",
        "Medium" : "orange",
        "Hard"   : "red"
    }.get(difficulty, "blue")

    date      = datetime.now().strftime("%Y-%m-%d")

    # ✅ use actual username in link
    repo_link = f"https://github.com/{username}/leetcode-ai-solver" if username else "https://github.com"

    return f"""# {title}

![Difficulty](https://img.shields.io/badge/Difficulty-{difficulty}-{color})
![Language](https://img.shields.io/badge/Language-{language}-blue)
![Status](https://img.shields.io/badge/Status-Accepted-brightgreen)

## Problem

{description[:500] if description else "See LeetCode for full problem description."}

## Examples
{examples_md if examples_md else "_No examples extracted_"}

## Solution Info

| Field    | Value        |
|----------|--------------|
| Language | {lang_badge} |
| Attempts | {attempts}   |
| Solved   | {date}       |

---
*Auto pushed by [LeetCode AI Solver]({repo_link})*
"""

# ════════════════════════════════════════════════
# MAIN — push solution to GitHub
# ════════════════════════════════════════════════
# def push_solution(
#     token       : str,
#     username    : str,
#     slug        : str,
#     title       : str,
#     difficulty  : str,
#     description : str,
#     examples    : list,
#     code        : str,
#     language    : str,
#     attempts    : int
# ) -> dict:
#     """
#     Push solution + README to GitHub

#     Creates:
#       leetcode-problems/
#         └── two-sum/
#             ├── solution.py
#             └── README.md
#     """

#     print(f"\n🚀 Pushing to GitHub: {slug}")

#     # step 1 — ensure repo exists
#     if not ensure_repo_exists(token, username):
#         return {
#             "success" : False,
#             "message" : "Could not create or find GitHub repo"
#         }

#     # step 2 — file extension by language
#     ext = {
#         "python"     : "py",
#         "javascript" : "js",
#         "java"       : "java"
#     }.get(language, "txt")

#     # step 3 — build file paths
#     solution_path = f"{slug}/solution.{ext}"
#     readme_path   = f"{slug}/README.md"

#     # step 4 — build README content
#     readme_content = build_readme(
#         title       = title,
#         difficulty  = difficulty,
#         description = description,
#         examples    = examples,
#         language    = language,
#         attempts    = attempts
#     )

#     # step 5 — add header comment to solution
#     comments = {
#         "python"     : f"# {title}\n# Difficulty: {difficulty}\n# Language: Python\n\n",
#         "javascript" : f"// {title}\n// Difficulty: {difficulty}\n// Language: JavaScript\n\n",
#         "java"       : f"// {title}\n// Difficulty: {difficulty}\n// Language: Java\n\n"
#     }
#     solution_with_header = comments.get(language, "") + code

#     # step 6 — commit message
#     commit_msg = f"✅ solve: {title} [{difficulty}] — {language}"

#     # step 7 — push both files
#     solution_ok = push_file(
#         token    = token,
#         username = username,
#         path     = solution_path,
#         content  = solution_with_header,
#         message  = commit_msg
#     )

#     readme_ok = push_file(
#         token    = token,
#         username = username,
#         path     = readme_path,
#         content  = readme_content,
#         message  = commit_msg
#     )

#     if solution_ok and readme_ok:
#         return {
#             "success"  : True,
#             "message"  : f"Pushed to github.com/{username}/{REPO_NAME}/{slug}",
#             "url"      : f"https://github.com/{username}/{REPO_NAME}/tree/main/{slug}"
#         }
#     else:
#         return {
#             "success"  : False,
#             "message"  : "Push failed — check token and username"
#         }



def push_solution(
    token       : str,
    username    : str,
    slug        : str,
    title       : str,
    difficulty  : str,
    description : str,
    examples    : list,
    code        : str,
    language    : str,
    attempts    : int
) -> dict:

    print(f"\n🚀 Push request: {slug} → {username}")

    if not ensure_repo_exists(token, username):
        return {
            "success" : False,
            "message" : "Could not create or find GitHub repo"
        }

    ext = {
        "python"     : "py",
        "javascript" : "js",
        "java"       : "java"
    }.get(language, "txt")

    solution_path = f"{slug}/solution.{ext}"
    readme_path   = f"{slug}/README.md"

    readme_content = build_readme(
        title       = title,
        difficulty  = difficulty,
        description = description,
        examples    = examples,
        language    = language,
        attempts    = attempts,
        username    = username      # ✅ pass username
    )

    comments = {
        "python"     : f"# {title}\n# Difficulty: {difficulty}\n# Language: Python\n\n",
        "javascript" : f"// {title}\n// Difficulty: {difficulty}\n// Language: JavaScript\n\n",
        "java"       : f"// {title}\n// Difficulty: {difficulty}\n// Language: Java\n\n"
    }
    solution_content = comments.get(language, "") + code
    commit_msg       = f"✅ solve: {title} [{difficulty}] — {language}"

    solution_ok = push_file(
        token    = token,
        username = username,
        path     = solution_path,
        content  = solution_content,
        message  = commit_msg
    )

    readme_ok = push_file(
        token    = token,
        username = username,
        path     = readme_path,
        content  = readme_content,
        message  = commit_msg
    )

    if solution_ok and readme_ok:
        url = f"https://github.com/{username}/{REPO_NAME}/tree/main/{slug}"
        print(f"✅ Push complete: {url}")
        return {
            "success" : True,
            "message" : f"Pushed to {url}",
            "url"     : url
        }
    else:
        return {
            "success" : False,
            "message" : "One or more files failed to push"
        }