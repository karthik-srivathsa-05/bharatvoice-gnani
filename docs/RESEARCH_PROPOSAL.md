# Research proposal: correction-scoped state and consent integrity

**Review draft — 10 November 2026 (IST).** Research plan only; no new application or test implementation is authorized by this document. Audited starting point: `7f786412523a232c9c39654c9184d4c7fda65290`. Evidence and references: [audit](RESEARCH_AUDIT.md), [prior art](PRIOR_ART.md).

## 1. Recommended thesis and contribution boundary

**Working thesis:** Explicitly representing the target, evidence and unresolved status of a correction, and binding approval to the resulting issue version, reduces stale or wrong-target action acceptance at comparable task completion and clarification cost, compared with competent structured-state and ordinary confirmation baselines.

Combine two deliverables: (1) a controlled trace benchmark of multi-issue self-repair and approval boundaries; (2) a small reference monitor over proposed state edits and version-bound consent, evaluated using the same extractors as its baselines. Use BharatVoice as the existing experimental host, not as evidence that the thesis is already true. Begin with English and a bounded intake schema. Kannada-English is an explicitly gated extension, not an assumed capability.

This is not a claim to invent dialogue state tracking, correction-aware SLU, confirmation, runtime monitors, idempotency, or voice benchmarks. Those overlap heavily with [R2/R3/R13–R18/R20–R24](PRIOR_ART.md). The differentiator to test is whether issue/field-specific correction traces plus approval invalidation reveal meaningful failures hidden by final-field accuracy. Closest competing work must be checked before a “new benchmark” claim; otherwise release an extension to existing evaluation.

## 2. Formal problem statement

Let a dialogue trace contain events `e_1 ... e_T`. An event has an ID, order, actor, modality and payload; possible event kinds include utterance, extracted proposal, clarify, approve, revoke, restart, retry and simulated commit. Speech gives observed transcript `x_t` through a possibly lossy recognizer; gold user intent is annotated from the original authorized utterance/audio, not inferred from the system's transcript alone.

For each stable issue `i`, the desired state contains fields `f`, with field status in `{unknown, resolved, disputed}`. Gold annotation `G_t` records values or acceptable alternatives, correction target issue/field, rejected values, source evidence, and whether clarification is required. Ambiguous language is not assigned an invented single value. A rejection is distinct from a mutation, and a new complaint is distinct from a correction to an existing complaint of the same service.

A system maintains `S_t` and proposes operations such as:

```text
SET(issue, field, value, evidence)
REJECT(issue, field, old_value, evidence)
DISPUTE(issue, field, candidate_set, evidence)
APPROVE(actor, issue, version, payload_digest)
REVOKE(actor, issue, version)
COMMIT(operation_id, issue, version, payload_digest)
```

These are proposed research abstractions, not existing APIs. A monitor either accepts the operation, requests clarification, or blocks it. The experimental sink is a simulated ticket database, never a real authority or payment endpoint.

Two correctness layers must be evaluated separately:

1. **Protocol integrity**, relative to observable events: commit requires current complete/resolved state, a matching explicit approval bound to the canonical payload/version and actor, no intervening invalidation, and appropriate operation deduplication.
2. **Semantic integrity**, relative to independently annotated `G_t`: the committed values and correction target must match the user's latest resolved intent. A valid protocol can still commit a confidently wrong extraction. No formal proof of layer 1 establishes layer 2.

Candidate invariants for the finite protocol model:

- Accepted edits change only their declared issue/field and retain evidence.
- A material field change or unresolved correction to an issue invalidates its previous approval.
- No commit while required fields are unknown/disputed; explicit approval is required for the current payload.
- An approval/retry for an old version cannot authorize a newer payload.
- For a simulated sink that durably enforces operation IDs, repeated delivery has at most one effect per operation ID.

The last property is conditional on the trusted sink and its deduplication retention. Do not claim universal exactly-once network execution. If the upstream extractor fails to emit an unresolved correction, the monitor may never observe it; test this failure explicitly. Proposed evidence checks cannot prove transcript-to-intent equivalence.

## 3. Testable hypotheses and preregistration

All thresholds below are proposed practical targets, not measured results. Freeze hypotheses, primary comparison, annotation manual, test split, stopping rules and cost limits before final evaluation.

