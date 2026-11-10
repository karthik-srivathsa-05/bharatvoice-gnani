# BharatVoice technical research audit

**Initial audit: 10 November 2026; methodology revision: 11 November 2026 (IST).** Audited repository: `karthik-srivathsa-05/bharatvoice-gnani`, commit `7f786412523a232c9c39654c9184d4c7fda65290`. This audit changes no application code or tests. Recommendations are future work, not implemented features. Related documents: [prior art](PRIOR_ART.md), [proposal](RESEARCH_PROPOSAL.md), [pinned gap matrix](PRIOR_ART_GAP_MATRIX.md), [executable counterexamples](COUNTEREXAMPLE_SPEC.md).

## 1. Executive finding

BharatVoice is a small, inspectable deterministic complaint-state prototype with a working batch STT adapter, useful regression tests, optimistic session updates, and explicit UI/API confirmation. It is not yet a research benchmark, a general intent extractor, a fault-tolerant voice runtime, or a verified action-commitment system. The strongest asset is a concrete failure-driven starting point for studying correction integrity. The principal risk is treating syntactically complete state as semantically trustworthy state.

The 80-test suite passes, but targeted audit probes reproduce stale confirmation, partial address capture, field-scope leakage, and a clarification gate that can discard an unresolved conflict without resolving its content. These findings do not imply external complaints were submitted: there is no submission integration.

## 2. Method and evidence boundaries

**Reproduced in the initial 10 November audit:** read `app/{normalization,engine,store,stt,main,evaluation}.py`, static UI behavior in source, fixtures, pytest and browser-smoke source, README and validation notes; reran the complete existing pytest suite and evaluation script; executed isolated engine and FastAPI TestClient probes with temporary databases. Scratch scripts/results are under ignored `work/research/`, not proposed repository changes.

Commands from repository root, using the existing isolated environment:

```sh
PYTHONDONTWRITEBYTECODE=1 work/gnani-live/venv/bin/python -m pytest -q -p no:cacheprovider
work/gnani-live/venv/bin/python evaluate.py
```

Result: **80 passed, one Starlette/httpx deprecation warning**. Evaluation: engine **5/5**, simple baseline **0/5** on the five known synthetic scenarios. No paid Gnani calls, browser run, throughput benchmark, process-kill experiment, or penetration test was performed in that audit. The 11 November documentation revision separately reran the embedded F1–F9 API reproducer; it did not rerun the complete suite or evaluate a new protocol.

**Historical execution evidence:** `docs/LIVE_NORMALIZATION_VALIDATION.md` and this session record one retained Flite clip rerun through the existing adapter, HTTP 200, model `prisma-v3.0`, request `ad7386c0-d1de-4900-9033-b32dc89069d2`; its actual transcript yields water / House 24 / Monday with an address revision. This establishes one synthetic English audio path, not a population-level STT result or independent replication.

Code references below identify symbols and approximate lines at the audited commit; they are not references to a future implementation.

## 3. Architecture: actual behavior versus broader interpretations

| Component | Implemented and evidenced | Not established / absent |
| --- | --- | --- |
| Speech | `stt.py:validate_audio`, `GnaniPrisma.transcribe`: decoded format/duration/channel/size checks; multipart REST request; explicit v3 model; bounded client I/O; sanitized failures | Streaming ASR, turn-end detection, silence rejection, diarization, confidence calibration, cancellable in-flight turns, multiple independent ASR comparisons |
| Normalization | `normalization.py:normalize`: English explicit house-number rewrite for extraction; original text retained; zero–99 and bounded hundreds grammar | General inverse text normalization, complete address parser, Kannada or mixed-language numbers, lossless character-span mapping |
| Extraction | `engine.py:process`, `apply_fields`, `values`: category lexicon, regex fields, order-based updates, heuristic reference targeting | Learned SLU, general coreference, semantic entailment, arbitrary intents/addresses, calibrated uncertainty, robust negation scope |
| State | Strict Pydantic issue/session models; stable UUIDs; missing-field/blocked flags; per-field revision tuples | Formally specified transition system, invariant proofs, typed event algebra, semantic schema versioning |
| Persistence | `store.py:save`: SQLite WAL, JSON aggregate, version-conditional update; resume by session ID | Event-sourced replay, replicated durability, backup validation, external exactly-once effects, crash recovery of in-flight audio |
| Confirmation | `main.py:review`: current session version, explicit confirm action, completeness/blocked checks; accepted changes usually revoke confirmation | Authenticated actor identity, content digest bound to consent, expiry, external transaction reservation/commit, proof of user understanding |
| Evaluation | Five fixed synthetic scenarios, exact ordered fields, transparent weak baseline, 80 regression tests | Held-out corpus, independent annotation, statistical intervals, speaker diversity, multi-model baseline study, credible commercial reliability estimate |

