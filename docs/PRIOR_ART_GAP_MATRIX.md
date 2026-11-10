# Pinned prior-art gap matrix

**Methodological revision — 11 November 2026 (IST).** Conclusions are bounded to the artifacts below, not claims about entire literatures or undisclosed implementations. This matrix supersedes the initial abstract-led gap discussion in [PRIOR_ART.md](PRIOR_ART.md). No external system was executed. Sections, schema and scoring definitions were inspected beyond abstracts. **P** = present; **L** = limited/related; **ND** = not defined in the inspected evaluation; **U** = unverified. ND does not mean technically impossible or absent everywhere.

## Pins and inspection record

| Key | Immutable publication / source pin | Inspected evidence |
| --- | --- | --- |
| T | Ray & Barres, τ-Elicitation, 11 September 2026, [arXiv 2609.13602v1](https://arxiv.org/html/2609.13602v1) | §§3.1–3.3, §4 matched runs, composition/repair discussion; not just abstract |
| TC | Official repository snapshot [`5e1fcb00da17c3e00cef86f9df703a704d46896a`](https://github.com/sierra-research/tau2-bench/tree/5e1fcb00da17c3e00cef86f9df703a704d46896a) on paper-linked branch | [main policy](https://github.com/sierra-research/tau2-bench/blob/5e1fcb00da17c3e00cef86f9df703a704d46896a/data/tau2/domains/intake/main_policy.md), [tools](https://github.com/sierra-research/tau2-bench/blob/5e1fcb00da17c3e00cef86f9df703a704d46896a/src/tau2/domains/intake/tools.py), [environment](https://github.com/sierra-research/tau2-bench/blob/5e1fcb00da17c3e00cef86f9df703a704d46896a/src/tau2/domains/intake/environment.py), [reproduction README](https://github.com/sierra-research/tau2-bench/blob/5e1fcb00da17c3e00cef86f9df703a704d46896a/papers/tau-intake/v1/reproduction/README.md), [prompt manifest](https://github.com/sierra-research/tau2-bench/blob/5e1fcb00da17c3e00cef86f9df703a704d46896a/papers/tau-intake/v1/reproduction/prompts/manifest.json) |
| A | Li, Chen & Wei, Aegis, 7 February 2026, [arXiv 2602.07379v1](https://arxiv.org/html/2602.07379v1) | §§3.1–3.3, §4, Appendix A headings and B; prompt content under Appendix A is not rendered in retrieved HTML, so exact prompt controls remain U |
| V | Lee & Pfister, AVERT, 1 September 2026, [arXiv 2609.01828v1](https://arxiv.org/html/2609.01828v1) | §§3.1, 3.4–3.6, 4.1–4.4, §5 and operator-slot appendix |
| C | W3C VoiceXML 2.0, [dated Recommendation, 16 March 2004](https://www.w3.org/TR/2004/REC-voicexml20-20040316/) | §2.1.5 mixed-initiative example and §5.3.3 clear; dated specification, not a mutable vendor page |
| D | Kim et al., SOM-DST, [ACL 2020 archival PDF](https://aclanthology.org/2020.acl-main.53.pdf), July 2020 | §3 state/operations, §4 setup and §5.1 JGA; fixed archival publication, not current repository code |

Publication pins do not pin software. For A/V no code release was audited here; claims about executable evaluators beyond the paper remain U. D is a representative DST method, not all DST. C is a conventional-workflow design precedent, not an empirical benchmark of all commercial systems. Lex/Temporal/Stripe references in the review remain useful living documentation but are not treated as frozen evaluation artifacts.

TC's manifest maps historical cells to content-addressed prompts and task snapshots; the repository's current policy is not assumed identical to every historical run. The detached audio corpus and historical evaluator were not reproduced. The archived scaffold policy [`a8281c…`](https://github.com/sierra-research/tau2-bench/blob/5e1fcb00da17c3e00cef86f9df703a704d46896a/papers/tau-intake/v1/reproduction/prompts/objects/agent_policy/a8281c6235f671679443d1e21863532b77278a0d27e688fbc6fdf81b2e30509f.md) was also read and matches the inspected scaffold policy. Exact consent enforcement in every archived cell remains U.

## Evaluation dimensions

“Approval invalidation” means a later correction makes a prior approval unusable, not merely asking for initial consent. “Correction scope” distinguishes issue identity and field, not just choosing a new slot value. “Multiple issue instances” means distinct same-service records in one dialogue, not multiple fields or domains. “Temporal exposure” measures the interval/opportunities during which obsolete approval remains usable, independently of final state.

| Artifact | Approval invalidation | Correction scope | Multiple issue instances | Temporal exposure |
| --- | --- | --- | --- | --- |
| T/TC | **L:** renewed read-back after correction is policy; tool confirmation is self-report, not a checked approval token | **P/L:** self-repair and wrong-field answers are covered; record/field targeting exists | **L:** linked two/three fields; inspected toolkit has one callback order, not a same-service issue-instance benchmark | **ND:** first/final capture and verification effort are scored; no version-bound stale-approval interval metric is defined in §3.3 |
| A | **U/ND:** published attack metrics do not define payload-version invalidation; exact prompt handling unverified | **L:** malicious workflow/record manipulation; no dedicated benign repair-target score defined | **U:** domains and records do not establish controlled same-service multiplicity evaluation | **ND:** §3.3 attack-outcome metrics do not define stale-consent exposure |
| V | **ND:** no approval/commit state in §3.1 task | **P/L:** slot-restricted edits and collateral-edit analysis; not the same as user repair intent | **ND:** evaluated state is schema slot/value pairs, not a defined issue-instance/approval model | **ND:** causal per-turn state scores, not stale-approval intervals |
| C | **P/L:** example clears data and go-ahead together; correction-sensitive re-confirmation is conventional | **P/L:** named variables, grammars, conditions and explicit clearing | **L:** forms/variables can encode separate records; no multiplicity benchmark | **ND:** specification supplies control constructs, no exposure evaluation |
| D | **ND:** defined memory contains domain-slot values, no approvals | **P:** per-slot carry/delete/update operations | **L/ND:** multiple domains; one domain-slot key does not define repeated issue IDs | **ND:** JGA and state-operation analysis, no approval-exposure score |

## What the evidence warrants

- **T/TC:** T §§3.2–3.3 explicitly includes repairs, wrong-field answers, multi-field composition and recovery diagnostics. TC `submit_fields` accepts a confirmation boolean without checking it; `log_capture` is stateless. The narrow missing measurement is a version-bound exposure interval in the inspected scoring, not “no confirmation” or “no corrections.”
- **A:** §3.3 evaluates adversarial outcome rates after transcript judging. Benign correction-to-approval semantics are not specified there. That bounded scoring gap does not exclude individual attacks involving old instructions or misdirected records.
- **V:** §§3/4/5 already ground and restrict slot edits and analyze harmful changes. Treat scope-sensitive editing as overlap. Its defined task lacks a consent state, so this publication cannot evaluate approval invalidation without extension.
- **C:** the weather form clears `start city state go_ahead`; `<clear>` revisits variables. Ordinary workflow logic can invalidate approval. The proposed system must beat a competent implementation of this idea, not claim it invented invalidation.
- **D:** fixed domain-slot memory and JGA establish update tracking and temporal state evaluation, but not consent exposure. A representative paper's scope cannot justify “DST never handles corrections or multiple entities.”

## Remaining checks and novelty gates

| Candidate distinction | Current finding | Required decision before a novelty claim |
| --- | --- | --- |
| Corrections, confirmation, multi-field capture | Already overlap | Remove generic novelty claims |
| Per-issue consent obligations across ambiguous corrections | Potential narrow extension, not established novelty | Compare equal-information B3 and proposed policies; audit pinned archived prompts/evaluator and at least one additional modern state/workflow system |
| Same-category issue identities plus approval timelines | Not defined as a controlled axis in inspected tasks; wider absence U | Verify dataset schemas/task samples, then publish a task-level mapping rather than relying on naming |
| Exposure despite identical final state | Not defined by inspected scoring | Demonstrate independently labeled trace pairs; check whether existing traces can be re-scored before collecting a new benchmark |
| New monitor guarantees | Conventional mechanisms overlap substantially | If B3 matches it, withdraw systems-superiority claim; publish benchmark/replication or diagnostic results |

No “first”, general absence, patent novelty, or publication guarantee follows from this matrix. Uninspected code, non-rendered prompts and evolving releases remain explicit uncertainty. This review inspected sources; it did not rerun T/A/V/D or implement the proposed protocol.