| Hypothesis | Comparison and primary outcome | Proposed success criterion |
| --- | --- | --- |
| H1: scoped correction representation improves state integrity | Same extractor with/without issue/field correction operations; held-out correction-event correctness and wrong-target edit rate | At least 5 percentage-point paired improvement in correction-event correctness; 95% CI excludes zero; no material increase in wrong-target edits |
| H2: evidence/dispute-aware approval invalidation reduces bad commitments beyond ordinary protocol hygiene | Full monitor versus version/digest-bound approval + idempotency baseline, matched extractor | At least 30% relative reduction in semantic-invalid commit events when comparator has enough events to estimate this, with positive paired absolute reduction; completion non-inferiority margin 5 points |
| H3: integrity measures add information beyond final-state accuracy | Compare/rank traces by final JGA and temporal correction/approval errors | Independently adjudicated examples with equal final JGA but different invalid exposures, plus system-level analysis; report uncertainty rather than forcing a new composite score |
| H4: replay preserves protocol integrity under bounded faults | Faulted versus unfaulted runs at defined event boundaries | Zero model-checked protocol violations within declared finite bounds, zero observed duplicate sink effects, and measured completion/recovery cost; these do not imply semantic correctness |

H1/H2 are confirmatory if powered; H3 is construct validation, H4 a bounded engineering result. If the ordinary protocol baseline already eliminates observed invalid commits, H2 has no room to succeed: report that negative result and study semantic extraction instead. Do not manufacture an effect by using only the current weak baseline.

## 4. Baseline systems and fair comparisons

| System | Purpose | Controls |
| --- | --- | --- |
| B0: existing first-match baseline and frozen BharatVoice `7f78641` | Historical reference and regression floor | Original schemas/limitations stated; never treated as the main competitor |
| B1: full-history schema-constrained extraction | Strong language baseline: reconstruct issue state from complete history each turn using a capable structured-output model | Same transcripts, evidence schema, bounded history policy, frozen prompt/model/date, few-shot budget and seeds |
| B2: incremental state-operation extractor | Strong update baseline inspired by SOM-DST/Correctable-DST; predict carry/set/delete/dispute and issue target | Same backbone as B1 where feasible; no claim of reproducing published model scores without retraining and official evaluation |
| B3: structured extraction plus competent conventional workflow | Main protocol competitor: explicit read-back, content/version-bound approval, per-issue revision invalidation on recognized changes, durable state and idempotent simulated sink | Same extractor as proposed system; include normal engineering safeguards rather than a straw-man button |
| B4: correction/read-back prompting scaffold | Voice/entity-repair comparison inspired by τ-Elicitation | Adapt to identical bounded schema; label as an adaptation, not an official benchmark score |
| Proposed: correction-evidence/dispute monitor | Tests whether field-scoped evidence and unresolved-repair obligations add value beyond B3 | Same extractor, approval UI/event source, sink and fault schedule; only proposed monitor policy differs |
| Oracle-proposal and oracle-transcript conditions | Attribute failures to recognition, extraction or protocol | Gold proposal replay and gold-text input are diagnostic upper bounds, not deployable competitors |

Use one inexpensive pinned model for development, then one stronger accessible model or open-weight system for external comparison. Gnani access does not imply access to an LLM extraction API; budget/credentials for B1–B4 must be secured or explicitly declared unavailable. Do not substitute mocked model outputs and call them strong baselines. An open-weight option requires measured hardware feasibility; do not assume Codex Cloud has a GPU. Include two genuinely distinct extractor strengths before broad model-independent claims.

Where licensing and task compatibility permit, run a small pinned external benchmark subset (e.g. entity elicitation or a spoken-state task) to test portability. Report adapted-task results separately from official scores. Assess whether issue multiplicity/approval annotations are genuinely absent in the chosen version before creating new labels.

## 5. Dataset design

### Proposed staged corpus

Start with a **60-dialogue pilot**, explicitly excluded from confirmatory testing. Use it to define correction semantics, estimate disagreements, reveal weak baselines and calculate power. The main proposed corpus is **600 independently authored scenario families**, each with roughly 3–8 turns: 150 training/examples, 150 development, 300 sealed test. Treat a family as the unit of independence; paraphrases/audio variants/fault traces from that family never cross splits.

The proposed six principal strata are: single-issue replacement/rejection; punctuation/cross-turn/repeated repairs; multiple issues including same-category instances; ambiguous/unresolved and incomplete requests; approval/revocation races; and restart/retry/reordering. Balance 100 families per principal stratum, while recording secondary attributes and reporting intersections only with sufficient support. Include benign no-correction controls in each relevant stratum. Do not design every test to contain an error or force every case to need clarification.

