"""Bounded, offline lexicon/grammar extractor. Synthetic coverage is not language robustness."""
import re
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, validate_assignment=True)

class Revision(Strict):
    field: str
    before: str | None
    after: str | None
    evidence: str

class Issue(Strict):
    id: str = Field(default_factory=lambda: str(uuid4()))
    category: Literal['water','streetlight','drainage','garbage','unknown']
    original_text: str
    location: str | None = None
    time_reference: str | None = None
    revisions: list[Revision] = Field(default_factory=list)
    confirmed: bool = False
    version: int = 1
    blocked: bool = False
    @property
    def missing(self):
        return (['category'] if self.category == 'unknown' else []) + ([] if self.location else ['location']) + (['clarification'] if self.blocked else [])
    def view(self):
        return {**self.model_dump(), 'missing_fields': self.missing, 'status': 'incomplete' if self.missing else ('confirmed' if self.confirmed else 'draft')}

class Session(Strict):
    id: str = Field(default_factory=lambda: str(uuid4()))
    version: int = 0
    issues: list[Issue] = Field(default_factory=list)
    turns: list[dict] = Field(default_factory=list)
    prompts: list[str] = Field(default_factory=list)
    def view(self):
        return {**self.model_dump(), 'issues': [i.view() for i in self.issues]}

LEXICON = {'water': r'\bwater\b|ನೀರು|\bneeru\b', 'streetlight': r'\bstreet\s*light\b|ಬೀದಿ ದೀಪ|\bbeedi deepa\b', 'drainage': r'\bdrain(?:age)?\b|ಚರಂಡಿ|\bcharandi\b', 'garbage': r'\bgarbage\b|\bwaste\b|ಕಸ|\bkasa\b'}
CATEGORY = re.compile('|'.join(f'(?P<{k}>{v})' for k,v in LEXICON.items()), re.I)
LOCATION = re.compile(r'\bhouse\s+\d+\b|\b(?:main road|(?:first|second|third|\d+) cross)\b|\b(?:near|at|in)\s+(?:the\s+)?(?:school|building|apartment|[a-z]+\s+(?:road|cross|street))\b', re.I)
TIME = re.compile(r'\b(?:yesterday|today|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|(?:one|two|three|\d+) days?)\b', re.I)
CORRECTION = re.compile(r'\b(?:not|actually|sorry|alla|badalu)\b|ಅಲ್ಲ', re.I)

def values(text, pattern):
    """Order-preserving evidence spans; negated spans cannot become final values."""
    found = list(pattern.finditer(text))
    result = []
    for m in found:
        value = re.sub(r'^(?:near|at|in)\s+(?:the\s+)?', '', m.group(), flags=re.I).title()
        pre, post = text[max(0,m.start()-8):m.start()], text[m.end():m.end()+12]
        neg = bool(re.search(r'\bnot\s*$',pre,re.I) or re.match(r'\s*(?:alla|ಅಲ್ಲ)\b',post,re.I))
        result.append((value,neg))
    return result

def apply_fields(issue, text):
    changed = False
    for field, pattern in [('location', LOCATION), ('time_reference', TIME)]:
        hits = values(text, pattern)
        current = getattr(issue, field)
        positives=[v for v,neg in hits if not neg]
        if len(set(positives))>1 and not CORRECTION.search(text):
            issue.blocked=True;issue.confirmed=False
        # Negation of a previously accepted value explicitly removes it.
        for value, neg in hits:
            if neg:
                if current != value:
                    issue.revisions.append(Revision(field=field,before=value,after=None,evidence=text))
                if current == value:
                    issue.revisions.append(Revision(field=field,before=current,after=None,evidence=text)); current=None; changed=True
                continue
            if current != value:
                issue.revisions.append(Revision(field=field,before=current,after=value,evidence=text)); current=value; changed=True
        if field == 'location' and re.search(r'the location is\s*(?:\.{3}|…)?\s*$',text,re.I):
            if current is not None:
                issue.revisions.append(Revision(field=field,before=current,after=None,evidence=text))
            current = None; changed=True
        setattr(issue,field,current)
    if CORRECTION.search(text) and not changed and re.search(r'\b(?:actually|sorry|alla|badalu)\b|ಅಲ್ಲ',text,re.I):
        issue.blocked=True;issue.confirmed=False;issue.version+=1
    if changed:
        issue.confirmed=False
        issue.version+=1
    return changed

def process(session: Session, text: str, source='typed', target_id=None):
    session.prompts=[]
    session.turns.append({'text':text,'source':source})
    mentions=list(CATEGORY.finditer(text))
    selected=next((i for i in session.issues if i.id==target_id),None)
    if selected and any(m.lastgroup!=selected.category for m in mentions):
        selected.blocked=True;selected.confirmed=False;selected.version+=1
        session.prompts.append('Selected issue conflicts with the service named in this turn. Review the target and clarify.')
        session.version+=1
        return session
    # Split on issue mentions, retaining any initial location-only preamble on the first issue.
    if mentions:
        for n,m in enumerate(mentions):
            start=0 if n==0 else m.start()
            end=mentions[n+1].start() if n+1<len(mentions) else len(text)
            fragment=text[start:end]
            category=m.lastgroup
            existing=[i for i in session.issues if i.category==category]
            is_reference=bool(CORRECTION.search(fragment) or re.search(r'\b(?:started|location|that|previous)\b',fragment,re.I))
            target=next((i for i in existing if i.id==target_id),None)
            if not target and is_reference and len(existing)==1:
                target=existing[0]
            if not target and is_reference and len(existing)>1:
                session.prompts.append('Multiple issues match. Select the issue to correct.')
                for i in existing: i.blocked=True;i.confirmed=False;i.version+=1
                continue
            if target is None:
                target=Issue(category=category,original_text=fragment.strip());session.issues.append(target)
            apply_fields(target,fragment)
    else:
        target=next((i for i in session.issues if i.id==target_id),None)
        if target is None and len(session.issues)==1: target=session.issues[0]
        if target is None and not session.issues and LOCATION.search(text):
            target=Issue(category='unknown',original_text=text);session.issues.append(target)
        if target: apply_fields(target,text)
        else:
            session.prompts.append('Please name the service and location, or select an issue to clarify.')
            if CORRECTION.search(text):
                for i in session.issues: i.blocked=True;i.confirmed=False;i.version+=1
    # A contradiction is unresolved rather than silently interpreted as consent.
    if re.search(r'\bconfirm\b',text,re.I) and re.search(r"\b(?:not|don.t|cancel)\b",text,re.I):
        for i in session.issues:
            i.confirmed=False;i.blocked=True;i.version+=1
        session.prompts.append('Contradictory instructions. Review and explicitly clarify each affected issue.')
    for i in session.issues:
        if i.missing: session.prompts.append(f'{i.category.title()} ({i.id[:8]}): please provide '+', '.join(i.missing)+'.')
    session.version+=1
    return session
