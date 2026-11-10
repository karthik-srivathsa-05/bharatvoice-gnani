"""Meaningful protocol, persistence, observation-isolation and metric checks."""
import copy
import json
from pathlib import Path
import random
import pytest
from research.protocol_pilot.model import Event, digest
from research.protocol_pilot.policies import Workflow, InjectedCrash
from research.protocol_pilot.replay import replay
from research.protocol_pilot.evaluate import evaluate

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / 'data/streams.json').read_text())
GOLD = json.loads((ROOT / 'data/oracle.json').read_text())
P = {'category': 'water', 'location': 'House 42', 'time_reference': None}

def event(seq, kind, **data):
    return Event(str(seq), seq, kind, data)

def setup(tmp_path, mode):
    w = Workflow(tmp_path / (mode + '.db'), mode)
    w.apply(event(1, 'proposal', issue='a', values=P, evidence='source'))
    w.apply(event(2, 'approval', issue='a', version=1, digest=digest(P), actor='reviewer'))
    assert w.eligible('a')
    return w

@pytest.mark.parametrize('case', CASES, ids=lambda c: c['id'])
def test_frozen_scenario_and_restart_equivalence(case, tmp_path):
    a = replay(case, 'B3', tmp_path / 'b.db')
    b = replay(case, 'M', tmp_path / 'm.db')
    assert a == b
    # Compare representation-neutral observations only, not private storage.
    metrics = evaluate(a, GOLD[case['id']])
    assert metrics['duplicate_sink_effects'] == 0
    assert metrics['protocol_state_mismatches'] == 0
    assert metrics['protocol_invalid_effects'] == 0
    assert len(a) == len(case['events'])
    # Reopening after EVERY event must not change no-fault semantics.
    changed = copy.deepcopy(case)
    changed['faults'] = {str(e['seq']): 'restart' for e in case['events']}
    assert replay(changed, 'B3', tmp_path / 'restart.db') == a

@pytest.mark.parametrize('mode', ['B3', 'M'])
def test_ack_edit_and_partial_resolution_never_erase_other_repair(mode, tmp_path):
    w = setup(tmp_path, mode)
    w.apply(event(3, 'correction', scopes=['a'], field='location', evidence='repair1'))
    w.apply(event(4, 'correction', scopes=['a'], field='location', evidence='repair2'))
    w.apply(event(5, 'acknowledgment', issue='a'))
    w.apply(event(6, 'proposal', issue='a', values={'time_reference': 'Monday'}, evidence='source'))
    assert set(w.pending('a')) == {'3', '4'} and not w.eligible('a')
    w.apply(event(7, 'clarification', issue='a', resolves=['3'], values={'location': 'House 24'}, evidence='resolve'))
    assert set(w.pending('a')) == {'4'}
    w.close()

@pytest.mark.parametrize('mode', ['B3', 'M'])
def test_invalid_resolution_and_validation_are_atomic(mode, tmp_path):
    w = setup(tmp_path, mode)
    w.apply(event(3, 'dispute', scopes=['a'], field='location', evidence='source'))
    result = w.apply(event(4, 'clarification', issue='a', resolves=['3'], values={'time_reference': 'Monday'}, evidence='source'))
    assert not result['accepted'] and '3' in w.pending('a')
    before = w.snapshot()['a']['fields']
    result = w.apply(event(5, 'clarification', issue='a', resolves=['3'], values={'location': 'House 24/7'}, evidence='source'))
    assert not result['accepted'] and w.snapshot()['a']['fields'] == before
    assert '3' in w.pending('a')
    w.close()

@pytest.mark.parametrize('mode', ['B3', 'M'])
def test_digest_actor_and_version_bound_approval(mode, tmp_path):
    w = setup(tmp_path, mode)
    w.apply(event(3, 'proposal', issue='a', values={'location': 'House 24'}, evidence='source'))
    new = dict(P, location='House 24')
    for seq, version, dg, actor in [(4, 1, digest(P), 'reviewer'), (5, 2, digest(P), 'reviewer'),
                                    (6, 2, digest(new), 'untrusted')]:
        assert not w.apply(event(seq, 'approval', issue='a', version=version, digest=dg, actor=actor))['accepted']
        assert not w.eligible('a')
    assert w.apply(event(7, 'approval', issue='a', version=2, digest=digest(new), actor='reviewer'))['accepted']
    assert w.eligible('a')
    w.close()

@pytest.mark.parametrize('mode', ['B3', 'M'])
@pytest.mark.parametrize('fault', ['before_commit', 'after_commit'])
def test_sink_crash_retry_and_payload_collision(mode, fault, tmp_path):
    w = setup(tmp_path, mode)
    e = event(3, 'commit', issue='a', operation='same-operation')
    with pytest.raises(InjectedCrash): w.apply(e, fault=fault)
    w.close(); w = Workflow(tmp_path / (mode + '.db'), mode)
    w.apply(e)
    w.apply(event(4, 'commit', issue='a', operation='same-operation'))
    assert len(w.effects()) == 1
    w.apply(event(5, 'proposal', issue='a', values={'location': 'House 24'}, evidence='new'))
    assert not w.apply(event(6, 'commit', issue='a', operation='same-operation'))['accepted']
    assert len(w.effects()) == 1
    w.close()

