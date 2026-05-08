#!/usr/bin/env python3
"""
Regression Pack Analyzer — Agentic Flow
Reads GitHub issues, analyzes impact on regression pack using Claude,
and applies changes to CSV + XML trade files.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
CSV_HEADERS = [
    "scenario_id", "description", "trade_id", "tradeId", "time", "amount",
    "partyAccount1", "partyAccount2",
    "partyAccount1_accountNumber", "partyAccount1_holderName",
    "partyAccount1_currency", "partyAccount1_branch",
    "partyAccount2_accountNumber", "partyAccount2_holderName",
    "partyAccount2_currency", "partyAccount2_branch",
    "expected_output"
]

CLAUDE_MODEL = "claude-sonnet-4-20250514"


# ─────────────────────────────────────────────
# File I/O Helpers
# ─────────────────────────────────────────────
def read_csv_file(csv_path: str) -> list[dict]:
    """Read tab-delimited CSV into list of dicts."""
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(dict(row))
    return rows


def write_csv_file(csv_path: str, rows: list[dict], headers: list[str] = None):
    """Write list of dicts to tab-delimited CSV."""
    fieldnames = headers if headers else CSV_HEADERS
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            clean_row = {h: row.get(h, "") for h in fieldnames}
            writer.writerow(clean_row)


def read_trade_xmls(trades_dir: str) -> dict[str, str]:
    """Read all XML files from trades directory. Returns {filename: content}."""
    xmls = {}
    trades_path = Path(trades_dir)
    if trades_path.exists():
        for xml_file in sorted(trades_path.glob("*.xml")):
            xmls[xml_file.name] = xml_file.read_text(encoding="utf-8")
    return xmls


def write_trade_xml(trades_dir: str, filename: str, content: str):
    """Write a single XML trade file."""
    filepath = Path(trades_dir) / filename
    filepath.write_text(content, encoding="utf-8")
    print(f"  Written XML: {filepath}")


def delete_trade_xml(trades_dir: str, filename: str):
    """Delete a single XML trade file."""
    filepath = Path(trades_dir) / filename
    if filepath.exists():
        filepath.unlink()
        print(f"  Deleted XML: {filepath}")


# ─────────────────────────────────────────────
# Prompt Builder
# ─────────────────────────────────────────────
def build_prompt(issues: list[dict], csv_rows: list[dict], xml_files: dict[str, str]) -> str:
    """Build the analysis prompt for Claude."""

    # Format CSV as readable text
    csv_text = "\t".join(CSV_HEADERS) + "\n"
    for row in csv_rows:
        csv_text += "\t".join(row.get(h, "") for h in CSV_HEADERS) + "\n"

    # Format XML files
    xml_text = ""
    for filename, content in xml_files.items():
        xml_text += f"\n--- {filename} ---\n{content}\n"

    # Format issues
    issues_text = ""
    for issue in issues:
        issues_text += f"\n{'='*60}\n"
        issues_text += f"ISSUE #{issue['id']}: {issue['title']}\n"
        issues_text += f"{'='*60}\n"
        issues_text += f"{issue['body']}\n"

    prompt = f"""You are a regression test pack analyzer for a Kafka-based Trade Enrichment System.

## YOUR TASK
Analyze the following GitHub issues (requirements) and determine the impact on the existing regression test pack.
You must decide which test cases (CSV rows) need to be MODIFIED, INSERTED, or DELETED, and update the corresponding trade XML files.

## RULES
1. **Prefer MODIFYING existing test cases** over creating new ones — only insert new ones if the scenario is genuinely new and not covered by any existing test case.
2. Each CSV row represents a test scenario. Each scenario has a corresponding XML file in the trades directory.
3. The `scenario_id` follows the pattern TC-XXX (e.g., TC-001, TC-022). For new scenarios, continue from the highest existing ID.
4. The `trade_id` and XML filename follow the pattern TRD-XXXX (e.g., TRD-0001). For new trades, continue from the highest existing number. Special trades like TRD-UNKNOWN, TRD-MISSING follow their own pattern.
5. XML files follow this structure:
```xml
<trade>
    <tradeId>TRD-XXXX</tradeId>
    <time>2026-05-05TXX:XX:XXZ</time>
    <amount>XXXX</amount>
    <partyAccount1>ACC-XXX</partyAccount1>
    <partyAccount2>ACC-XXX</partyAccount2>
</trade>
```
   New fields from issues should be added to this structure where applicable.
