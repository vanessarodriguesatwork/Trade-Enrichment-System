"""
functional_context_cache.py — Manages the functional context rules cache.

The cache stores functional rules extracted from Claude's responses across
issue processing runs. Rules accumulate over time so each new issue is
analyzed with full knowledge of all previously discovered rules.

Cache file location: .github/scripts/cache/functional_context.json

Cache format:
{
  "rules": [
    {
      "field": "amount",
      "rule": "amount must always have exactly 2 decimal places",
      "issue_id": "42",
      "applies_to": "all_rows"
    },
    ...
  ],
  "last_updated_by_issue": "42",
  "total_rules": 3
}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CACHE_DIR = Path(__file__).parent / "cache"
_CACHE_FILE = _CACHE_DIR / "functional_context.json"


def load_functional_context_cache() -> list[dict[str, Any]]:
    """
    Load all accumulated functional context rules from the cache file.
    Returns an empty list if the cache doesn't exist or is malformed.
    """
    if not _CACHE_FILE.exists():
        print(f"[functional_context_cache] No cache found at {_CACHE_FILE} — starting fresh")
        return []

    try:
        data = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        rules = data.get("rules", [])
        print(f"[functional_context_cache] Loaded {len(rules)} rule(s) from cache")
        return rules
    except Exception as exc:
        print(f"[functional_context_cache] WARNING: Could not read cache: {exc} — starting fresh")
        return []


def save_functional_context_cache(
    new_rules: list[dict[str, Any]],
    issue_id: Any,
) -> list[dict[str, Any]]:
    """
    Merge new_rules from the current issue into the existing cache and save.

    Deduplication strategy: a rule is considered a duplicate if the same
    (field, rule) combination already exists in the cache — regardless of
    which issue introduced it. New rules from the current issue always win
    (they overwrite older rules with the same field+rule key).

    Returns the full merged rule list after saving.
    """
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    existing_rules = load_functional_context_cache()

    # Build index of existing rules by (field, rule) key for dedup
    existing_index: dict[tuple[str, str], int] = {}
    for i, rule in enumerate(existing_rules):
        key = (rule.get("field", ""), rule.get("rule", ""))
        existing_index[key] = i

    merged = list(existing_rules)

    added = 0
    updated = 0
    for new_rule in new_rules:
        key = (new_rule.get("field", ""), new_rule.get("rule", ""))
        if key in existing_index:
            # Overwrite with the newer version from this issue
            merged[existing_index[key]] = new_rule
            updated += 1
        else:
            merged.append(new_rule)
            existing_index[key] = len(merged) - 1
            added += 1

    cache_data = {
        "rules": merged,
        "last_updated_by_issue": str(issue_id),
        "total_rules": len(merged),
    }

    try:
        _CACHE_FILE.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
        print(
            f"[functional_context_cache] Saved cache — "
            f"{added} new rule(s), {updated} updated, {len(merged)} total"
        )
    except Exception as exc:
        print(f"[functional_context_cache] WARNING: Could not write cache: {exc}")

    return merged


def format_rules_for_prompt(rules: list[dict[str, Any]]) -> str:
    """
    Formats the accumulated functional context rules into a markdown block
    suitable for injection into the Claude prompt.

    Returns an empty string if there are no rules yet (first issue).
    """
    if not rules:
        return ""

    lines = [
        "## Accumulated Functional Context Rules",
        "",
        "These rules have been extracted from previously analyzed issues in this release.",
        "You MUST respect these rules when generating CSV and XML changes.",
        "Do NOT contradict or ignore them — they represent confirmed business logic.",
        "",
    ]

    # Group by applies_to for readability
    for rule in rules:
        field = rule.get("field", "unknown")
        rule_text = rule.get("rule", "")
        applies_to = rule.get("applies_to", "")
        issue_id = rule.get("issue_id", "")

        lines.append(
            f"- **{field}** (issue #{issue_id}, applies to: {applies_to}): {rule_text}"
        )

    return "\n".join(lines)