from __future__ import annotations

import json
import os
import re
import urllib.request
import urllib.error
from typing import Any

from config import REVIEWABLE_EXTENSIONS, EXCLUDED_PATH_PARTS, log

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

        batch = github_request(method="GET", url=page_url, token=token)

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
    Expected commit message format:
      <issue id> - <issue title>
    e.g. 2 - Add Buyer/Seller Indicator (B/S) to Enriched Trade Output

    If multiple commits match, uses the latest matching commit.
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

def is_reviewable_file(path: str) -> bool:
    if not path:
        return False

    normalized = "/" + path.replace("\\", "/")

    for excluded in EXCLUDED_PATH_PARTS:
        if excluded in normalized:
            return False

    return path.endswith(REVIEWABLE_EXTENSIONS)


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
            continue
        else:
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


def list_issue_comments(
    owner: str,
    repo: str,
    issue_number: int,
    token: str,
    api_url: str,
) -> list[dict[str, Any]]:
    url = f"{api_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
    return get_paginated(url=url, token=token)


def create_issue_comment(
    owner: str,
    repo: str,
    issue_number: int,
    body: str,
    token: str,
    api_url: str,
) -> dict[str, Any]:
    url = f"{api_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
    return github_request(method="POST", url=url, token=token, payload={"body": body})


def update_issue_comment(
    owner: str,
    repo: str,
    comment_id: int,
    body: str,
    token: str,
    api_url: str,
) -> dict[str, Any]:
    url = f"{api_url}/repos/{owner}/{repo}/issues/comments/{comment_id}"
    return github_request(method="PATCH", url=url, token=token, payload={"body": body})


def post_inline_review_via_api(
    owner: str,
    repo: str,
    pull_number: int,
    head_sha: str,
    comments: list[dict[str, Any]],
    token: str,
    api_url: str,
) -> None:
    payload = {
        "commit_id": head_sha,
        "event": "COMMENT",
        "body": "Agentic PR Review inline findings",
        "comments": comments,
    }
    url = f"{api_url}/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
    github_request(method="POST", url=url, token=token, payload=payload)