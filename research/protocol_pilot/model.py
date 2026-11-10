"""Observable schema only. No oracle imports or language inference."""
from dataclasses import dataclass, asdict
import hashlib
import json
import re

FIELDS = {'category', 'location', 'time_reference'}
KINDS = {'proposal', 'correction', 'dispute', 'approval', 'revocation',
         'clarification', 'commit', 'acknowledgment', 'source'}
KEYS = {
    'proposal': {'issue', 'values', 'evidence'},
    'correction': {'scopes', 'field', 'evidence'},
    'dispute': {'scopes', 'field', 'evidence'},
    'approval': {'issue', 'version', 'digest', 'actor'},
    'revocation': {'issue', 'actor'},
    'clarification': {'issue', 'resolves', 'values', 'evidence'},
    'commit': {'issue', 'operation'},
    'acknowledgment': {'issue'},
    'source': {'text'},
}

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

@dataclass(frozen=True)
class Event:
    id: str
    seq: int
    kind: str
    data: dict

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id or type(self.seq) is not int or self.seq < 1:
            raise ValueError('invalid event identity/order')
        if self.kind not in KINDS or not isinstance(self.data, dict) or set(self.data) != KEYS[self.kind]:
            raise ValueError('invalid event kind/keys')
        d = self.data
        for key in ('issue', 'evidence', 'actor', 'operation', 'digest', 'text'):
            if key in d and (not isinstance(d[key], str) or not d[key]):
                raise ValueError('invalid string: ' + key)
        if 'version' in d and (type(d['version']) is not int or d['version'] < 0):
            raise ValueError('invalid approval version')
        if 'digest' in d and not re.fullmatch('[0-9a-f]{64}', d['digest']):
            raise ValueError('invalid digest')
        if 'field' in d and d['field'] not in FIELDS:
            raise ValueError('invalid scope field')
        for key in ('scopes', 'resolves'):
            if key in d and (not isinstance(d[key], list) or not d[key]
                             or any(not isinstance(x, str) or not x for x in d[key])
                             or len(set(d[key])) != len(d[key])):
                raise ValueError('invalid scope/resolution list')
        if 'values' in d and (not isinstance(d['values'], dict) or not d['values']
                              or not set(d['values']) <= FIELDS
                              or any(v is not None and not isinstance(v, str) for v in d['values'].values())):
            raise ValueError('invalid fields')

    def wire(self):
        return asdict(self)


def valid(field, value):
    if value is None:
        return True
    if field == 'category':
        return value in {'water', 'drainage', 'streetlight', 'garbage'}
    if field == 'location':
        return bool(re.fullmatch(r'House (0|[1-9][0-9]{0,2})', value))
    return bool(value.strip()) and len(value) <= 100
