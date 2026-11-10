# Research proposal: correction scope and temporal consent integrity

**Revised after provisional external approval — 11 November 2026 (IST).** This is a research plan, not protocol implementation. Application baseline: `7f786412523a232c9c39654c9184d4c7fda65290`. Work stays on `research/review-drafts`. See [audit](RESEARCH_AUDIT.md), [prior art](PRIOR_ART.md), [pinned gap matrix](PRIOR_ART_GAP_MATRIX.md), and [executable F1–F9 specifications](COUNTEREXAMPLE_SPEC.md).

## 1. Thesis, uncertainty and scope

**Hypothesis:** retaining issue/field-scoped unresolved-repair obligations may reduce the time obsolete approval remains usable, compared with a competent conventional workflow receiving the same evidence, without unacceptable completion loss or clarification burden.

This hypothesis is provisional. Ordinary workflows already invalidate approvals; evidence-aware state editing and repair benchmarks already exist. A contribution must survive comparison with B3, not merely the current regex prototype. If B3 matches the monitor, narrow the work to a benchmark extension, replication or negative-result study. No algorithmic novelty, “first” claim or publication guarantee is established.

The initial study is English, text-first, with cached Gnani transcripts as a diagnostic slice. One genuine synthetic English transcription is historical integration evidence, not a language benchmark. Human speech and Kannada-English evaluation require separately authorized data and qualified independent annotation. No full-duplex, production deployment, new ASR training, payment or real authority integration is planned.

## 2. Two correctness definitions and the guarantee boundary

Let actual latest user intent at event boundary `t` be `U_t`. It is latent, can be ambiguous, and is not necessarily identical to spoken words, an ASR transcript, or an annotator's interpretation. Annotated gold `G_t` is an independently adjudicated, uncertainty-bearing estimate of `U_t` from scenario instructions and authorized source dialogue/audio. Preserve set-valued/unknown intent when agreement is not justified; never define semantic correctness as agreement with the system's own extracted state.

The monitor sees only `O_≤t`: ordered source events it receives, extractor proposals, issue IDs, field candidates, evidence references, repair/uncertainty signals, approval-source events, versions, hashes and sink acknowledgments. Proposed state has per-field `{unknown, resolved, disputed}` statuses. Approval binds actor, issue, canonical payload digest and revision, not an unscoped “yes”. These event types and approval tokens do not yet exist in the application.

**Protocol correctness** is conformance to a published transition relation `P` over `O_≤t`. A commit is protocol-valid if its issue is observably complete/resolved, it has matching current explicit approval, no observable invalidation/repair obligation remains, event order is valid, and the simulated sink's operation-ID rule is satisfied.

**Semantic correctness** is consistency with latest actual intent `U_t`; experiments can only estimate it against `G_t`. A semantically valid action also requires correctly scoped user authorization as annotated independently of the extraction. A protocol-valid action can be semantically wrong; an accurate payload can be protocol-invalid if no approval occurred. Report both axes, including their intersection, rather than using one as a proxy for the other.

### Conditional properties to investigate, not achieved guarantees

Given complete event delivery, a trusted ordering/durable journal, correct canonicalization, an authenticated approval source faithfully bound to the reviewed payload, atomic eligibility checks, and a sink durably enforcing operation IDs, a correctly implemented monitor could enforce:

1. Only declared issue/field targets are mutated; rejected mentions and accepted transitions are recorded distinctly.
2. Observed material edits and unresolved repair obligations invalidate approval for affected or unresolved candidate issue IDs before the next action eligibility check.
3. No action is released for missing/disputed fields, unmatched old approvals, or unresolved obligations.
4. Repeated delivery of one logical operation has at most one sink effect within the sink's deduplication contract.

These are proposed observable invariants, not proofs. A declared target may itself be wrong. Evidence-reference validity establishes traceability, not entailment. A word span or confidence score does not certify actual intent. A missed correction, lossy ASR, false “resolved” proposal, unreceived utterance, actor impersonation, misleading read-back, bypassing client or compromised sink defeats the relevant assumptions. The monitor cannot infer an unobserved intent change or guarantee that a person understood a review screen. Counterexamples under valid assumptions falsify an invariant; failures outside them must be reported as boundary failures rather than hidden exclusions.

At receipt of an utterance, the future gate may suspend eligible actions for plausibly affected issues pending interpretation. A delayed or missing repair signal must be evaluated. Starting exposure measurement only after successful repair recognition would hide detection failures. Global suspension on every utterance is a reasonable conservative conventional control and must be tested for its burden.

