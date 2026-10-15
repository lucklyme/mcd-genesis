"""饲料库：麦当劳 MCP list-nutrition-foods 的真实快照 + 模糊匹配。"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple

_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT = os.path.join(_DIR, "data", "foods.json")

_CACHE: Optional[Dict[str, dict]] = None


def load() -> Dict[str, dict]:
    """加载饲料库（158 个真实在售餐品的营养数据）。"""
    global _CACHE
    if _CACHE is None:
        with open(SNAPSHOT, encoding="utf-8") as f:
            d = json.load(f)
        _CACHE = d["foods"]
    return _CACHE


def meta() -> dict:
    with open(SNAPSHOT, encoding="utf-8") as f:
        d = json.load(f)
    return {k: v for k, v in d.items() if k.startswith("_")}


# ── 实时模式：直连 MCP 刷新饲料库 ──
_RULES = (
    ("鸡", ("麦乐鸡", "鸡翅", "鸡腿", "鸡排", "麦辣鸡", "板烧", "鸡块")),
    ("薯条", ("薯条", "薯格", "薯饼")),
    ("甜品", ("圆筒", "麦旋风", "新地", "派", "冰淇淋", "冰激凌", "蛋糕", "甜筒")),
    ("饮料", ("可乐", "雪碧", "美汁源", "果汁", "奶茶", "咖啡", "拿铁", "豆浆", "牛奶", "茶", "酷")),
    ("牛肉", ("巨无霸", "牛", "汉堡", "堡")),
    ("鱼", ("麦香鱼", "鱼")),
    ("早餐", ("麦满分", "早安", "粥", "油条", "饼")),
    ("沙拉", ("沙拉", "苹果片", "玉米")),
)


def classify(name: str) -> str:
    for cat, kws in _RULES:
        for k in kws:
            if k in name:
                return cat
    return "其他"


def refresh_live() -> int:
    """从麦当劳 MCP 拉最新营养数据，覆盖内存缓存。

    需要环境变量 MCD_MCP_TOKEN。返回条数。
    """
    global _CACHE
    from .mcp_live import fetch_nutrition

    raw = fetch_nutrition()
    items = raw if isinstance(raw, list) else list(raw.values())
    foods: Dict[str, dict] = {}
    for it in items:
        name = (it.get("productName") or "").strip()
        if not name or name in foods:
            continue
        foods[name] = {
            "kcal": float(it.get("energyKcal") or 0),
            "protein": float(it.get("protein") or 0),
            "fat": float(it.get("fat") or 0),
            "carb": float(it.get("carbohydrate") or 0),
            "sodium": float(it.get("sodium") or 0),
            "calcium": float(it.get("calcium") or 0),
            "cat": classify(name),
        }
    if not foods:
        raise RuntimeError("MCP 返回为空，回退到本地快照")
    _CACHE = foods
    return len(foods)


def match(name: str) -> Optional[dict]:
    """模糊匹配：'麦乐鸡' 能命中 '麦乐鸡5块'，'薯条' 命中 '大薯条'。

    策略：精确 > 前缀 > 包含 > 逐字覆盖度。
    """
    foods = load()
    name = (name or "").strip()
    if not name:
        return None
    if name in foods:
        return dict(foods[name], name=name)

    # 去掉 OCR 常见的数量尾巴：「巨无霸 x2」「麦乐鸡*1」
    core = name
    for sep in ("x", "X", "*", "×", " ", "份", "个"):
        core = core.split(sep)[0]
    if core and core in foods:
        return dict(foods[core], name=core)

    hits = [k for k in foods if name in k or (core and core in k)]
    if len(hits) == 1:
        return dict(foods[hits[0]], name=hits[0])
    if hits:
        # 取覆盖度最高、名字最短的
        def score(k: str) -> Tuple[int, int]:
            s = sum(1 for ch in name if ch in k)
            return (-s, len(k))

        hits.sort(key=score)
        return dict(foods[hits[0]], name=hits[0])
    return None


def candidates(name: str, n: int = 3) -> List[str]:
    """给 OCR 误识别留一个人工纠正入口。"""
    foods = load()
    hits = [k for k in foods if any(ch in k for ch in name) and name]
    hits.sort(key=lambda k: (-sum(1 for ch in name if ch in k), len(k)))
    return hits[:n]


def all_names() -> List[str]:
    return sorted(load().keys())
