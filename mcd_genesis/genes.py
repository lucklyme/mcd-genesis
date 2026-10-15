"""基因映射：把一道菜的营养数据翻译成一段基因。

设计原则——每个数字都能追溯到 MCP 返回的真实字段，
再乘一个 [0.65, 1.35] 的随机系数：同一张账单，每次捏出来的都不一样。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List

# 五维属性 + 一个隐藏维度
ATTRS = ("charm", "wisdom", "vitality", "bp", "weight")
HIDDEN = ("luck",)

LABEL = {
    "charm": "颜值",
    "wisdom": "才智",
    "vitality": "体质",
    "bp": "血压",
    "weight": "体重",
    "luck": "气运",
}

# 单位
UNIT = {
    "charm": "",
    "wisdom": "",
    "vitality": "",
    "bp": "mmHg",
    "weight": "g",
    "luck": "",
}

# 体重换算：7700 kcal ≈ 1 kg 脂肪（营养学通用公式）
KCAL_PER_KG_FAT = 7700.0


@dataclass
class Gene:
    """一道菜贡献的一段基因。"""

    name: str
    qty: int
    delta: Dict[str, float] = field(default_factory=dict)
    source: Dict[str, float] = field(default_factory=dict)  # 原始营养字段
    luck_roll: float = 1.0  # 本条基因的随机系数


def roll(rng: random.Random, low: float = 0.65, high: float = 1.35) -> float:
    """基因表达的随机系数。"""
    return rng.uniform(low, high)


def express(food: dict, qty: int, rng: random.Random) -> Gene:
    """把一份餐品的营养数据表达成基因增量。

    每个营养字段对属性的贡献方向：
      热量   -> 体重(累积) / 体质
      蛋白质 -> 体质 / 才智
      脂肪   -> 血压(+) / 颜值(-)
      碳水   -> 颜值(+) / 才智(小幅)
      钠     -> 血压(显著)
      钙     -> 才智 / 体质
    """
    f = {k: float(food.get(k, 0) or 0) * qty for k in ("kcal", "protein", "fat", "carb", "sodium", "calcium")}

    g = Gene(name=food.get("name", ""), qty=qty, source=f)

    # 体重：唯一不使用随机系数的项——热量守恒，不跟上帝讨价还价
    g.delta["weight"] = f["kcal"] / KCAL_PER_KG_FAT * 1000.0

    # 其余四维都带随机浮动（系数经实算配平：单份餐品的增量落在可读范围内）
    g.delta["vitality"] = (f["kcal"] / 90.0 + f["protein"] * 0.30 + f["calcium"] * 0.008) * roll(rng)
    g.delta["wisdom"] = (f["protein"] * 0.10 + f["carb"] * 0.035 + f["calcium"] * 0.012) * roll(rng)
    g.delta["charm"] = (f["carb"] * 0.130 + f["calcium"] * 0.005 - f["fat"] * 0.160) * roll(rng)
    g.delta["bp"] = (f["sodium"] * 0.024 + f["fat"] * 0.250) * roll(rng)

    for k in ATTRS:
        g.delta[k] = round(g.delta.get(k, 0.0), 2)
    return g


def base_stats(rng: random.Random) -> Dict[str, float]:
    """出厂设置：每个生命的起点也不同。"""
    return {
        "charm": rng.uniform(2.0, 12.0),
        "wisdom": rng.uniform(2.0, 12.0),
        "vitality": rng.uniform(2.0, 12.0),
        "bp": rng.uniform(85.0, 105.0),
        "weight": rng.uniform(1800.0, 2600.0),  # 新生儿体重(g)
        "luck": rng.uniform(1.0, 100.0),  # 气运：完全随机，谁也说不准
    }


def fmt(v: float, attr: str) -> str:
    u = UNIT.get(attr, "")
    if attr == "weight":
        return f"{v:,.0f}{u}"
    if attr == "bp":
        return f"{v:.0f}{u}"
    return f"{v:.1f}{u}"