6. For malformed XML test cases, intentionally break the XML syntax (mismatched tags, etc.)
7. The `expected_output` column describes what should happen when this trade is processed.
8. When a test case is modified, update BOTH the CSV row AND the corresponding XML file.
9. Analyze ALL acceptance criteria from each issue and ensure every AC is covered by at least one test scenario.
10. **IMPORTANT**: partyAccount1 = buyer account, partyAccount2 = seller account in the system context.
11. For valid/enriched test cases, the partyAccount1/2_* fields contain the enriched account details from Account Service.
12. For rejected/failed test cases, the enriched fields are typically empty.

## CSV COLUMN STRUCTURE
The CSV columns are divided into two logical groups:

**Group 1 — Test Metadata:**
- `scenario_id`: Unique test case identifier (TC-XXX)
- `description`: Human-readable description of the test scenario
- `trade_id`: Reference to the corresponding input XML file in the trades directory 
  (e.g., TRD-0001 maps to TRD-0001.xml). This is the ONLY link to the input — 
  all input data lives in the XML file, NOT in the CSV.

**Group 2 — Expected Kafka Output:**
ALL remaining columns represent the expected message that should be published 
to the Kafka output queue after the system processes the input XML trade file.
- `tradeId`, `time`, `amount`, `partyAccount1`, `partyAccount2`: Core trade fields 
  expected in the Kafka output message.
- `partyAccount1_accountNumber`, `partyAccount1_holderName`, `partyAccount1_currency`, 
  `partyAccount1_branch`: Expected enriched fields for the buyer account in the Kafka output.
- `partyAccount2_accountNumber`, `partyAccount2_holderName`, `partyAccount2_currency`, 
  `partyAccount2_branch`: Expected enriched fields for the seller account in the Kafka output.
- `expected_output`: Overall expected result/status of the trade processing 
  (e.g., ENRICHED, REJECTED, FAILED).

**The input to the system is ALWAYS the XML file. The CSV only defines what 
the Kafka output should look like after processing.**

**Adding New Columns:**
- New columns should ONLY be added to Group 2 (Expected Kafka Output) — 
  since Group 1 (metadata) is fixed.
- Add a new column if a GitHub issue introduces a new field that should 
  appear in the Kafka output message.
- New column names should follow the existing naming convention: 
  `partyAccountX_<fieldName>` for account-related fields, or descriptive 
  camelCase for other fields.
- When adding new columns, backfill ALL existing rows with "" if not applicable.
- Always declare new columns in the `new_columns` field of your response.

## GITHUB ISSUES TO ANALYZE
{issues_text}

## CURRENT REGRESSION PACK — trade.csv (tab-delimited)
{csv_text}

## CURRENT TRADE XML FILES
{xml_text}

## REQUIRED OUTPUT FORMAT
You MUST respond with valid JSON only — no markdown, no explanation outside the JSON.
Use this exact structure:

{{
    "analysis_summary": "Brief summary of what changes are needed and why",
    "csv_changes": [
        {{
            "action": "modify|insert|delete",
            "scenario_id": "TC-XXX",
            "reason": "Why this change is needed, referencing the issue and AC",
            "issue_id": <issue_number>,
            "row": {{
                "scenario_id": "TC-XXX",
                "description": "...",
                "trade_id": "TRD-XXXX",
                "tradeId": "TRD-XXXX",
                "time": "2026-05-05TXX:XX:XXZ",
                "amount": "...",
                "partyAccount1": "...",
                "partyAccount2": "...",
                "partyAccount1_accountNumber": "...",
                "partyAccount1_holderName": "...",
                "partyAccount1_currency": "...",
                "partyAccount1_branch": "...",
                "partyAccount2_accountNumber": "...",
                "partyAccount2_holderName": "...",
                "partyAccount2_currency": "...",
                "partyAccount2_branch": "...",
                "expected_output": "..."
            }}
        }}
    ],
    "xml_changes": [
        {{
            "action": "modify|create|delete",
            "filename": "TRD-XXXX.xml",
            "reason": "Why this XML change is needed",
            "content": "<trade>...</trade>"
        }}
    ],
    "traceability": [
        {{
            "issue_id": <issue_number>,
            "issue_title": "...",
            "acceptance_criteria": ["AC1: ...", "AC2: ..."],
            "scenarios_impacted": ["TC-XXX", "TC-YYY"],
            "coverage_notes": "How each AC is covered"
        }}
    ],
    "new_columns": [
        {{
            "name": "column_name",
            "reason": "Why this column is being added, referencing the issue and AC"
        }}
    ]
}}

