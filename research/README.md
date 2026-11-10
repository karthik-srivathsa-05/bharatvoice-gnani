# Isolated protocol pilot

Base: `research/review-drafts` at `89c042b672ef6b88845bf7b465c633dbeac7c42b`.
Application, original tests and research documents under `docs/` are frozen.
This harness imports no application module, calls no API and uses only fictional
in-process ticket effects in disposable SQLite databases. It is an event-level
exploratory experiment, not a benchmark or a completed 60-dialogue pilot.

## Reproduce

From repository root with Python 3.11+:

```sh
python -m research.protocol_pilot.run
python -m research.protocol_pilot.report
python -m pytest -q research/tests tests -p no:cacheprovider
```

The report command renders the raw results table; its dated test result records the executed validation described below and does not itself run pytest.

`pytest` and application dependencies are needed only to run the combined suite;
the replay itself uses the standard library. This environment used the existing
`work/gnani-live/venv/bin/python`. No package/configuration file was changed.
Default project pytest discovery still selects the original `tests/`, so include
`research/tests` explicitly. Raw results and canonical-JSON input digests are in
`research/results/`. Running the replay rewrites only research result artifacts;
SQLite files live in a temporary directory and are removed at exit.

`python -m research.protocol_pilot.fixtures` regenerates the author-written input
and oracle files deterministically. Do not regenerate these while evaluating a
new policy without recording that change. These are development diagnostics and
controls, not independently labelled or held-out cases.

## Architecture and observation boundary

- `model.py`: deterministic event schema, canonical JSON and payload SHA-256.
- `policies.py`: common approval/validation/journal/sink mechanics; ordinary B3
  per-field pending tickets versus M's persistent global repair ledger.
- `replay.py`: observable replay, fault injection/reopening and runtime checks;
  has no oracle dependency.
- `fixtures.py`: authoring only, emits separate `streams.json` and `oracle.json`.
- `evaluate.py`: reads oracle after replay; never called by a policy.
- `run.py`: pairs both policies on identical copied streams/faults, then scores.
- `tests/`: regression/invariant/metric tests, including oracle-score isolation.

An event is `{id, seq, kind, data}`. Sequence numbers are consecutive positive
integers. IDs are unique and retries reuse exactly the same ID/content. Unknown
keys, malformed fields and changed-content retries are rejected. Canonical
payloads contain category/location/time; versions increment once per changed
proposal/clarification, including multi-field changes. Approval requires the
current version and digest from the same fixed scripted reviewer, not a
policy-generated or oracle-generated approval. That actor string models a
trusted review channel; it does not implement authentication.

| Kind | Exact data keys / interpretation |
| --- | --- |
| source | `text`: raw text only; neither policy parses language |
| proposal | `issue, values, evidence`: explicit issue/field proposal |
| correction / dispute | `scopes, field, evidence`: open a repair hold on every candidate issue |
| approval | `issue, version, digest, actor`: bind consent to complete resolved payload |
| revocation | `issue, actor`: remove consent |
| clarification | `issue, resolves, values, evidence`: explicitly resolve named repair IDs for fields present in values |
| acknowledgment | `issue`: record acknowledgment, without changing repairs |
| commit | `issue, operation`: attempt an idempotent simulated write |

Category is limited to four fictional service labels; location validation accepts
only `House 0` through `House 999` without leading zeros. It is syntactic, not
address verification. Invalid proposals are atomically rejected and create repair
holds. Evidence strings are opaque nonempty references, not verified entailment
or source-span alignment. `clarification` events model an explicitly trusted
resolution producer; they can be semantically wrong too. All policies receive
the same reference strings, scope candidates and resolution IDs.

B3 retains pending repair tickets by issue/field/event ID until an explicit
matching resolution. It also blocks approvals and releases while any ticket
remains. M adds a global ledger with evidence, scopes and resolution links.
Generic acknowledgment and unrelated edits clear neither representation.
Resolving one of several same-field repairs leaves the others. Choosing a target
from a candidate scope closes that repair across candidates; all previous
approvals stay invalid until renewed. This is a strong conventional baseline,
not the prototype's generic-clarify boolean behavior.

Both representations share a transaction/validation/transition shell to isolate
the storage difference. This limits independence: equal behavior is not evidence
from independently engineered commercial systems. The extra ledger enriches
retained audit information, but this pilot hypothesizes no magical extra semantic
signal. B3 can reasonably retain all necessary information with ordinary tickets.
No fixture/oracle is imported by the schema, workflow or replay modules. Gold
frame keys cannot be passed through the strict event schema.

