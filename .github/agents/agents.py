"""
agents.py — LangChain replacement for the two agent entry-points.

Public API (unchanged, so main.py needs zero edits):
    run_requirement_understanding_agent(config, requirement_issue) -> dict
    run_combined_review_agent(config, pr_event, ...) -> dict

What changed internally:
  - Every LLM call is now an LCEL chain:
        prompt | llm | StrOutputParser()  →  raw string
    followed by the same extract_json_from_text / repair_json_with_model
    fallback logic as before.
  - _build_llm(config) constructs the right LangChain LLM based on
    config["model_provider"], using the same routing logic as call_model().
  - The 4 review agents (_run_single_review_agent) each become their own
    LCEL chain so they could be parallelised with RunnableParallel if needed
    in the future (structure is ready, sequential execution kept for now to
    preserve token budget predictability).
  - Caching, local AC parsing, prompt loading, payload building, and merging
    are all identical to the original.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableParallel
from production_context_builder import build_production_context
from config import log
from model_client import extract_json_from_text, repair_json_with_model, token_tracker

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_CACHE_DIR   = Path(__file__).parent / "cache"
_PROJECT_CONTEXT_PATH = Path(__file__).parent / "project_context.md"

def load_project_context() -> str:
    if _PROJECT_CONTEXT_PATH.exists():
        return _PROJECT_CONTEXT_PATH.read_text(encoding="utf-8").strip()
    return ""

# =============================================================================
# Helpers shared by both agents
# =============================================================================

def load_prompt(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()


def _build_llm(config: dict[str, Any]):
    """
    Factory that returns the right LangChain chat model based on
    config["model_provider"].

    Returns a LangChain BaseChatModel — duck-typed, so both branches work
    identically inside LCEL chains.
    """
    provider = config["model_provider"]
    #provider = "groq" # do not remove this hard-coded override — we want to route all review agents to the Groq model for testing/comparison purposes, without affecting the requirement understanding agent which can stay on Anthropic for now.
    if provider == "anthropic":
        if not config.get("anthropic_api_key"):
            raise RuntimeError("ANTHROPIC_API_KEY missing")
        return ChatAnthropic(
            api_key=config["anthropic_api_key"],
            model_name=config["model"],
            max_tokens=8192,
            temperature=0.1,
        )

    elif provider == "groq":
        if not config.get("groq_api_key"):
            raise RuntimeError("GROQ_API_KEY missing")
        print("Using Groq model")
        return ChatGroq(
            groq_api_key=config["groq_api_key"],
            # Same hard-coded model as the original model_client.py
            model_name="meta-llama/llama-4-scout-17b-16e-instruct",
            max_tokens=8192,
            temperature=0.1,
        )
    raise RuntimeError(f"Unsupported model provider: {provider}")


def _invoke_chain_and_parse(
    config: dict[str, Any],
    label: str,
    system_prompt: str,
    user_content: str,
) -> dict[str, Any]:
    llm = _build_llm(config)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    # ── Input debug ──────────────────────────────────────────────────────────
    sep = "=" * 70
    print(f"\n{sep}")
    print(f"  LLM INPUT — {label}")
    print(f"  Model: {config['model']}")
    print(sep)
    print("[SYSTEM]")
    print(system_prompt)
    print("\n[USER]")
    print(user_content)
    print(f"{sep}\n")

    log(f"Calling {label} using model {config['model']}")

    raw_ai_msg = llm.invoke(messages)
    response: str = raw_ai_msg.content

    usage = getattr(raw_ai_msg, "usage_metadata", None) or {}
    input_tokens  = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    token_tracker.record(label, input_tokens, output_tokens)

    # ── Output debug ─────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print(f"  LLM OUTPUT — {label}")
    print(f"  Tokens — input: {input_tokens:,}  output: {output_tokens:,}  total: {input_tokens + output_tokens:,}")
    print(sep)
    print(response)
    print(f"{sep}\n")

    try:
        return extract_json_from_text(response)
    except Exception:
        log(f"{label} returned invalid JSON. Attempting repair.")
        return repair_json_with_model(config=config, invalid_text=response)

# =============================================================================
# Requirement Understanding Agent
# =============================================================================

def parse_acceptance_criteria_locally(issue_body: str) -> list[dict[str, str]]:
    """Deterministic AC extraction — unchanged from original."""
    criteria: list[dict[str, str]] = []
    if not issue_body:
        return criteria
    pattern = re.compile(r"^\s*(AC\d+)\s*:\s*(.+)$", re.IGNORECASE)
    for line in issue_body.splitlines():
        match = pattern.match(line)
        if match:
            criteria.append({"id": match.group(1).upper(), "description": match.group(2).strip()})
    return criteria


# ── Cache helpers (unchanged) ─────────────────────────────────────────────────

def _get_cache_path(issue_number: int) -> Path:
    _CACHE_DIR.mkdir(exist_ok=True)
    return _CACHE_DIR / f"requirement_{issue_number}.json"


def _read_requirement_cache(issue_number: int) -> dict | None:
    path = _get_cache_path(issue_number)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _write_requirement_cache(issue_number: int, data: dict) -> None:
    path = _get_cache_path(issue_number)
    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        log(f"Warning: could not write requirement cache: {exc}")


def run_requirement_understanding_agent(
    config: dict[str, Any],
    requirement_issue: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Agent 1 — converts a raw GitHub Issue into structured JSON.

    LCEL chain used: SystemMessage + HumanMessage | llm | StrOutputParser
    then JSON parse/repair.  Caching behaviour is identical to the original.
    """
    if not requirement_issue:
        return {"acceptanceCriteria": [], "functionalRules": [], "testExpectations": []}

    issue_number = requirement_issue.get("number")

    cached = _read_requirement_cache(issue_number)
    if cached:
        log(f"Requirement cache hit for issue #{issue_number}, skipping model call.")
        return cached

    local_criteria = parse_acceptance_criteria_locally(requirement_issue.get("body", ""))

    system_prompt = load_prompt("requirement_understanding.md")
    user_payload = json.dumps({
        "requirementIssue": {
            "number": requirement_issue.get("number"),
            "title":  requirement_issue.get("title"),
            "body":   requirement_issue.get("body", ""),
        },
        "locallyParsedAcceptanceCriteria": local_criteria,
    }, indent=2)

    parsed = _invoke_chain_and_parse(
        config=config,
        label="Requirement Understanding Agent",
        system_prompt=system_prompt,
        user_content=user_payload,
    )

    if "acceptanceCriteria" not in parsed:
        parsed["acceptanceCriteria"] = local_criteria

    _write_requirement_cache(issue_number, parsed)
    return parsed


