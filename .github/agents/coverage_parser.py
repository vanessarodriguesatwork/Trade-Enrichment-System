"""
coverage_parser.py — Parses Jacoco XML coverage report and maps diff lines
to covered/missed status.

Public API:
    parse_jacoco_coverage(jacoco_xml_path)  -> CoverageMap
    map_diff_to_coverage(pr_files, coverage_map, repo_root) -> DiffCoverageReport
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

# Type aliases
# { "src/main/java/com/example/TradeService.java": { 42: "covered" | "missed" | "partial" } }
CoverageMap = dict[str, dict[int, str]]

# Per-file diff coverage summary
DiffCoverageReport = dict[str, dict[str, Any]]


def parse_jacoco_coverage(jacoco_xml_path: str) -> CoverageMap:
    """
    Parse jacoco.xml and return a map of:
        repo-relative source path  →  { line_number: status }
    where status is one of: "covered", "missed", "partial".

    Jacoco stores source paths as package-relative (e.g. "com/example/Foo.java").
    This function resolves them by scanning common Maven source roots so callers
    get paths relative to the repo root (e.g.
    "trade-service/src/main/java/com/example/Foo.java").

    If the XML file doesn't exist (e.g. no tests ran), returns an empty dict.
    """
    xml_path = Path(jacoco_xml_path)
    if not xml_path.exists():
        print(f"[coverage_parser] WARNING: jacoco.xml not found at {jacoco_xml_path}")
        return {}

    try:
        # Jacoco XML uses a DOCTYPE that Python's parser can't resolve — strip it.
        raw = xml_path.read_text(encoding="utf-8")
        # Remove DOCTYPE declaration to avoid network fetch attempt
        raw = _strip_doctype(raw)
        root = ET.fromstring(raw)
    except Exception as exc:
        print(f"[coverage_parser] ERROR parsing jacoco.xml: {exc}")
        return {}

    coverage_map: CoverageMap = {}

    for package_el in root.iter("package"):
        package_name = package_el.get("name", "")  # e.g. "com/example/service"

        for sourcefile_el in package_el.iter("sourcefile"):
            filename = sourcefile_el.get("name", "")  # e.g. "TradeService.java"
            jacoco_relative = f"{package_name}/{filename}"  # e.g. "com/example/service/TradeService.java"

            line_map: dict[int, str] = {}
            for line_el in sourcefile_el.iter("line"):
                line_nr = int(line_el.get("nr", 0))
                missed_instructions = int(line_el.get("mi", 0))
                covered_instructions = int(line_el.get("ci", 0))

                if covered_instructions > 0 and missed_instructions > 0:
                    status = "partial"
                elif covered_instructions > 0:
                    status = "covered"
                else:
                    status = "missed"

                line_map[line_nr] = status

            if line_map:
                coverage_map[jacoco_relative] = line_map

    print(f"[coverage_parser] Parsed {len(coverage_map)} source files from jacoco.xml")
    return coverage_map


def map_diff_to_coverage(
    pr_files: list[dict[str, Any]],
    coverage_map: CoverageMap,
    repo_root: str = ".",
) -> DiffCoverageReport:
    """
    For each file in the PR diff, look up its changed lines in the coverage map
    and produce a per-file coverage summary.

    Returns:
    {
      "trade-service/src/main/java/com/example/TradeService.java": {
        "changed_lines": [42, 43, 44],
        "covered_lines": [42, 44],
        "missed_lines":  [43],
        "partial_lines": [],
        "coverage_pct":  66.7,
        "has_coverage_data": True,
      },
      ...
    }

    Files with no coverage data (e.g. resource files, deleted files) get
    has_coverage_data=False and are still included so the agent knows they
    were changed but couldn't be verified.
    """
    # Build a lookup: jacoco_relative_path → repo_relative_path
    # e.g. "com/example/TradeService.java" → "trade-service/src/main/.../TradeService.java"
    jacoco_to_repo = _build_jacoco_to_repo_index(coverage_map, repo_root)

    report: DiffCoverageReport = {}

    for file_obj in pr_files:
        repo_path: str = file_obj.get("filename", "")
        if not repo_path.endswith(".java"):
            continue  # Only Java files are relevant for Jacoco

        status = file_obj.get("status", "")
        if status == "removed":
            continue  # No coverage data for deleted files

        changed_lines = _extract_added_lines_from_patch(file_obj.get("patch", ""))
        if not changed_lines:
            continue

        # Find this file in the jacoco index
        file_coverage = _lookup_coverage(repo_path, jacoco_to_repo, coverage_map)

        if file_coverage is None:
            report[repo_path] = {
                "changed_lines": changed_lines,
                "covered_lines": [],
                "missed_lines":  changed_lines,
                "partial_lines": [],
                "coverage_pct":  0.0,
                "has_coverage_data": False,
            }
            continue

        covered, missed, partial = [], [], []
        for line in changed_lines:
            line_status = file_coverage.get(line)
            if line_status == "covered":
                covered.append(line)
            elif line_status == "partial":
                partial.append(line)
            elif line_status == "missed":
                missed.append(line)
            # lines not in Jacoco at all (blank/comment) → ignored

        measurable = len(covered) + len(missed) + len(partial)
        pct = round((len(covered) + len(partial) * 0.5) / measurable * 100, 1) if measurable else 0.0

        report[repo_path] = {
            "changed_lines": changed_lines,
            "covered_lines": covered,
            "missed_lines":  missed,
            "partial_lines": partial,
            "coverage_pct":  pct,
            "has_coverage_data": True,
        }

    print(f"[coverage_parser] Mapped coverage for {len(report)} changed Java files")
    return report


# =============================================================================
# Private helpers
# =============================================================================

def _strip_doctype(xml_text: str) -> str:
    """Remove DOCTYPE declaration so ElementTree doesn't try to fetch the DTD."""
    import re
    return re.sub(r"<!DOCTYPE[^>]*>", "", xml_text, flags=re.DOTALL)


