import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
r=json.loads((root/'results/per_case.json').read_text())
keys=[k for k,v in r[0]['policies']['B3']['metrics'].items() if type(v) in (int,bool)]
totals={m:{k:sum(x['policies'][m]['metrics'][k] for x in r) for k in keys} for m in ['B3','M']}
(root/'results/summary.json').write_text(json.dumps({'case_count':len(r),'identical':sum(x['behavior_identical'] for x in r),'totals':totals},indent=2)+'\n')
s='''# Exploratory protocol pilot results

**Executed 11 November 2026 (IST).** Base: `89c042b672ef6b88845bf7b465c633dbeac7c42b`; isolated branch `research/protocol-pilot`.

## Result and decision

**M has no observed behavioral advantage over competent B3: 28/28 paired event traces, neutral state snapshots, receipts, sink effects and metric sets are identical.** B3's ordinary durable pending-repair tickets already enforce the proposed ledger's release semantics. The M ledger retains a richer private audit record, not a measured improvement in safety or completion.

**No-go for a systems-superiority claim or immediate benchmark expansion.** Narrow to replication/diagnostic benchmarking, or identify a genuinely distinct requirement and preregister a fresh comparison. Do not weaken B3 to manufacture an advantage. This is a potential novelty failure under these observables, not statistical proof of universal equivalence or of uselessness of provenance.

## Execution and validation

- 9 event-adapted audit diagnostics (F1–F9) plus 19 benign/negative controls (N01–N19).
- `python -m research.protocol_pilot.run`: offline deterministic replay, no Gnani/model/network call or real complaint system.
- `PYTHONDONTWRITEBYTECODE=1 work/gnani-live/venv/bin/python -m pytest -q research/tests tests -p no:cacheprovider`: **131 passed** (51 pilot tests + original 80), one existing Starlette/httpx deprecation warning.
- Every paired row received identical observable inputs, repair scope/evidence, approval version/digest/actor, operation IDs and fault schedule. Oracle scoring occurs after replay. Oracle alteration is tested to change scores without changing policy traces.
- Protocol invariants, hand-labelled protocol eligibility, rollback/retry, response loss, restart before every event, overlapping repairs, invalid resolutions, malformed events, stale approvals and operation collisions are checked. These are regression/invariant executions, not a formal unbounded proof.
- Original `app/`, `tests/`, `docs/` and `main` are unchanged. Results artifacts contain only fictional records.

## Aggregate outcomes (each system, identical)

| Metric | B3 | M | Denominator / meaning |
| --- | --- | --- | --- |
'''
rows=[('Stale exposed boundaries','stale_exposed_boundaries','stale_at_risk_boundaries','gold-invalidated issue/event boundaries'),('Exposed episodes','stale_exposed_episodes','stale_episodes','gold invalidation episodes'),('Wrong-target edits','wrong_target_edits','accepted_edits','accepted field changes'),('Semantic-invalid release opportunities','semantic_invalid_commit_opportunities','commit_attempts','scripted logical commit attempts'),('Semantic-invalid sink effects','invalid_sink_effects','sink_effects','logical simulated effects'),('Unnecessary blocked boundaries','unnecessary_blocked_boundaries','allowed_issue_boundaries','gold-allowed issue/event boundaries')]
a=totals['B3']
for label,num,den,meaning in rows:s+=f"| {label} | {a[num]}/{a[den]} | {a[num]}/{a[den]} | {meaning} |\n"
s+=f'''| Terminal safe completion | {a['safe_completion']}/28 | {a['safe_completion']}/28 | all authored scenarios; includes appropriate clarification/non-action |
| Repair obligations opened | {a['clarification_obligations_opened']} | {a['clarification_obligations_opened']} | distinct repair IDs across cases |
| Clarification hold boundaries | {a['clarification_hold_boundaries']} | {a['clarification_hold_boundaries']} | issue/repair/event triples |
| Unnecessary hold boundaries | {a['unnecessary_hold_boundaries']} | {a['unnecessary_hold_boundaries']} | holds without gold clarification need |
| Duplicate effects | {a['duplicate_sink_effects']} | {a['duplicate_sink_effects']} | 22 unique logical effects, including retries |
| Protocol-state mismatches | {a['protocol_state_mismatches']} | {a['protocol_state_mismatches']} | 153 logical event boundaries |
| Observable-protocol-invalid effects | {a['protocol_invalid_effects']} | {a['protocol_invalid_effects']} | 22 effects; distinct from semantic errors |

These are fixed-case counts, not independent population samples or publication-level significance. Seven semantically invalid effects can coexist with zero observable protocol violations because the supplied interpretation/consent signals can be wrong or incomplete. No rule can infer gold intent from absent evidence. Zero unnecessary blocking reflects these scripted checkpoints, not measured real user burden.

## Raw per-case outcomes

Every cell below is identical for B3 and M (paired delta zero). `exposure` is exposed/at-risk issue-event boundaries; `target` wrong/all accepted edits; `bad opp` semantic-invalid release opportunities/all attempts; `bad effect` invalid/all sink effects; `holds` issue/repair boundaries; `block` unnecessary/all gold-allowed boundaries. A 0/0 entry means zero observed opportunities and an undefined rate, not zero risk. Safe is terminal outcome, not exposure-free history. Full per-event state and separate semantic/protocol gold are linked below.

| Case | Exposure | Target | Bad opp | Bad effect | Safe | Holds | Block | Duplicates | B3–M difference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
'''
for x in r:
 m=x['policies']['B3']['metrics']
 s+=f"| {x['case']} | {m['stale_exposed_boundaries']}/{m['stale_at_risk_boundaries']} | {m['wrong_target_edits']}/{m['accepted_edits']} | {m['semantic_invalid_commit_opportunities']}/{m['commit_attempts']} | {m['invalid_sink_effects']}/{m['sink_effects']} | {'yes' if m['safe_completion'] else 'no'} | {m['clarification_hold_boundaries']} | {m['unnecessary_blocked_boundaries']}/{m['allowed_issue_boundaries']} | {m['duplicate_sink_effects']} | none |\n"
