"""Temporal statute model for Criminal Code ss.276-279 built from step-3 artefacts.

* 27 section versions  -> research_steps_1_3/01_STATUTES/LAW/normalized/run_2026-10-07_v2/section_versions.json
* paragraph ASTs       -> research_steps_1_3/03_RULES/VERSIONED_RULES.json
* typed element attrs  -> research_steps_1_3/03_RULES/graph/data/nodes.jsonl (age thresholds, operators)

An *era* is a maximal date interval in which no version of 276-279 changes. Version selection uses
effective_from <= d < effective_to_exclusive (same rule as LAW-U-R build_graph.active()).
Only base_offence and aggravator paragraphs are outcome labels; definition / relief_exception /
sentencing_procedure layers are recorded but never produce a charge label.
"""
import json
from datetime import date
from functools import lru_cache
from lawu.common import STEP13

SECTIONS = ('276', '277', '278', '279')
LABEL_LAYERS = ('base_offence', 'aggravator')
FAR_PAST, FAR_FUTURE = '1957-01-01', '9999-12-31'

# Leaf-name -> slot mapping (engineering crosswalk, documented in REPORT.md).
LEAF_SLOT = {
    'threat': 'S11', 'force': 'S12', 'inability_to_resist': 'S13', 'mistaken_identity': 'S14',
    'sexual_purpose': 'S10', 'reverse_direction': 'S05', 'believed_weapon': 'S20',
    'firearm_explosive_have': 'S21', 'firearm_explosive_have_use': 'S21', 'weapon_use': 'S22',
    'joint_gang_conduct': 'S23', 'consent': 'S15', 'actor_genital_route': 'S01',
    'other_object_route': 'S03', 'other_instrument_intrusion': 'S03', 'other_body_object_intrusion': 'S03',
}
NEGATED_LEAF = {'spouse_exclusion': 'S18', 'gang_nonconsent': 'S15'}
# Leaves outside the 23-slot frame are assumed satisfied (documented assumption):
# actor ("ผู้ใด"), male_actor_female_child, court_relief_rule. object_person is evaluated by conduct_value (legal model v2).
ASSUMED_TRUE = {'actor', 'male_actor_female_child', 'court_relief_rule'}

# ---------------------------------------------------------------- legal model v2 (LEGAL_MODEL_V2.md, Amendment 13 addendum B)
# Meaning of "กระทำชำเรา" by era (276 ว.2 / 277 ว.2 from 2007-09-20; ม.1(18) from 2019-05-28 and 2025-12-30).
# S01 penis -> vagina · S04 penis -> anus/mouth · S03 other organ/object -> vagina/anus · S05 victim's penis made to penetrate
# the actor (all incl. attempt). อนาจาร has no statutory definition: any sexual act that is not ชำเรา in that era (S02 always).
DEF_2007, DEF_2019, DEF_2025 = '2007-09-20', '2019-05-28', '2025-12-30'


def rape_routes(era):
    start = ERAS[era][0]
    if start < DEF_2007:
        return ('S01',)                       # no statutory definition; ordinary meaning; victim "หญิง" (implied by S01)
    if start < DEF_2019:
        return ('S01', 'S04', 'S03', 'S05')   # 276 ว.2: actor's organ with vagina/anus/mouth, or any object with vagina/anus
    if start < DEF_2025:
        return ('S01', 'S04')                 # 1(18): actor's organ penetrating vagina/anus/mouth only
    return ('S01', 'S04', 'S03', 'S05')       # 1(18) new: + other organ/object, + causing the other to do the same


def indecency_routes(era):
    rape = set(rape_routes(era))
    return ('S02',) + tuple(s for s in ('S03', 'S04', 'S05') if s not in rape)


def _or(vals):
    return True if True in vals else None if None in vals else False


def conduct_value(sec, era, binary):
    if str(sec) in ('276', '277'):
        v = _or([binary.get(s) for s in rape_routes(era)])
        if ERAS[era][0] >= DEF_2007 and v is True and binary.get('S10') is False:
            return False                      # definition requires "เพื่อสนองความใคร่" (presumed unless denied)
        return v
    return _or([binary.get(s) for s in indecency_routes(era)])


def conduct_slots(sec, era):
    return rape_routes(era) if str(sec) in ('276', '277') else indecency_routes(era)


def _load():
    rules = json.loads((STEP13 / '03_RULES' / 'VERSIONED_RULES.json').read_text())
    nodes = {}
    with open(STEP13 / '03_RULES' / 'graph' / 'data' / 'nodes.jsonl', encoding='utf-8') as f:
        for line in f:
            n = json.loads(line)
            nodes[n['id']] = n
    versions = json.loads((STEP13 / '01_STATUTES' / 'LAW' / 'normalized' / 'run_2026-10-07_v2' /
                           'section_versions.json').read_text())
    return rules, nodes, versions


