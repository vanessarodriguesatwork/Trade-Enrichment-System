#!/usr/bin/env python3
"""
Agentic PR Review Agent v1

Runs inside GitHub Actions after Maven compile succeeds.

Responsibilities:
- Read PR metadata from GitHub Actions event payload
- Extract Requirement Issue ID from commit message format:
    <issue id> - <issue title>
- Fetch Requirement Issue from GitHub Issues
- Fetch PR changed files and patches
- Read changed/context files from local checkout
- Call GitHub Models inference API
- Normalize model findings
- Post inline PR review comments
- Create/update PR summary comment
- Fail the step based on configured severity threshold

No external Python dependencies required.
"""

from __future__ import annotations

import json
import os
import re
import sys
import glob
import urllib.request
import urllib.error
from typing import Any
from anthropic import Anthropic

SUMMARY_MARKER = "<!-- agentic-pr-review-summary -->"
INLINE_MARKER = "<!-- agentic-pr-review -->"

DEFAULT_MODEL = "openai/gpt-4.1"
DEFAULT_API_URL = "https://api.github.com"
GITHUB_MODELS_ENDPOINT = "https://models.github.ai/inference/chat/completions"

ALLOWED_SEVERITIES = {"CRITICAL", "MAJOR", "MINOR", "INFO"}
ALLOWED_CATEGORIES = {
    "FUNCTIONAL",
    "CODE_QUALITY",
    "KAFKA",
    "SPRING",
    "TEST_COVERAGE",
    "SECURITY",
    "OBSERVABILITY",
}

ALLOWED_AC_STATUSES = {
    "PASS",
    "PARTIAL",
    "FAIL",
    "NOT_APPLICABLE",
    "UNKNOWN",
}

REVIEWABLE_EXTENSIONS = (
    ".java",
    ".xml",
    ".yml",
    ".yaml",
    ".properties",
    ".json",
)

EXCLUDED_PATH_PARTS = (
    "/target/",
    "/.git/",
    "/build/",
    "/out/",
)


# =============================================================================
# Logging
# =============================================================================

def log(message: str) -> None:
    print(f"[agentic-review] {message}", flush=True)


# =============================================================================
# Configuration
# =============================================================================

def load_config() -> dict[str, Any]:
    token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    event_path = os.environ.get("GITHUB_EVENT_PATH")

    if not token:
        raise RuntimeError("GITHUB_TOKEN is required.")

    if not repository or "/" not in repository:
        raise RuntimeError("GITHUB_REPOSITORY must be in owner/repo format.")

    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH is required.")

    owner, repo = repository.split("/", 1)

    return {
        "token": token,
        "repository": repository,
        "owner": owner,
        "repo": repo,
        "event_path": event_path,
        "api_url": os.environ.get("GITHUB_API_URL", DEFAULT_API_URL),
        "model": os.environ.get("REVIEW_MODEL", DEFAULT_MODEL),
        "fail_on_severity": os.environ.get("REVIEW_FAIL_ON_SEVERITY", "MAJOR").upper(),
        "max_findings": int(os.environ.get("REVIEW_MAX_FINDINGS", "20")),
        "context_max_chars": int(os.environ.get("REVIEW_CONTEXT_MAX_CHARS", "3000")),
        "patch_max_chars": int(os.environ.get("REVIEW_PATCH_MAX_CHARS", "2500")),
        "max_changed_files": int(os.environ.get("REVIEW_MAX_CHANGED_FILES", "8")),
        "model_provider": os.environ.get("REVIEW_MODEL_PROVIDER", "github_models"),
        "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY"),
    }

# =============================================================================
# Claude Opus call function
# =============================================================================

def split_system_messages(
    messages: list[dict[str, str]],
) -> tuple[str | None, list[dict[str, str]]]:
    """
    Anthropic Messages API requires system prompt as top-level `system`,
    not as a message role.
    """
    system_parts: list[str] = []
    normal_messages: list[dict[str, str]] = []

    for message in messages:
        role = message.get("role")
        content = message.get("content", "")

        if role == "system":
            if content:
                system_parts.append(content)
        else:
            normal_messages.append(message)

    system_prompt = "\n\n".join(system_parts) if system_parts else None
    return system_prompt, normal_messages


