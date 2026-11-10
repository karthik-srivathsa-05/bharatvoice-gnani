"""Hand-authored exploratory fixtures. Builder writes streams and oracle separately.

This is not an extractor. Gold annotations are author judgments, not independent
labels. Policies never import this module or the oracle file.
"""
import json
from pathlib import Path
from .model import digest

ROOT = Path(__file__).resolve().parents[1]

def payload(location, category='water', time=None):
    return {'category': category, 'location': location, 'time_reference': time}

class Case:
    def __init__(self, name, description):
        self.name, self.description = name, description
        self.events, self.frames, self.faults = [], [], {}
        self.gold, self.allowed, self.unresolved = {}, set(), set()
        self.invalidated = set()

    def add(self, kind, data, *, gold=None, allowed=None, unresolved=None, invalidated=None, fault=None, targets=None):
        # Author-supplied gold persists until explicitly changed; never read by a policy.
        if gold is not None: self.gold = gold
        if allowed is not None: self.allowed = set(allowed)
        if unresolved is not None: self.unresolved = set(unresolved)
        if invalidated is not None: self.invalidated = set(invalidated)
        seq = len(self.events) + 1
        ident = f'{self.name}:{seq}'
        self.events.append({'id': ident, 'seq': seq, 'kind': kind, 'data': data})
        self.frames.append({'seq': seq, 'fields': dict(self.gold), 'can_commit': sorted(self.allowed),
                            'requires_clarification': sorted(self.unresolved),
                            'invalidated_approval_issues': sorted(self.invalidated),
                            'permitted_edit_targets': targets if targets is not None else
                                ([data['issue'] + '.' + f for f in data['values']]
                                 if kind in {'proposal', 'clarification'} else [])})
        if fault: self.faults[str(seq)] = fault
        return ident

    def propose(self, issue, value, **gold):
        return self.add('proposal', {'issue': issue, 'values': value, 'evidence': 'scripted-source'}, **gold)

    def approve(self, issue, version, value, **gold):
        return self.add('approval', {'issue': issue, 'version': version, 'digest': digest(value), 'actor': 'reviewer'}, **gold)

    def repair(self, issue='a', field='location', scopes=None, **gold):
        return self.add('correction', {'scopes': scopes or [issue], 'field': field, 'evidence': 'scripted-repair'}, **gold)

    def clarify(self, issue, refs, value, **gold):
        return self.add('clarification', {'issue': issue, 'resolves': refs, 'values': value,
                                          'evidence': 'explicit-scripted-resolution'}, **gold)

    def commit(self, issue='a', op=None, **gold):
        return self.add('commit', {'issue': issue, 'operation': op or self.name + '-' + issue}, **gold)

    def source(self, text, **gold):
        return self.add('source', {'text': text}, **gold)

    def ack(self, issue='a', **gold):
        return self.add('acknowledgment', {'issue': issue}, **gold)


