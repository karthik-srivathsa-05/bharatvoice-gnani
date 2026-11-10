# Executable audit counterexample specification: F1–F9

**11 November 2026 (IST).** Target: application at `7f786412523a232c9c39654c9184d4c7fda65290`, unchanged on `research/review-drafts`. These specifications reproduce existing behavior, not an implemented monitor. Proposed-policy outcomes below are normative hypotheses for review; the current app is not expected to satisfy them. This is documentation, not a new pytest module.

## Routes, execution contract and interpretation

Each case starts with a fresh temporary database and `POST /api/sessions` (201). A turn is `POST /api/sessions/{sid}/turns` with JSON `{"version": current_session_version, "text": exact_text}`. Review is `POST /api/sessions/{sid}/issues/{iid}/review` with JSON `{"version": current_session_version, "action": "confirm|clarify|revoke"}`. Refresh uses `GET /api/sessions/{sid}`. Every mutation uses the preceding returned version, never a guessed version. Issue IDs are copied from returned state. No upstream STT, audio, credentials, real actions, direct state mutation or database edits are required.

The executable block below uses these exact API routes in-process with `TestClient`, asserts observed current outcomes, and prints results. It intentionally does **not** implement or assert proposed-policy behavior. Run only in a scratch environment with existing requirements installed; extracting the code to `work/research/reproduce_spec.py` and using the existing venv is sufficient. Importing `app.main` creates its normal default app/database; the script sets `BHARATVOICE_DB` to a temporary path before import, and all case clients use separate temporary paths. It changes no tracked files.

`disputed`, approval tokens and action eligibility are proposed concepts. The app currently exposes `blocked`, `confirmed`, `missing_fields`, and derived status; do not treat those as identical semantics. There is **no commit API route**. Any claim about future commit denial is a specification, not observed action execution.

## Case records

### F1 — ignored bare rejection preserves approval

- **Setup:** create water at House 42, then explicitly confirm its returned issue through the review route.
- **Input:** `not forty-two` via turns route.
- **Observed:** House 42; confirmed true; blocked false; status confirmed. This is semantic stale-approval exposure, not a proven invalid external commit.
- **Proposed policy:** if an observable repair signal links this rejection to the sole water issue/address, mark location disputed/rejected, invalidate old approval before any action eligibility check, and ask for a replacement; never invent House 24. If extractor emits no repair signal, the monitor cannot guarantee detection. Gold evaluation still counts exposure.

### F2 — acknowledgment releases unresolved conflict

- **Setup:** water at House 42. No initial confirmation is needed.
- **Inputs:** `Water actually at house 10 or house 20`; review `clarify`; review `confirm` on the same issue.
- **Observed:** ambiguity retains House 42 and blocks; clarify clears block; confirm returns 200 and confirms House 42.
- **Proposed policy:** a generic acknowledgment cannot resolve the address obligation. Retain House 42 as historical only, candidates House 10/20 as disputed; old approval invalid. Require explicit selection/rejection of alternatives and a fresh current-payload approval. Confirmation should be refused until then (future error code not specified).

### F3 — time correction licenses an address change

- **Setup:** fresh session.
- **Input:** `Water at house 10. Monday, sorry Tuesday, house 20.`
- **Observed:** water, House 20, Tuesday, unblocked and awaiting confirmation.
- **Proposed policy:** time may resolve to Tuesday; address scope is ambiguous between House 10/20. Preserve both candidates/evidence, dispute location and ask for clarification. No approval/action eligibility. This is a conservative policy choice requiring annotation agreement, not a claim to know a hidden intended address.

### F4 — partial address accepted

- **Setup:** fresh session.
- **Input:** `Water at house 24/7`.
- **Observed:** House 24, unblocked and awaiting confirmation.
- **Proposed policy:** preserve raw `24/7`; do not normalize to House 24. Either validate the complete identifier under an explicit supported grammar or leave location unresolved and clarify. Neither a monitor nor annotator should infer whether the slash denotes a unit, range or something else.

### F5 — invalid spoken-number composition

- **Setup:** fresh session.
- **Input:** `Water at house twenty zero`.
- **Observed:** House 20, unblocked and awaiting confirmation.
- **Proposed policy:** flag unsupported number composition; location unresolved with original evidence; no silent collapse to 20, no approval/action eligibility. Ask which written identifier is intended.

### F6 — shared argument scope

- **Setup:** fresh session.
- **Input:** `Water and drainage at house 24`.
- **Observed:** two issues: water location missing; drainage House 24. Both unconfirmed.
- **Proposed policy:** retain two issue candidates; explicitly represent possible shared-address scope. Ask whether House 24 applies to both before resolving that linkage. Existing water incompleteness is conservative, not an unsafe action by itself. Measure burden/omission separately from stale consent. No initial approval exists to invalidate.

### F7 — ambiguous new issue versus update

- **Setup:** `Water at house 24`; explicitly confirm its issue.
- **Input:** `Water at house 26` without a target ID.
- **Observed:** two water issues; original House 24 remains confirmed; new House 26 awaits confirmation.
- **Proposed policy:** ask whether this is another complaint or a correction. Retain the first issue as history; temporarily suspend its action eligibility while identity is unresolved; keep House 26 as a candidate rather than silently overwriting/duplicating. This deliberately conservative suspension may be unnecessary if it really is a new complaint—measure that cost. No assertion that two issues is universally wrong.

