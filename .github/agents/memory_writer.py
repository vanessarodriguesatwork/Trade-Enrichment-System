from __future__ import annotations
import json
from pathlib import Path


_BASE = Path(__file__).parent  # resolves to .github/agents/ wherever the script lives

MEMORY_FILE    = _BASE / "cache" / "memory" / "agent_memory.json"
def _candidate_path(pr_number: int) -> Path:
    """Returns the candidate file path for a specific PR."""
    return _BASE / "cache" / "candidate" / f"agent_memory_{pr_number}.json"



def save_pending_findings(pr_number: int, findings: list[dict]) -> None:
    """
    Saves normalized findings to a PR-specific candidate file.
    memory_update.py looks for this file by PR number at merge time.
    """
    path = _candidate_path(pr_number)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"pr_number": pr_number, "findings": findings}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Saved {len(findings)} pending findings to {path}")

def load_suppress_rules(repo: str) -> list[dict]:
    """
    Loads active suppress rules from the stable memory folder.
    Returns empty list if no memory file exists yet.
    """
    if not MEMORY_FILE.exists():
        return []
    with open(MEMORY_FILE) as f:
        memory = json.load(f)
    rules = memory.get("suppress_rules", [])
    return [r for r in rules if r.get("repo") == repo and r.get("active", False)]


def format_suppress_rules_for_prompt(suppress_rules: list[dict]) -> str:
    if not suppress_rules:
        return ""
    lines = ["SUPPRESS RULES — do not raise findings below the stated severity for these patterns:\n"]
    for rule in suppress_rules:
        lines.append(
            f"- Rule: {rule['rule']} | File: {rule['file_pattern']} | "
            f"Suppress below: {rule['suppress_below']} | "
            f"Reason: {rule['reason']} | "
            f"Seen {rule.get('times_seen', rule.get('times_ignored', 0))}x (last PR #{rule['last_seen_pr']})"
        )
    return "\n".join(lines)