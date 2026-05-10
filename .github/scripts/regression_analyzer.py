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
def build_prompt(issues: list[dict], csv_rows: list[dict], xml_files: dict[str, str], csv_headers: list[str] = None) -> str:
    """Build the analysis prompt for Claude."""

    headers = csv_headers if csv_headers is not None else CSV_HEADERS

    # Format CSV as readable text
    csv_text = "\t".join(headers) + "\n"
    for row in csv_rows:
        csv_text += "\t".join(row.get(h, "") for h in headers) + "\n"

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

    # Dynamically build row template from current headers
    row_template = {h: "..." for h in headers}
    row_template_json = json.dumps(row_template, indent=4)
    row_template_str = row_template_json.replace("\n", "\n            ")

    # Dynamically list Group 2 columns so Claude sees all current output fields
    group2_cols = [h for h in headers if h not in ("scenario_id", "description", "trade_id")]
    group2_description = "\n".join(f"- `{col}`" for col in group2_cols)

    prompt = (
        "You are a regression test pack analyzer for a Kafka-based Trade Enrichment System.\n\n"

        "## YOUR TASK\n"
        "Analyze the following GitHub issues (requirements) and determine the impact on the existing regression test pack.\n"
        "You must decide which test cases (CSV rows) need to be MODIFIED, INSERTED, or DELETED, and update the corresponding trade XML files.\n\n"

        "## RULES\n"
        "1. Each CSV row represents a test scenario. Each scenario has a corresponding XML file in the trades directory.\n"
        "2. The `scenario_id` follows the pattern TC-XXX (e.g., TC-001, TC-022). For new scenarios, continue from the highest existing ID.\n"
        "3. The `trade_id` and XML filename follow the pattern TRD-XXXX (e.g., TRD-0001). For new trades, continue from the highest existing number. Special trades like TRD-UNKNOWN, TRD-MISSING follow their own pattern.\n"
        "4. XML files follow this structure:\n"
        "```xml\n"
        "<trade>\n"
        "    <tradeId>TRD-XXXX</tradeId>\n"
        "    <time>2026-05-05TXX:XX:XXZ</time>\n"
        "    <amount>XXXX</amount>\n"
        "    <partyAccount1>ACC-XXX</partyAccount1>\n"
        "    <partyAccount2>ACC-XXX</partyAccount2>\n"
        "</trade>\n"
        "```\n"
        "   New fields from issues should be added to this structure where applicable.\n"
        "5. For malformed XML test cases, intentionally break the XML syntax (mismatched tags, etc.)\n"
        "6. The `expected_output` column describes what should happen when this trade is processed.\n"
        "7. When a test case is modified, update BOTH the CSV row AND the corresponding XML file if the input condition changes.\n"
        "8. **IMPORTANT**: partyAccount1 = buyer account, partyAccount2 = seller account in the system context.\n"
        "9. For valid/enriched test cases, the partyAccount1/2_* fields contain the enriched account details from Account Service.\n"
        "10. For rejected/failed test cases, the enriched fields are typically empty.\n"
        "11. Prioritize modifying existing CSV rows to cover additional test conditions over inserting new rows, especially when the new conditions do not conflict with existing ones. A test case testing multiple non-conflicting conditions is fully valid and preferred.\n"
        "12. Prefer test cases that cover multiple fields or scenarios in a single test case, provided the conditions do not conflict with each other.\n"
        "13. Aggressively seek ways to modify existing test cases to incorporate new scenarios, even if it requires creative adaptation of descriptions or expected outputs. Only insert new tests as an absolute last resort.\n\n"

        "## COVERAGE ANALYSIS — DO THIS BEFORE MAKING ANY CHANGES\n\n"
        "For each AC in the issue, work through these steps in order before deciding any action.\n\n"

        "### STEP 1 — IDENTIFY THE REQUIRED INPUT CONDITION\n"
        "What must the input XML contain (or lack) to exercise this AC?\n"
        "Be specific. Examples:\n"
        '- "buyerSellerIndicator tag present with value BUYER"\n'
        '- "buyerSellerIndicator tag absent entirely"\n'
        '- "amount field has 3 decimal places"\n'
        '- "partyAccount1 references an unknown account"\n\n'

        "### STEP 2 — SCAN EXISTING XML FILES FOR THAT CONDITION\n"
        "Go through every XML file listed in CURRENT TRADE XML FILES.\n"
        "Ask: does any existing XML already have this exact input condition?\n\n"

        "### STEP 3 — APPLY THE DECISION TREE\n\n"
        "For each AC, apply this decision tree with the assumption that modification is possible unless proven impossible. Prioritize MODIFY over INSERT aggressively, especially for non-conflicting conditions.\n\n"
        "Does any existing XML have the required input fields for the test case?\n"
        "|\n"
        "└── YES — found a matching XML (and its CSV row)\n"
        "|    |\n"
        "|    |__ Is the existing test case already testing the new AC (same input condition) ?\n"
        "|        |__ YES -> Update the test scenario description to also mention the incremental AC being covered without updating the csv or the XML input file"
        "|        |"
        "|        |__NO-> Can the existing test case be modified to cover the new condition in addition to the original one (e.g., by updating description, expected output, or XML if needed)? \n"
        "|            ├── YES\n"
        "|            |     └── MODIFY the existing test case (update CSV row + XML if needed)\n"
        "|            |\n"   
        "|            └── NO\n"
        "|                  └── INSERT new CSV row, REUSE the existing XML file\n"
        "|                  (same trade_id, new scenario_id, different primary assertion)\n\n"
        "├── NO\n"
        "|   └── Can any existing XML be modified to include the new input condition, allowing the test case to cover it in addition to the original?\n"
        "|       |__ YES —> MODIFY the respective test case (update CSV row + XML file)\n"
        "|       |__ NO -> Create a new XML File and Insert new CSV row accordingly.\n"
        "|\n"
        
        "### STEP 4 — CONSOLIDATE BEFORE FINALIZING\n"
        "Before writing your response:\n"
        "- Can multiple ACs be satisfied by the same input condition? → Cover in one test case\n"
        "- Are you inserting two test cases that differ only in expected output, not input? → Consolidate into one\n"
        "- Does every INSERT have a genuinely unique input condition absent from all existing XMLs? → If not, convert to MODIFY or REUSE\n"
        "- Prefer MODIFY over INSERT: If an existing test case can be updated to cover additional conditions without conflict, do so instead of creating new ones.\n"
        "- Prefer combining multiple fields or scenarios into a single test case if they are non-conflicting.\n"
        "- Target at least 70-80% of actions as MODIFY; if planning more INSERTs, re-evaluate for modification opportunities.\n\n"

        "### STEP 5 — JUSTIFY EVERY INSERT\n"
        "For every INSERT action in your response you must state:\n"
        "- Which existing XMLs you checked for this input condition\n"
        "- Why none of them had the required condition\n"
        "- Why the existing test case whose XML you are reusing (if reusing) cannot simply be modified\n\n"
        "If you cannot provide a clear justification, convert the INSERT to a MODIFY.\n\n"

        "## TEST CASE INTEGRITY RULE\n\n"
        "NOTE: Multiple CSV rows can reference the same XML file. A new XML is only\n"
        "needed when the input condition itself is genuinely new.\n\n"
        "## CSV COLUMN STRUCTURE\n\n"
        "**Group 1 — Test Metadata (fixed, never add columns here):**\n"
        "- `scenario_id`: Unique test case identifier (TC-XXX)\n"
        "- `description`: Human-readable description of the test scenario\n"
        "- `trade_id`: Reference to the corresponding input XML file in the trades\n"
        "  directory (e.g., TRD-0001 maps to TRD-0001.xml). This is the ONLY link\n"
        "  to the input — all input data lives in the XML file, NOT in the CSV.\n\n"
        "**Group 2 — Expected Kafka Output (all remaining columns):**\n"
        "ALL columns below represent the expected message published to the Kafka\n"
        "output queue after the system processes the input XML trade file:\n"
        + group2_description + "\n\n"

        "**The input to the system is ALWAYS the XML file. The CSV only defines what\n"
        "the Kafka output should look like after processing.**\n\n"

        "**Adding New Columns:**\n"
        "- New columns should ONLY be added to Group 2 (Expected Kafka Output)\n"
        "- Add a new column only if a GitHub issue introduces a new field that should\n"
        "  appear in the Kafka output message\n"
        "- New column names should follow the existing naming convention:\n"
        "  `partyAccountX_<fieldName>` for account-related fields, or descriptive\n"
        "  camelCase for other fields\n"
        "- When adding new columns, backfill ALL existing rows with \"\" — this is a\n"
        "  structural change, do NOT report backfilled rows in csv_changes\n"
        "- Always declare new columns in the `new_columns` field of your response\n\n"
        "## GLOBAL OUTPUT FORMAT RULES\n\n"
        "Some issues introduce formatting rules that apply universally to ALL existing test cases, "
        "not just new ones. These must be applied as a sweep across the entire CSV before the "
        "coverage analysis for new scenarios.\n\n"
        "When an issue states that a field must ALWAYS appear in a specific format in the output "
        "(e.g. amount must always have exactly 2 decimal places), treat this as follows:\n\n"
        "STEP 0 — BEFORE running the coverage analysis for new scenarios:\n"
        "1. Identify every existing CSV row where the affected field does not already conform "
        "to the new format\n"
        "2. Update that field's value in the expected output to conform to the new format\n"
        "3. Report each such row as a MODIFY action in csv_changes\n"
        "4. Do NOT change the description of these rows — the test case is still testing the "
        "same condition, only the expected output value is being corrected to reflect what the "
        "system will now actually produce\n"
        "5. Do NOT create a new XML file for these rows — the input condition is unchanged\n\n"
        "These global format corrections are separate from and in addition to any new test cases "
        "created to cover new input condition scenarios introduced by the same issue.\n\n"
        "## GITHUB ISSUES TO ANALYZE\n"
        + issues_text + "\n"

        "## CURRENT REGRESSION PACK — trade.csv (tab-delimited)\n"
        + csv_text + "\n"

        "## CURRENT TRADE XML FILES\n"
        + xml_text + "\n"

        "## REQUIRED OUTPUT FORMAT\n"
        "You MUST respond with valid JSON only — no markdown, no explanation outside the JSON.\n"
        "Use this exact structure:\n\n"
        "{\n"
        '    "analysis_summary": "Brief summary of what changes are needed and why",\n'
        '    "csv_changes": [\n'
        "        {\n"
        '            "action": "modify|insert|delete",\n'
        '            "scenario_id": "TC-XXX",\n'
        '            "reason": "Why this change is needed. For INSERTs: which existing XMLs were checked and why none sufficed.",\n'
        '            "issue_id": <issue_number>,\n'
        '            "row": ' + row_template_str + "\n"
        "        }\n"
        "    ],\n"
        '    "xml_changes": [\n'
        "        {\n"
        '            "action": "modify|create|delete",\n'
        '            "filename": "TRD-XXXX.xml",\n'
        '            "reason": "Why this XML change is needed",\n'
        '            "content": "<trade>...</trade>"\n'
        "        }\n"
        "    ],\n"
        '    "traceability": [\n'
        "        {\n"
        '            "issue_id": <issue_number>,\n'
        '            "issue_title": "...",\n'
        '            "acceptance_criteria": ["AC1: ...", "AC2: ..."],\n'
        '            "scenarios_impacted": ["TC-XXX", "TC-YYY"],\n'
        '            "coverage_notes": "How each AC is covered and why the chosen action (modify/insert/reuse) was selected"\n'
        "        }\n"
        "    ],\n"
        '    "new_columns": [\n'
        "        {\n"
        '            "name": "column_name",\n'
        '            "reason": "Why this column is being added, referencing the issue and AC"\n'
        "        }\n"
        "    ]\n"
        "}\n\n"

        "IMPORTANT:\n"
        '- For "delete" actions in csv_changes, the "row" field can be empty {}.\n'
        '- For "delete" actions in xml_changes, the "content" field can be empty "".\n'
        "- Ensure the JSON is valid and parseable.\n"
        "- Do NOT wrap the JSON in markdown code blocks.\n"
        "- Make sure every acceptance criterion from every issue is traced to at least one test scenario.\n"
        "- Every INSERT must include justification in the \"reason\" field explaining why no existing test case could be modified instead.\n"
        "- Multiple ACs may map to the same scenario — you do not need one test case per AC.\n"
        "- Backfilling new columns across existing rows is NOT a csv_change — do not report it.\n"
    )

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
def apply_csv_changes(csv_rows: list[dict], changes: list[dict], new_columns: list[dict],current_headers: list[str] = None) -> tuple[list[dict], list[str]]:
    """Apply modify/insert/delete changes to CSV rows. Returns updated rows and updated headers."""
    headers = list(current_headers) if current_headers else list(CSV_HEADERS)  # ← changed

    # Build updated headers dynamically
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