RULES, NODES, VERSIONS = _load()
RULE_BY_ID = {r['node_id']: r for r in RULES}
PARAS = [r for r in RULES if r['node_id'].startswith('th-criminal:27') and r['node_id'][12:15] in SECTIONS
         and '/p' in r['node_id']]


def para_meta(node_id):
    sec = node_id[12:15]
    ver = node_id.split('@')[1].split('/')[0]
    p = int(node_id.rsplit('/p', 1)[1])
    return sec, ver, p


def _eras():
    cuts = sorted({v['effective_from'] for v in VERSIONS if int(v['section']) in map(int, SECTIONS)} |
                  {v['effective_to_exclusive'] for v in VERSIONS if v['effective_to_exclusive']})
    eras = []
    for i, start in enumerate(cuts):
        end = cuts[i + 1] if i + 1 < len(cuts) else None
        eras.append((start, end))
    return eras


ERAS = _eras()          # list of (from_iso, to_exclusive_iso|None)
LATEST_ERA = len(ERAS) - 1


def era_of(d):
    for i, (a, b) in enumerate(ERAS):
        if a <= d and (b is None or d < b):
            return i
    return None


def eras_overlapping(lo, hi):
    """Eras intersecting the closed ISO date interval [lo, hi]."""
    return [i for i, (a, b) in enumerate(ERAS) if (b is None or lo < b) and a <= hi]


def era_overlap_days(i, lo, hi):
    a, b = ERAS[i]
    s, e = max(a, lo), min(b or FAR_FUTURE, hi)
    return max(1, (date.fromisoformat(min(e, '2100-01-01')) - date.fromisoformat(s)).days)


@lru_cache(maxsize=None)
def active_paragraphs(era):
    """{(section, p): rule} active at the era start, label layers only, plus all paragraphs for REF."""
    start = ERAS[era][0]
    out, allp = {}, {}
    for r in PARAS:
        iv = r['interval']
        if iv['effective_from'] <= start and (iv['effective_to_exclusive'] is None or start < iv['effective_to_exclusive']):
            sec, ver, p = para_meta(r['node_id'])
            allp[(sec, p)] = r
            if r['rule_layer'] in LABEL_LAYERS:
                out[(sec, p)] = r
    return out, allp


def version_ids(era):
    start = ERAS[era][0]
    return sorted(v['version_id'] for v in VERSIONS if v['effective_from'] <= start and
                  (v['effective_to_exclusive'] is None or start < v['effective_to_exclusive']))


@lru_cache(maxsize=None)
def age_thresholds(era):
    """Thresholds used by age leaves of the active label paragraphs: {'S16': [...], 'S17': [...]}"""
    out = {'S16': set(), 'S17': set()}
    _, allp = active_paragraphs(era)
    for r in allp.values():
        for leaf in leaves(r['ast']):
            a = NODES.get(leaf, {}).get('attrs', {})
            if leaf.split('/element:')[-1].startswith('age_') and a.get('number') is not None:
                out['S17' if a.get('person_role') == 'actor' else 'S16'].add(a['number'])
    return {k: sorted(v) for k, v in out.items()}


def leaves(ast):
    if ast['op'] == 'LEAF':
        yield ast['node_id']
    for c in ast.get('children', []):
        yield from leaves(c)


@lru_cache(maxsize=None)
def era_slots(era):
    """Slots referenced (directly or through REF) by the label paragraphs of an era."""
    out = set()
    labels, allp = active_paragraphs(era)

    def visit(ast, seen):
        if ast['op'] == 'LEAF':
            name = ast['node_id'].split('/element:')[-1]
            if name in LEAF_SLOT:
                out.add(LEAF_SLOT[name])
            elif name in NEGATED_LEAF:
                out.add(NEGATED_LEAF[name])
            elif name.startswith('age_'):
                a = NODES.get(ast['node_id'], {}).get('attrs', {})
                if a.get('number') is not None:
                    out.add('S17' if a.get('person_role') == 'actor' else 'S16')
            elif name == 'conduct':
                out.update(conduct_slots(ast['node_id'][12:15], era))
                if ast['node_id'][12:15] in ('276', '277') and ERAS[era][0] >= DEF_2007:
                    out.add('S10')
        elif ast['op'] == 'REF':
            ref = RULE_BY_ID.get(ast['node_id'])
            if ref and ast['node_id'] not in seen:
                visit(ref['ast'], seen | {ast['node_id']})
        for c in ast.get('children', []):
            visit(c, seen)

    for r in labels.values():
        visit(r['ast'], frozenset())
    return frozenset(out)


