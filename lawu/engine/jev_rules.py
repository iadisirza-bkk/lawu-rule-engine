"""Deterministic three-valued legal evaluator over the temporal rule graph.

Given the slot ledger, it expands only the *relevant* unknown variables (Shannon expansion over
era -> binary slots -> age atoms) until every branch decides a primary charge label. The result is a
probability table over (label, assignment) used for prediction, conditions and information gain.
"""
import math
from lawu.engine import law
from lawu.engine.slots import NUMERIC, DATE, SLOT_IDS

AGE_ATOMS = {  # global thresholds across all eras (13 / 15 for the victim, 18 for the actor)
    'S16': [(0.0, 13.0), (13.001, 15.0), (15.001, 18.0), (18.001, 120.0)],
    'S17': [(0.0, 18.0), (18.001, 120.0)],
}
NO_OFFENSE = 'NO_OFFENSE'
DEFAULT_PRIORITY = ('277', '276', '279', '278')


def label_of(sec, p):
    return f'{sec} ว.{p}'


def decide(results, priority):
    """Primary label = highest satisfied paragraph of the first satisfied section in `priority`.
    Returns None if the three-valued results do not yet fix that label."""
    for sec in priority:
        ps = sorted((p for (s, p) in results if s == sec), reverse=True)
        for p in ps:
            v = results[(sec, p)]
            if v is None:
                return None
            if v is True:
                return label_of(sec, p)
    return NO_OFFENSE


def _intersect(a, b):
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    return (lo, hi) if lo <= hi else None


class Table:
    """rows: list of (label, mass, assignment-dict)."""

    def __init__(self, rows, priors):
        self.rows = rows
        self.priors = priors
        tot = sum(m for _, m, _ in rows) or 1.0
        self.rows = [(l, m / tot, a) for l, m, a in rows]

    def dist(self):
        d = {}
        for l, m, _ in self.rows:
            d[l] = d.get(l, 0.0) + m
        return dict(sorted(d.items(), key=lambda kv: -kv[1]))

    def entropy(self):
        return _H(self.dist().values())

    def joint(self, var):
        """P(Y, var=v): variables not branched on a path are independent of Y there -> use prior."""
        j = {}
        for l, m, a in self.rows:
            if var in a:
                j.setdefault(a[var], {}).setdefault(l, 0.0)
                j[a[var]][l] += m
            else:
                for v, pv in self.priors.get(var, {}).items():
                    j.setdefault(v, {}).setdefault(l, 0.0)
                    j[v][l] += m * pv
        return j

    def info_gain(self, var):
        j = self.joint(var)
        h = self.entropy()
        cond = 0.0
        for v, ys in j.items():
            pv = sum(ys.values())
            if pv > 0:
                cond += pv * _H([x / pv for x in ys.values()])
        return max(0.0, h - cond)

    def conditions(self, describe):
        """For each label, the variable values shared by all its paths but not by all labels."""
        by = {}
        for l, m, a in self.rows:
            by.setdefault(l, []).append(a)
        common = {}
        for l, assigns in by.items():
            keys = set(assigns[0])
            for a in assigns[1:]:
                keys &= set(a)
            common[l] = {k: assigns[0][k] for k in keys if all(a[k] == assigns[0][k] for a in assigns)}
        out = {}
        for l, cv in common.items():
            diff = {k: v for k, v in cv.items()
                    if not all(k in common[o] and common[o][k] == v for o in common)}
            out[l] = [describe(k, v) for k, v in sorted(diff.items())]
        return out


def _H(ps):
    return -sum(p * math.log2(p) for p in ps if p > 0)


def era_weights(state, now_iso, lookback_years, static_latest=False, lag_prior=None):
    if static_latest:
        return {law.LATEST_ERA: 1.0}
    iv = state.slots[DATE].interval
    if iv is None and lag_prior:
        # v10: P(era) = sum over lags of P(lag) * [incident year = now - lag falls in era] (mid-year point)
        w = {}
        y = int(now_iso[:4])
        for l, p in lag_prior.items():
            e = law.era_of(f'{y - int(l):04d}-07-01')
            if e is not None:
                w[e] = w.get(e, 0.0) + p
        w = {e: v for e, v in w.items() if v >= 0.01}
        tot = sum(w.values())
        return {e: v / tot for e, v in w.items()}
    if iv is None:
        y = int(now_iso[:4])
        iv = (f'{y - lookback_years:04d}{now_iso[4:]}', now_iso)
    eras = law.eras_overlapping(iv[0], iv[1]) or [law.era_of(iv[1]) or law.LATEST_ERA]
    w = {e: law.era_overlap_days(e, iv[0], iv[1]) for e in eras}
    tot = sum(w.values())
    return {e: v / tot for e, v in w.items()}


def build_table(state, priors, *, now_iso, lookback_years=10, priority=DEFAULT_PRIORITY,
                static_latest=False, max_rows=20000, date_prior='window'):
    known_bin = {}
    for s in SLOT_IDS:
        if s in NUMERIC:
            continue
        st = state.slots[s].status
        known_bin[s] = True if st == 'supported' else False if st == 'denied' else None
    known_age = {s: state.slots[s].interval if state.slots[s].status == 'supported' else None for s in NUMERIC}
    rows = []
    lag = priors.get('_lag') if date_prior == 'lag' else None
    for era, w in era_weights(state, now_iso, lookback_years, static_latest, lag).items():
        relevant = law.era_slots(era)
        order = [s for s in ('S01', 'S04', 'S02', 'S16', 'S15', 'S12', 'S11', 'S13', 'S14', 'S23', 'S21', 'S20',
                             'S22', 'S03', 'S05', 'S10', 'S18', 'S17') if s in relevant]
        _expand(era, w, dict(known_bin), dict(known_age), {DATE: era}, order, priors, priority, rows, max_rows)
    return Table(rows, priors)


def _expand(era, mass, binary, ages, assign, order, priors, priority, rows, max_rows):
    if len(rows) >= max_rows:
        raise RuntimeError('expansion budget exceeded')
    lab = decide(law.evaluate_era(era, binary, ages), priority)
    if lab is not None:
        rows.append((lab, mass, assign))
        return
    pending = law.pending_slots(era, binary, ages)
    for var in order:
        if var not in pending:
            continue
        if var in NUMERIC:
            cur = ages.get(var)
            if cur is not None and var in assign:
                continue
            opts = []
            for atom in AGE_ATOMS[var]:
                iv = _intersect(atom, cur) if cur is not None else atom
                if iv is not None:
                    opts.append((atom, iv))
            if len(opts) <= 1 and cur is not None:
                continue
            pri = priors.get(var, {})
            tot = sum(pri.get(a, 1e-6) for a, _ in opts) or 1.0
            for atom, iv in opts:
                _expand(era, mass * pri.get(atom, 1e-6) / tot, binary, dict(ages, **{var: iv}),
                        dict(assign, **{var: atom}), order, priors, priority, rows, max_rows)
            return
        if binary.get(var) is None:
            p = priors.get(var, {}).get(True, 0.5)
            for v, pv in ((True, p), (False, 1 - p)):
                _expand(era, mass * pv, dict(binary, **{var: v}), ages, dict(assign, **{var: v}),
                        order, priors, priority, rows, max_rows)
            return
    rows.append(('UNRESOLVED', mass, assign))
