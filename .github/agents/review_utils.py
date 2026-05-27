from __future__ import annotations

import glob
import os
from typing import Any

from config import (
    ALLOWED_SEVERITIES,
    ALLOWED_CATEGORIES,
    ALLOWED_AC_STATUSES,
    SUMMARY_MARKER,
    INLINE_MARKER,
    log,
)
from github_client import (
    list_issue_comments,
    create_issue_comment,
    update_issue_comment,
    post_inline_review_via_api,
    parse_patch_changed_lines,
    is_reviewable_file,
)


# =============================================================================
# Helpers
# =============================================================================

def truncate_text(value: str, max_chars: int) -> str:
    if not value:
        return ""
    if len(value) <= max_chars:
        return value
    return value[:max_chars] + "\n\n...[truncated to fit model token limit]..."


def compact_pr_files_for_prompt(
    pr_files: list[dict[str, Any]],
    max_files: int,
    patch_max_chars: int,
) -> list[dict[str, Any]]:
    compact_files: list[dict[str, Any]] = []

    for file_obj in pr_files[:max_files]:
        patch = file_obj.get("patch", "") or ""
        changed_lines = sorted(parse_patch_changed_lines(patch))

        compact_files.append({
            "filename": file_obj.get("filename"),
            "status": file_obj.get("status"),
            "additions": file_obj.get("additions"),
            "deletions": file_obj.get("deletions"),
            "changes": file_obj.get("changes"),
            "changedLines": changed_lines[:80],
            "patch": truncate_text(patch, patch_max_chars),
        })

    return compact_files


def compact_context_files_for_prompt(
    context_files: list[dict[str, str]],
    context_max_chars: int,
) -> list[dict[str, str]]:
    compact_context: list[dict[str, str]] = []
    remaining = context_max_chars

    for item in context_files:
        if remaining <= 0:
            break

        path = item.get("path", "")
        content = item.get("content", "")
        trimmed = truncate_text(content, min(remaining, 1200))

        compact_context.append({"path": path, "content": trimmed})
        remaining -= len(trimmed)

    return compact_context


# =============================================================================
# Context Retrieval
# =============================================================================

def read_file_safely(path: str, max_chars: int) -> str:
    try:
        if not os.path.exists(path):
            return ""
        if os.path.getsize(path) > 300_000:
            return ""
        with open(path, "r", encoding="utf-8", errors="replace") as file:
            content = file.read(max_chars)
        return content
    except Exception as exc:
        log(f"Unable to read file {path}: {exc}")
        return ""


def discover_related_context_files(
    changed_files: list[str],
    context_max_chars: int,
) -> list[dict[str, str]]:
    """
    Simple heuristic context discovery:
    - Always include changed files' current content.
    - Include likely related Java files by basename patterns.
    """
    candidate_paths: set[str] = set()

    for changed in changed_files:
        if os.path.exists(changed):
            candidate_paths.add(changed)

        basename = os.path.basename(changed)

        if basename.endswith(".java"):
            name_without_ext = basename[:-5]

            candidate_paths.update(glob.glob(f"**/{name_without_ext}Test.java", recursive=True))
            candidate_paths.update(glob.glob(f"**/{name_without_ext}Tests.java", recursive=True))

            if "TradeConsumer" in basename:
                candidate_paths.update(glob.glob("**/Trade.java", recursive=True))
                candidate_paths.update(glob.glob("**/TradeResponseDTO.java", recursive=True))
                candidate_paths.update(glob.glob("**/*TradeConsumer*Test*.java", recursive=True))

            if "Trade" in basename:
                candidate_paths.update(glob.glob("**/TradeConsumer.java", recursive=True))
                candidate_paths.update(glob.glob("**/TradeResponseDTO.java", recursive=True))

    context_files: list[dict[str, str]] = []
    total_chars = 0

    for path in sorted(candidate_paths):
        if not is_reviewable_file(path):
            continue

        remaining = context_max_chars - total_chars
        if remaining <= 0:
            break

        content = read_file_safely(path, max_chars=min(remaining, 6000))
        if not content:
            continue

        context_files.append({"path": path, "content": content})
        total_chars += len(content)

    return context_files


# =============================================================================
# Finding Normalization
# =============================================================================

def severity_rank(severity: str) -> int:
    ranks = {"CRITICAL": 4, "MAJOR": 3, "MINOR": 2, "INFO": 1}
    return ranks.get(str(severity).upper(), 1)


def normalize_severity(value: Any) -> str:
    severity = str(value or "INFO").upper()
    return severity if severity in ALLOWED_SEVERITIES else "INFO"


def normalize_category(value: Any) -> str:
    category = str(value or "CODE_QUALITY").upper()
    return category if category in ALLOWED_CATEGORIES else "CODE_QUALITY"


