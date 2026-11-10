"""All test utterances are synthetic; no recordings or language robustness claims."""
import json
import pytest
from pydantic import ValidationError
from app.engine import Session,Issue,process
from app.evaluation import FIXTURES,project,evaluate
from app.store import Store,Conflict

@pytest.mark.parametrize('fixture',json.loads(FIXTURES.read_text()),ids=lambda f:f['id'])
def test_required_synthetic(fixture):
    s=Session()
    for t in fixture['turns']:process(s,t)
    assert project(s)==fixture['expected']
    assert all(not i.confirmed for i in s.issues)

def test_house_revision_retained():
    s=process(Session(),'House 42, sorry not 42, house 24')
    assert s.issues[0].location=='House 24'
    assert any(r.after=='House 42' for r in s.issues[0].revisions)
    assert '42' in s.issues[0].original_text

def test_scope_only_water():
    s=process(Session(),'Drainage blocked near school and no water in building')
    ids=[i.id for i in s.issues]
    process(s,'Water actually started Monday, not Sunday')
    assert len(s.issues)==2
    assert s.issues[0].time_reference is None
    assert s.issues[1].time_reference=='Monday'
    assert ids==[i.id for i in s.issues]

def test_repeated_corrections():
    s=process(Session(),'Water at house 42')
    process(s,'Actually house 24');process(s,'Sorry not house 24, house 26')
    assert s.issues[0].location=='House 26'
    assert len(s.issues[0].revisions)>=4

def test_ambiguous_reference_does_not_mutate():
    s=process(Session(),'Water near school and streetlight at main road')
    before=project(s);process(s,'Actually second cross')
    assert project(s)==before and s.prompts

def test_explicit_target():
    s=process(Session(),'Water near school and streetlight at main road')
    process(s,'Actually second cross',target_id=s.issues[1].id)
    assert s.issues[0].location=='School' and s.issues[1].location=='Second Cross'

def test_missing_location():
    s=process(Session(),'Garbage not collected since yesterday')
    assert s.issues[0].missing==['location']

def test_plain_yes_is_not_confirmation():
    s=process(Session(),'Water near school');process(s,'yes confirm')
    assert not s.issues[0].confirmed

def test_correction_revokes_confirmation():
    s=process(Session(),'Water near school');s.issues[0].confirmed=True
    process(s,'Actually at main road')
    assert not s.issues[0].confirmed

def test_contradiction_blocks():
    s=process(Session(),'Water near school');process(s,'confirm but do not confirm')
    assert s.issues[0].blocked and not s.issues[0].confirmed

def test_interruption_disk_resume(tmp_path):
    path=str(tmp_path/'test.db');store=Store(path);s=store.create();process(s,'Water at house 42');store.save(s,0)
    other=Store(path);s=other.get(s.id);process(s,'Sorry house 24');other.save(s,1)
    assert Store(path).get(s.id).issues[0].location=='House 24'
    assert len(Store(path).get(s.id).turns)==2

def test_concurrent_save_rejected(tmp_path):
    store=Store(str(tmp_path/'test.db'));s=store.create();a=store.get(s.id);b=store.get(s.id)
    process(a,'Water near school');store.save(a,0);process(b,'Garbage near school')
    with pytest.raises(Conflict):store.save(b,0)

def test_strict_schema():
    with pytest.raises(ValidationError):Issue(category='water',original_text='x',confirmed='true')
    with pytest.raises(ValidationError):Issue(category='invented',original_text='x')
    with pytest.raises(ValidationError):Issue(category='water',original_text='x',confidence=.99)

def test_negated_previous_location():
    s=process(Session(),'Water at house 42');process(s,'not house 42')
    assert s.issues[0].location is None

def test_kannada_reference_across_turns():
    s=process(Session(),'Streetlight main road');process(s,'main road alla, second cross alli')
    assert s.issues[0].location=='Second Cross'

def test_unknown_text_asks():
    s=process(Session(),'Something happened somewhere')
    assert not s.issues and s.prompts

def test_evaluation_measured():
    d=evaluate();assert d['total']==5 and len(d['scenarios'])==5

def test_unresolved_correction_blocks_old_record():
    s=process(Session(),'Water near school');s.issues[0].confirmed=True
    process(s,'actually Maple Avenue')
    assert s.issues[0].blocked and not s.issues[0].confirmed

def test_ambiguous_correction_revokes_all_possible_targets():
    s=process(Session(),'Water near school and streetlight at main road')
    for i in s.issues:i.confirmed=True
    process(s,'actually second cross')
    assert all(i.blocked and not i.confirmed for i in s.issues)

def test_multiple_locations_without_correction_blocked():
    s=process(Session(),'Water near school at main road')
    assert s.issues[0].blocked and 'clarification' in s.issues[0].missing

def test_selected_issue_conflicts_with_named_category():
    s=process(Session(),'Water near school and streetlight at main road')
    before=project(s);s.issues[1].confirmed=True
    process(s,'Water actually started Monday',target_id=s.issues[1].id)
    assert project(s)==before
    assert s.issues[1].blocked and not s.issues[1].confirmed
    assert s.prompts
