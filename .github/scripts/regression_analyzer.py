#!/usr/bin/env python3
from file_io import read_csv_file, write_csv_file, read_trade_xmls
from prompt_builder import build_prompt
from claude_client import call_claude, filter_functional_changes,token_tracker
from changes import apply_csv_changes, apply_xml_changes
from reports import generate_html_report, generate_md_report
import copy
import argparse
import json
from functional_context_cache import load_functional_context_cache, save_functional_context_cache
def log_section(title):
    print("\n" + "═" * 60)
    print(f"  {title}")
    print("═" * 60)

def log_step(step, message):
    print(f"\n[STEP {step}] {message}")
    print("─" * 40)

def log_prompt(prompt):
    print("\n>>> PROMPT SENT TO CLAUDE <<<")
    print("─" * 40)
    print(prompt)
    print("─" * 40)
    print(f">>> PROMPT END (total: {len(prompt)} chars) <<<")

def log_response(analysis):
    print("\n<<< CLAUDE RESPONSE >>>")
    print("─" * 40)
    print(json.dumps(analysis, indent=2))
    print("─" * 40)
    print("<<< RESPONSE END >>>")

def main():
    parser = argparse.ArgumentParser(description="Regression Pack Analyzer")
    parser.add_argument("--issues-file", required=True, help="Path to issues JSON file")
    parser.add_argument("--csv-file", required=True, help="Path to trade.csv")
    parser.add_argument("--trades-dir", required=True, help="Path to trades XML directory")
    parser.add_argument("--reports-dir", required=True, help="Path to reports output directory")
    parser.add_argument("--release-tag", required=True, help="Release tag being analyzed")
    parser.add_argument("--readme-file", required=False, help="Path to project README.md")
    args = parser.parse_args()

    log_section("REGRESSION PACK ANALYZER")
    print(f"Release tag : {args.release_tag}")
    print(f"Issues file : {args.issues_file}")
    print(f"CSV file    : {args.csv_file}")
    print(f"Trades dir  : {args.trades_dir}")
    print(f"Reports dir : {args.reports_dir}")
    print(f"README file : {args.readme_file or 'Not provided'}")

    # ── Step 1: Read inputs ──
    log_section("STEP 1 — READING INPUTS")

    log_step("1.1", "Loading issues JSON")
    with open(args.issues_file, "r", encoding="utf-8") as f:
        issues = json.load(f)
    print(f"Issues loaded: {len(issues)}")
    for issue in issues:
        print(f"  #{issue['id']}: {issue['title']}")
        if issue.get('body'):
            print(f"    Body preview: {issue['body'][:200]}...")

    log_step("1.2", "Loading README")
    readme_content = ""
    if args.readme_file:
        with open(args.readme_file, "r", encoding="utf-8") as f:
            readme_content = f.read()
        print(f"README loaded: {len(readme_content)} chars")
        print(f"README preview:\n{readme_content[:300]}...")
    else:
        print("No README provided — skipping")

    log_step("1.3", "Loading CSV")
    csv_rows, csv_headers = read_csv_file(args.csv_file)
    old_csv_rows = copy.deepcopy(csv_rows)
    print(f"CSV rows loaded : {len(csv_rows)}")
    print(f"CSV headers     : {csv_headers}")
    print(f"First row sample: {csv_rows[0] if csv_rows else 'EMPTY'}")

    log_step("1.4", "Loading trade XMLs")
    xml_files = read_trade_xmls(args.trades_dir)
    print(f"XML files loaded: {len(xml_files)}")
    for fname, content in xml_files.items():
        print(f"  {fname}: {len(content)} chars")
    log_step("1.5", "Loading functional context cache")
    functional_context_rules = load_functional_context_cache()
    # ── Step 2: Process issues one by one ──
    log_section("STEP 2 — ANALYZING ISSUES WITH CLAUDE")

    all_csv_changes = []
    all_xml_changes = []
    all_traceability = []
    overall_summary_parts = []
    all_new_columns = []

    for i, issue in enumerate(issues, 1):
        log_section(f"ISSUE {i}/{len(issues)} — #{issue['id']}: {issue['title']}")

        log_step(f"2.{i}.1", "Building prompt")
        prompt = build_prompt([issue], csv_rows, xml_files, csv_headers, readme_content,functional_context_rules=functional_context_rules)
        print(f"Prompt size: {len(prompt)} chars")
        log_prompt(prompt)

        log_step(f"2.{i}.2", "Calling Claude")
        analysis = call_claude(prompt)
        log_response(analysis)

        print(f"\nAnalysis summary : {analysis.get('analysis_summary', 'N/A')}")
        print(f"CSV changes      : {len(analysis.get('csv_changes', []))}")
        print(f"XML changes      : {len(analysis.get('xml_changes', []))}")
        print(f"New columns      : {len(analysis.get('new_columns', []))}")
        print(f"Traceability     : {len(analysis.get('traceability', []))}")

        # Apply CSV changes
        csv_changes = analysis.get("csv_changes", [])
        new_columns = analysis.get("new_columns", [])

        if csv_changes or new_columns:
            log_step(f"2.{i}.3", "Applying CSV changes")
            for change in csv_changes:
                print(f"  [{change.get('action', '?').upper()}] {change.get('scenario_id', '?')} — {change.get('reason', '')[:100]}")

            if new_columns:
                print(f"  New columns: {[col['name'] for col in new_columns]}")

            csv_rows, csv_headers = apply_csv_changes(csv_rows, csv_changes, new_columns, csv_headers)
            write_csv_file(args.csv_file, csv_rows, csv_headers)
            csv_rows, csv_headers = read_csv_file(args.csv_file)
            print(f"  CSV after update — rows: {len(csv_rows)}, headers: {csv_headers}")
        else:
            print("\n  No CSV changes to apply for this issue")

        # Apply XML changes
        xml_changes = analysis.get("xml_changes", [])
        if xml_changes:
            log_step(f"2.{i}.4", "Applying XML changes")
            for change in xml_changes:
                print(f"  [{change.get('action', '?').upper()}] {change.get('filename', '?')} — {change.get('reason', '')[:100]}")
                print(f"  Content preview: {change.get('content', '')[:150]}")
            apply_xml_changes(args.trades_dir, xml_changes)
        else:
            print("\n  No XML changes to apply for this issue")

        log_step(f"2.{i}.5", "Re-reading XML files for next iteration")
        xml_files = read_trade_xmls(args.trades_dir)
        print(f"  XML files now: {list(xml_files.keys())}")
        new_rules = analysis.get("functional_context_updates", [])
        if new_rules:
            functional_context_rules = save_functional_context_cache(
                new_rules=new_rules,
                issue_id=issue["id"],
            )
        all_csv_changes.extend(csv_changes)
        all_xml_changes.extend(xml_changes)
        all_traceability.extend(analysis.get("traceability", []))
        overall_summary_parts.append(analysis.get("analysis_summary", ""))
        all_new_columns.extend(new_columns)

    # ── Step 3: Aggregate ──
    log_section("STEP 3 — AGGREGATING RESULTS")
    overall_analysis = {
        "analysis_summary": " ".join(overall_summary_parts),
        "csv_changes": all_csv_changes,
        "xml_changes": all_xml_changes,
        "traceability": all_traceability,
        "new_columns": all_new_columns,
    }
    print(f"Total CSV changes       : {len(all_csv_changes)}")
    print(f"Total XML changes       : {len(all_xml_changes)}")
    print(f"Total traceability items: {len(all_traceability)}")
    print(f"Total new columns       : {len(all_new_columns)}")

    # ── Step 4: Filter functional changes ──
    log_section("STEP 4 — FILTERING FUNCTIONAL CHANGES")
    print("Running filter_functional_changes...")
    overall_analysis = filter_functional_changes(overall_analysis, old_csv_rows)
    print(f"Functional CSV changes after filter: {len(overall_analysis.get('csv_changes', []))}")
    for change in overall_analysis.get("csv_changes", []):
        print(f"  [{change.get('action', '?').upper()}] {change.get('scenario_id', '?')} — {change.get('reason', '')[:100]}")

    # ── Step 5: Generate reports ──
    log_section("STEP 5 — GENERATING REPORTS")
    print("Generating HTML report...")
    generate_html_report(
        release_tag=args.release_tag,
        issues=issues,
        analysis=overall_analysis,
        reports_dir=args.reports_dir,
    )
    print("HTML report generated")

    print("Generating Markdown report...")
    generate_md_report(
        release_tag=args.release_tag,
        issues=issues,
        analysis=overall_analysis,
        reports_dir=args.reports_dir,
    )
    print("Markdown report generated")

    log_section("REGRESSION PACK ANALYZER COMPLETE")
    print(f"Reports written to: {args.reports_dir}")
    token_tracker.print_token_summary()

if __name__ == "__main__":
    main()