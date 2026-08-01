import json
import sys
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from constants import CLAUDE_MODEL

# ── Token tracker ──────────────────────────────────────────────────────────────

class TokenTracker:
    def __init__(self):
        self.total_input = 0
        self.total_output = 0
        self.calls: list[dict] = []

    def record(self, label: str, input_tokens: int, output_tokens: int):
        self.total_input += input_tokens
        self.total_output += output_tokens
        self.calls.append({
            "label": label,
            "input": input_tokens,
            "output": output_tokens,
        })

    def print_token_summary(self):
        print("\n" + "=" * 60)
        print("TOKEN USAGE SUMMARY")
        print("=" * 60)
        print(f"{'Stage':<35} {'Input':>8} {'Output':>8} {'Total':>8}")
        print("-" * 60)
        for call in self.calls:
            total = call["input"] + call["output"]
            print(f"{call['label']:<35} {call['input']:>8,} {call['output']:>8,} {total:>8,}")
        print("-" * 60)
        grand_total = self.total_input + self.total_output
        print(f"{'TOTAL':<35} {self.total_input:>8,} {self.total_output:>8,} {grand_total:>8,}")
        print("=" * 60)


token_tracker = TokenTracker()


# ── Token-tracking callback ────────────────────────────────────────────────────

class TokenTrackerCallback(BaseCallbackHandler):
    """LangChain callback that records token usage into the global TokenTracker."""

    def __init__(self, label: str):
        super().__init__()
        self.label = label

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        usage = {}
        if response.llm_output:
            usage = response.llm_output.get("usage", {})
        input_tokens  = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        print(f"Input tokens : {input_tokens}")
        print(f"Output tokens: {output_tokens}")
        token_tracker.record(self.label, input_tokens, output_tokens)


# ── Helpers ────────────────────────────────────────────────────────────────────
'''
def _parse_json_response(response_text: str) -> str:
    """Strip optional markdown fences and return a clean JSON string."""
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()
'''

def _parse_json_response(response_text: str) -> str:
    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    decoder = json.JSONDecoder()

    start = cleaned.find("{")
    while start != -1:
        try:
            obj, _ = decoder.raw_decode(cleaned[start:])
            return json.dumps(obj)
        except json.JSONDecodeError:
            start = cleaned.find("{", start + 1)

    raise ValueError("No valid JSON object found.")


def _make_llm(max_tokens: int, label: str) -> ChatAnthropic:
    """Return a ChatAnthropic instance wired with a token-tracking callback."""
    return ChatAnthropic(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        callbacks=[TokenTrackerCallback(label=label)],
    )


def _jinja2_chat_prompt(template_str: str, input_variables: list[str]) -> ChatPromptTemplate:
    """
    Build a ChatPromptTemplate that uses Jinja2 rendering for its single
    human message.

    ChatPromptTemplate.from_template() does NOT accept template_format, so
    we construct the inner PromptTemplate explicitly and wrap it in a
    HumanMessagePromptTemplate — the correct way to use Jinja2 inside a chat
    prompt in LangChain.
    """
    human_prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            input_variables=input_variables,
            template=template_str,
            template_format="jinja2",
        )
    )
    return ChatPromptTemplate.from_messages([human_prompt])


# ── Public API ─────────────────────────────────────────────────────────────────

def call_claude(prompt: str) -> dict:
        """Send a plain-string prompt to Claude and return the parsed JSON response.
    
        The prompt is already fully rendered by build_prompt(), so we pass it as
        a single literal string.  We use Jinja2 here too so that any stray { }
        characters in the rendered prompt don't confuse LangChain's str_format
        parser.
        """
        llm = _make_llm(max_tokens=10000, label="Claude API Call")
    
        # Pass the whole prompt as a single Jinja2 variable — safe against any
        # brace characters that may exist inside the rendered prompt string.
        chat_prompt = _jinja2_chat_prompt(
            template_str="{{ prompt }}",
            input_variables=["prompt"],
        )
        chain = chat_prompt | llm
    
        print("Calling Claude API...")
        response = chain.invoke({"prompt": prompt})
        
        print("=" * 80)
        print("FIRST 3 CONTENT BLOCKS:")
        for i, block in enumerate(response.content[:3]):
            print(f"\nBLOCK {i}")
        
            if isinstance(block, dict):
                print("Keys:", list(block.keys()))
                print("Type:", block.get("type"))
            else:
                print("OBJECT TYPE:", type(block))
            
                if hasattr(block, "type"):
                    print("OBJECT BLOCK TYPE:", block.type)
            
                if hasattr(block, "text"):
                    print("TEXT PREVIEW:", repr(block.text[:200]))
                
        print("=" * 80)    
            
        response_text = response.content
        if isinstance(response_text, list):
            parts = []

            for block in response_text:
                if hasattr(block, "text"):
                    parts.append(block.text)
                    
                elif isinstance(block, dict):
                    print("DICT TYPE:", block.get("type"))
                    print("DICT KEYS:", list(block.keys()))
                    
                    if "text" in block:
                        print("TEXT PREVIEW:", repr(block["text"][:200]))    
                        parts.append(block["text"])
            
            response_text = "".join(parts)
        print(f"Claude response received ({len(response_text)} chars)")

    
        print("RAW RESPONSE_TEXT:")
        print(response_text)
        
        return {}