def call_anthropic_model(
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int = 8192,
    temperature: float = 0.1,
) -> str:
    client = Anthropic(api_key=api_key)

    system_prompt, normal_messages = split_system_messages(messages)

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=normal_messages,
    )

    return response.content[0].text

# =============================================================================
# Unified model caller
# =============================================================================

def call_model(
    config: dict,
    messages: list[dict[str, str]],
    temperature: float = 0.1,
) -> str:
    provider = config["model_provider"]

    if provider == "anthropic":
        if not config.get("anthropic_api_key"):
            raise RuntimeError("ANTHROPIC_API_KEY missing")

        return call_anthropic_model(
            api_key=config["anthropic_api_key"],
            model=config["model"],
            messages=messages,
            max_tokens=8192,
            temperature=temperature,
        )

    raise RuntimeError(f"Unsupported model provider: {provider}")

# =============================================================================
# HTTP / GitHub API Client
# =============================================================================

def github_request(
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> Any:
    data = None

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "agentic-pr-review",
    }

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")
            if not response_body:
                return None
            return json.loads(response_body)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub API request failed: {method} {url}, "
            f"status={exc.code}, body={error_body}"
        ) from exc


def get_paginated(
    url: str,
    token: str,
) -> list[dict[str, Any]]:
    all_items: list[dict[str, Any]] = []
    page = 1

    while True:
        separator = "&" if "?" in url else "?"
        page_url = f"{url}{separator}per_page=100&page={page}"

        batch = github_request(
            method="GET",
            url=page_url,
            token=token,
        )

        if not batch:
            break

        all_items.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    return all_items


# =============================================================================
# PR Metadata
# =============================================================================

def get_pr_event(event_path: str) -> dict[str, Any]:
    with open(event_path, "r", encoding="utf-8") as file:
        event = json.load(file)

    pull_request = event.get("pull_request")
    if not pull_request:
        raise RuntimeError("This script must run on a pull_request event.")

    return {
        "pull_number": pull_request["number"],
        "title": pull_request.get("title", ""),
        "body": pull_request.get("body", ""),
        "base_ref": pull_request.get("base", {}).get("ref"),
        "head_ref": pull_request.get("head", {}).get("ref"),
        "base_sha": pull_request.get("base", {}).get("sha"),
        "head_sha": pull_request.get("head", {}).get("sha"),
    }


def get_pr_commits(
    owner: str,
    repo: str,
    pull_number: int,
    token: str,
    api_url: str,
) -> list[dict[str, Any]]:
    url = f"{api_url}/repos/{owner}/{repo}/pulls/{pull_number}/commits"
    return get_paginated(url=url, token=token)


def extract_requirement_issue_from_commits(
    commits: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """
    Expected commit message:
      2 - Add Buyer/Seller Indicator (B/S) to Enriched Trade Output

    If multiple commits match, use latest matching commit.
    """
    pattern = re.compile(r"^(\d+)\s*-\s*(.+)$")

    matched: dict[str, Any] | None = None

    for commit_obj in commits:
        message = (
            commit_obj
            .get("commit", {})
            .get("message", "")
            .splitlines()[0]
            .strip()
        )

        match = pattern.match(message)
        if match:
            matched = {
                "issue_id": int(match.group(1)),
                "title_from_commit": match.group(2).strip(),
                "matched_commit": message,
            }

    return matched


def get_requirement_issue(
    owner: str,
    repo: str,
    issue_id: int,
    token: str,
    api_url: str,
) -> dict[str, Any]:
    url = f"{api_url}/repos/{owner}/{repo}/issues/{issue_id}"
    return github_request(method="GET", url=url, token=token)


# =============================================================================
# PR Files / Diff
# =============================================================================

def get_pr_files(
    owner: str,
    repo: str,
    pull_number: int,
    token: str,
    api_url: str,
) -> list[dict[str, Any]]:
    url = f"{api_url}/repos/{owner}/{repo}/pulls/{pull_number}/files"
    files = get_paginated(url=url, token=token)
    return [file_obj for file_obj in files if is_reviewable_file(file_obj.get("filename", ""))]


def is_reviewable_file(path: str) -> bool:
    if not path:
        return False

    normalized = "/" + path.replace("\\", "/")

    for excluded in EXCLUDED_PATH_PARTS:
        if excluded in normalized:
            return False

    return path.endswith(REVIEWABLE_EXTENSIONS)


def parse_patch_changed_lines(patch: str) -> set[int]:
    """
    Parse unified diff patch and return new-file line numbers that were added.

    GitHub inline comments using `line` should target lines in the new version
    that are present in the PR diff.
    """
    changed_lines: set[int] = set()

    if not patch:
        return changed_lines

    new_line: int | None = None

    for raw_line in patch.splitlines():
        hunk_match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw_line)

        if hunk_match:
            new_line = int(hunk_match.group(1))
            continue

        if new_line is None:
            continue

        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            changed_lines.add(new_line)
            new_line += 1
        elif raw_line.startswith("-") and not raw_line.startswith("---"):
            # Deleted line exists only in old file, so do not increment new-line counter.
            continue
        else:
            # Context line.
            new_line += 1

    return changed_lines


