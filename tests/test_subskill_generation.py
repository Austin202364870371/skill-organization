import json

import pytest

from subskill_generation import _normalize_subskill_contract_mapping, _parse_proposals


def cores():
    return {
        f"family{i}-core": {"reference": {"required_apis": ["phone.search_contacts"]}}
        for i in range(3)
    }


def proposals(count=10):
    values = []
    for index in range(count):
        values.append({
            "capability": f"Reusable procedure {index}",
            "description": "A shared bounded procedure.",
            "supporting_core_ids": list(cores()),
            "supporting_apis": ["phone.search_contacts"],
            "inputs": ["query"],
            "outputs": ["matches"],
        })
    return json.dumps({"proposals": values})


def test_shared_proposals_require_supported_cross_family_evidence():
    parsed = _parse_proposals(proposals(), cores())
    assert len(parsed) == 10
    assert all(item["proposal_id"].startswith("shared-") for item in parsed)


def test_shared_proposals_enforce_count_gate():
    with pytest.raises(ValueError, match="10 to 15"):
        _parse_proposals(proposals(9), cores())


def test_shared_proposals_discard_unknown_api_but_keep_authoritative_evidence():
    value = json.loads(proposals())
    value["proposals"][0]["supporting_apis"] = ["invented.api", "phone.search_contacts"]
    parsed = _parse_proposals(json.dumps(value), cores())
    assert parsed[0]["supporting_apis"] == ["phone.search_contacts"]
    assert parsed[0]["rejected_supporting_apis"] == ["invented.api"]


def test_shared_proposals_reject_when_no_authoritative_api_remains():
    value = json.loads(proposals())
    value["proposals"][0]["supporting_apis"] = ["invented.api"]
    with pytest.raises(ValueError, match="no supporting API comes from references"):
        _parse_proposals(json.dumps(value), cores())


def test_structured_contract_items_are_losslessly_encoded():
    mapping = {
        "inputs": [{"name": "query", "type": "string", "description": "Search term"}],
        "outputs": [{"name": "matches", "type": "array"}],
        "failure_modes": ["No match", {"condition": "ambiguous", "action": "stop"}],
    }
    normalized = _normalize_subskill_contract_mapping(mapping)
    assert json.loads(normalized["inputs"][0]) == mapping["inputs"][0]
    assert json.loads(normalized["outputs"][0]) == mapping["outputs"][0]
    assert normalized["failure_modes"][0] == "No match"
    assert json.loads(normalized["failure_modes"][1]) == mapping["failure_modes"][1]
