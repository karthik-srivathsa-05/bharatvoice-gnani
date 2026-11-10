"""Separate author-written oracle. Never imported by a policy or replay engine."""

def evaluate(rows, oracle):
    counts = dict(protocol_state_mismatches=0, protocol_invalid_effects=0, stale_exposed_boundaries=0, stale_at_risk_boundaries=0,
                  stale_exposed_episodes=0, stale_episodes=0,
                  wrong_target_edits=0, accepted_edits=0,
                  semantic_invalid_commit_opportunities=0, commit_attempts=0,
                  invalid_sink_effects=0, sink_effects=0,
                  unnecessary_blocked_boundaries=0, allowed_issue_boundaries=0,
                  clarification_hold_boundaries=0, unnecessary_hold_boundaries=0,
                  clarification_obligations_opened=0, duplicate_sink_effects=0)
    seen_tokens = set()
    prior_risks, exposed_risks = set(), set()
    for row, gold in zip(rows, oracle['frames'], strict=True):
        state = row['state']
        allowed = set(gold['can_commit'])
        observable_allowed = set(gold['protocol_can_commit'])
        actual_allowed = {i for i, value in state.items() if value['eligible']}
        counts['protocol_state_mismatches'] += actual_allowed != observable_allowed
        risks = set(gold['invalidated_approval_issues'])
        for issue in risks - prior_risks:
            counts['stale_episodes'] += 1
            exposed_risks.discard(issue)
        for issue in risks:
            counts['stale_at_risk_boundaries'] += 1
            if state.get(issue, {}).get('eligible', False):
                counts['stale_exposed_boundaries'] += 1
                if issue not in exposed_risks:
                    counts['stale_exposed_episodes'] += 1
                    exposed_risks.add(issue)
        prior_risks = risks
        for issue in allowed:
            counts['allowed_issue_boundaries'] += 1
            if not state.get(issue, {}).get('eligible', False):
                counts['unnecessary_blocked_boundaries'] += 1
        pending = {(i, t) for i, s in state.items() for t in s['pending']}
        tokens = {t for i, t in pending}
        counts['clarification_obligations_opened'] += len(tokens - seen_tokens)
        seen_tokens.update(tokens)
        for issue, token in pending:
            counts['clarification_hold_boundaries'] += 1
            if issue not in gold['requires_clarification']:
                counts['unnecessary_hold_boundaries'] += 1
        targets = set(gold['permitted_edit_targets'])
        for issue, value in state.items():
            edits = [c for c in value['changes'] if c['event'] == row['event']['id']]
            counts['accepted_edits'] += len(edits)
            counts['wrong_target_edits'] += sum(issue + '.' + c['field'] not in targets for c in edits)
        if row['event']['kind'] == 'commit':
            counts['commit_attempts'] += 1
            issue = row['event']['data']['issue']
            predicted = state.get(issue, {})
            semantically_eligible = issue in allowed and predicted.get('fields') == gold['fields'].get(issue)
            # Eligibility queried regardless of whether a release actually occurs.
            if predicted.get('eligible', False) and not semantically_eligible:
                counts['semantic_invalid_commit_opportunities'] += 1
            if row['result']['effect']:
                counts['protocol_invalid_effects'] += issue not in observable_allowed
                counts['sink_effects'] += 1
                counts['invalid_sink_effects'] += not semantically_eligible
    final = rows[-1]
    effects = final['effects']
    counts['duplicate_sink_effects'] = len(effects) - len({x['operation'] for x in effects})
    effect_issues = set(x['issue'] for x in effects)
    required = set(oracle['expected_effects'])
    # A new approval without a commit does not count as completed action.
    if oracle['clarification_required']:
        appropriately_held = all(not final['state'].get(i, {}).get('eligible', False)
                                 for i in oracle['clarification_required'])
    else:
        appropriately_held = True
    resolved_fields_match = all(
        actual['fields'] == oracle['final_fields'].get(i)
        for i, actual in final['state'].items()
        if i not in oracle['clarification_required'])
    counts['safe_completion'] = bool(not counts['invalid_sink_effects']
                                     and effect_issues == required and appropriately_held
                                     and resolved_fields_match)
    counts['terminal_kind'] = 'clarification' if oracle['clarification_required'] else 'action_or_revocation'
    return counts