def generate_md_report(
    release_tag: str,
    issues: list[dict],
    analysis: dict,
    reports_dir: str
):
    """Generate a markdown traceability report."""

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    summary = analysis.get("analysis_summary", "No summary provided.")
    csv_changes = analysis.get("csv_changes", [])
    xml_changes = analysis.get("xml_changes", [])
    traceability = analysis.get("traceability", [])

    modified_count = sum(1 for c in csv_changes if c['action'] == 'modify')
    inserted_count = sum(1 for c in csv_changes if c['action'] == 'insert')
    deleted_count  = sum(1 for c in csv_changes if c['action'] == 'delete')

    lines = []

    # ── Header ──
    lines.append(f"# Regression Pack Analysis Report — Release {release_tag}")
    lines.append(f"\n**Generated:** {now}  ")
    lines.append(f"**Analyzer:** Claude AI ({CLAUDE_MODEL})\n")
    lines.append("---\n")

    # ── Stats ──
    lines.append("## Summary Stats\n")
    lines.append(f"| Issues Analyzed | Scenarios Modified | Scenarios Added | Scenarios Removed |")
    lines.append(f"|---|---|---|---|")
    lines.append(f"| {len(issues)} | {modified_count} | {inserted_count} | {deleted_count} |\n")

    # ── Analysis Summary ──
    lines.append("## Analysis Summary\n")
    lines.append(f"{summary}\n")
    lines.append("---\n")

    # ── Issues Analyzed ──
    lines.append("## Issues Analyzed\n")
    lines.append("| Issue | Title | Labels |")
    lines.append("|---|---|---|")
    for issue in issues:
        labels = ", ".join(issue.get("labels", [])) or "—"
        lines.append(f"| #{issue['id']} | {issue['title']} | {labels} |")
    lines.append("")

    # ── CSV Changes ──
    lines.append("## CSV Changes (Test Scenarios)\n")
    lines.append("| Action | Scenario | Issue | Reason |")
    lines.append("|---|---|---|---|")
    for change in csv_changes:
        action   = change['action'].upper()
        scenario = change.get('scenario_id', '—')
        issue_id = change.get('issue_id', '—')
        reason   = change.get('reason', '—')
        lines.append(f"| {action} | {scenario} | #{issue_id} | {reason} |")
    lines.append("")

    # ── Scenario Details ──
    lines.append("### Scenario Details\n")
    for change in csv_changes:
        scenario = change.get('scenario_id', '—')
        action   = change['action']
        row      = change.get('row', {})
        lines.append(f"#### {scenario} — {action}")
        if row:
            for key, value in row.items():
                if value:
                    lines.append(f"- **{key}:** {value}")
        lines.append("")
    lines.append("---\n")

    # ── XML Changes ──
    lines.append("## XML Trade File Changes\n")
    lines.append("| Action | File | Reason |")
    lines.append("|---|---|---|")
    for change in xml_changes:
        action   = change['action'].upper()
        filename = change.get('filename', '—')
        reason   = change.get('reason', '—')
        lines.append(f"| {action} | {filename} | {reason} |")
    lines.append("")

    lines.append("### XML File Contents\n")
    for change in xml_changes:
        if change['action'] in ('create', 'modify') and change.get('content'):
            lines.append(f"#### {change['filename']}")
            lines.append("```xml")
            lines.append(change['content'])
            lines.append("```\n")

    lines.append("---\n")

    # ── Traceability ──
    lines.append("## Traceability Matrix\n")
    for trace in traceability:
        lines.append(f"### Issue #{trace['issue_id']}: {trace['issue_title']}\n")

        lines.append("#### Acceptance Criteria\n")
        for ac in trace.get('acceptance_criteria', []):
            lines.append(f"- {ac}")
        lines.append("")

        lines.append("#### Scenarios Impacted\n")
        lines.append(", ".join(f"`{s}`" for s in trace.get('scenarios_impacted', [])))
        lines.append("")

        lines.append("#### Coverage Notes\n")
        lines.append(trace.get('coverage_notes', '—'))
        lines.append("")

    # ── Write file ──
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    report_file = reports_path / f"report-{release_tag}.md"
    report_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"MD report generated: {report_file}")
