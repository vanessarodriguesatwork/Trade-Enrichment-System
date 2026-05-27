#!/usr/bin/env python3
"""
Agentic PR Review Agent v1 — with full debug printing at every stage.
"""

from __future__ import annotations

import json
from typing import Any
from pathlib import Path

from config import load_config, log
from github_client import (
    get_pr_event,
    get_pr_commits,
    extract_requirement_issue_from_commits,
    get_requirement_issue,
    get_pr_files,
    build_changed_line_index,
)
from agents import (
    run_requirement_understanding_agent,
    run_combined_review_agent,
)
from review_utils import (
    discover_related_context_files,
    normalize_findings,
    split_inline_and_summary_findings,
    safe_post_inline_review_comments,
    should_fail_build,
    build_summary_comment_body,
    post_or_update_summary_comment,
    post_failure_summary_safely,
)
from model_client import token_tracker
from memory_writer import save_pending_findings, load_suppress_rules, format_suppress_rules_for_prompt
# [NEW] — imports for diff-aware test coverage
from coverage_parser import parse_jacoco_coverage, map_diff_to_coverage
from test_resolver import resolve_test_files_for_diff, build_coverage_context_summary

# ── Debug helper ─────────────────────────────────────────────────────────────

def debug_print(label: str, data: Any) -> None:
    """
    Prints a clearly delimited block showing the label and the full contents
    of whatever object is passed in. Uses JSON formatting where possible so
    nested dicts/lists are human-readable. Falls back to repr() for anything
    that isn't JSON-serialisable (e.g. custom objects).
    """
    separator = "=" * 70
    print(f"\n{separator}")
    print(f"DEBUG ── {label}")
    print(separator)
    try:
        # json.dumps will pretty-print dicts, lists, strings, numbers, None
        print(json.dumps(data, indent=2, default=str))
    except Exception:
        # Fallback for objects that can't be JSON-serialised
        print(repr(data))
    print(f"{separator}\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    config = load_config()

    # ── STEP 0: Config ────────────────────────────────────────────────────────
    # Shows every setting that will govern this run — model, thresholds,
    # budget limits, token, repo details, etc.
    debug_print("STEP 0 — Loaded config", config)

    pr_event: dict[str, Any] | None = None

    try:
        # ── STEP 1: PR Event Payload ──────────────────────────────────────────
        # This is the raw GitHub Actions event JSON. It contains pull_number,
        # head_sha, base/head ref, PR title, body, and more. This is the
        # starting point for everything else.
        pr_event = get_pr_event(config["event_path"])
        debug_print("STEP 1 — PR event payload", pr_event)

        pull_number = pr_event["pull_number"]
        head_sha = pr_event["head_sha"]

        log(f"Loaded PR #{pull_number}")
        log(f"Base: {pr_event.get('base_ref')} | Head: {pr_event.get('head_ref')}")

        # ── STEP 2: Commits ───────────────────────────────────────────────────
        # The list of commits on this PR. Each commit has a sha, message, and
        # author. The commit message format "<id> - <title>" is what your agent
        # uses to discover the linked requirement issue.
        commits = get_pr_commits(
            owner=config["owner"],
            repo=config["repo"],
            pull_number=pull_number,
            token=config["token"],
            api_url=config["api_url"],
        )
        debug_print("STEP 2 — Raw commits from GitHub API", commits)

        # ── STEP 3: Extracted Requirement Reference ───────────────────────────
        # Shows exactly which commit matched the "<id> - <title>" pattern and
        # what issue ID was parsed from it. If this is None, the agent has no
        # requirement to review against — worth knowing immediately.
        requirement_ref = extract_requirement_issue_from_commits(commits)
        debug_print("STEP 3 — Extracted requirement reference from commits", requirement_ref)

        # ── STEP 4: Requirement Issue Body ───────────────────────────────────
        # The full GitHub Issue fetched from the API: title, body, labels,
        # acceptance criteria etc. This is the raw requirement that Agent 1
        # will structure and Agent 2 will review against.
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
            debug_print("STEP 4 — Full requirement issue from GitHub Issues API", requirement_issue)
        else:
            log("No Requirement Issue reference found in commit messages.")
            debug_print("STEP 4 — No requirement issue found", None)

        # ── STEP 5: PR Changed Files and Diff Patches ────────────────────────
        # Each entry in this list is one changed file. It includes the filename,
        # status (added/modified/deleted), and the raw diff patch — the exact
        # lines that changed. This is what both agents ultimately review.
        pr_files = get_pr_files(
            owner=config["owner"],
            repo=config["repo"],
            pull_number=pull_number,
            token=config["token"],
            api_url=config["api_url"],
        )
        debug_print("STEP 5 — PR changed files and diff patches", pr_files)
        log(f"Reviewable changed files: {len(pr_files)}")

        if not pr_files:
            # Early exit path — still useful to see this happened
            debug_print("STEP 5a — Early exit: no reviewable files", {})
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

        # ── STEP 6: Changed Line Index ────────────────────────────────────────
        # A map of filename → set of line numbers that actually appear in the
        # diff. This is used later to decide whether a finding can be posted as
        # an inline comment (line is in the diff) or must go in the summary
        # (line is not in the diff, or file wasn't changed).
        changed_line_index = build_changed_line_index(pr_files)
        debug_print("STEP 6 — Changed line index (file → changed line numbers)", changed_line_index)

        # ── STEP 7: Context Files ─────────────────────────────────────────────
        # Related files discovered from the local checkout — typically test
        # classes and domain models associated with the changed files. These
        # give Agent 2 broader codebase context beyond just the raw diff.
        changed_file_paths = [file_obj["filename"] for file_obj in pr_files]
        context_files = discover_related_context_files(
            changed_files=changed_file_paths,
            context_max_chars=config["context_max_chars"],
        )
        debug_print("STEP 7 — Context files discovered from local checkout", context_files)
        log(f"Context files loaded: {len(context_files)}")
        
        # ── STEP 7b: Jacoco Coverage + Test File Resolution [NEW] ─────────────
        #
        # Parse the Jacoco XML report generated by "mvn clean test jacoco:report"
        # and map each diff file's changed lines to covered/missed status.
        # Then statically resolve which test classes reference the changed source
        # classes so the test_coverage agent gets full test source as context.
        #
        # Both steps are best-effort: if jacoco.xml doesn't exist (e.g. build
        # failed before reporting) or no test files are found, we log a warning
        # and pass None so run_combined_review_agent falls back to slim_payload.
        #
        # Jacoco XML path: Maven places it at
        #   <module>/target/site/jacoco/jacoco.xml
        # Adjust this path if your module name or surefire config differs.
        jacoco_xml_path = str(Path(__file__).parent.parent.parent / "trade-service/target/site/jacoco/jacoco.xml")
        test_source_root = str(Path(__file__).parent.parent.parent)
        diff_coverage: dict[str, Any] | None = None
        test_context_files: list[dict[str, str]] | None = None
 
        try:
            coverage_map = parse_jacoco_coverage(jacoco_xml_path)
 
            if coverage_map:
                diff_coverage = map_diff_to_coverage(
                    pr_files=pr_files,
                    coverage_map=coverage_map,
                    repo_root=test_source_root,
                )
                debug_print(
                    "STEP 7b — Diff coverage from Jacoco (file → covered/missed lines)",
                    diff_coverage,
                )
 
                test_context_files = resolve_test_files_for_diff(
                    pr_files=pr_files,
                    base_test_path=test_source_root,
                    max_chars=int(config.get("context_max_chars", 20000)),
                )
                debug_print(
                    "STEP 7c — Test files resolved for diff (paths + reasons)",
                    [{"path": tf["path"], "reason": tf["reason"]} for tf in test_context_files],
                )
                log(f"Coverage data: {len(diff_coverage)} files mapped")
                log(f"Covering test files: {len(test_context_files)}")
 
                # Print a human-readable summary to the Actions log
                summary = build_coverage_context_summary(diff_coverage, test_context_files)
                print(f"\n{'=' * 70}")
                print("  COVERAGE SUMMARY FOR TEST AGENT")
                print(f"{'=' * 70}")
                print(summary)
                print(f"{'=' * 70}\n")
 
            else:
                log("WARNING: jacoco.xml was empty or could not be parsed — skipping coverage context")
 
        except Exception as coverage_exc:
            print(f"Error occurred while parsing coverage data: {coverage_exc}")
            # Never let coverage parsing break the whole review
            log(f"WARNING: Coverage context step failed: {coverage_exc} — continuing without it")
            diff_coverage = None
            test_context_files = None
        # ── STEP 8: Agent 1 — Structured Requirement (OUTPUT) ────────────────
        # This is the output of the first AI call. Agent 1 takes the raw
        # requirement issue and converts it into structured JSON: parsed
        # acceptance criteria with expected severity, functional rules, and
        # test expectations. This structured output becomes the input to Agent 2.
        # To see what went INTO Agent 1's prompt, add a print inside
        # run_requirement_understanding_agent() before the API call.
        structured_requirement = run_requirement_understanding_agent(
            config=config,
            requirement_issue=requirement_issue,
        )
        debug_print("STEP 8 — Agent 1 output: structured requirement JSON", structured_requirement)

        # ── STEP 9: Agent 2 — Combined Review (OUTPUT) ───────────────────────
        # This is the output of the second AI call — the full review response.
        # It contains: findings (with severity, category, file, line, fix),
        # acceptance criteria coverage table, summary observations, and an
        # overall result (PASS / REVIEW_REQUIRED / FAILED).
        # To see what went INTO Agent 2's prompt, add a print inside
        # run_combined_review_agent() before the API call.
        suppress_rules = load_suppress_rules(repo=config["repository"])
        suppress_rules_prompt = format_suppress_rules_for_prompt(suppress_rules)

        model_response = run_combined_review_agent(
            config=config,
            pr_event=pr_event,
            requirement_ref=requirement_ref,
            requirement_issue=requirement_issue,
            structured_requirement=structured_requirement,
            pr_files=pr_files,
            context_files=context_files,
            suppress_rules_prompt=suppress_rules_prompt,
            diff_coverage=diff_coverage,            
            test_context_files=test_context_files,
        )
        debug_print("STEP 9 — Agent 2 output: full model review response", model_response)

        # ── STEP 10: Normalized Findings ─────────────────────────────────────
        # After normalization: severities have been validated, duplicates
        # removed, findings sorted by severity, and the list capped at
        # max_findings. Compare with Step 9 to see what was dropped/changed.
        findings = normalize_findings(
            raw_findings=model_response.get("findings", []),
            max_findings=config["max_findings"],
        )
        debug_print("STEP 10 — Normalized findings (after dedup, sort, cap)", findings)
        log(f"Normalized findings: {len(findings)}")
        save_pending_findings(pr_number=pull_number, findings=findings)  # <-- add 
        # ── STEP 11: Inline vs Summary Split ──────────────────────────────────
        # Findings are split based on whether their line number appears in the
        # changed line index (Step 6). Inline findings will become GitHub review
        # comments on specific lines. Summary-only findings go into the PR
        # comment body instead.
        inline_findings, summary_only_findings = split_inline_and_summary_findings(
            findings=findings,
            changed_line_index=changed_line_index,
        )
        debug_print("STEP 11a — Inline findings (line is in the diff)", inline_findings)
        debug_print("STEP 11b — Summary-only findings (line not in diff)", summary_only_findings)
        log(f"Inline-safe findings: {len(inline_findings)}")
        log(f"Summary-only findings: {len(summary_only_findings)}")

        # ── STEP 12: Inline Comment Posting Results ───────────────────────────
        # What actually got posted inline vs what fell back to summary.
        # posted_inline_findings = successfully posted as inline comments.
        # inline_fallback_findings = failed to post inline, moved to summary.
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
        debug_print("STEP 12a — Successfully posted inline findings", posted_inline_findings)
        debug_print("STEP 12b — Fallback findings (inline failed → moved to summary)", inline_fallback_findings)

        summary_only_findings.extend(inline_fallback_findings)

        # ── STEP 13: Quality Gate Decision ────────────────────────────────────
        # Shows the final list of all findings that were evaluated for the
        # quality gate, and whether the build will be failed.
        all_evaluated_findings = posted_inline_findings + summary_only_findings
        quality_gate_failed = should_fail_build(
            findings=all_evaluated_findings,
            fail_on_severity=config["fail_on_severity"],
        )
        debug_print("STEP 13 — Quality gate evaluation", {
            "fail_on_severity": config["fail_on_severity"],
            "total_findings_evaluated": len(all_evaluated_findings),
            "quality_gate_failed": quality_gate_failed,
            "findings_that_triggered_gate": [
                f for f in all_evaluated_findings
                if f.get("severity") in _severities_at_or_above(config["fail_on_severity"])
            ],
        })

        # ── STEP 14: Summary Comment Body ─────────────────────────────────────
        # The full markdown text that will be posted (or updated) as the PR
        # summary comment. This is the final human-readable output.
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
        debug_print("STEP 14 — Summary comment body (markdown that will be posted)", summary_body)

        post_or_update_summary_comment(
            owner=config["owner"],
            repo=config["repo"],
            pull_number=pull_number,
            body=summary_body,
            token=config["token"],
            api_url=config["api_url"],
        )
        token_tracker.print_token_summary()

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


def _severities_at_or_above(threshold: str) -> list[str]:
    """
    Helper used in Step 13 to filter which findings triggered the quality gate.
    Returns all severity levels that are >= the configured threshold.
    """
    order = ["INFO", "MINOR", "MAJOR", "CRITICAL"]
    if threshold not in order:
        return []
    return order[order.index(threshold):]


if __name__ == "__main__":
    main()