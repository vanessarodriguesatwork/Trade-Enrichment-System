#!/usr/bin/env python3
"""
memory_update.py

Runs on every PR merge. Takes findings from the candidate file and merges
them into agent_memory.json using Claude to produce a consolidated memory.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import anthropic

# ── Constants ─────────────────────────────────────────────────────────────────

ANTHROPIC_MODEL = "claude-sonnet-5"

_BASE = Path(__file__).parent
MEMORY_FILE    = _BASE / "cache" / "memory" / "agent_memory.json"
# ── Memory helpers ─────────────────────────────────────────────────────────────

def load_memory() -> dict:
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    return {"suppress_rules": []}


def save_memory(memory: dict) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(memory, indent=2), encoding="utf-8")
    print(f"Memory saved to {MEMORY_FILE}")


# ── Pending findings helpers ───────────────────────────────────────────────────


# Candidate path is now dynamic — resolved at runtime using PR_NUMBER
def _candidate_path(pr_number: int) -> Path:
    return _BASE / "cache" / "candidate" / f"agent_memory_{pr_number}.json"


def load_pending_findings(pr_number: int) -> list[dict]:
    path = _candidate_path(pr_number)
    if not path.exists():
        print(f"No candidate findings at {path}. Nothing to update.")
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("findings", [])


def delete_candidate(pr_number: int) -> None:
    path = _candidate_path(pr_number)
    if path.exists():
        path.unlink()
        print(f"Deleted candidate file: {path}")


# ── Agent merge ────────────────────────────────────────────────────────────────

def merge_with_llm(
    candidate_findings: list[dict],
    existing_memory: dict,
    repo: str,
    pr_number: int,
    client: anthropic.Anthropic,
) -> dict:
    """
    Sends candidate findings and existing memory to Claude.
    Claude produces a merged agent_memory.json with deduplicated,
    consolidated suppress rules.
    """
    existing_rules = existing_memory.get("suppress_rules", [])

    prompt = f"""You are maintaining a code review agent's memory file for the repository {repo}.

The agent just completed a review of PR #{pr_number} and produced these findings:

CANDIDATE FINDINGS (from PR #{pr_number}):
{json.dumps(candidate_findings, indent=2)}

EXISTING MEMORY (current suppress_rules already stored):
{json.dumps(existing_rules, indent=2)}

Your task is to produce a merged list of suppress_rules by:
1. Keeping all existing suppress rules as-is
2. For each candidate finding, check if a rule already exists for the same "rule" + "file" combination:
   - If it exists: increment "times_seen" by 1 and update "last_seen_pr" to {pr_number}
   - If it does not exist: add a new suppress rule entry for it
3. All rules should have "active": true
4. Do not duplicate rules — one entry per unique rule+file combination

Each suppress rule must have these fields:
  - rule: string (the finding rule name e.g. "missing_null_check")
  - file_pattern: string (the file path)
  - severity: string (MINOR / MAJOR / CRITICAL)
  - suppress_below: string (same as severity)
  - reason: string (why this is being suppressed)
  - active: true
  - times_seen: integer
  - created_from_pr: integer (pr number when first seen)
  - last_seen_pr: integer (pr number when last seen)
  - repo: "{repo}"

Respond ONLY with a valid JSON object in this exact shape. No explanation, no markdown fences:
{{
  "suppress_rules": [...],
  "last_updated_pr": {pr_number}
}}"""

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    try:
        merged = json.loads(raw)
    except json.JSONDecodeError:
        print(f"WARNING: LLM returned non-JSON. Falling back to simple merge.\n{raw}")
        merged = _fallback_merge(candidate_findings, existing_memory, repo, pr_number)

    return merged


def _fallback_merge(
    candidate_findings: list[dict],
    existing_memory: dict,
    repo: str,
    pr_number: int,
) -> dict:
    """
    Simple deterministic merge used if the LLM call fails or returns bad JSON.
    """
    suppress_rules: list[dict] = existing_memory.get("suppress_rules", [])

    for finding in candidate_findings:
        rule = finding.get("rule", "unknown")
        file_pattern = finding.get("file", "")
        severity = finding.get("severity", "MAJOR")

        existing = next(
            (r for r in suppress_rules
             if r["rule"] == rule and r["file_pattern"] == file_pattern),
            None,
        )

        if existing:
            existing["times_seen"] = existing.get("times_seen", 0) + 1
            existing["last_seen_pr"] = pr_number
            existing["active"] = True
        else:
            suppress_rules.append({
                "rule": rule,
                "file_pattern": file_pattern,
                "severity": severity,
                "suppress_below": severity,
                "reason": "Persisted from candidate at merge",
                "active": True,
                "times_seen": 1,
                "created_from_pr": pr_number,
                "last_seen_pr": pr_number,
                "repo": repo,
            })

    return {"suppress_rules": suppress_rules, "last_updated_pr": pr_number}


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    pr_number = int(os.environ["PR_NUMBER"])
    full_repo = os.environ["REPO"]

    print(f"Memory update starting for PR #{pr_number} in {full_repo}")

    # 1. Load candidate findings
    candidate_findings = load_pending_findings(pr_number)
    if not candidate_findings:
        print("No candidate findings. Nothing to merge.")
        sys.exit(0)

    print(f"Loaded {len(candidate_findings)} candidate findings")

    # 2. Load existing memory
    existing_memory = load_memory()
    existing_count = len(existing_memory.get("suppress_rules", []))
    print(f"Existing suppress rules in memory: {existing_count}")

    # 3. Merge via LLM
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    merged_memory = merge_with_llm(
        candidate_findings=candidate_findings,
        existing_memory=existing_memory,
        repo=full_repo,
        pr_number=pr_number,
        client=client,
    )

    # 4. Save merged memory
    save_memory(merged_memory)

    print("Memory update complete.")
    active_rules = [r for r in merged_memory.get("suppress_rules", []) if r.get("active")]
    print(f"Total active suppress rules: {len(active_rules)}")


if __name__ == "__main__":
    main()