# ─────────────────────────────────────────────
# Filter Functional Changes
# ─────────────────────────────────────────────
def filter_functional_changes(overall_analysis: dict, original_csv_rows: list[dict]) -> dict:
    """Filter csv_changes to only those representing genuine new testing behavior."""

    analysis_text = json.dumps(overall_analysis, indent=2)

    # Build a lookup of original rows by scenario_id so Claude can diff before vs after
    original_lookup = {row["scenario_id"]: row for row in original_csv_rows}
    original_lookup_text = json.dumps(original_lookup, indent=2)

    prompt = (
        "You are a regression test pack change reviewer. Your task is to filter a list of "
        "csv_changes down to only those that represent GENUINE NEW TESTING BEHAVIOR.\n\n"

        "## INPUT\n"
        "The following is the overall analysis from processing multiple GitHub issues:\n\n"
        + analysis_text + "\n\n"

        "## ORIGINAL CSV STATE (before any changes were applied)\n"
        "This is the state of every test case before this release's changes were made. "
        "Use this to compare against the modified rows in csv_changes to determine what "
        "actually changed.\n\n"
        + original_lookup_text + "\n\n"

        "## YOUR TASK\n"
        "For every entry in csv_changes, determine whether the test case is now testing "
        "a DIFFERENT CONDITION than it was before. The primary signal for this is the "
        "description field.\n\n"

        "## DECISION RULE\n\n"

        "The description field is the source of truth for what condition a test case is testing.\n\n"

        "KEEP a change if ANY of the following are true:\n"
        "- The description changed between the original and new row, indicating the test "
        "case is now testing a different or additional condition\n"
        "- The action is INSERT, meaning a brand new condition is being tested that did "
        "not exist before\n\n"

        "REMOVE a change if ALL of the following are true:\n"
        "- The action is 'modify'\n"
        "- The description in the new row is identical to the description in the original "
        "row from ORIGINAL CSV STATE, meaning the test case is still testing the same "
        "condition as before\n"
        "- Any field value changes are therefore just updates to reflect new system "
        "behaviour on an already-tested condition, not a new condition being introduced\n\n"

        "## HOW TO EVALUATE\n"
        "For each modify entry in csv_changes:\n"
        "1. Look up the scenario_id in ORIGINAL CSV STATE to get the original row\n"
        "2. Compare the description field between original and new row\n"
        "3. If description is unchanged → REMOVE\n"
        "4. If description changed → KEEP\n"
        "5. If scenario_id is not found in ORIGINAL CSV STATE → treat as INSERT → KEEP\n\n"

        "## OUTPUT FORMAT\n"
        "Return valid JSON only — no markdown, no explanation outside the JSON.\n\n"
        "{\n"
        '    "analysis_summary": "Summary covering only the kept functional changes and why they represent genuine new test coverage",\n'
        '    "csv_changes": [kept changes only],\n'
        '    "xml_changes": [unchanged from input],\n'
        '    "traceability": [unchanged from input],\n'
        '    "new_columns": [unchanged from input]\n'
        "}\n\n"

        "IMPORTANT:\n"
        "- Do NOT modify xml_changes, traceability, or new_columns\n"
        "- Do NOT modify the content of kept csv_changes entries — keep them exactly as-is\n"
        "- Only filter csv_changes to remove non-behavioral entries\n"
        "- Update analysis_summary to describe only what was kept and why\n"
        "- Ensure the JSON is valid and parseable\n"
        "- Do NOT wrap the JSON in markdown code blocks\n"
    )

    print("Filtering functional changes with Claude...")
    print(prompt)
    message = anthropic.Anthropic().messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text
    print(f"Filter response received ({len(response_text)} chars)")

    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        filtered_analysis = json.loads(cleaned)
        print(f"Filtered to {len(filtered_analysis.get('csv_changes', []))} functional changes")
        return filtered_analysis
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse filter response as JSON: {e}")
        print(f"Response text:\n{response_text}")
        return overall_analysis
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
    old_csv_rows = csv_rows.copy()  # Keep a copy of original for comparison
    print(f"Current CSV rows: {len(csv_rows)}")

    # Read current XMLs
    xml_files = read_trade_xmls(args.trades_dir)
    print(f"Current XML files: {len(xml_files)}")

    # ── Step 2: Process issues one by one ──
    print("\n" + "─" * 60)
    print("ANALYZING ISSUES WITH CLAUDE")
    print("─" * 60)

    # Initialize accumulators
    all_csv_changes = []
    all_xml_changes = []
    all_traceability = []
    overall_summary_parts = []
    all_new_columns = []
    csv_headers = CSV_HEADERS.copy()

    for i, issue in enumerate(issues, 1):
        print(f"\nProcessing issue {i}/{len(issues)}: #{issue['id']} - {issue['title']}")

        # Build prompt with single issue and current state
        prompt = build_prompt([issue], csv_rows, xml_files, csv_headers)
        print(f"  Prompt size: {len(prompt)} chars")

        analysis = call_claude(prompt)
        print(f"  Analysis summary: {analysis.get('analysis_summary', 'N/A')}")
        print(f"  CSV changes: {len(analysis.get('csv_changes', []))}")
        print(f"  XML changes: {len(analysis.get('xml_changes', []))}")

        # Apply CSV changes
        csv_changes = analysis.get("csv_changes", [])
        new_columns = analysis.get("new_columns", [])

        if csv_changes or new_columns:
            csv_rows, csv_headers = apply_csv_changes(csv_rows, csv_changes, new_columns, csv_headers)
            write_csv_file(args.csv_file, csv_rows, csv_headers)
            csv_rows = read_csv_file(args.csv_file)
            print(csv_headers)
            print(f"  CSV updated: {len(csv_rows)} total rows")
            if new_columns:
                print(f"  New columns added: {[col['name'] for col in new_columns]}")

        # Apply XML changes
        xml_changes = analysis.get("xml_changes", [])
        if xml_changes:
            apply_xml_changes(args.trades_dir, xml_changes)

        # Re-read XML files for next iteration
        xml_files = read_trade_xmls(args.trades_dir)

        # Accumulate results
        all_csv_changes.extend(csv_changes)
        all_xml_changes.extend(xml_changes)
        all_traceability.extend(analysis.get("traceability", []))
        overall_summary_parts.append(analysis.get("analysis_summary", ""))
        all_new_columns.extend(new_columns)

    # Create overall analysis
    overall_analysis = {
        "analysis_summary": " ".join(overall_summary_parts),
        "csv_changes": all_csv_changes,
        "xml_changes": all_xml_changes,
        "traceability": all_traceability,
        "new_columns": all_new_columns  # Include for completeness, though not used in reports
    }

    print(f"\nOverall analysis complete:")
    print(f"  Total CSV changes: {len(all_csv_changes)}")
    print(f"  Total XML changes: {len(all_xml_changes)}")
    print(f"  Total traceability entries: {len(all_traceability)}")

    # ── Step 3: Filter functional changes ──
    print("\n" + "─" * 60)
    print("FILTERING FUNCTIONAL CHANGES")
    print("─" * 60)

    overall_analysis = filter_functional_changes(overall_analysis,old_csv_rows)

    print(f"After filtering: {len(overall_analysis.get('csv_changes', []))} functional CSV changes")

    # ── Step 4: Generate final report ──
    print("\n" + "─" * 60)
    print("GENERATING FINAL REPORT")
    print("─" * 60)

    generate_html_report(
        release_tag=args.release_tag,
        issues=issues,
        analysis=overall_analysis,
        reports_dir=args.reports_dir,
    )
    generate_md_report(
        release_tag=args.release_tag,
        issues=issues,
        analysis=overall_analysis,
        reports_dir=args.reports_dir,
    )
    print("\n" + "=" * 60)
    print("REGRESSION PACK ANALYZER COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