def normalize_findings(
    raw_findings: list[dict[str, Any]],
    max_findings: int,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for raw in raw_findings:
        if not isinstance(raw, dict):
            continue

        severity = normalize_severity(raw.get("severity"))
        category = normalize_category(raw.get("category"))
        file_path = str(raw.get("file") or "").strip()
        title = str(raw.get("title") or "Review finding").strip()
        body = str(raw.get("body") or "").strip()
        suggested_fix = str(raw.get("suggestedFix") or "").strip()

        line = raw.get("line")
        try:
            line = int(line)
        except (TypeError, ValueError):
            line = None

        ac_raw = raw.get("acceptanceCriteria") or []
        if isinstance(ac_raw, str):
            acceptance_criteria = [ac_raw]
        elif isinstance(ac_raw, list):
            acceptance_criteria = [str(item) for item in ac_raw if item]
        else:
            acceptance_criteria = []

        key = (severity, category, file_path, title)
        if key in seen:
            continue
        seen.add(key)

        normalized.append({
            "severity": severity,
            "category": category,
            "file": file_path,
            "line": line,
            "title": title,
            "body": body,
            "acceptanceCriteria": acceptance_criteria,
            "suggestedFix": suggested_fix,
        })

    normalized.sort(
        key=lambda finding: severity_rank(finding.get("severity", "INFO")),
        reverse=True,
    )

    return normalized[:max_findings]


def resolve_finding_file_path(
    finding_file: str,
    changed_file_paths: list[str],
) -> str | None:
    if not finding_file:
        return None

    finding_file = finding_file.strip()

    if finding_file in changed_file_paths:
        return finding_file

    suffix_matches = [p for p in changed_file_paths if p.endswith(finding_file)]
    if len(suffix_matches) == 1:
        return suffix_matches[0]

    finding_basename = finding_file.split("/")[-1]
    basename_matches = [p for p in changed_file_paths if p.split("/")[-1] == finding_basename]
    if len(basename_matches) == 1:
        return basename_matches[0]

    return None


def split_inline_and_summary_findings(
    findings: list[dict[str, Any]],
    changed_line_index: dict[str, set[int]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    inline_findings: list[dict[str, Any]] = []
    summary_only_findings: list[dict[str, Any]] = []

    changed_file_paths = list(changed_line_index.keys())

    for finding in findings:
        copied = dict(finding)

        resolved_file = resolve_finding_file_path(
            finding_file=str(copied.get("file") or ""),
            changed_file_paths=changed_file_paths,
        )

        if not resolved_file:
            copied["summaryOnlyReason"] = "Finding file is not part of the PR changed files."
            summary_only_findings.append(copied)
            continue

        try:
            line = int(copied.get("line"))
        except (TypeError, ValueError):
            copied["file"] = resolved_file
            copied["summaryOnlyReason"] = "Finding line is missing or invalid."
            summary_only_findings.append(copied)
            continue

        commentable_lines = changed_line_index.get(resolved_file, set())

        if line not in commentable_lines:
            copied["file"] = resolved_file
            copied["line"] = line
            copied["summaryOnlyReason"] = (
                "Finding line is not a changed/commentable line in the PR diff."
            )
            summary_only_findings.append(copied)
            continue

        copied["file"] = resolved_file
        copied["line"] = line
        inline_findings.append(copied)

    return inline_findings, summary_only_findings


# =============================================================================
# Inline PR Review Comments
# =============================================================================

def build_inline_comment_body(finding: dict[str, Any]) -> str:
    severity = finding.get("severity", "INFO")
    category = finding.get("category", "CODE_QUALITY")
    title = finding.get("title", "Review finding")
    body = finding.get("body", "")
    suggested_fix = finding.get("suggestedFix", "")
    ac_list = finding.get("acceptanceCriteria", [])
    ac_text = ", ".join(ac_list) if ac_list else "N/A"

    comment_lines = [
        INLINE_MARKER,
        "",
        f"**{severity} | {category} | {ac_text}**",
        "",
        f"### {title}",
        "",
        body.strip(),
    ]

    if suggested_fix:
        comment_lines.extend([
            "",
            "**Suggested fix:**",
            "",
            suggested_fix.strip(),
        ])

    return "\n".join(comment_lines)


def build_review_comments(
    inline_findings: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return [
        {
            "path": finding["file"],
            "line": finding["line"],
            "body": build_inline_comment_body(finding),
        }
        for finding in inline_findings
    ]


def post_inline_review_comments(
    owner: str,
    repo: str,
    pull_number: int,
    head_sha: str,
    inline_findings: list[dict[str, Any]],
    token: str,
    api_url: str,
) -> int:
    if not inline_findings:
        log("No valid inline findings to publish.")
        return 0

    comments = build_review_comments(inline_findings)
    post_inline_review_via_api(
        owner=owner,
        repo=repo,
        pull_number=pull_number,
        head_sha=head_sha,
        comments=comments,
        token=token,
        api_url=api_url,
    )

    log(f"Posted {len(comments)} inline review comments.")
    return len(comments)


def safe_post_inline_review_comments(
    owner: str,
    repo: str,
    pull_number: int,
    head_sha: str,
    inline_findings: list[dict[str, Any]],
    token: str,
    api_url: str,
) -> tuple[int, list[dict[str, Any]], list[dict[str, Any]]]:
    if not inline_findings:
        return 0, [], []

    try:
        posted_count = post_inline_review_comments(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            head_sha=head_sha,
            inline_findings=inline_findings,
            token=token,
            api_url=api_url,
        )
        return posted_count, inline_findings, []
    except Exception as exc:
        log(f"Failed to post inline comments: {exc}")
        fallback_findings = [
            {
                **finding,
                "summaryOnlyReason": (
                    "Inline comment publishing failed; included in PR summary instead."
                ),
            }
            for finding in inline_findings
        ]
        return 0, [], fallback_findings


# =============================================================================
# PR Summary Comment
# =============================================================================

def find_existing_summary_comment(
    comments: list[dict[str, Any]]
) -> dict[str, Any] | None:
    for comment in comments:
        body = comment.get("body") or ""
        if SUMMARY_MARKER in body:
            return comment
    return None


def post_or_update_summary_comment(
    owner: str,
    repo: str,
    pull_number: int,
    body: str,
    token: str,
    api_url: str,
) -> None:
    if SUMMARY_MARKER not in body:
        body = f"{SUMMARY_MARKER}\n\n{body}"

    comments = list_issue_comments(
        owner=owner,
        repo=repo,
        issue_number=pull_number,
        token=token,
        api_url=api_url,
    )

    existing_comment = find_existing_summary_comment(comments)

    if existing_comment:
        comment_id = existing_comment["id"]
        update_issue_comment(
            owner=owner,
            repo=repo,
            comment_id=comment_id,
            body=body,
            token=token,
            api_url=api_url,
        )
        log(f"Updated summary comment: {comment_id}")
    else:
        created = create_issue_comment(
            owner=owner,
            repo=repo,
            issue_number=pull_number,
            body=body,
            token=token,
            api_url=api_url,
        )
        log(f"Created summary comment: {created.get('id')}")


def count_findings_by_severity(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"CRITICAL": 0, "MAJOR": 0, "MINOR": 0, "INFO": 0}
    for finding in findings:
        severity = normalize_severity(finding.get("severity"))
        counts[severity] += 1
    return counts


def escape_markdown_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def normalize_ac_coverage(
    ac_coverage: list[dict[str, Any]],
) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []

    for item in ac_coverage:
        if not isinstance(item, dict):
            continue

        ac_id = str(item.get("id", "")).strip()
        status = str(item.get("status", "UNKNOWN")).upper().strip()
        notes = str(item.get("notes", "")).strip()

        if status not in ALLOWED_AC_STATUSES:
            status = "UNKNOWN"

        normalized.append({"id": ac_id, "status": status, "notes": notes})

    return normalized


def build_ac_coverage_table(ac_coverage: list[dict[str, Any]]) -> list[str]:
    lines = ["| AC | Status | Notes |", "|---|---|---|"]

    for item in normalize_ac_coverage(ac_coverage):
        ac_id = escape_markdown_table_cell(item.get("id", ""))
        status = escape_markdown_table_cell(item.get("status", "UNKNOWN"))
        notes = escape_markdown_table_cell(item.get("notes", ""))
        lines.append(f"| {ac_id} | {status} | {notes} |")

    return lines


def build_top_findings_section(
    findings: list[dict[str, Any]],
    max_items: int = 10,
) -> list[str]:
    lines: list[str] = []

    sorted_findings = sorted(
        findings,
        key=lambda f: severity_rank(f.get("severity", "INFO")),
        reverse=True,
    )

    for index, finding in enumerate(sorted_findings[:max_items], start=1):
        severity = finding.get("severity", "INFO")
        category = finding.get("category", "CODE_QUALITY")
        title = finding.get("title", "Review finding")
        file_path = finding.get("file", "N/A")
        line = finding.get("line", "N/A")
        ac_list = finding.get("acceptanceCriteria", [])
        ac_text = ", ".join(ac_list) if ac_list else "N/A"
        reason = finding.get("summaryOnlyReason")
        location = f"`{file_path}:{line}`" if file_path != "N/A" else "`N/A`"

        lines.extend([
            f"{index}. **{severity} | {category} | {ac_text}**",
            f"   - **Location:** {location}",
            f"   - **Finding:** {title}",
        ])

        if reason:
            lines.append(f"   - **Note:** {reason}")

        body = finding.get("body")
        if body:
            lines.append(f"   - **Details:** {body}")

        lines.append("")

    if len(findings) > max_items:
        lines.append(f"_Showing top {max_items} findings out of {len(findings)}._")

    return lines


def build_summary_observations_section(
    observations: list[dict[str, Any]]
) -> list[str]:
    lines: list[str] = []

    if not observations:
        lines.append("_No additional observations._")
        return lines

    for item in observations[:10]:
        if not isinstance(item, dict):
            continue

        severity = normalize_severity(item.get("severity"))
        category = normalize_category(item.get("category"))
        body = str(item.get("body", "")).strip()

        if body:
            lines.append(f"- **{severity} | {category}:** {body}")

    if not lines:
        lines.append("_No additional observations._")

    return lines


def build_summary_comment_body(
    requirement_issue: dict[str, Any] | None,
    model_response: dict[str, Any],
    inline_findings: list[dict[str, Any]],
    summary_only_findings: list[dict[str, Any]],
    posted_inline_count: int,
    model: str,
    quality_gate_failed: bool,
    fail_on_severity: str,
) -> str:
    all_findings = inline_findings + summary_only_findings
    severity_counts = count_findings_by_severity(all_findings)
    ac_coverage = model_response.get("acceptanceCriteriaCoverage", [])
    summary_observations = model_response.get("summaryObservations", [])
    overall_result = model_response.get("overallResult", "UNKNOWN")

    requirement_text = "Not resolved from commit message"
    if requirement_issue:
        requirement_text = (
            f"#{requirement_issue.get('number')} - "
            f"{requirement_issue.get('title')}"
        )

    lines = [
        SUMMARY_MARKER,
        "",
        "## Agentic PR Review Summary",
        "",
        f"**Requirement Issue:** {requirement_text}  ",
        f"**Model:** `{model}`  ",
        "**Review Scope:** Changed files only. Surrounding files used for context.",
        "",
        "### Result",
        "",
        f"**{overall_result}**",
        "",
        "### Inline Review Comments",
        "",
        f"Posted inline comments: **{posted_inline_count}**  ",
        f"Summary-only findings: **{len(summary_only_findings)}**",
        "",
        "> Findings appear in this summary when they could not be safely mapped to a changed line in the PR diff.",
        "",
        "### Severity Counts",
        "",
        "| Severity | Count |",
        "|---|---:|",
        f"| CRITICAL | {severity_counts.get('CRITICAL', 0)} |",
        f"| MAJOR | {severity_counts.get('MAJOR', 0)} |",
        f"| MINOR | {severity_counts.get('MINOR', 0)} |",
        f"| INFO | {severity_counts.get('INFO', 0)} |",
        "",
        "### Acceptance Criteria Coverage",
        "",
    ]

    if ac_coverage:
        lines.extend(build_ac_coverage_table(ac_coverage))
    else:
        lines.append("_No acceptance criteria coverage returned._")

    lines.extend(["", "### Top Findings", ""])

    if all_findings:
        lines.extend(build_top_findings_section(all_findings))
    else:
        lines.append("_No findings reported._")

    lines.extend(["", "### Additional Observations", ""])
    lines.extend(build_summary_observations_section(summary_observations))
    lines.extend(["", "### Quality Gate", ""])

    if quality_gate_failed:
        lines.append(
            f"**Failed** because findings include `{fail_on_severity}` or higher severity."
        )
    else:
        lines.append(
            f"**Passed**. No findings at `{fail_on_severity}` or higher severity."
        )

    lines.extend(["", "---", "_Generated by Agentic PR Review._"])

    return "\n".join(lines)


# =============================================================================
# Quality Gate
# =============================================================================

def should_fail_build(
    findings: list[dict[str, Any]],
    fail_on_severity: str,
) -> bool:
    threshold = severity_rank(fail_on_severity)
    return any(severity_rank(f.get("severity", "INFO")) >= threshold for f in findings)


# =============================================================================
# Failure Summary Helper
# =============================================================================

def post_failure_summary_safely(
    config: dict[str, Any],
    pr_event: dict[str, Any] | None,
    message: str,
) -> None:
    if not pr_event:
        return

    try:
        body = "\n".join([
            SUMMARY_MARKER,
            "",
            "## Agentic PR Review Summary",
            "",
            "**Result:** FAILED",
            "",
            "The agentic PR review could not complete.",
            "",
            f"**Reason:** {message}",
            "",
            "---",
            "_Generated by Agentic PR Review._",
        ])

        post_or_update_summary_comment(
            owner=config["owner"],
            repo=config["repo"],
            pull_number=pr_event["pull_number"],
            body=body,
            token=config["token"],
            api_url=config["api_url"],
        )
    except Exception as exc:
        log(f"Unable to post failure summary: {exc}")