@pytest.mark.parametrize('mode', ['B3', 'M'])
def test_event_order_idempotency_and_changed_id_rejected(mode, tmp_path):
    w = setup(tmp_path, mode)
    e = event(3, 'source', text='neutral')
    a = w.apply(e)
    assert a == w.apply(e)
    before = w.snapshot()
    with pytest.raises(ValueError): w.apply(event(5, 'acknowledgment', issue='a'))
    with pytest.raises(ValueError): w.apply(event(3, 'source', text='changed'))
    assert w.snapshot() == before
    w.close()

@pytest.mark.parametrize('raw', [
    dict(id='x', seq=0, kind='source', data={'text': 'x'}),
    dict(id='x', seq=1, kind='proposal', data={'issue': 'a', 'values': {'invented': 'x'}, 'evidence': 'x'}),
    dict(id='x', seq=1, kind='source', data={'text': 'x', 'gold': True}),
    dict(id='x', seq=1, kind='correction', data={'scopes': [], 'field': 'location', 'evidence': 'x'}),
    dict(id='x', seq=1, kind='approval', data={'issue': 'a', 'version': True, 'digest': 'x', 'actor': 'reviewer'})])
def test_schema_rejects_malformed_or_oracle_fields(raw):
    with pytest.raises(ValueError): Event(**raw)

def test_oracle_changes_scores_not_policy_trace(tmp_path):
    case = next(c for c in CASES if c['id'] == 'F1')
    rows = replay(case, 'B3', tmp_path / 'b.db')
    first = evaluate(rows, GOLD['F1'])
    changed = copy.deepcopy(GOLD['F1'])
    for frame in changed['frames']:
        frame['can_commit'] = ['a']; frame['fields'] = {'a': P}
        frame['invalidated_approval_issues'] = []
    assert evaluate(rows, changed) != first
    assert replay(case, 'B3', tmp_path / 'other.db') == rows
    assert first['stale_exposed_episodes'] == 1
    assert first['semantic_invalid_commit_opportunities'] == 1
    assert first['invalid_sink_effects'] == 1

def test_known_wrong_target_and_utility_diagnostics(tmp_path):
    case = next(c for c in CASES if c['id'] == 'N19')
    m = evaluate(replay(case, 'M', tmp_path / 'm.db'), GOLD['N19'])
    assert m['wrong_target_edits'] == 1
    assert not m['safe_completion']
    case = next(c for c in CASES if c['id'] == 'N02')
    m = evaluate(replay(case, 'M', tmp_path / 'n.db'), GOLD['N02'])
    assert m['safe_completion'] and m['sink_effects'] == 2
    assert m['unnecessary_blocked_boundaries'] == 0

@pytest.mark.parametrize('mode', ['B3', 'M'])
def test_generated_observable_sequences_preserve_invariants(mode, tmp_path):
    # Seeded regression exercise; not exhaustive model checking.
    w = setup(tmp_path, mode)
    rng = random.Random(3107)
    tokens = []
    for seq in range(3, 103):
        kind = rng.choice(['correction', 'proposal', 'approval', 'acknowledgment', 'commit', 'revocation'])
        if kind == 'correction':
            e = event(seq, kind, scopes=['a'], field='location', evidence='repair'); tokens.append(str(seq))
        elif kind == 'proposal':
            e = event(seq, kind, issue='a', values={'location': 'House ' + str(rng.randrange(1, 40))}, evidence='source')
        elif kind == 'approval':
            i = w.snapshot()['a']
            e = event(seq, kind, issue='a', version=i['version'], digest=digest(i['fields']), actor='reviewer')
        elif kind == 'commit': e = event(seq, kind, issue='a', operation='op-' + str(seq % 3))
        elif kind == 'revocation': e = event(seq, kind, issue='a', actor='reviewer')
        else: e = event(seq, kind, issue='a')
        w.apply(e)
        assert set(w.pending('a')) == set(tokens)
        assert not w.eligible('a') or not tokens
        assert len(w.effects()) <= 3
    w.close()


@pytest.mark.parametrize('mode', ['B3', 'M'])
def test_historical_receipt_replay_after_revocation_does_not_release_again(mode, tmp_path):
    w = setup(tmp_path, mode)
    commit = event(3, 'commit', issue='a', operation='original')
    receipt = w.apply(commit)
    w.apply(event(4, 'revocation', issue='a', actor='reviewer'))
    assert not w.eligible('a')
    assert w.apply(commit) == receipt  # Historical receipt, not a new execution.
    assert len(w.effects()) == 1
    w.close()
