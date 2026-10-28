"""Question-selection policies.

* eig      : argmax_S IG(S) = H(Y) - sum_v P(S=v) H(Y|S=v) over the rule-expansion table (proposed)
* fixed    : ask slots 1..23 then DATE in form order (Ablation B)
* random   : random order of unasked slots, seeded (control)
Every policy first asks to confirm a slot in conflict. EIG stops when the label is unique,
when max IG < epsilon, or when nothing informative remains askable.
"""
import random
from lawu.engine.slots import SLOT_IDS, DATE

ASKABLE = SLOT_IDS + [DATE]


def askable(state, asked, refine_age=False):
    out = [s for s in ASKABLE if not state.known(s) and not state.slots[s].unavailable and s not in asked]
    if refine_age:  # a known age interval that still straddles a legal threshold may be asked once more
        for s in ('S16', 'S17'):
            sl = state.slots[s]
            if sl.status == 'supported' and straddles(s, sl.interval) and asked.count(s) < 2 and s not in out:
                out.append(s)
    return out


def straddles(slot, iv):
    from engine.jev_rules import AGE_ATOMS
    return iv is not None and sum(1 for a in AGE_ATOMS[slot] if max(a[0], iv[0]) <= min(a[1], iv[1])) > 1


def threshold_in(slot, iv):
    from engine.jev_rules import AGE_ATOMS
    for a in AGE_ATOMS[slot]:
        if iv[0] <= a[1] < iv[1]:
            return int(round(a[1]))
    return None


def choose(policy, state, table, asked, *, epsilon=1e-3, rng=None, stop_when_unique=True, refine_age=False):
    """Returns (action, slot, info) with action in {'confirm', 'ask', 'stop'}."""
    conflicts = state.conflicts()
    if conflicts:
        return 'confirm', conflicts[0], dict(reason='conflict')
    dist = table.dist()
    unique = len(dist) == 1
    if policy == 'eig':
        if unique and stop_when_unique:
            return 'stop', None, dict(reason='unique_label', entropy=0.0)
        cands = askable(state, asked, refine_age)
        gains = {s: table.info_gain(s) for s in cands}
        if not gains:
            return 'stop', None, dict(reason='nothing_askable', entropy=table.entropy())
        best = max(gains, key=lambda s: (gains[s], -ASKABLE.index(s)))
        if gains[best] < epsilon:
            return 'stop', None, dict(reason='no_informative_question', entropy=table.entropy(),
                                      top_gains=_top(gains))
        return 'ask', best, dict(reason='max_eig', gain=gains[best], entropy=table.entropy(), top_gains=_top(gains))
    cands = askable(state, asked)
    if not cands:
        return 'stop', None, dict(reason='form_complete', entropy=table.entropy())
    if policy == 'fixed':
        return 'ask', cands[0], dict(reason='form_order', entropy=table.entropy())
    if policy == 'random':
        return 'ask', (rng or random).choice(cands), dict(reason='random', entropy=table.entropy())
    raise ValueError(policy)


def _top(gains, k=5):
    return [(s, round(g, 4)) for s, g in sorted(gains.items(), key=lambda kv: -kv[1])[:k]]