# =============================================================================
# Review Agents (4 specialised — combined via run_combined_review_agent)
# =============================================================================

_REVIEW_AGENT_PROMPTS = {
    "functional":        "functional_review.md",
    "code_quality":      "code_quality_review.md",
    "production_safety": "production_safety_review.md",
    "test_coverage":     "test_coverage_review.md",
}


def _build_review_user_payload(
    pr_event: dict[str, Any],
    requirement_ref: dict[str, Any] | None,
    requirement_issue: dict[str, Any] | None,
    structured_requirement: dict[str, Any],
    pr_files: list[dict[str, Any]],
    context_files: list[dict[str, str]],
) -> dict[str, Any]:
    """Build the shared user payload — identical to original."""
    from review_utils import compact_pr_files_for_prompt, compact_context_files_for_prompt

    changed_files_payload = compact_pr_files_for_prompt(
        pr_files=pr_files,
        max_files=int(os.environ.get("REVIEW_MAX_CHANGED_FILES", "8")),
        patch_max_chars=int(os.environ.get("REVIEW_PATCH_MAX_CHARS", "2500")),
    )
    context_files_payload = compact_context_files_for_prompt(
        context_files=context_files,
        context_max_chars=int(os.environ.get("REVIEW_CONTEXT_MAX_CHARS", "3000")),
    )

    return {
        "pullRequest": pr_event,
        "requirementReference": requirement_ref,
        "requirementIssue": {
            "number": requirement_issue.get("number") if requirement_issue else None,
            "title":  requirement_issue.get("title")  if requirement_issue else None,
        },
        "structuredRequirement": structured_requirement,
        "changedFiles": changed_files_payload,
        "contextFiles": context_files_payload,
        "reviewScope": {
            "reviewOnlyChangedLines": True,
            "contextFilesAreReadOnly": True,
        },
    }

def _build_slim_review_payload(
    pr_event: dict[str, Any],
    requirement_issue: dict[str, Any] | None,
    pr_files: list[dict[str, Any]],
    context_files: list[dict[str, str]],
) -> dict[str, Any]:
    from review_utils import compact_pr_files_for_prompt, compact_context_files_for_prompt

    changed_files_payload = compact_pr_files_for_prompt(
        pr_files=pr_files,
        max_files=int(os.environ.get("REVIEW_MAX_CHANGED_FILES", "8")),
        patch_max_chars=int(os.environ.get("REVIEW_PATCH_MAX_CHARS", "2500")),
    )
    context_files_payload = compact_context_files_for_prompt(
        context_files=context_files,
        context_max_chars=int(os.environ.get("REVIEW_CONTEXT_MAX_CHARS", "3000")),
    )

    return {
        "pullRequest": pr_event,
        "requirementIssue": {
            "number": requirement_issue.get("number") if requirement_issue else None,
            "title":  requirement_issue.get("title")  if requirement_issue else None,
        },
        "changedFiles": changed_files_payload,
        "contextFiles": context_files_payload,
        "reviewScope": {
            "reviewOnlyChangedLines": True,
            "contextFilesAreReadOnly": True,
        },
    }