# ---------------------------------------------------------------- three-valued evaluation
def age_leaf_value(attrs, interval):
    """Exact-age interval [lo, hi] vs threshold. True/False/None (unknown)."""
    n, op = attrs.get('number'), attrs.get('operator_text')
    if n is None:
        return True
    if interval is None:
        return None
    lo, hi = interval
    if op in ('ไม่เกิน', 'ยังไม่เกิน'):
        return True if hi <= n else False if lo > n else None
    if op == 'กว่า':
        return True if lo > n else False if hi <= n else None
    raise ValueError(f'unhandled age operator {op}')


def eval_ast(ast, env, sec, _seen=frozenset()):
    """env: callable(leaf_node_id, section) -> True/False/None."""
    op = ast['op']
    if op == 'LEAF':
        return env(ast['node_id'], sec)
    if op == 'REF':
        ref = RULE_BY_ID.get(ast['node_id'])
        if ref is None or ast['node_id'] in _seen:
            return None
        return eval_ast(ref['ast'], env, ast['node_id'][12:15], _seen | {ast['node_id']})
    vals = [eval_ast(c, env, sec, _seen) for c in ast.get('children', [])]
    if op == 'AND':
        return False if False in vals else None if None in vals else True
    if op == 'OR':
        return True if True in vals else None if None in vals else False
    if op == 'NOT':
        v = vals[0]
        return None if v is None else not v
    raise ValueError(op)


def make_env(binary, ages, era):
    """binary: {slot: True/False/None}; ages: {'S16': interval|None, 'S17': interval|None}; era fixes the meaning of the
    conduct words (legal model v2)."""
    def env(leaf, sec):
        name = leaf.split('/element:')[-1]
        if name in ASSUMED_TRUE:
            return True
        if name == 'conduct':
            return conduct_value(leaf[12:15], era, binary)
        if name == 'object_person':
            # "หญิง"/"เด็กหญิง" (texts before 2007-09-20): satisfied by the only ชำเรา route of that era (S01, penis into
            # vagina); the conduct leaf already carries it. Other texts: "ผู้อื่น"/"บุคคล"/"เด็ก" -> any person.
            g = NODES.get(leaf, {}).get('attrs', {}).get('gender_restriction')
            return True if g is None else binary.get('S01')
        if name in LEAF_SLOT:
            return binary.get(LEAF_SLOT[name])
        if name in NEGATED_LEAF:
            v = binary.get(NEGATED_LEAF[name])
            return None if v is None else not v
        if name.startswith('age_'):
            a = NODES.get(leaf, {}).get('attrs', {})
            return age_leaf_value(a, ages.get('S17' if a.get('person_role') == 'actor' else 'S16'))
        return None  # unmapped leaf: stays unknown (never silently true)
    return env


def pending_slots(era, binary, ages):
    """Slots behind the leaves that evaluate to unknown in the era's label paragraphs (used to branch only on elements that
    can still change the label; legal model v2 made the fixed-order expansion too large)."""
    labels, _ = active_paragraphs(era)
    base = make_env(binary, ages, era)
    out = set()

    def env(leaf, sec):
        v = base(leaf, sec)
        if v is None:
            name = leaf.split('/element:')[-1]
            if name in ('conduct', 'object_person'):
                out.update(x for x in conduct_slots(leaf[12:15] if name == 'conduct' else '276', era) if binary.get(x) is None)
            elif name in LEAF_SLOT:
                out.add(LEAF_SLOT[name])
            elif name in NEGATED_LEAF:
                out.add(NEGATED_LEAF[name])
            elif name.startswith('age_'):
                a = NODES.get(leaf, {}).get('attrs', {})
                out.add('S17' if a.get('person_role') == 'actor' else 'S16')
        return v
    for k, r in labels.items():
        eval_ast(r['ast'], env, k[0])
    return out


def evaluate_era(era, binary, ages):
    """{(section, p): True/False/None} for label paragraphs of the era."""
    labels, _ = active_paragraphs(era)
    env = make_env(binary, ages, era)
    return {k: eval_ast(r['ast'], env, k[0]) for k, r in labels.items()}


def paragraph_exists(era, sec, p):
    return (str(sec), int(p)) in active_paragraphs(era)[0] or (p in (None, 1) and any(
        k[0] == str(sec) for k in active_paragraphs(era)[0]))