def build_changed_line_index(
    pr_files: list[dict[str, Any]]
) -> dict[str, set[int]]:
    index: dict[str, set[int]] = {}

    for file_obj in pr_files:
        filename = file_obj.get("filename")
        patch = file_obj.get("patch", "")

        if filename:
            index[filename] = parse_patch_changed_lines(patch)

    return index


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
    Simple heuristic context discovery for demo:
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

            # Related test class.
            candidate_paths.update(glob.glob(f"**/{name_without_ext}Test.java", recursive=True))
            candidate_paths.update(glob.glob(f"**/{name_without_ext}Tests.java", recursive=True))

            # Demo-specific important domain files.
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

        context_files.append({
            "path": path,
            "content": content,
        })
        total_chars += len(content)

    return context_files


# =============================================================================
# Requirement Processing
# =============================================================================

def parse_acceptance_criteria_locally(issue_body: str) -> list[dict[str, str]]:
    """
    Deterministic extraction of AC lines.
    Supports lines starting with AC1:, AC2:, etc.
    """
    criteria: list[dict[str, str]] = []

    if not issue_body:
        return criteria

    pattern = re.compile(r"^\s*(AC\d+)\s*:\s*(.+)$", re.IGNORECASE)

    for line in issue_body.splitlines():
        match = pattern.match(line)
        if match:
            criteria.append({
                "id": match.group(1).upper(),
                "description": match.group(2).strip(),
            })

    return criteria


def build_requirement_understanding_prompt(
    requirement_issue: dict[str, Any],
    local_criteria: list[dict[str, str]],
) -> list[dict[str, str]]:
    system_prompt = """
You are a Requirement Understanding Agent for a Java Spring Kafka trade enrichment service.

Convert the GitHub Requirement Issue into structured JSON.

Return valid JSON only. No markdown. No explanations outside JSON.

Schema:
{
  "acceptanceCriteria": [
    {
      "id": "AC1",
      "description": "...",
      "expectedFiles": ["..."],
      "expectedBehavior": ["..."],
      "severityIfMissing": "MAJOR"
    }
  ],
  "functionalRules": [
    {
      "rule": "...",
      "severityIfMissing": "CRITICAL",
      "acceptanceCriteria": ["AC1"]
    }
  ],
  "testExpectations": ["..."]
}

Severity must be one of: CRITICAL, MAJOR, MINOR, INFO.
""".strip()

    user_payload = {
        "requirementIssue": {
            "number": requirement_issue.get("number"),
            "title": requirement_issue.get("title"),
            "body": requirement_issue.get("body", ""),
        },
        "locallyParsedAcceptanceCriteria": local_criteria,
    }

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, indent=2)},
    ]


# =============================================================================
# GitHub Models
# =============================================================================

def call_github_model(
    token: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.1,
) -> str:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "agentic-pr-review",
    }

    payload = {
        "model": model,
        "temperature": temperature,
        "messages": messages,
    }

    request = urllib.request.Request(
        url=GITHUB_MODELS_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")
            result = json.loads(response_body)
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub Models request failed: status={exc.code}, body={error_body}"
        ) from exc


def extract_json_from_text(text: str) -> Any:
    """
    Tries to parse JSON directly.
    If model wraps JSON accidentally, extracts first JSON object block.
    """
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Remove common code fences if present.
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        candidate = text[start:end + 1]
        return json.loads(candidate)

    raise ValueError("Unable to parse JSON from model response.")


