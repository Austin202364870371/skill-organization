import json

import pytest

from family_generation import instance_terms, parse_candidate_response


def response(body):
    return json.dumps({"skills": [{
        "type": "core",
        "skill_markdown": body,
        "contract": {
            "capability": "manage records", "domain": "productivity",
            "apps": ["notes"], "inputs": ["query"], "outputs": ["updated record"],
            "preconditions": [], "effects": ["record updated"],
            "api_patterns": ["notes.search", "notes.update"],
            "failure_modes": ["ambiguous match"],
        },
    }]})


BODY = """---
name: Update a matched record
description: Find one record safely and update it.
---
## When to Use
When one existing record must change.
## Preconditions
API access.
## Procedure
Search, disambiguate, update, and verify.
## Relevant APIs / Tools
Search and update APIs.
## Failure Handling
Stop on ambiguity.
## Verification
Read the record again.
"""


def test_candidate_response_builds_skill_and_contract():
    parsed = parse_candidate_response("abc123", response(BODY), "Update Velvet Echo.")
    assert parsed[0][1].skill_id == "abc123-core"
    assert parsed[0][2].skill_id == "abc123-core"


def test_candidate_response_rejects_instance_term():
    leaked = BODY.replace("Update a matched record", "Update Velvet Echo")
    with pytest.raises(ValueError, match="task-instance"):
        parse_candidate_response("abc123", response(leaked), "Update Velvet Echo.")


def test_instance_terms_extracts_specific_values():
    terms = instance_terms('Add "Velvet Echo" to the list before 2030.')
    assert {"Velvet Echo", "2030"} <= terms