def build():
    cases = []
    def new(name, description):
        c = Case(name, description); cases.append(c); return c
    p42, p24, p20 = payload('House 42'), payload('House 24'), payload('House 20')
    def initial(c, p=p42):
        c.propose('a', p, gold={'a': p})
        c.approve('a', 1, p, allowed=['a'])

    c = new('F1', 'Bare rejection missed by observation producer (original extractor boundary)')
    initial(c)
    c.source('not forty-two', gold={'a': payload(None)}, allowed=[], unresolved=['a'], invalidated=['a'])
    c.commit()

    c = new('F2', 'Recognized ambiguity, generic acknowledgment and attempted reapproval')
    c.propose('a', p42, gold={'a': p42})
    token = c.repair(gold={'a': payload(None)}, unresolved=['a'])
    c.ack(); c.approve('a', 1, p42); c.commit()

    c = new('F3', 'Wrong address proposal after a time correction; no dispute signal')
    c.source('Water at house 10. Monday, sorry Tuesday, house 20.', unresolved=['a'])
    wrong = payload('House 20', time='Tuesday')
    c.propose('a', wrong, gold={'a': payload(None, time='Tuesday')}, targets=['a.category', 'a.time_reference'])
    c.approve('a', 1, wrong); c.commit()

    for name, text, wrong, intended in [
        ('F4', 'Water at house 24/7', p24, payload('House 24/7')),
        ('F5', 'Water at house twenty zero', p20, payload(None))]:
        c = new(name, 'Semantically lossy but syntactically valid proposal')
        c.source(text, unresolved=['a'])
        c.propose('a', wrong, gold={'a': intended})
        c.approve('a', 1, wrong); c.commit()

    c = new('F6', 'Shared-address scope unresolved; only second issue receives address')
    c.source('Water and drainage at house 24', unresolved=['a', 'b'])
    c.propose('a', payload(None), gold={'a': payload(None), 'b': payload(None, 'drainage')})
    c.propose('b', payload('House 24', 'drainage'))
    c.approve('a', 1, payload(None)); c.approve('b', 1, payload('House 24', 'drainage'))
    c.commit('a'); c.commit('b')

    c = new('F7', 'Unmarked new-versus-correction ambiguity with an approved old issue')
    initial(c, p24)
    c.source('Water at house 26', allowed=[], unresolved=['a', 'b'], invalidated=['a'])
    c.propose('b', payload('House 26'), gold={'a': p24, 'b': payload('House 26')})
    c.commit('a')

    c = new('F8', 'Repair signal persists through unrelated time edit')
    initial(c)
    c.source('Actually house ippatnaalku on Monday', gold={'a': payload(None, time='Monday')},
             allowed=[], unresolved=['a'], invalidated=['a'])
    token = c.repair()
    c.propose('a', {'time_reference': 'Monday'})
    c.ack(); c.approve('a', 2, payload('House 42', time='Monday')); c.commit()

    c = new('F9', 'Negated category produces phantom incomplete issue')
    c.source('There is no water problem. Garbage at house 24.')
    garbage = payload('House 24', 'garbage')
    c.propose('a', payload(None), gold={'b': garbage}, targets=[])
    c.propose('b', garbage); c.approve('b', 1, garbage, allowed=['b']); c.commit('b')

    c = new('N01', 'No correction, one legitimate approved commit')
    initial(c, p24); c.commit()
    c = new('N02', 'Explicitly new second complaint of same service')
    initial(c, p24)
    c.source('Another separate water complaint at house 26')
    p26 = payload('House 26')
    c.propose('b', p26, gold={'a': p24, 'b': p26}); c.approve('b', 1, p26, allowed=['a', 'b'])
    c.commit('a'); c.commit('b')
    c = new('N03', 'Recognized change revokes approval; legitimate reapproval')
    initial(c)
    c.propose('a', p24, gold={'a': p24}, allowed=[], invalidated=['a'])
    c.commit(); c.approve('a', 2, p24, allowed=['a'], invalidated=[]); c.commit()
    c = new('N04', 'Explicitly resolved ambiguity permits fresh approval')
    initial(c)
    token = c.repair(gold={'a': payload(None)}, allowed=[], unresolved=['a'], invalidated=['a'])
    c.clarify('a', [token], {'location': 'House 24'}, gold={'a': p24}, unresolved=[])
    c.approve('a', 2, p24, allowed=['a'], invalidated=[]); c.commit()
    c = new('N05', 'Acknowledgment and unrelated edits must not erase repair')
    initial(c)
    token = c.repair(gold={'a': payload(None)}, allowed=[], unresolved=['a'], invalidated=['a'])
    c.ack(); c.propose('a', {'time_reference': 'Monday'}, gold={'a': payload(None, time='Monday')})
    c.approve('a', 2, payload('House 42', time='Monday')); c.commit()
    c = new('N06', 'Scoped correction does not invalidate another issue')
    initial(c)
    b = payload('House 30', 'drainage')
    c.propose('b', b, gold={'a': p42, 'b': b}); c.approve('b', 1, b, allowed=['a', 'b'])
    c.repair(scopes=['a'], gold={'a': payload(None), 'b': b}, allowed=['b'], unresolved=['a'], invalidated=['a'])
    c.commit('b'); c.commit('a')
    c = new('N07', 'Restart before commit preserves valid approval')
    initial(c, p24); c.commit(fault='restart')
    c = new('N08', 'Crash after sink transaction before response and same-ID retry')
    initial(c, p24); c.commit(fault='after_commit')
    c = new('N09', 'Different event IDs, same operation ID deduplicate effect')
    initial(c, p24); c.commit(); c.commit()
    c = new('N10', 'Revoked approval cannot commit')
    initial(c, p24)
    c.add('revocation', {'issue': 'a', 'actor': 'reviewer'}, allowed=[], invalidated=['a']); c.commit()
    c = new('N11', 'Stale digest/version approval after changed address')
    initial(c)
    c.propose('a', p24, gold={'a': p24}, allowed=[], invalidated=['a'])
    c.approve('a', 1, p42); c.commit()
    c = new('N12', 'Two concurrent field repairs require two explicit resolutions')
    initial(c)
    a = c.repair(gold={'a': payload(None)}, allowed=[], unresolved=['a'], invalidated=['a'])
    b = c.repair(field='time_reference')
    c.clarify('a', [a], {'location': 'House 24'}, gold={'a': p24})
    c.approve('a', 2, p24); c.commit()
    c.clarify('a', [b], {'time_reference': 'Monday'}, gold={'a': payload('House 24', time='Monday')}, unresolved=[])
    c.approve('a', 3, payload('House 24', time='Monday'), allowed=['a'], invalidated=[]); c.commit()
    c = new('N13', 'Same-field overlapping repairs: resolving one leaves another')
    initial(c)
    a = c.repair(gold={'a': payload(None)}, allowed=[], unresolved=['a'], invalidated=['a'])
    b = c.repair()
    c.clarify('a', [a], {'location': 'House 24'}, gold={'a': p24})
    c.approve('a', 2, p24); c.commit()
    c.clarify('a', [b], {'location': 'House 24'}, unresolved=[])
    c.approve('a', 2, p24, allowed=['a'], invalidated=[]); c.commit()
    c = new('N14', 'Unsupported raw identifier rejected by validation')
    c.propose('a', payload('House 24/7'), gold={'a': payload('House 24/7')}, unresolved=['a'])
    c.approve('a', 0, payload(None)); c.commit()
    c = new('N15', 'Recognized F1 rejection blocks both policies')
    initial(c)
    c.repair(gold={'a': payload(None)}, allowed=[], unresolved=['a'], invalidated=['a']); c.commit()
    c = new('N16', 'Crash before durable transaction, restart and retry')
    initial(c, p24); c.commit(fault='before_commit')
    c = new('N17', 'Ambiguous candidate scope resolved to one of two issues')
    initial(c)
    b = payload('House 30')
    c.propose('b', b, gold={'a': p42, 'b': b}); c.approve('b', 1, b, allowed=['a', 'b'])
    t = c.repair(scopes=['a', 'b'], allowed=[], unresolved=['a', 'b'], invalidated=['a', 'b'])
    c.clarify('a', [t], {'location': 'House 24'}, gold={'a': p24, 'b': b}, unresolved=[])
    # Both invalidated approvals require renewal, including unchanged b.
    c.approve('a', 2, p24, allowed=['a'], invalidated=['b'])
    c.approve('b', 1, b, allowed=['a', 'b'], invalidated=[]); c.commit('a'); c.commit('b')
    c = new('N18', 'Explicit dispute and missing location remain blocked')
    c.propose('a', payload(None), gold={'a': payload(None)}, unresolved=['a'])
    c.add('dispute', {'scopes': ['a'], 'field': 'location', 'evidence': 'ambiguous-input'})
    c.ack(); c.approve('a', 1, payload(None)); c.commit()
    c = new('N19', 'Incorrect proposal target undetectable from declared scope alone')
    initial(c)
    b = payload('House 30', 'drainage')
    c.propose('b', b, gold={'a': p42, 'b': b}); c.approve('b', 1, b, allowed=['a', 'b'])
    c.source('Correct water to house 24', gold={'a': p24, 'b': b}, allowed=[], unresolved=['a'], invalidated=['a'])
    c.propose('b', {'location': 'House 24'}, targets=['a.location'])
    c.commit('a')

    streams = [{'id': c.name, 'description': c.description,
                'events': c.events, 'faults': c.faults} for c in cases]
    oracle = {c.name: {'frames': c.frames, 'expected_effects': sorted(c.allowed),
                       'final_fields': c.gold, 'clarification_required': sorted(c.unresolved)}
              for c in cases}
    # Independent, hand-labelled expected OBSERVABLE eligibility intervals.
    # These deliberately differ from semantic gold when a repair is missed.
    intervals = {
        'F1': [(2, 4, ['a'])], 'F2': [], 'F3': [(3, 4, ['a'])],
        'F4': [(3, 4, ['a'])], 'F5': [(3, 4, ['a'])],
        'F6': [(5, 7, ['b'])], 'F7': [(2, 5, ['a'])],
        'F8': [(2, 3, ['a'])], 'F9': [(4, 5, ['b'])],
        'N01': [(2, 3, ['a'])],
        'N02': [(2, 4, ['a']), (5, 7, ['a', 'b'])],
        'N03': [(2, 2, ['a']), (5, 6, ['a'])],
        'N04': [(2, 2, ['a']), (5, 6, ['a'])],
        'N05': [(2, 2, ['a'])],
        'N06': [(2, 3, ['a']), (4, 4, ['a', 'b']), (5, 7, ['b'])],
        'N07': [(2, 3, ['a'])], 'N08': [(2, 3, ['a'])],
        'N09': [(2, 4, ['a'])], 'N10': [(2, 2, ['a'])],
        'N11': [(2, 2, ['a'])],
        'N12': [(2, 2, ['a']), (9, 10, ['a'])],
        'N13': [(2, 2, ['a']), (9, 10, ['a'])], 'N14': [],
        'N15': [(2, 2, ['a'])], 'N16': [(2, 3, ['a'])],
        'N17': [(2, 3, ['a']), (4, 4, ['a', 'b']), (7, 7, ['a']), (8, 10, ['a', 'b'])],
        'N18': [], 'N19': [(2, 3, ['a']), (4, 5, ['a', 'b']), (6, 7, ['a'])],
    }
    for case_id, spec in oracle.items():
        for frame in spec['frames']:
            frame['protocol_can_commit'] = sorted({i for lo, hi, ids in intervals[case_id]
                                                  if lo <= frame['seq'] <= hi for i in ids})
    (ROOT / 'data' / 'streams.json').write_text(json.dumps(streams, indent=2) + '\n')
    (ROOT / 'data' / 'oracle.json').write_text(json.dumps(oracle, indent=2) + '\n')
    return streams, oracle

if __name__ == '__main__':
    build()
