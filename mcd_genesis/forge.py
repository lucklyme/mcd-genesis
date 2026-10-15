"""捏人流程：注入基因 → 随时翻车 → 出生。

同一张账单每次跑结果都不同：基因表达带随机系数、翻车随机触发、
气运纯随机。想复现就给 --seed。
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import accident as acc_mod
from . import foods as foods_mod
from . import genes as genes_mod
from . import forms as forms_mod
from .receipt import Item, Receipt

# 单条基因的翻车概率；全局最多翻这么多次（不然就不是意外，是事故）
ACCIDENT_CHANCE = 0.26
MAX_ACCIDENTS = 3


def _w() -> int:
    try:
        import shutil
        return min(shutil.get_terminal_size().columns, 96)
    except Exception:
        return 78


def _pad(s: str, width: int) -> str:
    """按终端显示宽度补齐（中日韩字符算 2 格）。"""
    n = 0
    for ch in s:
        n += 2 if ord(ch) > 0x2E80 else 1
    return s + " " * max(width - n, 0)


def bar(done: int, total: int, width: int = 22) -> str:
    if total <= 0:
        return "[" + " " * width + "]"
    f = int(width * done / total)
    return "[" + "█" * f + "░" * (width - f) + "]"


@dataclass
class Birth:
    stats: Dict[str, float]
    form: forms_mod.Form
    tags: List[str]
    accidents: List[str]
    accident_names: List[str]
    genes: List[genes_mod.Gene]
    items: List[Item]
    seed: Optional[int]
    receipt_total: Optional[float]


def forge(receipt: Receipt, seed: Optional[int] = None,
          quiet: bool = False, stream=None) -> Birth:
    """捏一只麦麦。stream 用于把过程实时写出去（默认 stdout）。"""
    out = stream or sys.stdout

    def say(s: str = "") -> None:
        if not quiet:
            out.write(s + "\n")

    # 种子：不给就随机——每次都是新的一条命
    if seed is None:
        seed = random.randrange(1, 10**9)
    rng = random.Random(seed)

    foods = foods_mod.load()
    stats = genes_mod.base_stats(rng)
    cats: Dict[str, int] = {}
    total_qty = 0
    used: List[Item] = [it for it in receipt.items if it.ok]
    genes: List[genes_mod.Gene] = []
    tags: List[str] = []
    accident_names: List[str] = []
    blood_override = ""

    W = _w()
    say()
    say("  " + "─" * (W - 4))
    say("   上 帝 捏 人   ·   M c G e n e s i s")
    say(f"   账单 {len(used)} 项 / 共 {sum(i.qty for i in used)} 份    种子 {seed}")
    say("  " + "─" * (W - 4))

    # ── 逐条注入 ──
    for idx, it in enumerate(used, 1):
        food = it.food or {}
        g = genes_mod.express(food, it.qty, rng)
        genes.append(g)

        say()
        say(f"  {bar(idx - 1, len(used))}  {idx}/{len(used)}")
        say(f"  ▸ 注入「{it.matched}」" + (f" ×{it.qty}" if it.qty > 1 else ""))

        parts = []
        for k in ("charm", "wisdom", "vitality", "bp", "weight"):
            v = g.delta.get(k, 0.0)
            if abs(v) < 0.05:
                continue
            parts.append(f"{genes_mod.LABEL[k]} {v:+.1f}")
        say("    " + "   ".join(parts))
        say(f"    （{g.source['kcal']:.0f} kcal · 钠 {g.source['sodium']:.0f} mg · 脂肪 {g.source['fat']:.0f} g）")

        # 先注入
        for k, v in g.delta.items():
            stats[k] = stats.get(k, 0.0) + v

        cat = food.get("cat", "其他")
        cats[cat] = cats.get(cat, 0) + it.qty
        total_qty += it.qty

        # ── 翻车判定 ──
        if len(accident_names) < MAX_ACCIDENTS and rng.random() < ACCIDENT_CHANCE:
            a = acc_mod.pick(rng, cat)
            if a is not None:
                say()
                say("    ╔══════════ 打 翻 了 ══════════")
                say(f"    ║ {a.name}")
                say(f"    ║ {a.line}")
                changes, tag, blood, logs = acc_mod.resolve(a, stats, rng)
                for ln in logs:
                    say("    ║" + ln[3:] if ln.startswith("    ") else "    ║ " + ln)
                for k, v in changes.items():
                    stats[k] = stats.get(k, 0.0) + v
                if tag:
                    tags.append(tag)
                    tags = list(dict.fromkeys(tags))  # 同一词条不重复
                if blood:
                    blood_override = blood
                say(f"    ║ → {a.after}")
                say("    ╚" + "═" * 28)
                accident_names.append(a.name)

    # ── 属性收口 ──
    for k in ("charm", "wisdom", "vitality"):
        stats[k] = max(0.0, stats[k])
    stats["bp"] = max(40.0, stats["bp"])
    stats["weight"] = max(500.0, stats["weight"])
    stats["luck"] = max(1.0, min(100.0, stats["luck"]))

    form = forms_mod.judge(stats, cats, total_qty, len(accident_names), blood_override)

    return Birth(
        stats=stats, form=form, tags=tags, accidents=accident_names,
        accident_names=accident_names, genes=genes, items=used,
        seed=seed, receipt_total=receipt.total,
    )


def panel(b: Birth) -> str:
    """出生公告：立绘 + 属性面板 + 稀有度。"""
    L: List[str] = []
    W = 62
    inner = W - 2          # 内容区宽度；整框总宽 = 2 + 1 + inner + 1

    st = b.stats
    f = b.form

    L.append("")
    L.append("  ┌" + "─" * inner + "┐")

    # 标题
    title = f"  {f.rarity}   {f.name}"
    L.append("  │" + _pad(title, inner) + "│")
    L.append("  ├" + "─" * inner + "┤")

    # 立绘 + 属性并排
    art = f.art
    rows: List[str] = []
    rows.append(f"{'颜值':<4} {_bar(st['charm'], 100)}")
    rows.append(f"{'才智':<4} {_bar(st['wisdom'], 100)}")
    rows.append(f"{'体质':<4} {_bar(st['vitality'], 130)}")
    rows.append(f"{'血压':<4} {_bar(st['bp'], 220)}")
    rows.append(f"{'体重':<4} {st['weight']:,.0f} g")
    rows.append(f"{'气运':<4} {_bar(st['luck'], 100)}  ← 隐藏属性")

    for i in range(max(len(art), len(rows))):
        a = art[i] if i < len(art) else " " * 14
        r = rows[i] if i < len(rows) else ""
        L.append("  │ " + _pad(a + "  " + r, inner - 1) + "│")

    L.append("  ├" + "─" * inner + "┤")
    L.append("  │ " + _pad(f"血统：{f.blood}", inner - 1) + "│")
    L.append("  │ " + _pad(f"      {f.blood_note}", inner - 1) + "│")
    L.append("  │ " + _pad(f"综合评分：{f.score}", inner - 1) + "│")
    if b.tags:
        L.append("  │ " + _pad("词条：" + " / ".join(b.tags), inner - 1) + "│")
    if b.accidents:
        L.append("  │ " + _pad(f"翻车记录：{len(b.accidents)} 次 — " + "、".join(b.accidents), inner - 1) + "│")
    L.append("  ├" + "─" * (W - 2) + "┤")

    # 判词（自动折行）
    for ln in _wrap(f.verdict, inner - 2):
        L.append("  │ " + _pad(ln, inner - 1) + "│")
    L.append("  │ " + _pad("", inner - 1) + "│")
    L.append("  │ " + _pad("  " + f.rarity_note, inner - 1) + "│")
    L.append("  └" + "─" * inner + "┘")
    L.append("")
    L.append(f"  种子 {b.seed}（加 --seed {b.seed} 可复现这一只）")
    return "\n".join(L)


def _bar(v: float, cap: float, width: int = 12) -> str:
    f = max(0.0, min(1.0, v / cap))
    n = int(round(width * f))
    return "█" * n + "░" * (width - n) + f" {v:.1f}"


def _wrap(s: str, width: int) -> List[str]:
    out, cur = [], ""
    n = 0
    for ch in s:
        w = 2 if ord(ch) > 0x2E80 else 1
        if n + w > width:
            out.append(cur)
            cur, n = "", 0
        cur += ch
        n += w
    if cur:
        out.append(cur)
    return out or [""]