def repair_json_with_model(
    token: str,
    model: str,
    invalid_text: str,
) -> Any:
    messages = [
        {
            "role": "system",
            "content": (
                "You repair invalid JSON. Return valid JSON only. "
                "Do not add markdown or explanation."
            ),
        },
        {
            "role": "user",
            "content": invalid_text,
        },
    ]

    repaired_text = call_model(
        config=config,
        messages=messages,
    )


    return extract_json_from_text(repaired_text)


def run_requirement_understanding_agent(
    config: dict[str, Any],
    requirement_issue: dict[str, Any] | None,
) -> dict[str, Any]:
    if not requirement_issue:
        return {
            "acceptanceCriteria": [],
            "functionalRules": [],
            "testExpectations": [],
        }

    local_criteria = parse_acceptance_criteria_locally(requirement_issue.get("body", ""))

    messages = build_requirement_understanding_prompt(
        requirement_issue=requirement_issue,
        local_criteria=local_criteria,
    )

    log(f"Calling Requirement Understanding Agent using model {config['model']}")

    raw = call_model(
        config=config,
        messages=messages,
    )


    try:
        parsed = extract_json_from_text(raw)
    except Exception:
        log("Requirement Understanding Agent returned invalid JSON. Attempting repair.")
        parsed = repair_json_with_model(
            token=config["token"],
            model=config["model"],
            invalid_text=raw,
        )

    if "acceptanceCriteria" not in parsed:
        parsed["acceptanceCriteria"] = local_criteria

    return parsed


def build_combined_review_prompt(
    pr_event: dict[str, Any],
    requirement_ref: dict[str, Any] | None,
    requirement_issue: dict[str, Any] | None,
    structured_requirement: dict[str, Any],
    pr_files: list[dict[str, Any]],
    context_files: list[dict[str, str]],
) -> list[dict[str, str]]:
    system_prompt = """
You are an Agentic PR Review system for a Java Spring Kafka trade enrichment service.

Act as these sub-agents:
1. Functional Review Agent
2. Java/Spring Code Quality Agent
3. Kafka Review Agent
4. Test Coverage Review Agent

Rules:
1. Review only changed files and changed lines.
2. You may use context files only for understanding.
3. Do not create findings for unchanged files.
4. Every inline finding must map to a changed line from the patch.
5. Use severity only from: CRITICAL, MAJOR, MINOR, INFO.
6. Use category only from: FUNCTIONAL, CODE_QUALITY, KAFKA, SPRING, TEST_COVERAGE, SECURITY, OBSERVABILITY.
7. Functional findings must reference acceptance criteria IDs where applicable.
8. Prefer concrete, actionable feedback.
9. Do not invent files, methods, or line numbers.
10. If uncertain, use summaryObservations instead of findings.
11. Return valid JSON only. No markdown. No explanation outside JSON.

Expected response schema:
{
  "findings": [
    {
      "severity": "MAJOR",
      "category": "FUNCTIONAL",
      "file": "path/to/File.java",
      "line": 123,
      "title": "Short title",
      "body": "Clear explanation",
      "acceptanceCriteria": ["AC5"],
      "suggestedFix": "Actionable suggestion"
    }
  ],
  "acceptanceCriteriaCoverage": [
    {
      "id": "AC1",
      "status": "PASS",
      "notes": "..."
    }
  ],
  "summaryObservations": [
    {
      "severity": "INFO",
      "category": "OBSERVABILITY",
      "body": "..."
    }
  ],
  "overallResult": "PASS | REVIEW_REQUIRED | FAILED | UNKNOWN"
}
""".strip()

    
    changed_files_payload = compact_pr_files_for_prompt(
        pr_files=pr_files,
        max_files=int(os.environ.get("REVIEW_MAX_CHANGED_FILES", "8")),
        patch_max_chars=int(os.environ.get("REVIEW_PATCH_MAX_CHARS", "2500")),
    )

    context_files_payload = compact_context_files_for_prompt(
        context_files=context_files,
        context_max_chars=int(os.environ.get("REVIEW_CONTEXT_MAX_CHARS", "3000")),
    )


    user_payload = {
        "pullRequest": pr_event,
        "requirementReference": requirement_ref,
        "requirementIssue": {
            "number": requirement_issue.get("number") if requirement_issue else None,
            "title": requirement_issue.get("title") if requirement_issue else None,
        },
        "structuredRequirement": structured_requirement,
        "changedFiles": changed_files_payload,
        "contextFiles": context_files_payload,
        "reviewScope": {
            "reviewOnlyChangedLines": True,
            "contextFilesAreReadOnly": True,
        },
    }

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, indent=2)},
    ]


