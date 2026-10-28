"""The 23 legal-element slots (ALL23_DEFINITIONS.json) plus the incident-date variable.

Statuses follow LAW-U-R/dialogue/state.py: supported / denied / unknown / conflict.
Age slots (S16, S17) carry an interval of exact age in years; the date slot carries a date interval.
"""
import json
from dataclasses import dataclass, field
from lawu.common import STEP13

DEFS = json.loads((STEP13 / '03_RULES' / 'ALL23_DEFINITIONS.json').read_text())
SLOT_IDS = [f'S{d["number"]:02d}' for d in DEFS]
FIELD = {f'S{d["number"]:02d}': d['field'] for d in DEFS}
SCOPE = {f'S{d["number"]:02d}': d['scope'] for d in DEFS}
NUMERIC = {'S16', 'S17'}
DATE = 'DATE'
STATUSES = ('supported', 'denied', 'unknown', 'conflict')

# Lay-Thai label, question asked by the agent, and affirmed/denied statements (used by templates
# for confirmation questions and by the simulator's contradiction injection).
TH = {
    'S01': ('การสอดใส่อวัยวะเพศเข้าทางช่องคลอด (รวมพยายาม)', 'ขอถามตรง ๆ นะคะ เขาสอดใส่อวัยวะเพศของเขาเข้าไปในอวัยวะเพศของผู้เสียหายหรือไม่ หรือพยายามจะทำแต่ไม่สำเร็จ',
            'เขาสอดใส่หรือพยายามสอดใส่อวัยวะเพศของเขาเข้าไปในอวัยวะเพศของฉัน', 'เขาไม่ได้สอดใส่หรือพยายามสอดใส่อวัยวะเพศเข้าทางช่องคลอด'),
    'S02': ('การจับต้อง/ลวนลามทางเพศ', 'เขาจับต้อง ลูบคลำ กอดจูบ ให้จับต้องตัวเขา หรือทำอะไรในทางเพศกับร่างกายโดยไม่ถึงขั้นสอดใส่หรือไม่',
            'เขาจับต้องลวนลามทางเพศ', 'ไม่มีการจับต้องลวนลาม'),
    'S03': ('ใช้วัตถุหรืออวัยวะอื่น', 'เขาใช้นิ้ว วัตถุ หรือสิ่งของอื่นล่วงล้ำอวัยวะเพศหรือทวารหนักหรือไม่',
            'เขาใช้นิ้วหรือวัตถุล่วงล้ำ', 'ไม่ได้ใช้นิ้วหรือวัตถุ'),
    'S04': ('การสอดใส่อวัยวะเพศเข้าทางทวารหนักหรือปาก (รวมพยายาม)', 'เขาสอดใส่อวัยวะเพศของเขาเข้าไปทางทวารหนักหรือทางปากของผู้เสียหายหรือไม่ หรือพยายามจะทำแต่ไม่สำเร็จ',
            'เขาสอดใส่หรือพยายามสอดใส่อวัยวะเพศของเขาเข้าทางทวารหนักหรือปากของฉัน', 'เขาไม่ได้สอดใส่อวัยวะเพศเข้าทางทวารหนักหรือปาก'),
    'S05': ('อวัยวะเพศของผู้เสียหายถูกทำให้สอดใส่ผู้กระทำ', 'เขาทำให้อวัยวะเพศของผู้เสียหายเข้าไปในตัวเขาหรือไม่ เช่น ผู้หญิงที่ทำมีเพศสัมพันธ์กับเด็กผู้ชาย',
            'เขาทำให้อวัยวะเพศของฉันเข้าไปในตัวเขา', 'ไม่มีการทำให้อวัยวะเพศของฉันเข้าไปในตัวเขา'),
    'S06': ('อวัยวะเพศจากการผ่าตัด', 'มีเรื่องอวัยวะเพศที่ได้จากการผ่าตัดแปลงเพศเกี่ยวข้องด้วยหรือไม่',
            'เกี่ยวข้องกับอวัยวะเพศจากการผ่าตัด', 'ไม่เกี่ยวข้อง'),
    'S07': ('ผู้กระทำรู้ตัวขณะทำ', 'ตอนนั้นเขาดูรู้ตัวว่ากำลังทำอะไรอยู่หรือไม่ เช่น ไม่ได้ละเมอหรือหมดสติ',
            'เขารู้ตัวดีว่าทำอะไร', 'เขาไม่รู้ตัว'),
    'S08': ('ผู้กระทำตั้งใจ', 'คุณคิดว่าเขาตั้งใจทำแบบนั้นหรือไม่',
            'เขาตั้งใจทำ', 'เขาไม่ได้ตั้งใจ'),
    'S09': ('ผู้กระทำรู้ข้อเท็จจริง (เช่น อายุ)', 'เขารู้หรือไม่ว่าคุณอายุเท่าไร หรือรู้สถานการณ์ของคุณตอนนั้น',
            'เขารู้อายุ/สถานการณ์ของฉัน', 'เขาไม่รู้'),
    'S10': ('ทำเพื่อสนองความใคร่', 'การกระทำนั้นเป็นไปในทางเพศหรือเพื่อความต้องการทางเพศของเขาหรือไม่',
            'เขาทำเพื่อความต้องการทางเพศ', 'ไม่ได้เป็นเรื่องทางเพศ'),
    'S11': ('การขู่', 'เขาขู่คุณหรือไม่ เช่น ขู่ว่าจะทำร้าย ฆ่า หรือทำให้เสียหาย',
            'เขาขู่ฉัน', 'เขาไม่ได้ขู่'),
    'S12': ('การใช้กำลัง', 'เขาใช้กำลัง เช่น จับ กด ตบ ตี หรือทำร้ายร่างกายคุณหรือไม่',
            'เขาใช้กำลังจับกดหรือทำร้ายฉัน', 'เขาไม่ได้ใช้กำลัง'),
    'S13': ('อยู่ในภาวะขัดขืนไม่ได้', 'ตอนนั้นคุณอยู่ในสภาพที่ขัดขืนไม่ได้หรือไม่ เช่น เมา หลับ หมดสติ ถูกมัด หรือป่วย',
            'ตอนนั้นฉันขัดขืนไม่ได้ (เช่น เมา หลับ หมดสติ ถูกมัด ป่วย)', 'ตอนนั้นฉันขัดขืนได้ตามปกติ'),
    'S14': ('หลอกว่าเป็นบุคคลอื่น', 'เขาทำให้คุณเข้าใจผิดว่าเขาเป็นคนอื่นหรือไม่ เช่น แอบอ้างเป็นแฟนหรือสามี',
            'เขาหลอกว่าเป็นคนอื่น', 'เขาไม่ได้แอบอ้างเป็นคนอื่น'),
    'S15': ('ความยินยอม', 'ตอนที่เกิดเหตุ คุณยินยอมหรือเต็มใจหรือไม่',
            'ฉันยินยอม', 'ฉันไม่ยินยอม'),
    'S16': ('อายุผู้เสียหายขณะเกิดเหตุ', 'ตอนเกิดเหตุ ผู้เสียหายอายุเท่าไรคะ (ถ้าจำไม่ได้แน่ชัด บอกช่วงอายุโดยประมาณได้)',
            None, None),
    'S17': ('อายุผู้กระทำขณะเกิดเหตุ', 'คนที่ทำอายุประมาณเท่าไรคะ',
            None, None),
    'S18': ('เป็นสามีภริยากัน', 'คุณกับผู้กระทำเป็นสามีภรรยากันหรือไม่',
            'เราเป็นสามีภรรยากัน', 'เราไม่ได้เป็นสามีภรรยากัน'),
    'S19': ('บทบาทของแต่ละคน', 'มีคนอื่นร่วมกระทำด้วยนอกจากเขาหรือไม่',
            'มีหลายคนแบ่งหน้าที่กัน', 'มีเพียงผู้กระทำคนเดียว'),
    'S20': ('ทำให้เชื่อว่ามีปืน/ระเบิด', 'เขาทำให้คุณเชื่อว่าเขามีปืนหรือระเบิดหรือไม่ เช่น บอกว่ามีปืนหรือทำท่าเหมือนพกปืน',
            'เขาทำให้ฉันเชื่อว่ามีปืน', 'เขาไม่ได้ทำให้เชื่อว่ามีปืน'),
    'S21': ('มีปืน/ระเบิดจริง', 'เขามีปืนหรือวัตถุระเบิดติดตัวจริงตอนเกิดเหตุหรือไม่',
            'เขามีปืนติดตัว', 'เขาไม่มีปืนหรือระเบิด'),
    'S22': ('ใช้อาวุธ', 'เขาใช้อาวุธอะไรหรือไม่ เช่น มีด ไม้ หรือปืน',
            'เขาใช้หรือถืออาวุธ เช่น มีด ไม้ ปืน ขณะก่อเหตุ', 'เขาไม่ได้ใช้หรือถืออาวุธ'),
    'S23': ('ร่วมกันหลายคน (โทรม)', 'มีผู้ชายหลายคนผลัดกันหรือร่วมกันทำกับคุณหรือไม่',
            'มีผู้กระทำหลายคนร่วมกันหรือผลัดกันทำ', 'มีคนทำเพียงคนเดียว'),
    'DATE': ('วันเกิดเหตุ', 'เหตุการณ์นี้เกิดขึ้นเมื่อไหร่คะ (วัน เดือน ปี หรือปีโดยประมาณ)', None, None),
}


