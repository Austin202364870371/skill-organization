import json

from family_validation import _subskill_stage_evidence


def test_subskill_stage_evidence_uses_executed_api(tmp_path):
    skill_id = "shared-pagination-abc123"
    directory = tmp_path / skill_id
    directory.mkdir()
    (directory / "metadata.json").write_text(json.dumps({
        "skill_id": skill_id,
        "supporting_apis": ["spotify.search_songs", "phone.search_contacts"],
    }))
    record = {
        "steps": [{"code": "x = apis.spotify.search_songs(query='q')"}],
        "used_skill_ids": [skill_id],
    }
    evidence = _subskill_stage_evidence([skill_id], tmp_path, record)[skill_id]
    assert evidence["stage_observed"]
    assert evidence["supporting_apis_observed"] == ["spotify.search_songs"]
    assert evidence["agent_reported_used"]