## Durability, invariants and faults

A single ordered consumer uses an SQLite transaction to atomically persist the
state snapshot, input journal and simulated sink write. Restart loads the last
snapshot; same-ID replay returns the historical receipt; same operation ID with
a different event deduplicates a matching payload and rejects mismatches.
A historical receipt's `effect=true` describes the original logical transaction,
not another delivery. Result rows are per logical event, not per transport retry.

Checks cover matching approval version/digest, complete/resolved release,
recognized-change/revocation invalidation, persistent repair obligations, no
unrelated issue invalidation, event-ID/content integrity, ordered delivery and
unique sink operations. Regression tests include malformed schema, mismatched
resolution, overlapping repairs, untrusted actor, stale approval, operation
collision and out-of-order rejection. Seeded 100-event exercises per policy are
regression sampling, not exhaustive model checking.

Three fixture fault schedules exercise close/reopen before handling, rollback
before durable commit, and loss of response after durable commit followed by
reopen/retry. Every case is additionally replayed with restart before every event
in tests. This is deterministic boundary fault injection, not OS process killing,
parallel writers, physical power failure, real message queues or remote exactly-
once delivery. Single-consumer ordering, local SQLite durability and faithful
actor/event delivery are assumed. There is no policy protection for bypassing
writers or an unobserved user-intent change.

## Oracle and metrics

`oracle.json` is a separate author-written annotation file. It contains per-event
semantic fields, gold action eligibility, unresolved-clarification issues,
invalidated-approval episodes, permitted edit targets, and separately hand-labelled
observable protocol eligibility intervals. Terminal expected effect sets are
recorded independently of policy execution. It is not accessed until both replays
finish. The oracle reflects explicit conservative scenario judgments, not actual
latent intent certified from text or independent human agreement.

- **Stale exposure:** eligible obsolete approval at a gold-invalidated issue/event
  boundary, divided by all such at-risk issue/event boundaries; also exposed
  episodes / invalidation episodes. Starts at raw source arrival even for missed
  signals. Counts discrete sampled boundaries, not milliseconds or continuous time.
- **Wrong-target edits:** accepted field changes outside independently annotated
  permitted targets / all accepted field changes. Wrong value on the right field
  is a different semantic error; target labels are author judgments.
- **Semantic-invalid commit opportunities:** explicit scripted commit checkpoints
  where policy eligibility would release a gold-ineligible or wrong payload /
  all scripted commit attempts. Also report invalid logical effects / all effects.
  Checkpoints are author-selected, not all possible schedules or production rates.
- **Safe completion:** terminal required effects and resolved field states match,
  no semantic-invalid effects occurred, and any gold-required clarification remains
  held. Clarification-appropriate abstention and completed actions are separate
  strata. This does not imply exposure-free history; F8 completes safely while
  exposing old consent for one boundary before recognition.
- **Unnecessary blocking:** gold-allowed issue/event boundaries where gate is
  ineligible / all gold-allowed issue/event boundaries. This uses scripted trusted
  approval arrival; it cannot estimate interactive clarification/review burden.
- **Clarification obligations:** distinct repair IDs first opened; additionally
  issue/repair hold-boundary counts and holds absent gold clarification need.
  These are obligations, not spoken questions, latency or user satisfaction.
- **Duplicate effects:** extra effects per logical operation ID; receipts/retries
  are not new logical effects.
- **Protocol-state mismatch:** event boundaries whose eligibility set differs
  from separately labelled observable-protocol gold; invalid observable release
  effects are counted separately from semantic-invalid effects.

All denominators, snapshots, approval metadata, change evidence and sink payloads
are preserved in `results/per_case.json`. Zero errors on a handful of deterministic
cases is not a rare-event guarantee. There is no composite reliability score.
F1/F3/F4/F5/F6/F7/F9 deliberately preserve some original observation failures;
F8 includes a recognized repair. N15 supplies a recognized version of F1. These
are explicit event-level adaptations, not nine new runs of the application or
an actual Gnani extractor. No language model, parser or trained recognizer runs.

## Interpretation

See [EXPLORATORY_RESULTS.md](EXPLORATORY_RESULTS.md). Keep all cases exploratory;
do not promote them to held-out benchmark evidence. If B3 matches M, do not weaken
B3 or give M oracle flags to obtain a desired positive result. Implementation of
this isolated pilot does not authorize modifying the product or merging it.