def _extract_added_lines_from_patch(patch: str) -> list[int]:
    """
    Parse a unified diff patch string and return the list of line numbers
    that were ADDED (lines starting with '+', not '+++').

    Hunk headers look like: @@ -a,b +c,d @@
    We track the current line number in the new file.
    """
    if not patch:
        return []

    import re
    added_lines: list[int] = []
    current_line = 0
    hunk_header = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

    for raw_line in patch.splitlines():
        hunk_match = hunk_header.match(raw_line)
        if hunk_match:
            current_line = int(hunk_match.group(1))
            continue

        if raw_line.startswith("+++") or raw_line.startswith("---"):
            continue

        if raw_line.startswith("+"):
            added_lines.append(current_line)
            current_line += 1
        elif raw_line.startswith("-"):
            pass  # removed line — don't advance new-file counter
        else:
            current_line += 1  # context line

    return added_lines


def _build_jacoco_to_repo_index(
    coverage_map: CoverageMap,
    repo_root: str,
) -> dict[str, str]:
    """
    Build a reverse index:
        jacoco_relative (e.g. "com/example/Foo.java")
        → repo_relative  (e.g. "trade-service/src/main/java/com/example/Foo.java")

    Strategy: scan the repo for actual .java files and match by the suffix
    that Jacoco reports.
    """
    index: dict[str, str] = {}
    root = Path(repo_root)

    # Find all .java files under common Maven source roots
    java_files: list[Path] = []
    for pattern in ["**/src/main/java/**/*.java", "**/src/test/java/**/*.java"]:
        java_files.extend(root.glob(pattern))

    for java_file in java_files:
        try:
            repo_relative = str(java_file.relative_to(root)).replace("\\", "/")
        except ValueError:
            repo_relative = str(java_file).replace("\\", "/")

        # The jacoco key is the package-relative path, e.g. "com/example/Foo.java"
        # We match it by checking if repo_relative ends with the jacoco key
        for jacoco_key in coverage_map:
            if repo_relative.endswith(jacoco_key):
                index[jacoco_key] = repo_relative
                break

    return index


def _lookup_coverage(
    repo_path: str,
    jacoco_to_repo: dict[str, str],
    coverage_map: CoverageMap,
) -> dict[int, str] | None:
    """
    Given a repo-relative path, find the matching coverage data in the map.
    Returns None if no coverage data is found.
    """
    # Reverse lookup: find the jacoco key whose repo path matches
    for jacoco_key, mapped_repo_path in jacoco_to_repo.items():
        if mapped_repo_path == repo_path:
            return coverage_map.get(jacoco_key)

    # Fallback: try matching by filename suffix directly
    for jacoco_key, line_map in coverage_map.items():
        if repo_path.endswith(jacoco_key):
            return line_map

    return None