def run_combined_review_agent(
    config: dict[str, Any],
    pr_event: dict[str, Any],
    requirement_ref: dict[str, Any] | None,
    requirement_issue: dict[str, Any] | None,
    structured_requirement: dict[str, Any],
    pr_files: list[dict[str, Any]],
    context_files: list[dict[str, str]],
) -> dict[str, Any]:
    messages = build_combined_review_prompt(
        pr_event=pr_event,
        requirement_ref=requirement_ref,
        requirement_issue=requirement_issue,
        structured_requirement=structured_requirement,
        pr_files=pr_files,
        context_files=context_files,
    )

    log(f"Calling Combined PR Review Agent using model {config['model']}")

    raw = call_model(
        config=config,
        messages=messages,
    )


    try:
        parsed = extract_json_from_text(raw)
    except Exception:
        log("Combined PR Review Agent returned invalid JSON. Attempting repair.")
        parsed = repair_json_with_model(
            token=config["token"],
            model=config["model"],
            invalid_text=raw,
        )

    parsed.setdefault("findings", [])
    parsed.setdefault("acceptanceCriteriaCoverage", [])
    parsed.setdefault("summaryObservations", [])
    parsed.setdefault("overallResult", "UNKNOWN")

    return parsed


# =============================================================================
# Finding Normalization
# =============================================================================

def severity_rank(severity: str) -> int:
    ranks = {
        "CRITICAL": 4,
        "MAJOR": 3,
        "MINOR": 2,
        "INFO": 1,
    }
    return ranks.get(str(severity).upper(), 1)


def normalize_severity(value: Any) -> str:
    severity = str(value or "INFO").upper()
    if severity not in ALLOWED_SEVERITIES:
        return "INFO"
    return severity


