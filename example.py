"""Minimal example: a synthetic consultation state, the outcome distribution over the versioned rules, and the next
question chosen by expected information gain. No language model and no case data are needed.
python3 example.py"""
from lawu.engine.slots import SlotState, SLOT_IDS, NUMERIC, DATE, TH
from lawu.engine import jev_rules, policy, law

# uniform priors over the open elements (the study estimates them from training folds)
PRIORS = {**{s: {True: 0.5, False: 0.5} for s in SLOT_IDS if s not in NUMERIC},
          **{s: {a: 1.0 / len(jev_rules.AGE_ATOMS[s]) for a in jev_rules.AGE_ATOMS[s]} for s in NUMERIC}}

st = SlotState()
# the user has said: forced intercourse (penile-vaginal), in 2018, by one person, no weapon
st.apply('S01', 'supported', turn=0, source='example')
st.apply('S12', 'supported', turn=0, source='example')
st.apply('S23', 'denied', turn=0, source='example')
st.apply('S22', 'denied', turn=0, source='example')
st.slots[DATE].interval, st.slots[DATE].status = ('2018-01-01', '2018-12-31'), 'supported'

table = jev_rules.build_table(st, PRIORS, now_iso='2026-10-28')
print('Outcome distribution:', {k: round(v, 3) for k, v in sorted(table.dist().items(), key=lambda x: -x[1])})
print('Entropy (bits):', round(table.entropy(), 3))
action, slot, info = policy.choose('eig', st, table, asked=set())
print('Next action:', action, slot, '-', TH.get(slot, ('',))[0] if slot else '', '| EIG', round(info.get('gain', 0), 3))
print('Versions known to the rule graph:', len(law.ERAS), 'eras;', 'tested elements in the latest era:', sorted(law.era_slots(len(law.ERAS) - 1)))
