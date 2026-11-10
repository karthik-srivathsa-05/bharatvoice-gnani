"""Run frozen fixtures; write machine-readable outcomes and human review report."""
import json
from pathlib import Path
import tempfile
from .evaluate import evaluate
from .model import digest
from .replay import replay

ROOT = Path(__file__).resolve().parents[1]


def run(output=None):
    cases = json.loads((ROOT / 'data/streams.json').read_text())
    gold = json.loads((ROOT / 'data/oracle.json').read_text())
    results = []
    with tempfile.TemporaryDirectory() as td:
        for case in cases:
            item = {'case': case['id'], 'description': case['description'],
                    'input_sha256': digest(case), 'policies': {}}
            for mode in ('B3', 'M'):
                rows = replay(case, mode, Path(td) / (case['id'] + '-' + mode + '.db'))
                item['policies'][mode] = {'metrics': evaluate(rows, gold[case['id']]), 'trace': rows}
            item['behavior_identical'] = item['policies']['B3'] == item['policies']['M']
            results.append(item)
    if output:
        output.mkdir(parents=True, exist_ok=True)
        (output / 'per_case.json').write_text(json.dumps(results, indent=2) + '\n')
        manifest = {'base': '89c042b672ef6b88845bf7b465c633dbeac7c42b',
                    'streams_sha256': digest(cases), 'oracle_sha256': digest(gold),
                    'scenarios': len(cases), 'identical': sum(r['behavior_identical'] for r in results)}
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return results

if __name__ == '__main__':
    results = run(ROOT / 'results')
    print(json.dumps({'cases': len(results), 'identical': sum(r['behavior_identical'] for r in results)}, indent=2))