@dataclass
class Slot:
    status: str = 'unknown'
    interval: tuple | None = None          # numeric slots: (lo, hi) in years; DATE: (from_iso, to_iso)
    unavailable: bool = False              # user said they do not know -> never re-asked
    history: list = field(default_factory=list)


class SlotState:
    """Ledger of all 23 slots + DATE with turn-level provenance and conflict tracking."""

    def __init__(self):
        self.slots = {s: Slot() for s in SLOT_IDS + [DATE]}
        self.attempt = None
        self.events = []

    def known(self, s):
        sl = self.slots[s]
        return sl.status in ('supported', 'denied') or sl.interval is not None

    def apply(self, s, status=None, interval=None, *, turn, source, correction=False):
        """Update one slot. Returns 'new' | 'same' | 'corrected' | 'conflict'."""
        sl = self.slots[s]
        before = dict(status=sl.status, interval=sl.interval)
        outcome = 'new'
        if s in NUMERIC or s == DATE:
            if interval is None:
                return 'same'
            if sl.interval is not None and not correction and not _overlap(sl.interval, interval):
                sl.status, outcome = 'conflict', 'conflict'
                sl.history.append(dict(turn=turn, source=source, proposed=interval, before=before))
                self.events.append(dict(turn=turn, slot=s, event='conflict', old=before, new=interval))
                sl.pending = interval
                return outcome
            if sl.interval is not None:
                outcome = 'corrected' if correction else 'same'
                interval = interval if correction else _intersect(sl.interval, interval)
            sl.interval, sl.status = interval, 'supported'
        else:
            if status not in ('supported', 'denied'):
                return 'same'
            if sl.status in ('supported', 'denied') and sl.status != status and not correction:
                sl.status, outcome = 'conflict', 'conflict'
                sl.history.append(dict(turn=turn, source=source, proposed=status, before=before))
                self.events.append(dict(turn=turn, slot=s, event='conflict', old=before['status'], new=status))
                return outcome
            if sl.status == status:
                outcome = 'same'
            elif sl.status in ('supported', 'denied', 'conflict'):
                outcome = 'corrected'
            sl.status = status
        sl.unavailable = False
        sl.history.append(dict(turn=turn, source=source, status=sl.status, interval=sl.interval, before=before,
                               correction=correction))
        if outcome == 'corrected':
            self.events.append(dict(turn=turn, slot=s, event='corrected', old=before, new=dict(status=sl.status, interval=sl.interval)))
        return outcome

    def resolve_conflict(self, s, status=None, interval=None, *, turn, source):
        sl = self.slots[s]
        if s in NUMERIC or s == DATE:
            sl.interval = interval if interval is not None else sl.interval
            sl.status = 'supported' if sl.interval is not None else 'unknown'
        else:
            sl.status = status if status in ('supported', 'denied') else 'unknown'
        sl.history.append(dict(turn=turn, source=source, status=sl.status, interval=sl.interval, resolved=True))
        self.events.append(dict(turn=turn, slot=s, event='resolved', value=sl.status if s not in NUMERIC else sl.interval))

    def conflicts(self):
        return [s for s, sl in self.slots.items() if sl.status == 'conflict']

    def snapshot(self):
        return {s: dict(status=sl.status, interval=sl.interval, unavailable=sl.unavailable)
                for s, sl in self.slots.items()}

    def n_known(self):
        return sum(self.known(s) for s in self.slots)


def _overlap(a, b):
    return not (a[1] < b[0] or b[1] < a[0])


def _intersect(a, b):
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    return (lo, hi) if lo <= hi else b