The browser renders stored values and revision evidence with HTML escaping. The audio endpoint enforces an authorization boolean, but this is a caller assertion, not verified consent. Audio bytes are not persisted by this app. Session transcripts are persisted, so privacy concerns remain even without audio retention.

## 4. Reproduced failure modes

These are deterministic counterexamples at the audited commit, not estimates of prevalence. Fresh sessions were used unless a sequence is shown. Engine probes set `confirmed=True` only after a complete first turn when examining state revocation; findings F1 and F2 were independently reproduced through legitimate API confirm/review calls.

| ID / severity for a future transactional system | Input / setup | Observed | Interpretation |
| --- | --- | --- | --- |
| F1 / high | Create `Water at house 42`, explicitly confirm through API, then `not forty-two` | House 42 remains `confirmed=True`, `blocked=False` | Unsupported bare spoken negation is ignored without invalidating consent. This is stale semantic approval, despite correct version bookkeeping. |
| F2 / high | Starting from House 42, submit `Water actually at house 10 or house 20`; then call review `clarify`, then `confirm` | Ambiguity initially blocks and retains House 42; `clarify` clears the flag; confirm returns HTTP 200 for House 42 | The generic clarify action acknowledges away the conflict; it does not require replacement evidence or a resolved choice. This may be intentional UI acknowledgment, but it is not verified semantic resolution. |
| F3 / high | `Water at house 10. Monday, sorry Tuesday, house 20.` | House 20 / Tuesday, unblocked, awaiting confirmation | A marker between first/last address spans can actually belong to time correction. Current field-scope protection is incomplete. Expected policy should ask which address is intended. |
| F4 / medium | `Water at house 24/7` | House 24, awaiting confirmation | Unsupported suffix is silently lost, contrary to an interpretation that all unsupported complex addresses safely abstain. |
| F5 / medium | `Water at house twenty zero` | House 20 | Invalid tens/unit composition is accepted. Broad supported-grammar claims need lexical negative tests. |
| F6 / medium | `Water and drainage at house 24` | Water has no address; drainage gets House 24 | Splitting at category mentions does not propagate shared arguments. This conservative omission requires clarification, not automatic copying. |
| F7 / medium | `Water at house 24`; then `Water at house 26` | Two water issues | “Same service” is insufficient for identity; without reference markers the system makes a new issue. Intended new complaint versus update is unresolved. |
| F8 / high | House 42 exists; `Actually house ippatnaalku on Monday` | Retains House 42, changes Monday, unblocked, unconfirmed | A recognized time change suppresses the unresolved-correction block for an unrecognized address. Completion can mask partial comprehension. No claim is made that this spelling is a validated Kannada expression. |
| F9 / medium | `There is no water problem. Garbage at house 24.` | Extra incomplete water issue plus garbage issue | Category mention detection is not semantic problem/negation recognition. |

Reproduce F1/F2 without any upstream request using `TestClient(create_app(temp_db))`: create session; post typed turns with current version; POST `/issues/{id}/review` with `action=confirm`; apply the follow-up; inspect location, confirmed, blocked. For F2, use the ambiguous follow-up, `action=clarify`, then `action=confirm`, always with returned versions. These public routes reach the problematic states; no direct database editing is required.

### Normalization assumptions