### F8 — partial comprehension masks unresolved repair

- **Setup:** water at House 42; explicitly confirm it.
- **Input:** `Actually house ippatnaalku on Monday`.
- **Observed:** House 42 retained, Monday set, confirmed false, blocked false, awaiting confirmation.
- **Proposed policy:** accept independently supported Monday if policy permits, but retain an unresolved location-repair obligation and invalidate approval. No fresh approval until the address is clarified. Do not assert a numeric interpretation or linguistic validity for this unvalidated romanized string. A missed repair signal remains an extraction failure beyond monitor-only guarantees.

### F9 — negated problem mention becomes an issue

- **Setup:** fresh session.
- **Input:** `There is no water problem. Garbage at house 24.`
- **Observed:** extra incomplete water issue and a garbage issue at House 24; neither confirmed.
- **Proposed policy:** in this specified scenario, only garbage is an asserted complaint. Keep the water negation as evidence, not an active ticket; ask rather than create an actionable water issue if the parser is uncertain. This is semantic extraction/scope, not primarily protocol invalidation.

## Runnable current-behavior specification

```python
import json
import os
import tempfile
from pathlib import Path

# Run from repository root; dependencies are those already used by the app.
with tempfile.TemporaryDirectory() as temp:
    os.environ['BHARATVOICE_DB'] = str(Path(temp) / 'default-import.db')
    from fastapi.testclient import TestClient
    from app.main import create_app

    def state(rows):
        return [(i['category'], i['location'], i['time_reference'],
                 i['confirmed'], i['blocked']) for i in rows]

    def run(name, steps, expected):
        with TestClient(create_app(str(Path(temp) / (name + '.db')))) as c:
            r = c.post('/api/sessions')
            assert r.status_code == 201
            s = r.json()
            checkpoints = []
            for kind, value in steps:
                if kind == 'turn':
                    r = c.post(f"/api/sessions/{s['id']}/turns",
                               json={'version': s['version'], 'text': value})
                else:
                    iid = s['issues'][0]['id']
                    r = c.post(f"/api/sessions/{s['id']}/issues/{iid}/review",
                               json={'version': s['version'], 'action': value})
                assert r.status_code == 200, (name, r.status_code, r.text)
                s = r.json()
                checkpoints.append(state(s['issues']))
            assert state(s['issues']) == expected, (name, state(s['issues']))
            resumed = c.get(f"/api/sessions/{s['id']}")
            assert resumed.status_code == 200 and resumed.json() == s
            if name == 'F2':
                assert checkpoints[1][0] == ('water', 'House 42', None, False, True)
                assert checkpoints[2][0] == ('water', 'House 42', None, False, False)
            print(json.dumps({'case': name, 'current': state(s['issues']),
                              'checkpoints': checkpoints}))

    run('F1', [('turn', 'Water at house 42'), ('review', 'confirm'),
               ('turn', 'not forty-two')],
        [('water', 'House 42', None, True, False)])
    run('F2', [('turn', 'Water at house 42'),
               ('turn', 'Water actually at house 10 or house 20'),
               ('review', 'clarify'), ('review', 'confirm')],
        [('water', 'House 42', None, True, False)])
    run('F3', [('turn', 'Water at house 10. Monday, sorry Tuesday, house 20.')],
        [('water', 'House 20', 'Tuesday', False, False)])
    run('F4', [('turn', 'Water at house 24/7')],
        [('water', 'House 24', None, False, False)])
    run('F5', [('turn', 'Water at house twenty zero')],
        [('water', 'House 20', None, False, False)])
    run('F6', [('turn', 'Water and drainage at house 24')],
        [('water', None, None, False, False),
         ('drainage', 'House 24', None, False, False)])
    run('F7', [('turn', 'Water at house 24'), ('review', 'confirm'),
               ('turn', 'Water at house 26')],
        [('water', 'House 24', None, True, False),
         ('water', 'House 26', None, False, False)])
    run('F8', [('turn', 'Water at house 42'), ('review', 'confirm'),
               ('turn', 'Actually house ippatnaalku on Monday')],
        [('water', 'House 42', 'Monday', False, False)])
    run('F9', [('turn', 'There is no water problem. Garbage at house 24.')],
        [('water', None, None, False, False),
         ('garbage', 'House 24', None, False, False)])
```

## Evidence status and future scoring

The block was extracted to ignored scratch storage and executed on 11 November 2026: **all nine current-behavior assertions and persisted-state checks passed**. This revalidates counterexamples; it is not an experiment showing a new system works. No application/test file changed and no upstream request was made. The original 80-test result belongs to the 10 November audit; no new full-suite run is claimed for this documentation revision.

For a future protocol experiment, replay the same extraction/proposal events to B3 and the proposed monitor, including identical repair omissions and spurious signals. Keep approval-source events and predeclared fault/commit-probe checkpoints identical. Gold policy states above are evaluation-only and must never be fed to either system. F1/F2/F7 measure temporal exposure; F3 tests field scope; F4/F5/F8 test unsupported/partial evidence; F6/F9 test semantic omission/extra issues and burden. No single aggregate should obscure those distinctions.