def _build_code_quality_payload(
    pr_files: list[dict[str, Any]],
) -> dict[str, Any]:
    from review_utils import compact_pr_files_for_prompt

    changed_files_payload = compact_pr_files_for_prompt(
        pr_files=pr_files,
        max_files=int(os.environ.get("REVIEW_MAX_CHANGED_FILES", "8")),
        patch_max_chars=int(os.environ.get("REVIEW_PATCH_MAX_CHARS", "2500")),
    )

    return {
        "changedFiles": changed_files_payload,
        "reviewScope": {
            "reviewOnlyChangedLines": True,
        },
    }
def _build_test_coverage_payload(
    pr_files: list[dict[str, Any]],
    diff_coverage: dict[str, Any],
    test_context_files: list[dict[str, str]],
) -> dict[str, Any]:
    """
    [NEW] Builds the payload specifically for the test_coverage review agent.
 
    Unlike the slim payload, this includes:
    - coverageByFile: per-file Jacoco coverage data for each changed line
      (covered / missed / partial with line numbers and coverage %)
    - testFiles: full source of test classes that reference the changed source
      classes, resolved by static analysis in test_resolver.py
 
    The agent uses coverageByFile to identify which diff lines lack coverage,
    then cross-references testFiles to determine whether:
      (a) a test exists but doesn't reach those lines — a gap to flag
      (b) no test exists at all — a missing test to flag as a finding
 
    Parameters
    ----------
    pr_files:
        Raw PR file objects from the GitHub API (same as all other payloads).
    diff_coverage:
        Output of coverage_parser.map_diff_to_coverage() — keyed by repo path,
        values contain changed_lines, covered_lines, missed_lines, coverage_pct.
    test_context_files:
        Output of test_resolver.resolve_test_files_for_diff() — list of dicts
        with keys: path, content, reason.
    """
    from review_utils import compact_pr_files_for_prompt
 
    changed_files_payload = compact_pr_files_for_prompt(
        pr_files=pr_files,
        max_files=int(os.environ.get("REVIEW_MAX_CHANGED_FILES", "8")),
        patch_max_chars=int(os.environ.get("REVIEW_PATCH_MAX_CHARS", "2500")),
    )
 
    # Compact the test files — strip content to a char budget so the payload
    # doesn't blow the context window. Each file already has its content
    # truncated by test_resolver, but we enforce a per-file cap here too.
    per_file_cap = int(os.environ.get("REVIEW_CONTEXT_MAX_CHARS", "3000"))
    compacted_test_files = []
    for tf in test_context_files:
        content = tf.get("content", "")
        if len(content) > per_file_cap:
            content = content[:per_file_cap] + f"\n... [truncated]"
        compacted_test_files.append({
            "path":    tf.get("path", ""),
            "reason":  tf.get("reason", ""),
            "content": content,
        })
 
    return {
        "changedFiles":  changed_files_payload,
        "coverageByFile": diff_coverage,       # Jacoco line-level data
        "testFiles":     compacted_test_files,  # Covering test class sources
        "reviewScope": {
            "reviewOnlyChangedLines": True,
            "instructions": (
                "Use coverageByFile to identify which changed lines are missed "
                "or have no coverage data. Cross-reference testFiles to determine "
                "if a test exists but doesn't reach those lines (coverage gap) "
                "or if no test covers the class at all (missing test). "
                "Only raise findings for changed lines that lack adequate coverage."
            ),
        },
    }

def _run_single_review_agent(
    config: dict[str, Any],
    agent_key: str,
    user_payload: dict[str, Any],
    suppress_rules_prompt: str = "",
) -> dict[str, Any]:
    """
    One specialised review agent — now an LCEL chain.

    The chain is:  llm.invoke([SystemMessage, HumanMessage])
    followed by JSON parse/repair, same as before.
    Suppress rules are appended to the system prompt exactly as in the original.
    """
    system_prompt = load_prompt(_REVIEW_AGENT_PROMPTS[agent_key])
    if suppress_rules_prompt:
        system_prompt = system_prompt + "\n\n" + suppress_rules_prompt
    _CONTEXT_AWARE_AGENTS = {"code_quality", "production_safety", "test_coverage"}
    if agent_key in _CONTEXT_AWARE_AGENTS:
        project_context = load_project_context()
        if project_context:
            system_prompt = system_prompt + "\n\n## PROJECT-SPECIFIC CONTEXT\n" + project_context

    agent_label = agent_key.replace("_", " ").title() + " Review Agent"

    result = _invoke_chain_and_parse(
        config=config,
        label=agent_label,
        system_prompt=system_prompt,
        user_content=json.dumps(user_payload, indent=2),
    )

    result.setdefault("findings", [])
    result.setdefault("summaryObservations", [])
    return result