This is a feasibility target subject to pilot annotation time, not an existing dataset or guaranteed power. A smaller independently annotated corpus is preferable to thousands of unchecked generated paraphrases.

### Annotation record and independence

Each family needs scenario intent and acceptable action, speaker/author metadata at privacy-safe granularity, original text/audio, observed transcript, per-turn gold issue IDs and fields, rejected candidates, correction target, uncertainty/clarification requirement, evidence spans where possible, consent scope/version, and expected sink effects. Annotate both an utterance's intended correction and what a transcript-only observer can reasonably know. Some ASR errors are unrecoverable without clarification; do not score abstention as failure in such cases.

Define two modes: fixed trace replay for exact reproducible state/protocol comparison, and a small interactive subset for clarification/completion. Fixed scripts cannot fairly answer arbitrary agent questions. In interactive trials use a constrained scenario oracle/human adjudicator, cap turns, and audit whether a model user invented new facts. Keep user simulation and system evaluation independent; deterministic sink checks are primary, LLM judges only supplementary and human-audited.

At least two people independently annotate correction target, disputed status and commit validity on the held-out set, then adjudicate disagreements without seeing system identities. Report raw agreement and Krippendorff's alpha or an appropriate categorical agreement statistic; continuous state/value disagreement needs separate exact agreement reporting. Preserve a set-valued gold where ambiguity remains. If only the solo author can annotate, label the corpus provisional and reduce publication claims. Kannada-English gold requires proficient independent reviewers, not machine translation alone.

Split by scenario family, address/entity value, author and, for audio, speaker. Reserve unseen composition patterns and distractor structures for test. Do not expose sealed data to prompt iteration or use the same generative model to write gold and judge it without human checks. Synthetic/TTS, read speech and spontaneous speech must be labeled and scored separately. Publish consent, redistribution rights, licenses and redaction process; use fictional identifiers and addresses. Check each reused dataset's terms before distribution.

### Speech and credit plan

First evaluate on gold text and cached Gnani transcripts. Then, subject to budget, select **120 short human utterances from at least 8 consenting speakers** plus **120 locally synthesized controls** from held-out families. At about 15 seconds each this is roughly 60 audio minutes total; actual billing must be checked in the account before running. Human sessions need at least enough preceding context for each correction, not isolated misleading sentences. This sample is a diagnostic speech slice, not a representative accent/dialect benchmark.

Hash authorized audio, cache raw sanitized API outputs with model/request/time metadata, and reuse transcripts across systems. One transcription per clip initially; reserve at most 10% extra calls for labeled repeatability diagnostics/failures. Count failed billed requests and prohibit automatic unbounded retries. Record total billed minutes and extraction-token costs. If human collection or credits are unavailable, publish a text-first benchmark with a clearly secondary TTS feasibility demonstration. No claims of code-mixed robustness follow from that fallback.

A Kannada-English phase should be a separately preregistered slice, with native-script/romanized/mixed-number annotations and speaker/dialect metadata. Start only after qualified review and corpus-use authorization. It is not necessary to train a new ASR system.

## 6. Metrics and denominators

Avoid one opaque “intent preservation” scalar initially. Report a vector with counts and uncertainty:

| Metric | Definition / denominator | Why needed |
| --- | --- | --- |
| Turn joint state accuracy (JGA) | Fraction of evaluated turns where all gold resolved values and disputed/unknown statuses match; stable issue matching specified in advance | Standard state accuracy; report final and all-turn variants |
| Correction-event correctness | Fraction of gold correction events with correct target issue/field, rejection/replacement and required dispute state | Tests actual repairs rather than only final fields |
| Wrong-target edit rate | Number of accepted mutations to a gold-unaffected issue/field divided by accepted mutations; also count per dialogue | Detects collateral edits; publish opportunity counts to prevent denominator gaming |
| Unsupported-value rate | Accepted values lacking admissible source support divided by accepted resolved values | Measures grounding separately from formatting |
| Semantic-invalid commit rate | Commits inconsistent with gold latest resolved intent or lacking gold-valid consent, divided by commit attempts reaching the sink; also report affected dialogues / all dialogues | Captures wrong but protocol-valid actions; abstention cannot hide behind a small denominator |
| Protocol violation rate | Invalid transitions under the formal observable policy divided by evaluated transitions, plus any-violation dialogue rate | Distinguishes enforceable rules from semantic correctness |
| Stale approval exposure | Number of correction opportunities leaving old approval usable before repair/revocation, divided by gold invalidation opportunities; also report duration in events | Detects unsafe intermediate states even if final slots recover |
| Safe completion / coverage | Correct authorized terminal outcomes / eligible dialogues; accepted proposals / all proposals; abstentions separately | Prevents an always-block monitor from appearing successful |
| User burden / efficiency | Clarification turns, review requests, median/p95 latency, model tokens, API minutes per successful eligible task | Quantifies commercial tradeoffs |
| Recovery / duplicate effects | Faulted runs matching the no-fault committed result and approval state; duplicate effects per logical operation | Tests recovery with explicit logical event IDs |

