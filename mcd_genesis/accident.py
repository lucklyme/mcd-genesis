"""翻车事件库：上帝捏着捏着，手一抖。

每条基因注入时按概率触发；事件会真实改动属性，并可能留下词条 / 血统。
同一张账单每次跑翻的车都不一样——这是「不确定性」的主要来源。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from .genes import LABEL


@dataclass
class Accident:
    key: str
    name: str
    line: str                      # 翻车瞬间的台词
    cats: Tuple[str, ...] = ()     # 偏好类别；空表示任何菜都可能
    weight: float = 1.0
    # 效果：返回 (属性改动, 词条, 血统)
    effect: Optional[Callable[[random.Random], Tuple[Dict[str, float], str, str]]] = None
    after: str = ""                # 翻车之后的补刀


def _r(lo: float, hi: float) -> Callable[[random.Random], float]:
    return lambda rng: rng.uniform(lo, hi)


def _ev(changes: Dict[str, float], tag: str = "", blood: str = "",
        rng_range: Optional[Dict[str, Tuple[float, float]]] = None):
    """构造一个带随机幅度的效果。"""

    def f(rng: random.Random) -> Tuple[Dict[str, float], str, str]:
        out = {}
        for k, v in changes.items():
            if rng_range and k in rng_range:
                lo, hi = rng_range[k]
                out[k] = rng.uniform(lo, hi) * (1 if v >= 0 else -1)
            else:
                out[k] = float(v)
        return out, tag, blood

    return f


ACCIDENTS: List[Accident] = [
    Accident(
        key="cone_drop",
        name="甜筒掉地上了",
        line="甜筒脱手，在空中转了半圈，啪。",
        cats=("甜品",),
        weight=2.0,
        effect=_ev({"charm": -8.0, "wisdom": -2.0},
                   tag="地板甜筒", rng_range={"charm": (6.0, 11.0), "wisdom": (1.0, 3.0)}),
        after="它盯着地上的甜筒看了三秒，然后决定不介意。",
    ),
    Accident(
        key="coke_spill",
        name="可乐泼了",
        line="可乐沿着操作台一路漫延，漫过了它的脚。",
        cats=("饮料",),
        weight=2.0,
        effect=_ev({"charm": -5.0, "bp": -12.0, "weight": 180.0},
                   tag="碳酸洗礼", blood="碳酸诗人",
                   rng_range={"charm": (3.0, 7.0), "bp": (8.0, 18.0), "weight": (120.0, 260.0)}),
        after="它身上的气泡一直没散。医生说这叫气质。",
    ),
    Accident(
        key="fries_spill",
        name="薯条撒了一地",
        line="整盒薯条以慢动作飞出去，落点遍布三个工位。",
        cats=("薯条",),
        weight=2.0,
        effect=_ev({"charm": -6.0, "vitality": 9.0, "bp": 14.0},
                   tag="满地金黄", blood="薯条精",
                   rng_range={"charm": (4.0, 9.0), "vitality": (5.0, 14.0), "bp": (8.0, 22.0)}),
        after="它从此走路带盐。",
    ),
    Accident(
        key="sauce_burst",
        name="酱包爆了",
        line="你捏酱包的力度，比捏它的五官大得多。",
        cats=("鸡", "牛肉", "鱼"),
        weight=1.6,
        effect=_ev({"charm": -12.0, "bp": 9.0},
                   tag="酱渍", rng_range={"charm": (8.0, 16.0), "bp": (5.0, 14.0)}),
        after="糖醋酱从额头流到下巴。它笑了，所以不算浪费。",
    ),
    Accident(
        key="tray_flip",
        name="整个托盘翻了",
        line="你也不知道怎么搞的，总之托盘在空中翻了一整圈。",
        cats=(),
        weight=0.9,
        effect=_ev({"charm": 0.0}, tag="", rng_range={}),
        after="它从废墟里站起来，眼神变了。",
    ),
    Accident(
        key="sneeze",
        name="上帝打了个喷嚏",
        line="你没有感冒，但那一瞬间宇宙确实震了一下。",
        cats=(),
        weight=1.1,
        effect=_ev({}, tag="神的 sneeze", rng_range={}),
        after="某项数值被吹高了。至于是哪一项，上帝也没看清。",
    ),
    Accident(
        key="five_second",
        name="汉堡掉地上了",
        line="五秒定律启动。你数到四就捡起来了。",
        cats=("牛肉", "鸡", "鱼"),
        weight=1.4,
        effect=_ev({"charm": -4.0, "vitality": 6.0},
                   tag="五秒定律", rng_range={"charm": (2.0, 6.0), "vitality": (3.0, 10.0)}),
        after="它获得了一点来自地板的勇气。",
    ),
    Accident(
        key="nugget_lost",
        name="麦乐鸡滚进沙发缝了",
        line="你听见它滚进去的声音，然后是一片沉默。",
        cats=("鸡",),
        weight=1.5,
        effect=_ev({"weight": -160.0, "charm": -3.0},
                   tag="失踪人口", rng_range={"weight": (100.0, 240.0), "charm": (1.0, 5.0)}),
        after="这块麦乐鸡将永远活在它的传说里。",
    ),
    Accident(
        key="straw_bend",
        name="吸管戳歪了",
        line="你戳了三次，杯盖上出现了三个洞。",
        cats=("饮料",),
        weight=1.3,
        effect=_ev({"bp": -18.0, "wisdom": -3.0},
                   tag="漏风", rng_range={"bp": (10.0, 26.0), "wisdom": (1.0, 5.0)}),
        after="它学会了用三个洞同时喝。这算才智吗？不算。",
    ),
    Accident(
        key="coffee_burn",
        name="热咖啡洒手上了",
        line="你甩手的动作，把它甩出去半米。",
        cats=("饮料", "其他"),
        weight=1.0,
        effect=_ev({"vitality": -6.0, "charm": -5.0},
                   tag="烫伤", rng_range={"vitality": (3.0, 9.0), "charm": (3.0, 8.0)}),
        after="它发出了生命中第一个音节。听起来像「烫」。",
    ),
]


def pick(rng: random.Random, cat: str) -> Optional[Accident]:
    """按类别偏好加权抽一个翻车事件。"""
    pool = [a for a in ACCIDENTS if (not a.cats or cat in a.cats)]
    if not pool:
        return None
    weights = [a.weight for a in pool]
    return rng.choices(pool, weights=weights, k=1)[0]


def resolve(acc: Accident, stats: Dict[str, float],
            rng: random.Random) -> Tuple[Dict[str, float], str, str, List[str]]:
    """结算一次翻车。返回 (属性改动, 词条, 血统, 展示行)。"""
    logs: List[str] = []
    changes, tag, blood = {}, "", ""

    if acc.key == "tray_flip":
        # 托盘翻了：全部四维打折，但气运大涨（大难不死必有后福）
        mul = rng.uniform(0.78, 0.92)
        for k in ("charm", "wisdom", "vitality"):
            before = stats.get(k, 0.0)
            after_v = before * mul
            changes[k] = after_v - before
        changes["luck"] = rng.uniform(15.0, 28.0)
        tag = "大难不死"
        logs.append(f"    四维 ×{mul:.2f}，但气运 +{changes['luck']:.0f}（大难不死）")
    elif acc.key == "sneeze":
        k = rng.choice(["charm", "wisdom", "vitality", "bp", "weight"])
        cur = stats.get(k, 0.0)
        factor = rng.uniform(1.5, 2.2)
        changes[k] = cur * (factor - 1.0)
        tag = "神之喷嚏"
        logs.append(f"    {LABEL.get(k, k)} ×{factor:.2f}（上帝吹的）")
    elif acc.effect is not None:
        changes, tag, blood = acc.effect(rng)
        for k, v in changes.items():
            logs.append(f"    {LABEL.get(k, k)} {v:+.1f}")

    return changes, tag, blood, logs