## 3. B3 as principal comparator: equal information first

**B3** is a competent conventional stateful workflow, not the existing boolean gate. It uses explicit read-back, revision/content-bound approval, revision invalidation after accepted changes, blocking for missing/disputed fields and observable unresolved repairs, durable ordered state, atomic eligibility checks and an idempotent simulated sink. Generic acknowledgment is not semantic resolution. Give B3 a reasonable policy-development budget and document it before held-out runs.

**Proposed monitor M** maintains durable obligations keyed by repair-event ID, candidate issue IDs, field, old/rejected candidates, evidence references, resolution criteria and approval invalidation state. A repair obligation stays open despite changes to unrelated fields or a generic clarify acknowledgment. Scope ambiguity suspends approvals for candidate targets until explicit resolution or retraction. M cannot close an obligation from gold labels.

| Input/control | Principal B3 versus M contract |
| --- | --- |
| Extractor/model | Identical frozen extractor, prompts, outputs, signal omissions, seeds and normalization |
| Source input | Same original text/cached ASR and arrival schedule; no extra audio, oracle spans or gold targets for M |
| Evidence | Both receive the same candidate scope, span references, rejected values, repair/uncertainty flags and confidence if provided |
| Approval source | Same trusted actor and payload-bound review events; no speech yes/no classifier advantage; identical stale/duplicate approval events |
| Faults and probes | Same restart/retry/reordering schedule, operation IDs, sink and hypothetical commit-probe checkpoints |
| Policy resources | Same development traces, clarification budget and tuning access; publish differences |

**Additional information versus additional memory:** compared with a value-only workflow, M wants repair-event identity, candidate target sets, unresolved status and resolution links. This is additional structured annotation, not inherently private information. A competent B3 could reasonably obtain and persist it from the same extractor. Therefore the principal comparison exposes it to both. The intended treatment is how obligations are retained and checked across time, not secret access to better semantics. If B3 implements the same ledger, the methods may become behaviorally identical; that is an important novelty-failure result.

A secondary factorial study may compare value-only versus enriched proposals crossed with B3 versus M. Attribute any gain from enriched proposals to representation/extraction, and any gain from the ledger to policy conditional on identical inputs. Include B3 with conservative suspend-on-inbound-utterance/re-confirm behavior. Oracle-repair/proposal replay is diagnostic only. Never give M gold repair flags and B3 ordinary extraction in a superiority comparison.

B0 (frozen BharatVoice and first-match baseline) is historical context only. B1 full-history schema-constrained extraction and B2 incremental state-operation extraction supply two extractor conditions if budget permits. B4 is a pinned repair/read-back prompt adaptation. They do not replace B3 as the principal protocol comparator. Gnani credentials do not supply an extraction LLM: secure model access/budget or report that baseline limitation. Do not assume cloud GPU capacity or use mocks as strong competitors.

Fixed-trace replay holds events/proposals identical and isolates protocol effects. Interactive trials necessarily diverge after different clarification choices; use the same initial scenario, response oracle, budget and seed, but label them as paired scenario trials, not identical-trace experiments. Do not force a caller to answer a question it was never asked.

## 4. Staged study and scale gates

### Stage A: 60-dialogue exploratory pilot

Exclude all 60 from later evaluation. Cover F1–F9, straightforward no-correction controls, repeated same-service issues, ambiguous new-versus-update requests, unsupported identifiers and short approval/restart races. Use pilot findings to refine semantics, estimate annotation disagreement, timing, API/token costs and paired outcome discordance. This is discovery, not confirmatory hypothesis testing.

Two people independently annotate repair targets, uncertainty and consent validity; report raw agreement and an appropriate categorical statistic such as Krippendorff's alpha with uncertainty. Proposed progression target is alpha ≥0.8 on principal categorical labels, with disagreements/types and sample counts published. That threshold is a planning rule, not a guarantee of valid gold. If independent review is unavailable, label data provisional and do not advance research-grade claims. Unresolved interpretations remain alternatives, not forced consensus.

### Stage B: 100–150-family feasibility study, conditional on Stage A

Choose and freeze the total and stratification before collection; an example is 120 families: 40 development and 80 sealed feasibility evaluation. Keep the 60 pilot dialogues excluded. Family, not turn/paraphrase/retry, is the independent unit. Split by scenario author/template/entity and by speaker for any audio, with no family variants across splits. Include benign controls and mark deliberately enriched failure cases as stress tests, not prevalence samples.