def _merge_review_results(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Merge 4 agent outputs — identical to original."""
    merged_findings:    list[dict[str, Any]] = []
    merged_summary:     list[dict[str, Any]] = []
    merged_ac_coverage: list[dict[str, Any]] = []

    for agent_key, result in results.items():
        merged_findings.extend(result.get("findings", []))
        merged_summary.extend(result.get("summaryObservations", []))
        if agent_key == "functional":
            merged_ac_coverage.extend(result.get("acceptanceCriteriaCoverage", []))

    severities = {f.get("severity") for f in merged_findings}
    if "CRITICAL" in severities:
        overall = "FAILED"
    elif "MAJOR" in severities:
        overall = "REVIEW_REQUIRED"
    elif merged_findings or merged_ac_coverage:
        overall = "PASS"
    else:
        overall = "UNKNOWN"

    return {
        "findings":                merged_findings,
        "acceptanceCriteriaCoverage": merged_ac_coverage,
        "summaryObservations":     merged_summary,
        "overallResult":           overall,
        "reviewerNotes": (
            "Review performed by 4 specialized agents: "
            "Functional, Code Quality, Production Safety, and Test Coverage."
        ),
    }


def run_combined_review_agent(
    config: dict[str, Any],
    pr_event: dict[str, Any],
    requirement_ref: dict[str, Any] | None,
    requirement_issue: dict[str, Any] | None,
    structured_requirement: dict[str, Any],
    pr_files: list[dict[str, Any]],
    context_files: list[dict[str, str]],
    suppress_rules_prompt: str = "",
    diff_coverage: dict[str, Any] | None = None,
    test_context_files: list[dict[str, str]] | None = None,

) -> dict[str, Any]:
    """
    Orchestrates 4 specialised LCEL chains sequentially and merges results.
    Signature is identical to the original so main.py needs no changes.

    Future upgrade path: swap the for-loop for RunnableParallel to run all 4
    agents concurrently and cut wall-clock time by ~75 %.
    """
    
    full_payload = _build_review_user_payload(
        pr_event=pr_event,
        requirement_ref=requirement_ref,
        requirement_issue=requirement_issue,
        structured_requirement=structured_requirement,
        pr_files=pr_files,
        context_files=context_files,
    )
    slim_payload = _build_slim_review_payload(
        pr_event=pr_event,
        requirement_issue=requirement_issue,
        pr_files=pr_files,
        context_files=context_files,
    )
    production_payload = dict(slim_payload)
 
    production_context = build_production_context(
        pr_files=pr_files,
        context_files=context_files
    )
 
    print("\n" + "=" * 70)
    print("PRODUCTION CONTEXT")
    print("=" * 70)
    print(
        json.dumps(
            production_context,
            indent=2
        )
    )
    print("=" * 70 + "\n")
    production_payload[
        "repositorySignals"
    ] = production_context

    cq_payload = _build_code_quality_payload(pr_files=pr_files)
    if diff_coverage is not None and test_context_files is not None:
        tc_payload = _build_test_coverage_payload(
            pr_files=pr_files,
            diff_coverage=diff_coverage,
            test_context_files=test_context_files,
        )
        log(
            f"Test coverage payload built: "
            f"{len(diff_coverage)} files with coverage data, "
            f"{len(test_context_files)} test file(s) loaded"
        )
    else:
        # Fallback — no Jacoco data, use slim payload (original behaviour)
        tc_payload = slim_payload
        log("No Jacoco coverage data available — test_coverage agent using slim payload")
 
    _PAYLOAD_MAP = {
        "functional":        full_payload,
        "code_quality":      cq_payload,
        "production_safety": production_payload,
        "test_coverage":     tc_payload,   # [CHANGED] was slim_payload
    }
 
    results: dict[str, dict[str, Any]] = {}
    for agent_key in _REVIEW_AGENT_PROMPTS:
        payload = _PAYLOAD_MAP[agent_key]
        results[agent_key] = _run_single_review_agent(
            config=config,
            agent_key=agent_key,
            user_payload=payload,
            suppress_rules_prompt=suppress_rules_prompt,
        )
    merged = _merge_review_results(results)

    log(
        f"All 4 review agents complete. "
        f"Total findings: {len(merged['findings'])}, "
        f"Overall: {merged['overallResult']}"
    )
    return merged