def normalize_category(value: Any) -> str:
    category = str(value or "CODE_QUALITY").upper()
    if category not in ALLOWED_CATEGORIES:
        return "CODE_QUALITY"
    return category


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

    suffix_matches = [
        path for path in changed_file_paths
        if path.endswith(finding_file)
    ]
    if len(suffix_matches) == 1:
        return suffix_matches[0]

    finding_basename = finding_file.split("/")[-1]
    basename_matches = [
        path for path in changed_file_paths
        if path.split("/")[-1] == finding_basename
    ]
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

        raw_file = copied.get("file")
        raw_line = copied.get("line")

        resolved_file = resolve_finding_file_path(
            finding_file=str(raw_file or ""),
            changed_file_paths=changed_file_paths,
        )

        if not resolved_file:
            copied["summaryOnlyReason"] = "Finding file is not part of the PR changed files."
            summary_only_findings.append(copied)
            continue

        try:
            line = int(raw_line)
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
    comments: list[dict[str, Any]] = []

    for finding in inline_findings:
        comments.append({
            "path": finding["file"],
            "line": finding["line"],
            "body": build_inline_comment_body(finding),
        })

    return comments


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

    payload = {
        "commit_id": head_sha,
        "event": "COMMENT",
        "body": "Agentic PR Review inline findings",
        "comments": comments,
    }

    url = f"{api_url}/repos/{owner}/{repo}/pulls/{pull_number}/reviews"

    github_request(
        method="POST",
        url=url,
        token=token,
        payload=payload,
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
        fallback_findings: list[dict[str, Any]] = []

        for finding in inline_findings:
            copied = dict(finding)
            copied["summaryOnlyReason"] = (
                "Inline comment publishing failed; included in PR summary instead."
            )
            fallback_findings.append(copied)

        return 0, [], fallback_findings


# =============================================================================
# PR Summary Comment
# =============================================================================

def list_issue_comments(
    owner: str,
    repo: str,
    issue_number: int,
    token: str,
    api_url: str,
) -> list[dict[str, Any]]:
    url = f"{api_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
    return get_paginated(url=url, token=token)


def find_existing_summary_comment(
    comments: list[dict[str, Any]]
) -> dict[str, Any] | None:
    for comment in comments:
        body = comment.get("body") or ""
        if SUMMARY_MARKER in body:
            return comment

    return None


def create_issue_comment(
    owner: str,
    repo: str,
    issue_number: int,
    body: str,
    token: str,
    api_url: str,
) -> dict[str, Any]:
    url = f"{api_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"

    payload = {
        "body": body,
    }

    return github_request(
        method="POST",
        url=url,
        token=token,
        payload=payload,
    )


def update_issue_comment(
    owner: str,
    repo: str,
    comment_id: int,
    body: str,
    token: str,
    api_url: str,
) -> dict[str, Any]:
    url = f"{api_url}/repos/{owner}/{repo}/issues/comments/{comment_id}"

    payload = {
        "body": body,
    }

    return github_request(
        method="PATCH",
        url=url,
        token=token,
        payload=payload,
    )


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


def count_findings_by_severity(
    findings: list[dict[str, Any]]
) -> dict[str, int]:
    counts = {
        "CRITICAL": 0,
        "MAJOR": 0,
        "MINOR": 0,
        "INFO": 0,
    }

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

        normalized.append({
            "id": ac_id,
            "status": status,
            "notes": notes,
        })

    return normalized


def build_ac_coverage_table(
    ac_coverage: list[dict[str, Any]],
) -> list[str]:
    lines = [
        "| AC | Status | Notes |",
        "|---|---|---|",
    ]

    normalized = normalize_ac_coverage(ac_coverage)

    for item in normalized:
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
        key=lambda finding: severity_rank(finding.get("severity", "INFO")),
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

    lines.extend([
        "",
        "### Top Findings",
        "",
    ])

    if all_findings:
        lines.extend(build_top_findings_section(all_findings))
    else:
        lines.append("_No findings reported._")

    lines.extend([
        "",
        "### Additional Observations",
        "",
    ])

    lines.extend(build_summary_observations_section(summary_observations))

    lines.extend([
        "",
        "### Quality Gate",
        "",
    ])

    if quality_gate_failed:
        lines.append(
            f"**Failed** because findings include `{fail_on_severity}` or higher severity."
        )
    else:
        lines.append(
            f"**Passed**. No findings at `{fail_on_severity}` or higher severity."
        )

    lines.extend([
        "",
        "---",
        "_Generated by Agentic PR Review._",
    ])

    return "\n".join(lines)


# =============================================================================
# Quality Gate
# =============================================================================

def should_fail_build(
    findings: list[dict[str, Any]],
    fail_on_severity: str,
) -> bool:
    threshold = severity_rank(fail_on_severity)

    for finding in findings:
        severity = finding.get("severity", "INFO")
        if severity_rank(severity) >= threshold:
            return True

    return False


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

# =============================================================================
# helper to truncate text
# =============================================================================

def truncate_text(value: str, max_chars: int) -> str:
    if not value:
        return ""

    if len(value) <= max_chars:
        return value

    return (
        value[:max_chars]
        + "\n\n...[truncated to fit model token limit]..."
    )

# =============================================================================
# compact PR files function
# =============================================================================

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

# =============================================================================
# compact context files function
# =============================================================================
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

        compact_context.append({
            "path": path,
            "content": trimmed,
        })

        remaining -= len(trimmed)

    return compact_context


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    config = load_config()
    pr_event: dict[str, Any] | None = None

    try:
        pr_event = get_pr_event(config["event_path"])

        pull_number = pr_event["pull_number"]
        head_sha = pr_event["head_sha"]

        log(f"Loaded PR #{pull_number}")
        log(f"Base: {pr_event.get('base_ref')} | Head: {pr_event.get('head_ref')}")

        commits = get_pr_commits(
            owner=config["owner"],
            repo=config["repo"],
            pull_number=pull_number,
            token=config["token"],
            api_url=config["api_url"],
        )

        requirement_ref = extract_requirement_issue_from_commits(commits)

        requirement_issue = None
        if requirement_ref:
            log(
                f"Found Requirement Issue #{requirement_ref['issue_id']} "
                f"from commit: {requirement_ref['matched_commit']}"
            )
            requirement_issue = get_requirement_issue(
                owner=config["owner"],
                repo=config["repo"],
                issue_id=requirement_ref["issue_id"],
                token=config["token"],
                api_url=config["api_url"],
            )
        else:
            log("No Requirement Issue reference found in commit messages.")

        pr_files = get_pr_files(
            owner=config["owner"],
            repo=config["repo"],
            pull_number=pull_number,
            token=config["token"],
            api_url=config["api_url"],
        )

        log(f"Reviewable changed files: {len(pr_files)}")

        if not pr_files:
            model_response = {
                "findings": [],
                "acceptanceCriteriaCoverage": [],
                "summaryObservations": [
                    {
                        "severity": "INFO",
                        "category": "CODE_QUALITY",
                        "body": "No reviewable changed files found.",
                    }
                ],
                "overallResult": "PASS",
            }

            summary_body = build_summary_comment_body(
                requirement_issue=requirement_issue,
                model_response=model_response,
                inline_findings=[],
                summary_only_findings=[],
                posted_inline_count=0,
                model=config["model"],
                quality_gate_failed=False,
                fail_on_severity=config["fail_on_severity"],
            )

            post_or_update_summary_comment(
                owner=config["owner"],
                repo=config["repo"],
                pull_number=pull_number,
                body=summary_body,
                token=config["token"],
                api_url=config["api_url"],
            )

            log("No reviewable files. Exiting successfully.")
            return

        changed_line_index = build_changed_line_index(pr_files)

        changed_file_paths = [file_obj["filename"] for file_obj in pr_files]
        context_files = discover_related_context_files(
            changed_files=changed_file_paths,
            context_max_chars=config["context_max_chars"],
        )

        log(f"Context files loaded: {len(context_files)}")

        structured_requirement = run_requirement_understanding_agent(
            config=config,
            requirement_issue=requirement_issue,
        )

        model_response = run_combined_review_agent(
            config=config,
            pr_event=pr_event,
            requirement_ref=requirement_ref,
            requirement_issue=requirement_issue,
            structured_requirement=structured_requirement,
            pr_files=pr_files,
            context_files=context_files,
        )

        findings = normalize_findings(
            raw_findings=model_response.get("findings", []),
            max_findings=config["max_findings"],
        )

        log(f"Normalized findings: {len(findings)}")

        inline_findings, summary_only_findings = split_inline_and_summary_findings(
            findings=findings,
            changed_line_index=changed_line_index,
        )

        log(f"Inline-safe findings: {len(inline_findings)}")
        log(f"Summary-only findings: {len(summary_only_findings)}")

        posted_inline_count, posted_inline_findings, inline_fallback_findings = (
            safe_post_inline_review_comments(
                owner=config["owner"],
                repo=config["repo"],
                pull_number=pull_number,
                head_sha=head_sha,
                inline_findings=inline_findings,
                token=config["token"],
                api_url=config["api_url"],
            )
        )

        summary_only_findings.extend(inline_fallback_findings)

        quality_gate_failed = should_fail_build(
            findings=posted_inline_findings + summary_only_findings,
            fail_on_severity=config["fail_on_severity"],
        )

        summary_body = build_summary_comment_body(
            requirement_issue=requirement_issue,
            model_response=model_response,
            inline_findings=posted_inline_findings,
            summary_only_findings=summary_only_findings,
            posted_inline_count=posted_inline_count,
            model=config["model"],
            quality_gate_failed=quality_gate_failed,
            fail_on_severity=config["fail_on_severity"],
        )

        post_or_update_summary_comment(
            owner=config["owner"],
            repo=config["repo"],
            pull_number=pull_number,
            body=summary_body,
            token=config["token"],
            api_url=config["api_url"],
        )

        if quality_gate_failed:
            log("Quality gate failed.")
            raise SystemExit(1)

        log("Quality gate passed.")

    except SystemExit:
        raise
    except Exception as exc:
        log(f"Agentic PR review failed: {exc}")
        post_failure_summary_safely(
            config=config,
            pr_event=pr_event,
            message=str(exc),
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()