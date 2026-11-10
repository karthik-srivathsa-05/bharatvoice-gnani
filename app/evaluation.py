import json
import re
from pathlib import Path
from .engine import Session,process, CATEGORY, LOCATION, TIME

FIXTURES=Path(__file__).resolve().parent.parent/'fixtures/scenarios.json'
def project(s):
    return [{k:getattr(i,k) for k in ('category','location','time_reference')} for i in s.issues]
def baseline(text):
    """Deliberately simple: one record, first category/location/time; no corrections."""
    cat=CATEGORY.search(text);loc=LOCATION.search(text);time=TIME.search(text)
    return [{'category':cat.lastgroup if cat else 'unknown','location':re.sub(r'^(near|at|in)\s+(the\s+)?','',loc.group(),flags=re.I).title() if loc else None,'time_reference':time.group().title() if time else None}]
def evaluate():
    rows=[]
    for f in json.loads(FIXTURES.read_text()):
        s=Session()
        for t in f['turns']:process(s,t,'synthetic_fixture')
        actual=project(s);base=baseline(' '.join(f['turns']))
        rows.append({'id':f['id'],'name':f['name'],'expected':f['expected'],'engine':actual,'baseline':base,'engine_pass':actual==f['expected'],'baseline_pass':base==f['expected']})
    return {'synthetic':True,'metric':'Exact match of ordered category/location/time records on five hand-authored synthetic scenarios. No STT measurement.', 'baseline_definition':'One record; first category, first location, first time; no corrections or session state.', 'engine_passed':sum(r['engine_pass'] for r in rows),'baseline_passed':sum(r['baseline_pass'] for r in rows),'total':len(rows),'scenarios':rows}