Match issue IDs by annotated entity/mention linkage or a preregistered deterministic bipartite assignment independent of predicted slot correctness, not by array position alone. Penalize omitted/extra issues; do not match away wrong-target corrections. Report exact raw identifier match and a narrowly documented formatting-equivalence score separately; never collapse House 24/7 and House 24.

Report WER as a speech diagnostic alongside critical entity/correction-token errors, not as a proxy for end-to-end safety. Language metrics use human references; gold intent is independent of ASR text. Repeated-trial success may be reported with an explicit all-k-success definition following the τ-bench lineage, distinct from at-least-one-success pass@k. Repeated runs are not additional independent dialogues.

## 7. Ablation and fault experiments

Run a small planned comparison matrix on development first, then freeze the confirmatory subset. Full factorial experiments across all models/audio/faults are unaffordable and unnecessary.

1. Remove address normalization while preserving original transcript; measure representation sensitivity.
2. Remove issue identity/field scope checks; test wrong-target edits including two water complaints.
3. Remove evidence/dispute obligations while keeping version-bound confirmation and idempotency (the principal B3 comparison).
4. Remove payload/version binding, retain explicit confirmation; isolate ordinary protocol safeguards.
5. Remove approval invalidation on uncertainty, leaving recognized-change invalidation; target stale approval exposure.
6. Remove operation deduplication/journaling only in the simulated sink; test retry/restart failure contribution.
7. Gold versus observed transcripts, and oracle proposals versus actual extraction; identify irrecoverable ASR and missed-correction limits.
8. Punctuation, filler, entity and unrelated-issue transformations expected to preserve or selectively change state; credit behavioral-testing prior art.

Inject faults at recorded boundaries: before save; after save before response; after approval; after correction invalidation; before sink delivery; after sink delivery before acknowledgment; and during replay. Include duplicate event IDs, stale approvals, out-of-order events and malformed proposal evidence. Process restart is distinct from mid-utterance barge-in. Full-duplex speech interruption is out of the initial scope.

A finite reference model should enumerate bounded issue counts, field statuses, approvals, operation IDs and fault interleavings, with declared bounds and trusted assumptions. Model checking plus implementation conformance tests is a plausible systems artifact; exhaustive finite exploration is not proof for unbounded deployment.

## 8. Statistical validation and stopping rules

The independent unit is scenario family, with speaker/session clustering for speech. Use the same held-out families, cached transcripts, extractor outputs where appropriate, and fault seeds for paired comparisons. For stochastic extractors, run three repeats on the primary test condition if budget allows; retain all runs and aggregate within family before confidence intervals. Never count variants/retries as independent samples.

Report paired absolute effect sizes and 95% cluster-bootstrap CIs (e.g. 10,000 resamples). For a single binary success per independent family, an exact McNemar comparison is appropriate; use clustered paired permutation/bootstrap for repeated variants. Use a one-sided non-inferiority interval for H2 completion with the preregistered five-point margin. Apply Holm correction to a small declared confirmatory family (H1/H2); mark other slice/ablation analyses exploratory. Publish per-case outcomes, exclusions and inference details.

Power is not guaranteed by “300 test dialogues.” Use pilot discordance and event frequencies to simulate the sample size needed for the prespecified H1/H2 effects. If rare invalid commits make H2 underpowered, extend collection under a fixed predeclared cap or report uncertainty, not post-hoc significance. A safety-oriented stress set deliberately enriches failures and does not estimate real deployment prevalence.

With zero invalid outcomes in `n` independent applicable trials, report a binomial upper bound, not “100% safe.” The rough one-sided 95% rule of three is `3/n`; at `n=300` it is about 1%, and at 30 actual commit opportunities about 10%. Clustering reduces effective information. The true denominator must be stated. No limited-credit study can certify a very rare commercial failure target.