Use 3–8 turns where appropriate; balance repair scope, approval timing, ambiguity and no-repair controls without an unaffordable full factorial. Record case provenance, uncertainty, issue IDs, source spans, rejected mentions versus mutations, per-boundary consent validity, policy-observable flags and expected sink effects. Independently double-annotate the evaluation set and adjudicate blind to system identity.

Begin with text and existing authorized cached ASR. A budget-gated speech slice can use 20–30 short consented human utterances with context and matched TTS controls; it is diagnostic, not speaker-population evidence. Record speaker/author clustering. Cache sanitized API output, request/model/time metadata and audio hashes; count failures and billed minutes, check actual account pricing and use a fixed retry cap. Machine translation or English TTS cannot validate Kannada-English semantics.

### Stage C: no commitment to 600 families

The earlier 600-family plan is withdrawn as a committed target. Expansion requires evidence of label agreement, meaningful B3/M discordance, affordable annotation/model costs, power simulation for a prespecified practically relevant effect, licensing/consent readiness and a distinct gap after pinned-source review. Seek separate authorization and preregistration. If 100–150 families cannot resolve rare-event effects, report feasibility uncertainty rather than quietly treating it as a powered safety benchmark.

## 5. Hypotheses, primary outcomes and denominators

All B3/M comparisons are paired within scenario family, extractor outputs, confirmation source and fault schedule. No experimental gains have been measured. The pilot/feasibility study estimates effects; confirmatory claims require prospective power and a frozen analysis plan.

| Question / hypothesis | Primary measurement and denominator | Paired analysis / guardrail |
| --- | --- | --- |
| H1: M reduces stale-consent exposure beyond B3 | For each gold invalidation opportunity after an approval, fraction with any boundary where that obsolete approval remains usable; opportunities form a fixed shared denominator | Pair per-family rates/counts; separately report observable-signal versus missed-signal strata; never drop missed repairs |
| H1-duration diagnostic | Exposed event-boundary intervals / all at-risk intervals, and event-count duration from gold invalidation to unusability or trace end | Common ordered event clock and predeclared eligibility probes; right-censor unresolved tails, do not score them as repaired; wall time only where arrival clocks are comparable |
| H2: scope obligations reduce wrong-target edits | Accepted mutations to gold-unaffected issue/fields / all accepted mutations; also wrong-target edits / gold repair opportunities and affected families / all families | Pair both systems; report zero-action denominators as undefined, not zero error; retained old values and extra/omitted issues separately |
| H3: exposure reductions matter to action quality | Semantic-invalid logical sink effects / all logical sink effects; additionally invalid effects / fixed eligible scenario opportunities and affected families / all evaluated families | Judge against independent uncertainty-bearing intent/consent gold; report protocol-valid-but-semantic-invalid separately; same sink/probe plan |
| H4: gains do not simply suppress useful actions | Safe task completion / all predeclared eligible scenarios | Pair family success; completed means correct authorized outcome or gold-required clarification/non-action for genuinely unresolved scenarios; report action-completion and appropriate-abstention strata separately |
| H4-burden | Clarification questions / all scenarios and / completed action scenarios; redundant reviews / all review opportunities; median/p95 latency | Include failures/timeouts, not only successful calls; compare interactive trials separately from fixed replay |

Do not merge these into one reliability score. Supporting outcomes are final/all-turn JGA, repair target accuracy, unsupported-value rate, recovery equivalence and duplicate effects per logical operation ID. Stable issue linkage must not match away collateral edits; canonicalization must not collapse distinct identifiers (House 24/7 ≠ House 24). Repeated-run all-success and at-least-one-success are different statistics.

**Exposure definition:** a gold invalidation opportunity begins when the latest user correction would invalidate an existing approval in the scripted scenario, whether recognized or not. Observe eligibility immediately after source-event receipt, after interpretation, before simulated release, after restart and after any resolution. Count exposure even without a commit. For policy-only analysis also start a second clock at the first observable repair event; report both rather than using the easier clock as the primary measure. Omitted event delivery and extractor latency are visible failure strata. A monitor-only theorem concerns its observable clock; the semantic exposure metric concerns the scenario clock.

At identical boundaries, a side-effect-free shadow eligibility query can test whether each gate would release the old payload. Such a query is a proposed harness feature, absent today. Actual simulated sink effects are scored separately. If source ordering is unknown, annotate interval uncertainty and give bounds rather than false timing precision. Exposure ending at reapproval requires gold-valid explicit resolution and current-payload consent, not a generic acknowledgment.

