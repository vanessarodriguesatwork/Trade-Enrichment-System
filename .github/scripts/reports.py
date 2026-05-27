from datetime import datetime, timezone
from pathlib import Path

from constants import CLAUDE_MODEL


def generate_html_report(
    release_tag: str,
    issues: list[dict],
    analysis: dict,
    reports_dir: str,
):
    """Generate a clean, light-themed HTML traceability report."""

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    summary = analysis.get("analysis_summary", "No summary provided.")
    csv_changes = analysis.get("csv_changes", [])
    xml_changes = analysis.get("xml_changes", [])
    traceability = analysis.get("traceability", [])

    # ── Build table row fragments ──
    issues_rows = ""
    for issue in issues:
        labels = ", ".join(issue.get("labels", [])) or "—"
        issues_rows += f"""
        <tr>
            <td><strong>#{issue['id']}</strong></td>
            <td>{issue['title']}</td>
            <td><span class="label">{labels}</span></td>
        </tr>"""

    csv_change_rows = ""
    for change in csv_changes:
        action_class = change["action"]
        scenario = change.get("scenario_id", "—")
        reason = change.get("reason", "—")
        issue_id = change.get("issue_id", "—")
        csv_change_rows += f"""
        <tr>
            <td><span class="badge badge-{action_class}">{change['action'].upper()}</span></td>
            <td><code>{scenario}</code></td>
            <td>#{issue_id}</td>
            <td>{reason}</td>
        </tr>"""

    xml_change_rows = ""
    for change in xml_changes:
        action_class = change["action"]
        xml_change_rows += f"""
        <tr>
            <td><span class="badge badge-{action_class}">{change['action'].upper()}</span></td>
            <td><code>{change['filename']}</code></td>
            <td>{change.get('reason', '—')}</td>
        </tr>"""

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

    modified_count = sum(1 for c in csv_changes if c["action"] == "modify")
    inserted_count = sum(1 for c in csv_changes if c["action"] == "insert")
    deleted_count  = sum(1 for c in csv_changes if c["action"] == "delete")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Regression Pack Report — Release {release_tag}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f8f9fb;
            color: #2d3748;
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }}
        .header h1 {{ font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
        .header .meta {{
            display: flex;
            gap: 2rem;
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }}
        .header .meta span {{ display: flex; align-items: center; gap: 0.3rem; }}
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
        .stat-card.issues  {{ border-color: #667eea; }}
        .stat-card.modified {{ border-color: #f6ad55; }}
        .stat-card.inserted {{ border-color: #68d391; }}
        .stat-card.deleted  {{ border-color: #fc8181; }}
        .stat-card .number {{ font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; }}
        .stat-card.issues .number   {{ color: #667eea; }}
        .stat-card.modified .number {{ color: #dd6b20; }}
        .stat-card.inserted .number {{ color: #38a169; }}
        .stat-card.deleted .number  {{ color: #e53e3e; }}
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
        table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
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
        tr:hover {{ background: #f7fafc; }}
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
        .badge-modify  {{ background: #fefcbf; color: #975a16; }}
        .badge-insert  {{ background: #c6f6d5; color: #276749; }}
        .badge-delete  {{ background: #fed7d7; color: #9b2c2c; }}
        .badge-create  {{ background: #c6f6d5; color: #276749; }}
        .label {{
            background: #e2e8f0;
            padding: 0.15rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            color: #4a5568;
        }}
        .ac-cell {{ font-size: 0.85rem; line-height: 1.8; }}
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
                <tbody>{issues_rows}</tbody>
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
                <tbody>{csv_change_rows}</tbody>
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
                <tbody>{xml_change_rows}</tbody>
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
                <tbody>{trace_rows}</tbody>
            </table>
        </div>

        <div class="footer">
            Auto-generated by Regression Pack Analyzer &middot; Powered by Claude AI &middot; Release {release_tag}
        </div>
    </div>
</body>
</html>"""

    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    report_file = reports_path / f"report-{release_tag}.html"
    report_file.write_text(html, encoding="utf-8")
    print(f"HTML report generated: {report_file}")


def generate_md_report(
    release_tag: str,
    issues: list[dict],
    analysis: dict,
    reports_dir: str,
):
    """Generate a markdown traceability report."""

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    summary = analysis.get("analysis_summary", "No summary provided.")
    csv_changes = analysis.get("csv_changes", [])
    xml_changes = analysis.get("xml_changes", [])
    traceability = analysis.get("traceability", [])

    modified_count = sum(1 for c in csv_changes if c["action"] == "modify")
    inserted_count = sum(1 for c in csv_changes if c["action"] == "insert")
    deleted_count  = sum(1 for c in csv_changes if c["action"] == "delete")

    lines = []

    lines.append(f"# Regression Pack Analysis Report — Release {release_tag}")
    lines.append(f"\n**Generated:** {now}  ")
    lines.append(f"**Analyzer:** Claude AI ({CLAUDE_MODEL})\n")
    lines.append("---\n")

    lines.append("## Summary Stats\n")
    lines.append("| Issues Analyzed | Scenarios Modified | Scenarios Added | Scenarios Removed |")
    lines.append("|---|---|---|---|")
    lines.append(f"| {len(issues)} | {modified_count} | {inserted_count} | {deleted_count} |\n")

    lines.append("## Analysis Summary\n")
    lines.append(f"{summary}\n")
    lines.append("---\n")

    lines.append("## Issues Analyzed\n")
    lines.append("| Issue | Title | Labels |")
    lines.append("|---|---|---|")
    for issue in issues:
        labels = ", ".join(issue.get("labels", [])) or "—"
        lines.append(f"| #{issue['id']} | {issue['title']} | {labels} |")
    lines.append("")

    lines.append("## CSV Changes (Test Scenarios)\n")
    lines.append("| Action | Scenario | Issue | Reason |")
    lines.append("|---|---|---|---|")
    for change in csv_changes:
        lines.append(
            f"| {change['action'].upper()} "
            f"| {change.get('scenario_id', '—')} "
            f"| #{change.get('issue_id', '—')} "
            f"| {change.get('reason', '—')} |"
        )
    lines.append("")

    lines.append("### Scenario Details\n")
    for change in csv_changes:
        scenario = change.get("scenario_id", "—")
        row = change.get("row", {})
        lines.append(f"#### {scenario} — {change['action']}")
        if row:
            for key, value in row.items():
                if value:
                    lines.append(f"- **{key}:** {value}")
        lines.append("")
    lines.append("---\n")

    lines.append("## XML Trade File Changes\n")
    lines.append("| Action | File | Reason |")
    lines.append("|---|---|---|")
    for change in xml_changes:
        lines.append(
            f"| {change['action'].upper()} "
            f"| {change.get('filename', '—')} "
            f"| {change.get('reason', '—')} |"
        )
    lines.append("")

    lines.append("### XML File Contents\n")
    for change in xml_changes:
        if change["action"] in ("create", "modify") and change.get("content"):
            lines.append(f"#### {change['filename']}")
            lines.append("```xml")
            lines.append(change["content"])
            lines.append("```\n")
    lines.append("---\n")

    lines.append("## Traceability Matrix\n")
    for trace in traceability:
        lines.append(f"### Issue #{trace['issue_id']}: {trace['issue_title']}\n")

        lines.append("#### Acceptance Criteria\n")
        for ac in trace.get("acceptance_criteria", []):
            lines.append(f"- {ac}")
        lines.append("")

        lines.append("#### Scenarios Impacted\n")
        lines.append(", ".join(f"`{s}`" for s in trace.get("scenarios_impacted", [])))
        lines.append("")

        lines.append("#### Coverage Notes\n")
        lines.append(trace.get("coverage_notes", "—"))
        lines.append("")

    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    report_file = reports_path / f"report-{release_tag}.md"
    report_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"MD report generated: {report_file}")