"""Observable replay only: this module has no oracle dependency."""
import copy
from .model import Event, digest
from .policies import Workflow, InjectedCrash


def replay(case, mode, path):
    workflow = Workflow(path, mode)
    rows = []
    for raw in case['events']:
        wire = copy.deepcopy(raw)
        event = Event(**wire)
        fault = case['faults'].get(str(event.seq))
        if fault == 'restart':
            workflow.close(); workflow = Workflow(path, mode)
            fault = None
        try:
            result = workflow.apply(event, fault=fault)
        except InjectedCrash:
            workflow.close(); workflow = Workflow(path, mode)
            result = workflow.apply(event)
        snap = workflow.snapshot()
        # Runtime protocol checks use only observations/state, never evaluation gold.
        for ident, issue in snap.items():
            if issue['eligible']:
                assert not issue['pending'] and issue['fields']['category'] and issue['fields']['location']
                assert issue['approval']['digest'] == digest(issue['fields'])
                assert issue['approval']['version'] == issue['version']
        effects = workflow.effects()
        assert len({x['operation'] for x in effects}) == len(effects)
        if result['effect'] and event.kind == 'commit':
            assert snap[event.data['issue']]['eligible']
        rows.append({'seq': event.seq, 'event': wire, 'result': result,
                     'state': snap, 'effects': effects})
    workflow.close()
    assert case['events'] == [r['event'] for r in rows]
    return rows
