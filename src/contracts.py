"""Contract parsing and strict validation."""

from __future__ import annotations

import json
import re
from typing import Any

from schemas import Contract


JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


def contract_from_mapping(value: dict[str, Any]) -> Contract:
    list_fields = ("apps", "inputs", "outputs", "preconditions", "effects", "api_patterns", "failure_modes")
    normalized: dict[str, Any] = {
        "skill_id": value.get("skill_id"),
        "capability": value.get("capability"),
        "domain": value.get("domain"),
    }
    for field in list_fields:
        items = value.get(field, [])
        if not isinstance(items, list) or not all(isinstance(item, str) and item.strip() for item in items):
            raise ValueError(f"contract {field} must be a list of non-empty strings")
        normalized[field] = tuple(dict.fromkeys(item.strip() for item in items))
    return Contract(**normalized)


def parse_contract_response(text: str, expected_skill_id: str) -> Contract:
    match = JSON_BLOCK.search(text)
    payload = json.loads(match.group(1) if match else text)
    if not isinstance(payload, dict):
        raise ValueError("contract response must contain one JSON object")
    if payload.get("skill_id") != expected_skill_id:
        raise ValueError("contract skill_id does not match requested skill")
    return contract_from_mapping(payload)


def contract_prompt(skill_id: str, skill_body: str) -> str:
    return f"""Extract a factual contract from the skill below. Return JSON only with keys:
skill_id, capability, domain, apps, inputs, outputs, preconditions, effects,
api_patterns, failure_modes. Use only evidence present in the skill and use empty lists
when absent. skill_id must be {skill_id!r}.

SKILL:\n{skill_body}"""

