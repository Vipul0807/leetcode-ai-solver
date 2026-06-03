# backend/scraper.py

import re
import requests
from bs4 import BeautifulSoup
from state import TestCase


# ════════════════════════════════════════════════
# HELPER — extract slug from URL
# ════════════════════════════════════════════════
def extract_slug(url: str) -> str:
    parts = url.rstrip("/").split("/")
    try:
        idx  = parts.index("problems")
        slug = parts[idx + 1]
        return slug
    except (ValueError, IndexError):
        raise ValueError(f"Could not extract slug from URL: {url}")


# ════════════════════════════════════════════════
# HELPER — clean HTML tags from description
# ════════════════════════════════════════════════
def clean_html(raw: str) -> str:
    soup = BeautifulSoup(raw, "html.parser")

    # replace <p> and <br> with newlines
    for tag in soup.find_all(["p", "br"]):
        tag.insert_before("\n")

    # replace <strong> <em> with plain text
    for tag in soup.find_all(["strong", "em", "code"]):
        tag.unwrap()

    text = soup.get_text(separator=" ")

    # clean excessive whitespace
    text = re.sub(r'[ \t]+', ' ', text)

    # clean excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # fix broken words across lines
    text = re.sub(r'\n([a-z,\.\)])', r' \1', text)

    return text.strip()


# ════════════════════════════════════════════════
# HELPER — parse examples from description text
# ════════════════════════════════════════════════
def parse_examples(description: str) -> list[TestCase]:
    examples = []

    # match Input: ... Output: ... blocks
    pattern = re.findall(
        r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=\n|Example|\Z)',
        description,
        re.DOTALL
    )

    for inp, out in pattern:
        # clean up multiline input
        inp = re.sub(r'\s+', ' ', inp).strip()
        out = re.sub(r'\s+', ' ', out).strip()

        # only take first line of output (ignore explanation)
        out = out.split("\n")[0].strip()
        out = out.split("Explanation")[0].strip()

        if inp and out:
            examples.append(TestCase(
                input    = inp,
                expected = out
            ))

    return examples


# ════════════════════════════════════════════════
# MAIN — fetch problem from LeetCode GraphQL API
# ════════════════════════════════════════════════
def fetch_problem(url: str) -> dict:

    slug = extract_slug(url)
    print(f"🔍 Fetching problem: {slug}")

    query = """
    query getQuestion($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            title
            content
            difficulty
            exampleTestcaseList
        }
    }
    """

    response = requests.post(
        url     = "https://leetcode.com/graphql",
        json    = {
            "query"     : query,
            "variables" : { "titleSlug": slug }
        },
        headers = {
            "Content-Type" : "application/json",
            "Referer"      : "https://leetcode.com",
            "User-Agent"   : "Mozilla/5.0"
        },
        timeout = 10
    )

    if response.status_code != 200:
        raise Exception(
            f"LeetCode API returned {response.status_code}"
        )

    data     = response.json()
    question = data.get("data", {}).get("question")

    if not question:
        raise Exception(f"Problem not found for slug: {slug}")

    # clean description
    raw_description = question.get("content", "")
    clean_desc      = clean_html(raw_description)

    # parse examples from cleaned description
    examples = parse_examples(clean_desc)

    # ── fallback if parse_examples found nothing ──
    if not examples:
        print("⚠️ Falling back to exampleTestcaseList")

        raw_examples  = question.get("exampleTestcaseList", [])
        raw_outputs   = re.findall(
            r'Output:\s*(.*?)(?=\n|$)',
            clean_desc
        )

        for i, inp in enumerate(raw_examples):
            expected = raw_outputs[i] if i < len(raw_outputs) else "see description"
            examples.append(TestCase(
                input    = inp.strip(),
                expected = expected.strip()
            ))

    print(f"✅ Found: {question['title']}")
    print(f"📝 Examples found: {len(examples)}")

    return {
        "slug"        : slug,
        "title"       : question["title"],
        "description" : clean_desc,
        "difficulty"  : question.get("difficulty", ""),
        "examples"    : examples
    }


# ════════════════════════════════════════════════
# TEST — run directly to verify
# ════════════════════════════════════════════════
if __name__ == "__main__":
    url    = "https://leetcode.com/problems/two-sum/"
    result = fetch_problem(url)

    print("\n── TITLE ──")
    print(result["title"])

    print("\n── DIFFICULTY ──")
    print(result["difficulty"])

    print("\n── DESCRIPTION (first 400 chars) ──")
    print(result["description"][:400])

    print("\n── EXAMPLES ──")
    for i, ex in enumerate(result["examples"]):
        print(f"\nExample {i+1}:")
        print(f"  Input    : {ex['input']}")
        print(f"  Expected : {ex['expected']}")