`HOUSE` accepts only explicit “house” prefixes and selected English number forms. `CONTINUATION` rejects some trailing number words but is not a whole-address validator. The replacement sentinel prevents some partial parses, not all. Numeric `24/7` is truncated downstream; zero is allowed as a unit after a tens word. Leading zeros in numeric identifiers collapse through `int`, potentially changing an identifier such as House 007 to House 7. City, street, apartment, and postal identifiers are not modeled structurally. These are static-code deductions except F4/F5, which were executed.

### Correction and provenance assumptions

Negation uses an eight-character preceding window and a short following window (`engine.py:48–56`), not syntactic scope. Category occurrences define issue fragments (`process:109–126`); pronouns and shared locations do not. The word “not” also appears in ordinary complaints, so it is an unreliable signal of a reference. Revision `before` can be recorded for a negated value that was never accepted (`apply_fields:78–82`): this is rejection evidence, not necessarily an actual state transition. A research event schema must distinguish mention rejection from mutation.

Original turn text and original issue fragment are retained; `extraction_text` is separately stored. Revision evidence is an entire fragment, not an aligned source span, timestamp, speaker, normalizer version, or immutable audio hash. The history can support debugging but does not prove an extracted value is grounded. The SQLite payload is mutable and not tamper-evident.

## 5. Confirmation and action-safety assessment

The API blocks confirmation when category/location are missing or the issue is blocked. Time is optional. Accepted recognized edits revoke confirmation. Transcript words alone never grant confirmation. Session compare-and-swap rejects stale writes and reviews. These are real useful controls.

However, completeness is only non-null category/location plus a flag: House 24 is not a dispatch-ready verified address. An ignored correction can preserve a prior approval (F1); `clarify` can release an old value (F2). `confirmed` and `blocked` are mutable booleans, not tokens bound to a specific canonical payload and actor. The session version gives optimistic concurrency, not authorization or semantic correctness. Confirmation does not increase issue version on its own, though session version and a review event change.

No authentication/tenant isolation exists: possession of a session UUID grants read/write capability. Random IDs reduce guessing but do not constitute identity management. No action sink, outbox, downstream acknowledgment, idempotency key, compensation or commit receipt exists. Therefore “verified commitment” is a research proposal, not an implemented guarantee. Text-only confirmation attacks and full hostile-prompt behavior have not been systematically tested.

## 6. Persistence, concurrency, and scale

**Verified:** each save rewrites the full serialized aggregate with `WHERE id=? AND version=?`; losing writers get a conflict. The normal disk-resume test creates another Store and reloads data. SQLite WAL permits readers alongside a writer, but does not turn SQLite into a distributed state service.

**Deduced limitations, not measured load results:** unbounded turns/revisions cause larger JSON serialization, transfer and write costs; repeated full-history snapshots increase cumulative work. SQLite serializes writers and uses a ten-second connection timeout. Sync database and decode work inside the async audio route can block its event-loop worker. A new HTTP client is created per transcription, so no persistent pooled client is shared. File reads are capped, but rate limits, tenant quotas and retention policy are absent. Connection context managers transact but do not explicitly close SQLite connections; lifetime should be reviewed under sustained load rather than assumed bounded.

**Failure window:** the audio route loads/checks a version, awaits paid STT, then saves. A concurrent update can cause the STT result to be discarded with HTTP 409 after the upstream charge. Process loss after STT but before save loses the result; retry can repeat cost. Request UUIDs are metadata, not durable request deduplication. There is no in-flight journal or replay recovery. Audio uploads cannot select an issue target as typed turns can, making repeated same-category corrections especially difficult.

WAL/atomic SQL protects a local update, not a multi-service transaction. Recovery claims need process-kill, response-loss, disk-full, corruption, concurrent-tab, duplicate-request and schema-upgrade experiments. Network partitions and multi-node deployment remain untested.

## 7. Tests: what 80 passing cases do and do not show

Strengths: strict schemas, stale-version rejection, basic persistence, missing-field gates, manual edit revocation, multiple issue examples, mocked upstream error handling, and the exact real-transcript regression are covered. The zero–99 loop checks all constructed values, although pytest counts it as one test.

Weaknesses:

- Most language examples are hand-authored around the rules. Five evaluation fixtures were known during implementation; no held-out authors, templates, entities, speakers or languages exist.
- The baseline intentionally returns one first-match record. Beating it does not compare against modern dialogue-state tracking or a carefully prompted structured-output model.
- Exact ordered final fields ignore transient wrong state, rejected alternatives, incorrect issue linkage, confirmation exposure, and recovery time. Equivalent issue ordering can fail while wrong histories can pass.
- The captured Gnani transcript test is now offline text replay. Genuine HTTP calls are historical manual evidence, not part of routine pytest. Mocked success cannot measure ASR quality.
- Silent generated WAVs are intentionally accepted in decoder tests: passing validation proves decodability, not speech presence. No accent/noise/overlap study exists.
- Normal resume is not crash recovery; sequential conflicting saves are not a parallel stress test. No randomized fault injection, property-based transition tests, replay determinism or state-machine model checking exists.
- No regression presently covers the reproduced stale spoken negation or clarify-with-old-value bypass. Broad “correction-aware” descriptions exceed tested semantic coverage.
- Browser smoke is a useful optional UI path, not a research benchmark and not automatically run by pytest. Dependencies use version ranges rather than a reproducible lock.

## 8. Claims ledger and prioritized recommendations

| Claim | Verdict |
| --- | --- |
| Genuine Gnani Prisma v3 integration | Supported for the documented English synthetic clip; no broader accuracy claim |
| Preserves original transcript | Supported for stored text; does not retain audio or exact aligned spans |
| Handles scoped corrections | Partially supported on bounded cases; F1/F3/F8 falsify general coverage |
| Resumable session | Supported for saved aggregates; in-flight/interruption-safe recovery absent |
| Explicit confirmation gate | Implemented, but not sufficient to guarantee correct current intent |
| Research-grade benchmark / commercial integrity layer | Not yet supported |
| No external complaint committed | Supported: no external submission implementation |

**P0, research prerequisites:** specify ambiguity, correction and consent semantics; freeze held-out evaluation; introduce distinguishable rejected-mention and state-change annotations in the proposed corpus; count stale approval exposure; make strong comparisons. These are recommendations, not changes authorized here.

**P1, future experimental system:** separate uncertain proposals from state mutations, bind approval to version/content, require semantic resolution, journal/deduplicate operations, and evaluate failures at boundaries. Do not equate a monitor proof with correct language understanding.

**P2, commercial prerequisites:** identity/tenant controls, privacy and retention, resource limits, observability, dependency pinning, crash/load tests and downstream reconciliation. Product UI expansion should wait.

The research opportunity is a narrowly specified and independently evaluated correction-to-confirmation boundary, not another collection of address regexes. Publication and novelty assessment are in the companion documents. External review provisionally approved the direction, with methodological revisions required before implementation. The five research documents may be committed to `research/review-drafts`; the application remains unchanged.

## 9. Revision: semantic versus observable failures

The proposed monitor can constrain only operations and consent signals actually delivered to it. It cannot guarantee the latest actual user intent from an ASR transcript, nor establish semantic truth from a valid evidence span. Independent annotated intent is an uncertain evaluation reference, not a monitor input. Conditional version-bound approval and at-most-one simulated sink effect are observable protocol properties, not a proof of semantically correct action. Trusted actor identity, event ordering/delivery, canonicalization, atomic gating and sink deduplication remain assumptions, absent from the present app.

F1 exposes semantic stale approval even though the current parser emits no repair. A monitor receiving the same omission may miss it too. F2 is a resolution-policy failure; F3 is scope ambiguity; F4/F5 are normalization/identifier errors; F6 is conservative incompleteness; F7 is ambiguous issue identity; F8 is partial interpretation; F9 is a false semantic issue. These are not nine equivalent protocol violations. Proposed policy responses are defined separately from reproduced state in `COUNTEREXAMPLE_SPEC.md`. No action was committed: there is no action route.

All nine current-API outcomes and persisted-state checks in that document were reproduced on 11 November, using legitimate review actions rather than direct boolean mutation. No normative future-policy assertion was run. The earlier 80-pass suite and live Prisma result remain dated historical evidence. A competent B3 receives the same proposals/repair flags and can retain the same obligations; proving advantage over the present prototype alone would not establish research novelty.
