"""Two equal-information policies, different durable obligation representations.

B3 is deliberately competent: ordinary per-field pending repair tickets are
persistent too. No policy receives gold. Shared mechanics isolate representation.
"""
import copy
import json
import sqlite3
from .model import Event, canonical, digest, valid

class InjectedCrash(RuntimeError):
    pass

class Workflow:
    def __init__(self, path, mode):
        if mode not in {'B3', 'M'}:
            raise ValueError(mode)
        self.mode = mode
        self.db = sqlite3.connect(path)
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, payload TEXT);
            CREATE TABLE IF NOT EXISTS journal (id TEXT PRIMARY KEY, seq INTEGER UNIQUE, wire TEXT, result TEXT);
            CREATE TABLE IF NOT EXISTS sink (operation TEXT PRIMARY KEY, issue TEXT, version INTEGER, digest TEXT, payload TEXT);
        ''')
        self.db.commit()
        row = self.db.execute('SELECT payload FROM state WHERE id=1').fetchone()
        if row:
            self.s = json.loads(row[0])
            if self.s['mode'] != mode:
                raise ValueError('policy/database mismatch')
        else:
            self.s = {'mode': mode, 'last': 0, 'issues': {}, 'ledger': {}}
            self.db.execute('INSERT INTO state VALUES(1,?)', (canonical(self.s),))
            self.db.commit()

    def close(self):
        self.db.close()

    def issue(self, ident):
        return self.s['issues'].setdefault(ident, {
            'fields': {'category': None, 'location': None, 'time_reference': None},
            'version': 0, 'approval': None, 'pending': {}, 'changes': []})

    def open(self, event_id, scopes, field, evidence):
        for ident in scopes:
            i = self.issue(ident)
            i['approval'] = None
            if self.mode == 'B3':
                i['pending'].setdefault(field, {})[event_id] = evidence
        if self.mode == 'M':
            self.s['ledger'][event_id] = {'scopes': scopes, 'field': field,
                                         'evidence': evidence, 'resolved': False,
                                         'resolution': None}

    def pending(self, ident):
        if self.mode == 'B3':
            return {token: field for field, tokens in self.issue(ident)['pending'].items()
                    for token in tokens}
        return {token: item['field'] for token, item in self.s['ledger'].items()
                if ident in item['scopes'] and not item['resolved']}

    def resolve(self, ident, tokens, values, evidence):
        pending = self.pending(ident)
        if any(t not in pending or pending[t] not in values for t in tokens):
            return False
        # Scope selection must release all candidate issue holds atomically.
        if self.mode == 'B3':
            for issue in self.s['issues'].values():
                for token in tokens:
                    for entries in issue['pending'].values():
                        entries.pop(token, None)
        else:
            for token in tokens:
                self.s['ledger'][token]['resolved'] = True
                self.s['ledger'][token]['resolution'] = {'issue': ident, 'evidence': evidence}
        return True

    def eligible(self, ident):
        if ident not in self.s['issues']:
            return False
        i = self.s['issues'][ident]
        a = i['approval']
        return bool(i['fields']['category'] and i['fields']['location']
                    and not self.pending(ident) and a
                    and a['version'] == i['version'] and a['digest'] == digest(i['fields']))

    def update(self, ident, values, event):
        i = self.issue(ident)
        edits = {f: v for f, v in values.items() if i['fields'][f] != v}
        if edits:
            i['version'] += 1
            i['approval'] = None
            for f, value in edits.items():
                i['changes'].append({'event': event.id, 'field': f,
                                     'before': i['fields'][f], 'after': value,
                                     'evidence': event.data['evidence']})
                i['fields'][f] = value

    def snapshot(self):
        return {ident: {'fields': copy.deepcopy(i['fields']), 'version': i['version'],
                        'approval': copy.deepcopy(i['approval']),
                        'pending': self.pending(ident), 'eligible': self.eligible(ident),
                        'changes': copy.deepcopy(i['changes'])}
                for ident, i in self.s['issues'].items()}

    def effects(self):
        return [{'operation': op, 'issue': issue, 'version': version,
                 'digest': dg, 'payload': json.loads(payload)} for op, issue, version, dg, payload
                in self.db.execute('SELECT * FROM sink ORDER BY operation')]

    def apply(self, event, fault=None):
        # Revalidate even if the caller mutated a dataclass's nested dict.
        event = Event(**event.wire())
        wire = canonical(event.wire())
        old = self.db.execute('SELECT wire,result FROM journal WHERE id=?', (event.id,)).fetchone()
        if old:
            if old[0] != wire:
                raise ValueError('event ID reused with changed content')
            return json.loads(old[1])
        if event.seq != self.s['last'] + 1:
            raise ValueError('out-of-order event')
        before = copy.deepcopy(self.s)
        result = {'accepted': True, 'reason': 'recorded', 'effect': False}
        d = event.data
        try:
            self.db.execute('BEGIN IMMEDIATE')
            if event.kind in {'correction', 'dispute'}:
                self.open(event.id, d['scopes'], d['field'], d['evidence'])
            elif event.kind in {'proposal', 'clarification'}:
                ident = d['issue']
                self.issue(ident)
                bad = [f for f, v in d['values'].items() if not valid(f, v)]
                if bad:
                    for f in bad:
                        self.open(event.id + ':' + f, [ident], f, d['evidence'])
                    result.update(accepted=False, reason='invalid fields')
                elif event.kind == 'clarification' and not self.resolve(
                        ident, d['resolves'], d['values'], d['evidence']):
                    result.update(accepted=False, reason='missing/mismatched resolution')
                else:
                    self.update(ident, d['values'], event)
            elif event.kind == 'approval':
                i = self.issue(d['issue'])
                if (d['actor'] != 'reviewer' or self.pending(d['issue'])
                        or not i['fields']['category'] or not i['fields']['location']
                        or d['version'] != i['version'] or d['digest'] != digest(i['fields'])):
                    result.update(accepted=False, reason='approval rejected')
                else:
                    i['approval'] = {'actor': d['actor'], 'version': d['version'], 'digest': d['digest']}
            elif event.kind == 'revocation':
                if d['actor'] != 'reviewer':
                    result.update(accepted=False, reason='untrusted actor')
                else:
                    self.issue(d['issue'])['approval'] = None
            elif event.kind == 'commit':
                i = self.s['issues'].get(d['issue'])
                existing = self.db.execute('SELECT issue,version,digest FROM sink WHERE operation=?',
                                           (d['operation'],)).fetchone()
                if existing:
                    if not i or existing != (d['issue'], i['version'], digest(i['fields'])):
                        result.update(accepted=False, reason='operation payload mismatch')
                    else:
                        result['reason'] = 'deduplicated receipt'
                elif not self.eligible(d['issue']):
                    result.update(accepted=False, reason='ineligible')
                else:
                    self.db.execute('INSERT INTO sink VALUES(?,?,?,?,?)',
                                    (d['operation'], d['issue'], i['version'], digest(i['fields']), canonical(i['fields'])))
                    result.update(effect=True, reason='simulated commit')
            # source and acknowledgment never assert language understanding or resolve holds.
            self.s['last'] = event.seq
            self.db.execute('UPDATE state SET payload=? WHERE id=1', (canonical(self.s),))
            self.db.execute('INSERT INTO journal VALUES(?,?,?,?)',
                            (event.id, event.seq, wire, canonical(result)))
            if fault == 'before_commit':
                raise InjectedCrash('before durable transaction commit')
            self.db.commit()
        except Exception:
            self.db.rollback()
            self.s = before
            raise
        if fault == 'after_commit':
            raise InjectedCrash('after durable commit before response')
        return result
