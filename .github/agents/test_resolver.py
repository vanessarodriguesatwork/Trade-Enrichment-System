"""
test_resolver.py — Statically resolves which test classes are related to the
changed source files in a PR diff, and loads their full source for the agent.

Public API:
    resolve_test_files_for_diff(pr_files, base_test_path, max_chars) -> list[dict]
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


def resolve_test_files_for_diff(
    pr_files: list[dict[str, Any]],
    base_test_path: str = ".",
    max_chars: int = 20000,
) -> list[dict[str, str]]:
    """
    For each changed Java source file in pr_files, find test classes that
    reference it by scanning the test source tree.

    Strategy (static analysis — no runtime overhead):
    1. Extract the simple class name from each changed source file
       e.g. "trade-service/src/main/java/com/example/TradeService.java"
            → "TradeService"
    2. Scan all .java files under base_test_path for that class name
    3. Deduplicate and load full source of matching test files

    Returns a list of dicts (same shape as context_files in review_utils.py):
        [{"path": "...", "content": "...full source...", "reason": "..."}]

    Total character budget across all files is capped at max_chars.
    """
    changed_classes = _extract_changed_class_names(pr_files)
    if not changed_classes:
        print("[test_resolver] No changed Java source classes found in diff")
        return []

    print(f"[test_resolver] Looking for tests covering: {list(changed_classes.keys())}")

    # Find all test files under base_test_path
    test_java_files = _discover_test_java_files(base_test_path)
    print(f"[test_resolver] Scanning {len(test_java_files)} test files")

    # Match test files to changed classes
    matched: dict[str, list[str]] = {}  # test_file_path → [class names it covers]
    for test_file in test_java_files:
        try:
            source = test_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        covering = []
        for class_name, source_path in changed_classes.items():
            if _test_file_references_class(source, class_name):
                covering.append(class_name)

        if covering:
            matched[str(test_file)] = covering

    print(f"[test_resolver] Found {len(matched)} covering test file(s)")

    # Load content, respecting character budget
    result: list[dict[str, str]] = []
    chars_used = 0

    for test_path, covered_classes in sorted(matched.items()):
        if chars_used >= max_chars:
            print(f"[test_resolver] Character budget exhausted, skipping remaining test files")
            break

        try:
            content = Path(test_path).read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            print(f"[test_resolver] Could not read {test_path}: {exc}")
            continue

        remaining = max_chars - chars_used
        if len(content) > remaining:
            content = content[:remaining] + f"\n... [truncated at {remaining} chars]"

        # Make path relative to cwd for cleaner display
        try:
            display_path = str(Path(test_path).relative_to(Path.cwd())).replace("\\", "/")
        except ValueError:
            display_path = test_path.replace("\\", "/")

        result.append({
            "path": display_path,
            "content": content,
            "reason": f"covers: {', '.join(covered_classes)}",
        })
        chars_used += len(content)

    return result


def build_coverage_context_summary(
    diff_coverage: dict[str, Any],
    test_files: list[dict[str, str]],
) -> str:
    """
    Builds a human-readable markdown summary of coverage gaps to prepend
    to the test coverage agent's system or user prompt.

    This gives the agent a quick overview before it has to parse the full JSON.
    """
    lines = ["## Diff Coverage Summary\n"]

    if not diff_coverage:
        lines.append("No coverage data available for changed files.\n")
        return "\n".join(lines)

    for filepath, cov in diff_coverage.items():
        filename = Path(filepath).name
        if not cov.get("has_coverage_data"):
            lines.append(f"- **{filename}**: No Jacoco data (may be untested or excluded)")
            continue

        pct = cov.get("coverage_pct", 0.0)
        missed = cov.get("missed_lines", [])
        covered = cov.get("covered_lines", [])

        status_icon = "✅" if pct == 100.0 else ("⚠️" if pct >= 50 else "❌")
        lines.append(
            f"- {status_icon} **{filename}**: {pct}% of changed lines covered "
            f"({len(covered)} covered, {len(missed)} missed)"
        )
        if missed:
            missed_str = ", ".join(str(ln) for ln in missed[:10])
            suffix = f" ..." if len(missed) > 10 else ""
            lines.append(f"  - Uncovered lines: {missed_str}{suffix}")

    lines.append(f"\n**Covering test files loaded**: {len(test_files)}")
    for tf in test_files:
        lines.append(f"  - `{tf['path']}` ({tf.get('reason', '')})")

    return "\n".join(lines)


# =============================================================================
# Private helpers
# =============================================================================

def _extract_changed_class_names(
    pr_files: list[dict[str, Any]],
) -> dict[str, str]:
    """
    From the list of PR changed files, extract a map of:
        simple class name → repo-relative file path

    Only includes Java source files (not test files themselves, not deleted).
    e.g. {"TradeService": "trade-service/src/main/java/com/example/TradeService.java"}
    """
    result = {}
    for file_obj in pr_files:
        path: str = file_obj.get("filename", "")
        status: str = file_obj.get("status", "")

        if status == "removed":
            continue
        if not path.endswith(".java"):
            continue
        # Skip test files — we're looking for *source* classes to find tests for
        if "/test/" in path:
            continue

        class_name = Path(path).stem  # e.g. "TradeService"
        result[class_name] = path

    return result


def _discover_test_java_files(base_path: str) -> list[Path]:
    """
    Recursively find all .java files under the test source tree.
    Looks in common Maven test locations.
    """
    root = Path(base_path)
    candidates: list[Path] = []

    # Common Maven test source patterns
    search_patterns = [
        "**/src/test/java/**/*.java",
        "**/src/test/**/*.java",
    ]

    for pattern in search_patterns:
        found = list(root.glob(pattern))
        candidates.extend(found)

    # Deduplicate
    seen = set()
    unique = []
    for p in candidates:
        resolved = str(p.resolve())
        if resolved not in seen:
            seen.add(resolved)
            unique.append(p)

    return unique


def _test_file_references_class(test_source: str, class_name: str) -> bool:
    """
    Returns True if the test file's source code references the given class name.

    Checks:
    1. Import statement: "import ...ClassName;"
    2. Direct instantiation or annotation: "new ClassName(" or "@...ClassName"
    3. Type reference: "ClassName " or "ClassName."
    4. Conventional naming: test file is named "<ClassName>Test" or "Test<ClassName>"

    Uses word-boundary matching to avoid false positives
    (e.g. "Trade" matching "TradeService").
    """
    # Word-boundary pattern: class name appears as a whole word
    pattern = re.compile(rf"\b{re.escape(class_name)}\b")
    return bool(pattern.search(test_source))