s+='''
## Scenario interpretation

- **F1/F7:** a missed rejection or issue-identity ambiguity leaves old approval eligible; both fail. M has no extra repair detector.
- **F2/F8:** recognized unresolved repairs survive generic acknowledgment and unrelated edits in both systems. F8 has one exposed source-arrival boundary before the explicit repair event; terminal abstention is nevertheless safe.
- **F3/F4/F5:** wrong-target or lossy-but-schema-valid proposals can receive scripted matching consent and commit. A digest authenticates the observed payload, not intended meaning. Both fail semantic evaluation.
- **F6:** no shared-scope repair signal is emitted for drainage; a syntactically complete second issue can commit even though authored gold requires scope clarification.
- **F9:** the phantom water issue remains; the garbage effect itself is valid, but terminal state has an extra unresolved issue, so terminal completion fails.
- **N01–N18:** normal commitments, explicit second complaints, re-approval, actual resolution, retained overlapping holds, invalid raw identifiers, scoped repairs, revocation, stale approvals, crash rollback/receipt loss and retries behave as expected in both.
- **N19:** deliberately wrong declared target edits drainage instead of water and leaves old water approval usable. Both fail; the monitor cannot establish semantic target correctness from a wrong proposal alone.

F diagnostics achieve terminal safe completion 2/9; controls 18/19, with N19 deliberately retaining a semantic fault. This partition is a description of selected cases, not comparative model accuracy. No significance test or confidence interval is offered for these author-selected, non-independent development traces.

## Limitations and next step

B3 and M share transition, validation and persistence mechanics; only pending-ticket versus ledger representation differs. This isolates ledger necessity but is not an independent implementation challenge. B3 was deliberately given ordinary durable repair tracking because a competent workflow can reasonably obtain the same information. Equality is unsurprising and falsifies an advantage claim for this treatment, not all possible future policies.

The 28 fixtures are not the proposed 60 independently reviewed dialogues. A single author wrote streams and separate gold; no human annotation agreement, blind test split, language extraction, acoustic evaluation, full-duplex interruption or customer utility study occurred. Golden conservative interpretations of F3/F6/F7 are contestable and need independent review. No policy reads gold, but that alone does not make the corpus independent.

Trusted `reviewer` identity, resolution signals and opaque evidence references are simulated. Sources are not parsed and no suspend-on-every-utterance comparator was run; delayed/missed recognition remains explicit. Local transactional fault injection is not real process death, concurrent consumers, remote side effects or production durability. Clarification holds are a burden proxy, not actual questions or elapsed user time. All denominators and policy/semantic distinctions are documented in [README.md](README.md).

**Recommendation:** retain this as a reproducible negative-result artifact. Have independent reviewers examine the semantic oracle and possible requirements not represented here before authorizing additional engineering or the 60-dialogue exploratory collection. If a distinct obligation cannot be articulated that ordinary B3 cannot reasonably implement, continue only as benchmarking/replication. No product code change, deployment, merge or full-corpus expansion follows from this result.

## Artifacts

- [Observable streams and fault schedules](data/streams.json)
- [Separate semantic/protocol oracle](data/oracle.json)
- [Raw per-case and per-event paired outcomes](results/per_case.json)
- [Aggregate raw counts](results/summary.json)
- [Canonical-JSON input digests and base revision](results/manifest.json)
- [Pilot tests](tests/test_protocol_pilot.py)
'''
(root/'EXPLORATORY_RESULTS.md').write_text(s)
