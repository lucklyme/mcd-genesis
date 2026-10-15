"""形态库：10 种出生结果 + 稀有度 + 血统判定。

ASCII 立绘统一 14 格宽，全部用半角字符，避免终端宽度算错。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# ── ASCII 立绘（每项 4 行，行尾留空格以规避 raw string 结尾反斜杠问题）──
ART: Dict[str, List[str]] = {
    "普通麦麦": [
        r"   /\___/\   ",
        r"  (  o.o  )  ",
        r"  (   >    ) ",
        r"   (_____)   ",
    ],
    "麦乐鸡侠": [
        r"   /\___/\   ",
        r"  ( `^`'  )  ",
        r"  /|鸡鸡鸡|\ ",
        r"   (_____)   ",
    ],
    "巨无霸兽": [
        r"  /\______/\ ",
        r" (  O  O   ) ",
        r" (  ▂▂▂▂   ) ",
        r" (_________) ",
    ],
    "高血压猫": [
        r"   /\___/\   ",
        r"  ( @  @  )  ",
        r"  (  ~~~  )  ",
        r"   (_____)   ",
    ],
    "糖分恶魔": [
        r"   /\___/\   ",
        r"  ( *  *  )  ",
        r"  (  ~~~  )  ",
        r"   (_____)   ",
    ],
    "碳酸诗人": [
        r"   /\___/\   ",
        r"  ( -  -  )  ",
        r"  ( °o°o  )  ",
        r"   (_____)   ",
    ],
    "薯条精": [
        r"   /\___/\   ",
        r"  ( |  |  )  ",
        r"  ( IIII  )  ",
        r"   (_____)   ",
    ],
    "麦门圣猫": [
        r"   /\___/\   ",
        r"  ( ^  ^  )  ",
        r"  (  \~/   ) ",
        r"   (_____)   ",
    ],
    "麦香哲学家": [
        r"   /\___/\   ",
        r"  ( -. -  )  ",
        r"  (  ___  )  ",
        r"   (_____)   ",
    ],
    "天弃之子": [
        r"   /\___/\   ",
        r"  ( x  x  )  ",
        r"  ( ~~~~~ )  ",
        r"   (_____)   ",
    ],
}

# ── 形态判定表：(形态, 优先级, 判定函数说明) ──
# 高优先级先命中
FORMS: List[Tuple[str, int, str]] = [
    ("天弃之子", 100, "翻车 3 次以上（上帝今天手抖）"),
    ("高血压猫", 90, "血压 ≥ 200 mmHg"),
    ("巨无霸兽", 80, "体重 ≥ 6000 g"),
    ("天弃之子", 70, "翻车 2 次且气运 < 20"),
    ("糖分恶魔", 60, "甜品占比 ≥ 40%"),
    ("碳酸诗人", 55, "饮料占比 ≥ 50%"),
    ("薯条精", 50, "薯条占比 ≥ 40%"),
    ("麦乐鸡侠", 45, "鸡类占比 ≥ 50%"),
    ("麦门圣猫", 30, "颜值 ≥ 60"),
    ("麦香哲学家", 25, "才智 ≥ 60"),
    ("普通麦麦", 0, "以上皆不满足"),
]

# ── 稀有度 ──
RARITY: List[Tuple[str, int, str]] = [
    ("SP", 225, "神迹。建议截图，你可能再捏不出第二个。"),
    ("UR", 175, "稀有。朋友圈素材已就位。"),
    ("SSR", 130, "很能打。可以拿去跟同事炫耀。"),
    ("SR", 85, "不错。比大多数麦麦强。"),
    ("R", 45, "普通。但它是你的。"),
    ("N", -10**9, "……要不，再点一份？"),
]


@dataclass
class Form:
    name: str
    rarity: str
    rarity_note: str
    blood: str
    blood_note: str
    art: List[str]
    verdict: str
    score: float
    tags: List[str]


def _ratio(cats: Dict[str, int], total: int) -> Dict[str, float]:
    if total <= 0:
        return {}
    return {k: v / total for k, v in cats.items()}


def judge(stats: Dict[str, float], cats: Dict[str, int], total_qty: int,
          accidents: int, blood_override: str = "") -> Form:
    """综合判定形态 / 稀有度 / 血统。"""
    ratio = _ratio(cats, total_qty)
    charm = stats.get("charm", 0.0)
    wisdom = stats.get("wisdom", 0.0)
    vitality = stats.get("vitality", 0.0)
    bp = stats.get("bp", 0.0)
    weight = stats.get("weight", 0.0)
    luck = stats.get("luck", 0.0)

    # ── 形态 ──
    name = "普通麦麦"
    for fname, prio, _ in sorted(FORMS, key=lambda x: -x[1]):
        if fname == "天弃之子" and prio == 100 and accidents >= 3:
            name = fname
            break
        if fname == "天弃之子" and prio == 70 and accidents >= 2 and luck < 20:
            name = fname
            break
        if fname == "高血压猫" and bp >= 190:
            name = fname
            break
        if fname == "巨无霸兽" and weight >= 6000:
            name = fname
            break
        if fname == "糖分恶魔" and ratio.get("甜品", 0) >= 0.30:
            name = fname
            break
        if fname == "碳酸诗人" and ratio.get("饮料", 0) >= 0.40:
            name = fname
            break
        if fname == "薯条精" and ratio.get("薯条", 0) >= 0.30:
            name = fname
            break
        if fname == "麦乐鸡侠" and ratio.get("鸡", 0) >= 0.40:
            name = fname
            break
        if fname == "麦门圣猫" and charm >= 18:
            name = fname
            break
        if fname == "麦香哲学家" and wisdom >= 26:
            name = fname
            break

    # ── 血统 ──
    blood, blood_note = "杂食地球人", "什么都吃，什么都不精。"
    if blood_override:
        blood = blood_override
        blood_note = "翻车留下的印记，比血统更深。"
    elif ratio:
        top, v = max(ratio.items(), key=lambda x: x[1])
        if v >= 0.5:
            blood = {
                "鸡": "麦乐鸡纯血", "牛肉": "牛肉贵族", "甜品": "糖分血脉",
                "饮料": "碳酸血脉", "薯条": "薯条血脉", "鱼": "深海血脉",
                "早餐": "晨型血脉", "沙拉": "草食血脉", "其他": "杂食血脉",
            }.get(top, "杂食血脉")
            blood_note = f"账单里 {top} 类占了 {v * 100:.0f}%，血统纯正。"
        elif v >= 0.3:
            blood = "混血麦麦"
            blood_note = f"{top} 类占 {v * 100:.0f}%，血统有点杂，但杂得好看。"

    # ── 综合分 ──
    score = (
        charm * 1.2
        + wisdom * 1.2
        + vitality * 0.4
        + luck * 0.6
        - max(0.0, bp - 160.0) * 0.40
        - max(0.0, weight - 4500.0) * 0.002
        + accidents * 6.0
    )
    if name == "天弃之子":
        score += 25.0

    rarity, note = "N", ""
    for lv, th, n in RARITY:
        if score >= th:
            rarity, note = lv, n
            break

    verdict = _verdict(name, stats, ratio, accidents, luck)

    return Form(
        name=name, rarity=rarity, rarity_note=note,
        blood=blood, blood_note=blood_note,
        art=ART.get(name, ART["普通麦麦"]),
        verdict=verdict, score=round(score, 1), tags=[],
    )


def _verdict(name: str, stats: Dict[str, float], ratio: Dict[str, float],
             accidents: int, luck: float) -> str:
    charm, wisdom, vitality = stats.get("charm", 0), stats.get("wisdom", 0), stats.get("vitality", 0)
    bp, weight = stats.get("bp", 0), stats.get("weight", 0)

    if name == "天弃之子":
        return "上帝今天手抖了三次。它不是残次品，它是行为的艺术。"
    if name == "高血压猫":
        return f"血压 {bp:.0f} mmHg。它看你的眼神里带着一点责备，和很多钠。"
    if name == "巨无霸兽":
        return f"出生体重 {weight:,.0f} g。产房门可能不够宽。"
    if name == "糖分恶魔":
        return "它的第一声啼哭是「还要」。"
    if name == "碳酸诗人":
        return "它打嗝的节奏，和十四行诗押韵。"
    if name == "薯条精":
        return "它认为自己是一根薯条。我们不打算纠正它。"
    if name == "麦乐鸡侠":
        return "白天是猫，晚上是麦乐鸡。它自己也不清楚切换条件。"
    if name == "麦门圣猫":
        return f"颜值 {charm:.1f}。麦当劳门徒见了要行礼。"
    if name == "麦香哲学家":
        return f"才智 {wisdom:.1f}。它睁眼第一件事是思考「我为什么是鸡做的」。"
    if luck >= 85:
        return f"气运 {luck:.0f}。它还没睁眼，好运就已经排队了。"
    if luck <= 15:
        return f"气运 {luck:.0f}。它出生的那一刻，灯闪了一下。"
    if accidents == 0:
        return "全程零失误。这份完美，反而不太像你。"
    return f"颜值 {charm:.1f} / 才智 {wisdom:.1f} / 体质 {vitality:.1f}。一个说得过去的麦麦。"
