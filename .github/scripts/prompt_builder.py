import json

from langchain_core.prompts import PromptTemplate

from constants import PROMPT_TEMPLATE_PATH


def build_prompt(
    issues: list[dict],
    csv_rows: list[dict],
    xml_files: dict[str, str],
    csv_headers: list[str] = None,
    readme_content: str = "",
    functional_context_rules: list[dict] = None,
) -> str:
    """Build the analysis prompt by filling the markdown template via LangChain PromptTemplate.

    Uses Jinja2 template format so that literal curly braces in the template
    (JSON examples, XML snippets, the {{ROW_TEMPLATE}} output placeholder) do
    NOT collide with LangChain's variable-substitution syntax.

    Template file must use Jinja2-style placeholders:  {{ VARIABLE_NAME }}
    Literal single braces in JSON/XML examples are left as-is — Jinja2 only
    treats {{ ... }} as interpolation, so bare { and } are safe.
    """

    headers = csv_headers

    # ── Format CSV ──
    csv_text = "\t".join(headers) + "\n"
    for row in csv_rows:
        csv_text += "\t".join(row.get(h, "") for h in headers) + "\n"

    # ── Format XML files ──
    xml_text = ""
    for filename, content in xml_files.items():
        xml_text += f"\n--- {filename} ---\n{content}\n"

    # ── Format issues ──
    issues_text = ""
    for issue in issues:
        issues_text += f"\n{'=' * 60}\n"
        issues_text += f"ISSUE #{issue['id']}: {issue['title']}\n"
        issues_text += f"{'=' * 60}\n"
        issues_text += f"{issue['body']}\n"

    # ── Build dynamic row template ──
    row_template = {h: "..." for h in headers}
    row_template_str = json.dumps(row_template, indent=4)

    # ── Build Group 2 column list ──
    group2_cols = [h for h in headers if h not in ("scenario_id", "description", "trade_id")]
    group2_description = "\n".join(f"- `{col}`" for col in group2_cols)

    # ── Format functional context rules ──
    from functional_context_cache import format_rules_for_prompt
    functional_context_block = format_rules_for_prompt(functional_context_rules or [])

    # ── Load template and build LangChain PromptTemplate (Jinja2) ──
    template_text = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")

    prompt_template = PromptTemplate(
        input_variables=[
            "GROUP2_COLUMNS",
            "ISSUES",
            "CSV_CONTENT",
            "XML_CONTENT",
            "ROW_TEMPLATE",
            "README_CONTENT",
            "FUNCTIONAL_CONTEXT_RULES",
        ],
        template=template_text,
        template_format="jinja2",   # ← key change: Jinja2 handles literal { } safely
    )

    return prompt_template.format(
        GROUP2_COLUMNS=group2_description,
        ISSUES=issues_text,
        CSV_CONTENT=csv_text,
        XML_CONTENT=xml_text,
        ROW_TEMPLATE=row_template_str,
        README_CONTENT=readme_content,
        FUNCTIONAL_CONTEXT_RULES=functional_context_block,
    )


# ── One-off template migration helper ─────────────────────────────────────────

def migrate_template_to_jinja2(template_path=None) -> None:
    """Convert the prompt template from {VAR} / {{VAR}} syntax to Jinja2 {{ VAR }}.

    The template has three kinds of content handled differently:

    1. Placeholder variables  →  become {{ VAR_NAME }}
       Old forms accepted:  {VAR_NAME}  or  {{VAR_NAME}}

    2. Literal JSON braces in example blocks  →  left completely alone.
       e.g.  {"action": "modify"}  stays as  {"action": "modify"}
       Jinja2 only interprets {{ ... }}, so bare { } are always safe.

    3. {{ROW_TEMPLATE}} in the JSON output block is a known variable and will
       be converted to {{ ROW_TEMPLATE }}. The value passed in is the already-
       rendered JSON object string, so the final prompt contains the literal
       JSON — exactly what was there before.

    Run once, then commit the updated template file.

    Usage:
        from prompt_builder import migrate_template_to_jinja2
        migrate_template_to_jinja2()          # uses PROMPT_TEMPLATE_PATH from constants
    """
    import re
    from pathlib import Path

    path = Path(template_path) if template_path else PROMPT_TEMPLATE_PATH

    known_vars = {
        "GROUP2_COLUMNS",
        "ISSUES",
        "CSV_CONTENT",
        "XML_CONTENT",
        "ROW_TEMPLATE",
        "README_CONTENT",
        "FUNCTIONAL_CONTEXT_RULES",
    }

    original = path.read_text(encoding="utf-8")

    # Match {{VAR}} (double-brace) first, then {VAR} (single-brace).
    # Only converts known placeholder names; leaves everything else untouched.
    def replacer(match: re.Match) -> str:
        # group 1 = name from {{VAR}}, group 2 = name from {VAR}
        var = match.group(1) or match.group(2)
        if var in known_vars:
            return f"{{{{ {var} }}}}"    # writes  {{ VAR }}  into the file
        return match.group(0)            # unknown token — leave as-is

    migrated = re.sub(
        r"\{\{([A-Z_]+)\}\}|\{([A-Z_]+)\}",
        replacer,
        original,
    )

    path.write_text(migrated, encoding="utf-8")
    print(f"Template migrated to Jinja2 syntax and saved to {path}")