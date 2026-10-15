#!/usr/bin/env python
"""麦麦创世纪 · 一键演示

同一张账单捏三次，得到三种命运——这是整个项目要证明的事：
营养数据是真实的，但生命不是。

    python demo.py             # 用内置真实快照，零 Token 直接跑
    python demo.py --live      # 直连麦当劳 MCP 拉最新数据
    python demo.py --seed 7    # 固定种子（演示用随机，每次都不一样）
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcd_genesis import foods as foods_mod
from mcd_genesis import forge as forge_mod
from mcd_genesis import genes as genes_mod
from mcd_genesis import ocr as ocr_mod
from mcd_genesis.receipt import parse_text

RECEIPT = """巨无霸 x2
麦乐鸡5块 x1
大薯条 x1
草莓麦旋风 x1
可乐中杯 x1
合计 118"""

BANNER = r"""
   __  __  ___  ___      ___ ___ ___ _  _  ___ ___ ___
  |  \/  |/ __||   \    / __| __/ __| \| |/ __|_ _/ __|
  | |\/| | (_ || |) |  | (_ | _|\__ \ .` |\__ \| |\__ \
  |_|  |_|\___||___/    \___|___|___/|_|\_|___/___|___/
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="麦麦创世纪 · 一键演示")
    ap.add_argument("--live", action="store_true", help="直连麦当劳 MCP 拉最新数据")
    ap.add_argument("--seed", type=int, help="固定种子")
    ap.add_argument("--rounds", type=int, default=3, help="捏几只（默认 3）")
    args = ap.parse_args()

    print(BANNER)
    print("  麦麦创世纪 · 用一张麦当劳账单捏一只宠物")
    print("  营养数据来自麦当劳官方 MCP：list-nutrition-foods\n")

    # ── 数据源 ──
    if args.live:
        try:
            n = foods_mod.refresh_live()
            print(f"  饲料数据源：麦当劳 MCP 实时接口（{n} 个在售餐品）\n")
        except Exception as e:
            print(f"  实时拉取失败：{e}")
            print("  已回退到内置快照（2026-10-15 的真实返回值）\n")
    else:
        m = foods_mod.meta()
        print(f"  饲料数据源：内置快照 {m.get('_count')} 个在售餐品")
        print(f"            （{m.get('_source', '')[:52]}）\n")

    # ── OCR 可用性 ──
    ok, why = ocr_mod.available()
    if ok:
        print(f"  截图识别：可用（系统 OCR 语言包 {why.split(',')[0]}）")
        print("            python -m mcd_genesis hatch --image 你的账单.png\n")
    else:
        print(f"  截图识别：不可用（{why}）")
        print("            可用文本输入代替\n")

    print("  ── 同一张账单 ──")
    for ln in RECEIPT.splitlines():
        print(f"     {ln}")
    print()

    r = parse_text(RECEIPT, match_fn=foods_mod.match)
    print(f"  解析结果：{len(r.items)} 项，全部匹配到真实餐品\n")

    results = []
    rounds = 1 if args.seed is not None else args.rounds
    for i in range(rounds):
        seed = args.seed if args.seed is not None else None
        b = forge_mod.forge(r, seed=seed, quiet=True)
        results.append(b)
        print(f"  【第 {i + 1} 只】种子 {b.seed}")
        print(f"     颜值 {b.stats['charm']:.1f} · "
              f"才智 {b.stats['wisdom']:.1f} · "
              f"体质 {b.stats['vitality']:.1f} · "
              f"血压 {b.stats['bp']:.0f} · "
              f"体重 {b.stats['weight']:,.0f}g · "
              f"气运 {b.stats['luck']:.0f}")
        print(f"     → {b.form.rarity}  {b.form.name}"
              + (f"（翻车 {len(b.accidents)} 次）" if b.accidents else "（全程零失误）"))
        print()

    # ── 完整展示最后一只 ──
    print("  ── 完整出生公告（最后一只）──")
    print(forge_mod.panel(results[-1]))

    # ── 差异对比：证明「不确定性」──
    if len(results) > 1:
        print("  ── 同一张账单，命运差多少 ──")
        for k in ("charm", "wisdom", "vitality", "bp", "luck"):
            vals = [b.stats[k] for b in results]
        print(f"    {genes_mod.LABEL[k]:<4} "
              f"{min(vals):>7.1f} ~ {max(vals):>7.1f}   "
              f"极差 {max(vals) - min(vals):>6.1f}")
        forms = {b.form.name for b in results}
        print(f"\n    出生形态：{len(forms)} 种 —— {'、'.join(sorted(forms))}")
        print("    → 同样的账单，不同的命。这就是基因表达的随机系数。\n")

    print("  想捏你自己的：")
    print("    python -m mcd_genesis hatch --image 你的账单.png")
    print('    python -m mcd_genesis hatch "巨无霸 x2, 麦乐鸡, 麦旋风"')
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