def filter_functional_changes(
    overall_analysis: dict,
    original_csv_rows: list[dict],
) -> dict:
    """Filter csv_changes to only those representing genuine new testing behaviour."""

    analysis_text      = json.dumps(overall_analysis, indent=2)
    original_lookup    = {row["scenario_id"]: row for row in original_csv_rows}
    original_lookup_text = json.dumps(original_lookup, indent=2)

    filter_prompt_template = """\
You are a regression test pack change reviewer. Your task is to filter a list of \
csv_changes down to only those that represent GENUINE NEW TESTING BEHAVIOR.

## INPUT
The following is the overall analysis from processing multiple GitHub issues:

{{ analysis_text }}

## ORIGINAL CSV STATE (before any changes were applied)
This is the state of every test case before this release's changes were made. \
Use this to compare against the modified rows in csv_changes to determine what \
actually changed.

{{ original_lookup_text }}

## YOUR TASK
For every entry in csv_changes, determine whether the test case is now testing \
a DIFFERENT CONDITION than it was before. The primary signal for this is the \
description field.

## DECISION RULE

The description field is the source of truth for what condition a test case is testing.

KEEP a change if ANY of the following are true:
- The description changed between the original and new row, indicating the test \
case is now testing a different or additional condition
- The action is INSERT, meaning a brand new condition is being tested that did \
not exist before

REMOVE a change if ALL of the following are true:
- The action is 'modify'
- The description in the new row is identical to the description in the original \
row from ORIGINAL CSV STATE, meaning the test case is still testing the same \
condition as before
- Any field value changes are therefore just updates to reflect new system \
behaviour on an already-tested condition, not a new condition being introduced

## HOW TO EVALUATE
For each modify entry in csv_changes:
1. Look up the scenario_id in ORIGINAL CSV STATE to get the original row
2. Compare the description field between original and new row
3. If description is unchanged → REMOVE
4. If description changed → KEEP
5. If scenario_id is not found in ORIGINAL CSV STATE → treat as INSERT → KEEP

## OUTPUT FORMAT
Return valid JSON only — no markdown, no explanation outside the JSON.

{
    "analysis_summary": "Summary covering only the kept functional changes and why they represent genuine new test coverage",
    "csv_changes": [kept changes only],
    "xml_changes": [unchanged from input],
    "traceability": [unchanged from input],
    "new_columns": [unchanged from input]
}

IMPORTANT:
- Do NOT modify xml_changes, traceability, or new_columns
- Do NOT modify the content of kept csv_changes entries — keep them exactly as-is
- Only filter csv_changes to remove non-behavioral entries
- Update analysis_summary to describe only what was kept and why
- Ensure the JSON is valid and parseable
- Do NOT wrap the JSON in markdown code blocks
"""

    llm = _make_llm(max_tokens=8192, label="Claude API Call")

    # Build the chat prompt correctly: HumanMessagePromptTemplate wrapping a
    # Jinja2 PromptTemplate so that the JSON blobs in analysis_text and
    # original_lookup_text (which contain { } characters) are not misread as
    # variable placeholders.
    chat_prompt = _jinja2_chat_prompt(
        template_str=filter_prompt_template,
        input_variables=["analysis_text", "original_lookup_text"],
    )
    chain = chat_prompt | llm

    print("Filtering functional changes with Claude...")
    response = chain.invoke(
        {
            "analysis_text": analysis_text,
            "original_lookup_text": original_lookup_text,
        }
    )

    response_text = response.content
    print(f"Filter response received ({len(response_text)} chars)")

    try:
        filtered = json.loads(_parse_json_response(response_text))
        print(f"Filtered to {len(filtered.get('csv_changes', []))} functional changes")
        return filtered
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse filter response as JSON: {e}")
        print(f"Response text:\n{response_text}")
        return overall_analysis