Separate timeout/provider failures, harness faults, abstention, invalid responses and semantic errors. End-to-end completion includes operational failures; additionally report conditional semantic scores with clear counts. Excluding errors or repeatedly rerunning until success would inflate reliability.

## 9. Failure criteria and decision gates

Stop or narrow the research claim if any of the following holds:

- Closest prior work already supplies the same correction/approval label space and experiments: publish a replication/extension, not a novelty claim.
- Independent reviewers cannot agree on target/correction/consent labels (proposed pilot target alpha ≥0.8 for key categorical labels): revise the task/manual before expansion; do not hide ambiguity through forced consensus.
- Proposed monitoring only beats the regex floor but not B3 or the prompt scaffold: no demonstrated systems advantage.
- Safety gains arise from withholding most actions or exceed the completion non-inferiority margin: report a tradeoff, not a successful integrity layer.
- Any counterexample violates the claimed formal invariant under the stated trusted assumptions: the protocol claim fails until repaired and rechecked.
- Speech gains disappear on human recordings or unseen authors: narrow claims to text/TTS; do not generalize to live voice.
- Dataset leakage, uncertain rights or lack of qualified mixed-language annotation prevents a valid held-out release: do not label it a research-grade Kannada-English benchmark.

## 10. Solo feasibility, milestones and commercial integration

A realistic initial effort is **10–14 focused weeks**, conditional on external annotation help and accessible baseline models. This is an estimate, not a delivery guarantee.

| Stage | Time budget | Exit artifact / go-no-go |
| --- | --- | --- |
| Scope and closest-work inspection | 1–2 weeks | Gap table versus pinned τ-Elicitation/voice/state-repair work; drop duplicate novelty claims |
| Pilot and task manual | 2 weeks | 60 excluded dialogues, independent annotation audit, model/cost/power estimates |
| Corpus and baseline harness | 3–4 weeks | Versioned splits, B1–B4, deterministic scoring and cached speech slice if affordable |
| Reference monitor and fault study | 2–3 weeks | Finite protocol specification, bounded checks and matched-extractor ablations |
| Frozen evaluation and write-up | 2–3 weeks | Paired results/CIs, negative findings, reproducible artifact and limitations |

No UI redesign, telephony deployment, fine-tuning, new ASR training or payments integration is needed initially. Use the existing Python/FastAPI stack and temporary SQLite sink. Budget the independent annotation and stronger-baseline access before spending on large speech runs. Without those resources, aim for a rigorous small workshop/replication study rather than an unsupported large benchmark claim.

**Commercial scenario (recommendation):** an intake agent drafts two maintenance tickets, hears an address correction, and proposes CRM writes. An integrity adapter receives transcript/proposals and stable issue IDs, records disputes/evidence, invalidates affected approvals, and releases only explicitly approved payload versions to a sandbox ticket sink. It can first run in shadow mode against recorded authorized sessions. Validate fewer wrong-address tickets against added clarification time and manual review workload, not attractive UI screenshots.

Customer discovery should test whether teams will supply de-identified error traces, integration hooks, operation IDs and a budget for review. No market demand, revenue or ROI has been verified. A customer-controlled integration still needs authentication, tenant isolation, retention policy, auditability, threat analysis and downstream reconciliation absent from today's app. The monitor cannot repair inaudible speech or an undetected semantic correction automatically.

## 11. Publication assessment and review action

**Strongest realistic direction:** benchmark/resource plus an empirical systems contribution on correction-to-consent integrity. A workshop or focused empirical paper is plausible after independent labels, strong baselines and reproducible failures; a larger benchmark paper needs substantially stronger scale/diversity and construct validation. A systems paper needs protocol-specific insight beyond conventional confirmation/idempotency and measured fault/overhead results. An algorithmic paper is currently the least credible direction: no new learning/inference algorithm has been established.

The current 80 tests and one synthetic live speech example are engineering evidence, not a publishability threshold. The first research milestone is to show that temporal consent/correction labels matter beyond final-state accuracy and the closest existing benchmark, including negative results. All hypotheses and monitor designs here remain unimplemented.

**Review disposition:** these three research documents are prepared for user review. Application/tests are unchanged. Commit and push only the three documents after that review; do not deploy or start the proposed implementation on the basis of this draft.
