"""
model_client.py — LangChain replacement for direct Anthropic/Groq SDK calls.

Drop-in replacement: call_model(), extract_json_from_text(), repair_json_with_model()
all keep the same signatures so main.py and agents.py need no changes in how
they call this module.

Key changes vs the original:
  - call_anthropic_model / call_groq_model are now thin wrappers around
    LangChain's ChatAnthropic / ChatGroq.
  - call_model() routes to the right LangChain LLM based on config["model_provider"].
  - Token tracking is done via LangChain's UsageMetadata instead of SDK-specific fields.
  - extract_json_from_text() now uses LangChain's JsonOutputParser as the
    first-pass parser, falling back to the existing regex-strip logic.
  - repair_json_with_model() is unchanged in behaviour but uses call_model().
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from config import log


# =============================================================================
# Token Tracker  (same public API as before)
# =============================================================================

class TokenTracker:
    def __init__(self) -> None:
        self.total_input = 0
        self.total_output = 0
        self.calls: list[dict] = []

    def record(self, label: str, input_tokens: int, output_tokens: int) -> None:
        self.total_input += input_tokens
        self.total_output += output_tokens
        self.calls.append({"label": label, "input": input_tokens, "output": output_tokens})

    def print_token_summary(self) -> None:
        print("\n" + "=" * 60)
        print("TOKEN USAGE SUMMARY")
        print("=" * 60)
        print(f"{'Stage':<35} {'Input':>8} {'Output':>8} {'Total':>8}")
        print("-" * 60)
        for call in self.calls:
            total = call["input"] + call["output"]
            print(f"{call['label']:<35} {call['input']:>8,} {call['output']:>8,} {total:>8,}")
        print("-" * 60)
        grand = self.total_input + self.total_output
        print(f"{'TOTAL':<35} {self.total_input:>8,} {self.total_output:>8,} {grand:>8,}")
        print("=" * 60)


token_tracker = TokenTracker()


# =============================================================================
# Internal: build LangChain message list from the legacy messages format
# =============================================================================

def _to_langchain_messages(
    messages: list[dict[str, str]],
) -> list[SystemMessage | HumanMessage]:
    """
    Convert the legacy [{"role": "system"|"user"|"assistant", "content": "..."}]
    format into LangChain message objects.

    Anthropic's ChatAnthropic accepts a system message as the first element in
    the list when passed as a SystemMessage, so no special splitting is needed.
    """
    lc_messages: list[SystemMessage | HumanMessage] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            lc_messages.append(SystemMessage(content=content))
        else:
            # "user" and "assistant" both map to HumanMessage for our simple
            # two-turn prompts; for multi-turn you would use AIMessage for
            # "assistant" — but the agents here only ever send system + user.
            lc_messages.append(HumanMessage(content=content))
    return lc_messages


# =============================================================================
# Provider: Anthropic
# =============================================================================

def call_anthropic_model(
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int = 8192,
    temperature: float = 0.1,
) -> str:
    """
    Calls Claude via LangChain's ChatAnthropic.
    Extracts token usage from response.usage_metadata.
    """
    llm = ChatAnthropic(
        api_key=api_key,
        model_name=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    lc_messages = _to_langchain_messages(messages)

    print(f"[model_client] Anthropic call | model={model} | messages={len(messages)}")
    response = llm.invoke(lc_messages)

    # LangChain stores token counts in usage_metadata (LangChain ≥ 0.2)
    usage = getattr(response, "usage_metadata", None) or {}
    input_tokens  = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    token_tracker.record("Anthropic API Call", input_tokens, output_tokens)

    return response.content


# =============================================================================
# Provider: Groq
# =============================================================================

def call_groq_model(
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int = 8192,
    temperature: float = 0.1,
) -> str:
    """
    Calls a Groq-hosted model via LangChain's ChatGroq.
    """
    llm = ChatGroq(
        groq_api_key=api_key,
        model_name=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    lc_messages = _to_langchain_messages(messages)

    print(f"[model_client] Groq call | model={model} | messages={len(messages)}")
    response = llm.invoke(lc_messages)

    usage = getattr(response, "usage_metadata", None) or {}
    input_tokens  = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    print(f"Input Tokens: {input_tokens}")
    print(f"Output Tokens: {output_tokens}")
    token_tracker.record("Groq API Call", input_tokens, output_tokens)

    return response.content


# =============================================================================
# Unified caller  (same signature as before)
# =============================================================================

def call_model(
    config: dict,
    messages: list[dict[str, str]],
    temperature: float = 0.1,
) -> str:
    """
    Routes to the correct LangChain provider based on config["model_provider"].
    Keeps the exact same signature as the original so agents.py is unchanged.
    """
    # ── debug header (mirrors original) ──────────────────────────────────────
    provider = config["model_provider"]
    provider = "groq"
    print("\n" + "=" * 60)
    print(" CALL_MODEL INPUT")
    print("=" * 60)
    print(f"Provider   : {provider}")
    print(f"Temperature: {temperature}")
    print(f"Messages ({len(messages)}):")
    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown").upper()
        preview = msg.get("content", "")[:200]
        print(f"  [{i}] {role}: {preview}")
    print("=" * 60)

    # ── routing ───────────────────────────────────────────────────────────────
    if provider == "anthropic":
        if not config.get("anthropic_api_key"):
            raise RuntimeError("ANTHROPIC_API_KEY missing")
        response = call_anthropic_model(
            api_key=config["anthropic_api_key"],
            model=config["model"],
            messages=messages,
            max_tokens=8192,
            temperature=temperature,
        )

    elif provider == "groq":
        if not config.get("groq_api_key"):
            raise RuntimeError("GROQ_API_KEY missing")
        response = call_groq_model(
            api_key=config["groq_api_key"],
            # Hard-coded in the original too — keep it consistent
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            max_tokens=8192,
            temperature=temperature,
        )

    else:
        raise RuntimeError(f"Unsupported model provider: {provider}")

    # ── debug footer ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(" CALL_MODEL OUTPUT")
    print("=" * 60)
    print(response[:500])        # first 500 chars to keep logs readable
    print("=" * 60 + "\n")

    return response


# =============================================================================
# JSON extraction  (same API as before, LangChain parser used as first-pass)
# =============================================================================

# A single shared instance — stateless, safe to reuse.
_json_parser = JsonOutputParser()


def extract_json_from_text(text: str) -> Any:
    """
    Parses JSON from a model response.

    Pass 1 — LangChain's JsonOutputParser (handles ```json fences automatically).
    Pass 2 — Manual markdown fence strip + json.loads.
    Pass 3 — Find first { ... } block and parse that.
    """
    text = text.strip()

    # Pass 1: LangChain parser (strips ```json fences and calls json.loads)
    try:
        return _json_parser.parse(text)
    except Exception:
        pass

    # Pass 2: manual fence strip
    cleaned = re.sub(r"^```json\s*", "", text)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Pass 3: extract first top-level JSON object
    start = text.find("{")
    end   = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError("Unable to parse JSON from model response.")


def repair_json_with_model(config: dict, invalid_text: str) -> Any:
    """Asks the model to fix broken JSON. Behaviour unchanged from original."""
    messages = [
        {
            "role": "system",
            "content": (
                "You repair invalid JSON. Return valid JSON only. "
                "Do not add markdown or explanation."
            ),
        },
        {"role": "user", "content": invalid_text},
    ]
    repaired_text = call_model(config=config, messages=messages)
    return extract_json_from_text(repaired_text)