"""Small OpenAI JSON helper with deterministic fallback support."""

from __future__ import annotations

import json
import os
from typing import Any

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


def has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def safe_json_loads(raw_text: str, fallback: Any) -> Any:
    try:
        return json.loads(raw_text)
    except (TypeError, json.JSONDecodeError):
        return fallback


def call_openai_json(
    *,
    system_prompt: str,
    user_prompt: str,
    fallback: Any,
    model: str = "gpt-4o-mini",
) -> Any:
    """Call OpenAI for JSON; return fallback on missing key or parse/API failure."""

    if not has_api_key():
        return fallback

    try:
        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = response.choices[0].message.content or ""
        return safe_json_loads(content, fallback)
    except Exception:
        return fallback
