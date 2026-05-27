from __future__ import annotations

import os
from typing import Any

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

SUMMARY_MARKER = "<!-- agentic-pr-review-summary -->"
INLINE_MARKER = "<!-- agentic-pr-review -->"


def log(message: str) -> None:
    print(f"[agentic-review] {message}", flush=True)


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
        "groq_api_key": os.environ.get("GROQ_API_KEY"),
    }