Proposed decision margins, to be frozen after pilot and before feasibility evaluation: five percentage points for completion non-inferiority and at most one additional clarification question per scenario on average. They are not achieved results; revise them based on pilot usability/cost justification before preregistration, never after inspecting sealed outcomes. Practical exposure/error targets require pilot event-frequency and discordance estimates; the earlier fixed relative-30% claim is withdrawn.

## 6. Analysis, validation and failure gates

Use paired absolute differences with 95% family-cluster bootstrap CIs, retaining linked variants/fault runs together; if speech speakers span families use an appropriate hierarchical/multiway approach or report speaker-specific sensitivity. Use exact McNemar for one binary outcome per independent family; otherwise clustered paired permutation/bootstrap. Record n for every rate. Repeated model seeds are within-family replicates, not extra data. Use a small predeclared confirmatory family with multiplicity control only if powered; label feasibility analyses exploratory. No optional collection until significance.

Use pilot discordance and anticipated event counts to simulate power before choosing a later confirmatory sample. In an 80-family sealed slice, zero independent errors implies only a rough one-sided 95% bound of 3/80 (3.75%), worse for fewer commits/clustering; it does not certify commercial rare-event safety. Undefined ratios and confidence bounds must be explicit. Publish exclusions, timeouts, provider errors and all failed retries. Compute unconditional completion including operational failure, plus conditional language diagnostics with separate counts.

Preregister these **negative-result/novelty-failure gates**:

- If equal-information B3 matches M within justified practical margins on exposure/errors/completion/burden, stop systems-superiority claims and narrow to benchmarking, replication or negative results. Wide intervals imply inconclusive evidence, not equivalence.
- If gains disappear against B3 with reasonable repair flags/ledger or conservative suspension, credit ordinary workflow engineering; do not call it a new protocol.
- If gains require extra oracle signals or an improved extractor unavailable to B3, attribute them to information/extraction, not the monitor.
- If pinned existing tasks/evaluators already support the proposed labels, extend/re-score them rather than claim a new benchmark gap.
- If semantic errors remain while protocol invariants hold, report the semantic limit; no “verified intent” claim.
- If abstention/latency/review burden breaches frozen utility margins, report the tradeoff, not blanket reliability improvement.
- If annotation agreement, cost or power fails the scale gate, do not expand the corpus. If rights or qualified language review are missing, omit that slice.
- If any claimed observable invariant fails under valid assumptions, reject that protocol claim. Source-loss and actor/sink failures remain explicit limits even if outside a bounded proof.

## 7. Future experiments and feasibility

After separate implementation authorization, test: B3/M crossed with value-only/enriched proposals; repair-obligation persistence versus acknowledgment reset; scope ledger versus conventional dirty-state tracking; gold versus cached ASR; real versus oracle repair flags; ordinary versus conservative global suspension; and same-issue versus repeated-instance ambiguity. Hold approval/version/digest and sink deduplication protections constant in the principal comparison. Removing them is only a secondary conventional-safeguard ablation.

Use the same fault schedule before/after save, approval, repair receipt, invalidation, sink delivery and acknowledgment, plus duplicate IDs and stale approvals. Restart/replay is not speech barge-in. A future finite model may check declared bounded states/interleavings; no model checking, fault experiment or new-protocol run has occurred in this revision. F1–F9 executable current-API reproductions are documentation validation only.

A solo plan is 1–2 weeks pinned-scope/manual work, 2–3 weeks pilot and independent annotation, then a go/no-go; conditionally 3–5 weeks feasibility collection/harness and 1–2 weeks analysis. These are estimates dependent on baseline model access and external annotation help. UI work is not on the critical path. Defer corpus expansion, new speech spending and commercial hardening until justified.

A plausible commercial setting is shadow review of address corrections before CRM ticket writes. A customer would need to supply stable issue/operation IDs, trustworthy review events and de-identified authorized traces; value would be fewer wrong tickets at acceptable review cost. Demand/ROI and production security remain unverified. Today's application supplies neither a real action sink nor authenticated consent tokens.

## 8. Research disposition

The direction is provisionally approved; implementation is not. Strongest plausible publication route remains an independently annotated benchmark extension or empirical systems/negative-result paper. A systems contribution depends on beating competent B3 with equal information; an algorithmic contribution is not established. All new protocol properties, datasets, hypotheses and commercial advantages remain proposed. This revision commits research documents only; no merge, deployment or application change is authorized.