IMPORTANT:
- For "delete" actions in csv_changes, the "row" field can be empty {{}}.
- For "delete" actions in xml_changes, the "content" field can be empty "".
- Ensure the JSON is valid and parseable.
- Do NOT wrap the JSON in markdown code blocks.
- Make sure every acceptance criterion from every issue is traced to at least one test scenario.
"""
    return prompt


# ─────────────────────────────────────────────
# Claude API Call
# ─────────────────────────────────────────────
def call_claude(prompt: str) -> dict:
    """Send prompt to Claude and parse the JSON response."""
    client = anthropic.Anthropic()

    print("Calling Claude API...")
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8192,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text
    print(f"Claude response received ({len(response_text)} chars)")

    # Parse JSON — handle potential markdown wrapping
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse Claude response as JSON: {e}")
        print(f"Response text:\n{response_text}")
        sys.exit(1)

    return result


# ─────────────────────────────────────────────
# Apply Changes
# ─────────────────────────────────────────────
def apply_csv_changes(csv_rows: list[dict], changes: list[dict], new_columns: list[dict]) -> tuple[list[dict], list[str]]:
    """Apply modify/insert/delete changes to CSV rows. Returns updated rows and updated headers."""

    # Build updated headers dynamically
    headers = list(CSV_HEADERS)
    for col in new_columns:
        if col["name"] not in headers:
            # All new columns are Kafka output fields — always insert before expected_output
            headers.insert(headers.index("expected_output"), col["name"])
            print(f"  New column added: {col['name']} — {col['reason']}")

    # Backfill new columns in existing rows
    for row in csv_rows:
        for col in new_columns:
            if col["name"] not in row:
                row[col["name"]] = ""

    # Index rows by scenario_id for quick lookup
    row_index = {row["scenario_id"]: i for i, row in enumerate(csv_rows)}

    rows_to_delete = set()
    rows_to_insert = []

    for change in changes:
        action = change["action"]
        scenario_id = change.get("scenario_id", "")
        reason = change.get("reason", "")

        if action == "modify":
            if scenario_id in row_index:
                idx = row_index[scenario_id]
                csv_rows[idx] = change["row"]
                print(f"  Modified: {scenario_id} — {reason}")
            else:
                print(f"  WARNING: Cannot modify {scenario_id} — not found, inserting instead")
                rows_to_insert.append(change["row"])

        elif action == "insert":
            rows_to_insert.append(change["row"])
            print(f"  Inserted: {scenario_id} — {reason}")

        elif action == "delete":
            if scenario_id in row_index:
                rows_to_delete.add(scenario_id)
                print(f"  Deleted: {scenario_id} — {reason}")
            else:
                print(f"  WARNING: Cannot delete {scenario_id} — not found")

    csv_rows = [row for row in csv_rows if row.get("scenario_id") not in rows_to_delete]
    csv_rows.extend(rows_to_insert)

    def sort_key(row):
        sid = row.get("scenario_id", "")
        try:
            return int(sid.replace("TC-", ""))
        except ValueError:
            return 9999
    csv_rows.sort(key=sort_key)

    return csv_rows, headers

def apply_xml_changes(trades_dir: str, changes: list[dict]):
    """Apply create/modify/delete changes to XML trade files."""
    for change in changes:
        action = change["action"]
        filename = change["filename"]
        content = change.get("content", "")
        reason = change.get("reason", "")

        if action in ("create", "modify"):
            write_trade_xml(trades_dir, filename, content)
            print(f"  {'Created' if action == 'create' else 'Modified'}: {filename} — {reason}")
        elif action == "delete":
            delete_trade_xml(trades_dir, filename)
            print(f"  Deleted: {filename} — {reason}")


# ─────────────────────────────────────────────
# HTML Report Generator
# ─────────────────────────────────────────────
def generate_html_report(
    release_tag: str,
    issues: list[dict],
    analysis: dict,
    reports_dir: str
):
    """Generate a clean, light-themed HTML traceability report."""

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    summary = analysis.get("analysis_summary", "No summary provided.")
    csv_changes = analysis.get("csv_changes", [])
    xml_changes = analysis.get("xml_changes", [])
    traceability = analysis.get("traceability", [])

    # Build issues table rows
    issues_rows = ""
    for issue in issues:
        labels = ", ".join(issue.get("labels", [])) or "—"
        issues_rows += f"""
        <tr>
            <td><strong>#{issue['id']}</strong></td>
            <td>{issue['title']}</td>
            <td><span class="label">{labels}</span></td>
        </tr>"""

    # Build CSV changes table rows
    csv_change_rows = ""
    for change in csv_changes:
        action_class = change['action']
        scenario = change.get('scenario_id', '—')
        reason = change.get('reason', '—')
        issue_id = change.get('issue_id', '—')
        csv_change_rows += f"""
        <tr>
            <td><span class="badge badge-{action_class}">{change['action'].upper()}</span></td>
            <td><code>{scenario}</code></td>
            <td>#{issue_id}</td>
            <td>{reason}</td>
        </tr>"""

    # Build XML changes table rows
    xml_change_rows = ""
    for change in xml_changes:
        action_class = change['action']
        xml_change_rows += f"""
        <tr>
            <td><span class="badge badge-{action_class}">{change['action'].upper()}</span></td>
            <td><code>{change['filename']}</code></td>
            <td>{change.get('reason', '—')}</td>
        </tr>"""

    # Build traceability matrix
    trace_rows = ""
    for trace in traceability:
        acs = "<br>".join(trace.get("acceptance_criteria", []))
        scenarios = ", ".join(f"<code>{s}</code>" for s in trace.get("scenarios_impacted", []))
        notes = trace.get("coverage_notes", "—")
        trace_rows += f"""
        <tr>
            <td><strong>#{trace['issue_id']}</strong></td>
            <td>{trace['issue_title']}</td>
            <td class="ac-cell">{acs}</td>
            <td>{scenarios}</td>
            <td>{notes}</td>
        </tr>"""

    # Count stats
    modified_count = sum(1 for c in csv_changes if c['action'] == 'modify')
    inserted_count = sum(1 for c in csv_changes if c['action'] == 'insert')
    deleted_count = sum(1 for c in csv_changes if c['action'] == 'delete')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Regression Pack Report — Release {release_tag}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f8f9fb;
            color: #2d3748;
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }}
        .header h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        .header .meta {{
            display: flex;
            gap: 2rem;
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }}
        .header .meta span {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border-top: 3px solid;
        }}
        .stat-card.issues {{ border-color: #667eea; }}
        .stat-card.modified {{ border-color: #f6ad55; }}
        .stat-card.inserted {{ border-color: #68d391; }}
        .stat-card.deleted {{ border-color: #fc8181; }}
        .stat-card .number {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }}
        .stat-card.issues .number {{ color: #667eea; }}
        .stat-card.modified .number {{ color: #dd6b20; }}
        .stat-card.inserted .number {{ color: #38a169; }}
        .stat-card.deleted .number {{ color: #e53e3e; }}
        .stat-card .label-text {{
            font-size: 0.85rem;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .section {{
            background: white;
            border-radius: 10px;
            padding: 1.8rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .section h2 {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #edf2f7;
            color: #2d3748;
        }}
        .summary-text {{
            background: #f7fafc;
            padding: 1rem 1.2rem;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            font-size: 0.95rem;
            color: #4a5568;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        th {{
            background: #f7fafc;
            padding: 0.75rem 1rem;
            text-align: left;
            font-weight: 600;
            color: #4a5568;
            border-bottom: 2px solid #e2e8f0;
        }}
        td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #edf2f7;
            vertical-align: top;
        }}
        tr:hover {{
            background: #f7fafc;
        }}
        code {{
            background: #edf2f7;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-size: 0.85rem;
            color: #553c9a;
        }}
        .badge {{
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        .badge-modify {{
            background: #fefcbf;
            color: #975a16;
        }}
        .badge-insert {{
            background: #c6f6d5;
            color: #276749;
        }}
        .badge-delete {{
            background: #fed7d7;
            color: #9b2c2c;
        }}
        .badge-create {{
            background: #c6f6d5;
            color: #276749;
        }}
        .label {{
            background: #e2e8f0;
            padding: 0.15rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            color: #4a5568;
        }}
        .ac-cell {{
            font-size: 0.85rem;
            line-height: 1.8;
        }}
        .footer {{
            text-align: center;
            margin-top: 2rem;
            padding: 1rem;
            font-size: 0.8rem;
            color: #a0aec0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Regression Pack Analysis Report</h1>
            <p>Release <strong>{release_tag}</strong></p>
            <div class="meta">
                <span>Generated: {now}</span>
                <span>Analyzer: Claude AI ({CLAUDE_MODEL})</span>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card issues">
                <div class="number">{len(issues)}</div>
                <div class="label-text">Issues Analyzed</div>
            </div>
            <div class="stat-card modified">
                <div class="number">{modified_count}</div>
                <div class="label-text">Scenarios Modified</div>
            </div>
            <div class="stat-card inserted">
                <div class="number">{inserted_count}</div>
                <div class="label-text">Scenarios Added</div>
            </div>
            <div class="stat-card deleted">
                <div class="number">{deleted_count}</div>
                <div class="label-text">Scenarios Removed</div>
            </div>
        </div>

        <div class="section">
            <h2>Analysis Summary</h2>
            <div class="summary-text">{summary}</div>
        </div>

        <div class="section">
            <h2>Issues Analyzed</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width:80px">Issue</th>
                        <th>Title</th>
                        <th style="width:120px">Labels</th>
                    </tr>
                </thead>
                <tbody>
                    {issues_rows}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>CSV Changes (Test Scenarios)</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width:100px">Action</th>
                        <th style="width:100px">Scenario</th>
                        <th style="width:80px">Issue</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody>
                    {csv_change_rows}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>XML Trade File Changes</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width:100px">Action</th>
                        <th style="width:180px">File</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody>
                    {xml_change_rows}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Traceability Matrix</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width:70px">Issue</th>
                        <th style="width:180px">Title</th>
                        <th>Acceptance Criteria</th>
                        <th style="width:180px">Scenarios</th>
                        <th>Coverage Notes</th>
                    </tr>
                </thead>
                <tbody>
                    {trace_rows}
                </tbody>
            </table>
        </div>

        <div class="footer">
            Auto-generated by Regression Pack Analyzer &middot; Powered by Claude AI &middot; Release {release_tag}
        </div>
    </div>
</body>
</html>"""

    # Write report
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    report_file = reports_path / f"report-{release_tag}.html"
    report_file.write_text(html, encoding="utf-8")
    print(f"Report generated: {report_file}")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Regression Pack Analyzer")
    parser.add_argument("--issues-file", required=True, help="Path to issues JSON file")
    parser.add_argument("--csv-file", required=True, help="Path to trade.csv")
    parser.add_argument("--trades-dir", required=True, help="Path to trades XML directory")
    parser.add_argument("--reports-dir", required=True, help="Path to reports output directory")
    parser.add_argument("--release-tag", required=True, help="Release tag being analyzed")
    args = parser.parse_args()

    # ── Step 1: Read inputs ──
    print("=" * 60)
    print("REGRESSION PACK ANALYZER")
    print("=" * 60)
    print(f"Release tag: {args.release_tag}")

    # Read issues
    with open(args.issues_file, "r", encoding="utf-8") as f:
        issues = json.load(f)
    print(f"Issues loaded: {len(issues)}")
    for issue in issues:
        print(f"  - #{issue['id']}: {issue['title']}")

    # Read current CSV
    csv_rows = read_csv_file(args.csv_file)
    print(f"Current CSV rows: {len(csv_rows)}")

    # Read current XMLs
    xml_files = read_trade_xmls(args.trades_dir)
    print(f"Current XML files: {len(xml_files)}")

    # ── Step 2: Build prompt & call Claude ──
    print("\n" + "─" * 60)
    print("ANALYZING WITH CLAUDE")
    print("─" * 60)

    prompt = build_prompt(issues, csv_rows, xml_files)
    print(f"Prompt size: {len(prompt)} chars")

    analysis = call_claude(prompt)
    # Print full agent response
    print(f"\nFull agent response:\n{json.dumps(analysis, indent=2)}")

    print(f"\nAnalysis summary: {analysis.get('analysis_summary', 'N/A')}")
    print(f"CSV changes: {len(analysis.get('csv_changes', []))}")
    print(f"XML changes: {len(analysis.get('xml_changes', []))}")

    # ── Step 3: Apply CSV changes ──
    print("\n" + "─" * 60)
    print("APPLYING CSV CHANGES")
    print("─" * 60)

    csv_changes = analysis.get("csv_changes", [])
    new_columns = analysis.get("new_columns", [])

    if csv_changes or new_columns:
        csv_rows, updated_headers = apply_csv_changes(csv_rows, csv_changes, new_columns)
        write_csv_file(args.csv_file, csv_rows, updated_headers)
        print(f"CSV updated: {len(csv_rows)} total rows")
        if new_columns:
            print(f"New columns added: {[col['name'] for col in new_columns]}")
    else:
        print("No CSV changes to apply")

    # ── Step 4: Apply XML changes ──
    print("\n" + "─" * 60)
    print("APPLYING XML CHANGES")
    print("─" * 60)

    xml_changes = analysis.get("xml_changes", [])
    if xml_changes:
        apply_xml_changes(args.trades_dir, xml_changes)
    else:
        print("No XML changes to apply")

    # ── Step 5: Generate report ──
    print("\n" + "─" * 60)
    print("GENERATING REPORT")
    print("─" * 60)

    generate_html_report(
        release_tag=args.release_tag,
        issues=issues,
        analysis=analysis,
        reports_dir=args.reports_dir,
    )

    print("\n" + "=" * 60)
    print("REGRESSION PACK ANALYZER COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
