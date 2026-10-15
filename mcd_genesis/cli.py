"""命令行入口。"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from . import foods as foods_mod
from . import forge as forge_mod
from . import forms as forms_mod
from . import ocr as ocr_mod
from . import receipt as receipt_mod


def _out(s: str = "") -> None:
    sys.stdout.write(s + "\n")


# ──────────────────────────────────────────────────────────
# hatch
# ──────────────────────────────────────────────────────────
DEMO_RECEIPT = """巨无霸 x2
麦乐鸡 x1
大薯条 x1
麦旋风 x1
可乐 x1
合计 118"""


def cmd_hatch(args) -> int:
    text: Optional[str] = None
    img: Optional[str] = None

    if args.image:
        img = args.image
        ok, why, lines = ocr_mod.read(img)
        if not ok:
            _out(f"\n  截图识别失败：{why}")
            _out("  可以改成直接输菜品，例如：")
            _out('    python -m mcd_genesis hatch "巨无霸 x2, 麦乐鸡, 麦旋风"\n')
            return 2
        text = "\n".join(lines)
        _out(f"\n  识别到 {len(lines)} 行：")
        for ln in lines:
            _out(f"    │ {ln}")
    elif args.text:
        text = " ".join(args.text) if isinstance(args.text, list) else args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        text = DEMO_RECEIPT
        _out("\n  （没给账单，用示例账单演示；"
             '想捏你自己的：python -m mcd_genesis hatch --image 你的账单.png）')

    r = receipt_mod.parse_text(text, match_fn=foods_mod.match)

    if not r.items:
        _out("\n  没从账单里认出任何菜品。")
        _out('  试试：python -m mcd_genesis hatch "巨无霸 x2, 麦乐鸡, 麦旋风"\n')
        return 2

    _out(f"\n  账单解析：{len(r.items)} 行，匹配到 {sum(1 for i in r.items if i.ok)} 项")
    for it in r.items:
        flag = "✓" if it.ok else "?"
        tgt = it.matched or "（没认出来）"
        price = f"  ¥{it.price:.1f}" if it.price else ""
        _out(f"    {flag} {it.name:<16} ×{it.qty}{price}  -> {tgt}")
    if r.unmatched:
        _out(f"\n  没认出来的：{', '.join(r.unmatched)}")
        _out("  （OCR 误识别很常见，可以手动改一下再跑）")
    if r.total:
        _out(f"\n  账单总金额 ¥{r.total:.1f}")

    b = forge_mod.forge(r, seed=args.seed)
    _out(forge_mod.panel(b))
    return 0


# ──────────────────────────────────────────────────────────
# 其他子命令
# ──────────────────────────────────────────────────────────
def cmd_menu(args) -> int:
    foods = foods_mod.load()
    names = foods_mod.all_names()
    if args.cat:
        names = [n for n in names if foods[n].get("cat") == args.cat]
    if args.keyword:
        names = [n for n in names if args.keyword in n]
    _out(f"\n  饲料库共 {len(foods_mod.load())} 项，当前筛出 {len(names)} 项：\n")
    for n in names[: args.limit]:
        f = foods[n]
        _out(f"    {n:<26} {f['kcal']:>6.0f}kcal  钠{f['sodium']:>6.0f}mg  [{f.get('cat','')}]")
    _out()
    return 0


def cmd_forms(args) -> int:
    _out("\n  可能的出生结果：\n")
    for name, prio, cond in sorted(forms_mod.FORMS, key=lambda x: -x[1]):
        if name == "普通麦麦":
            continue
        _out(f"    {name:<8} {cond}")
    _out("\n  稀有度：\n")
    for lv, th, note in forms_mod.RARITY:
        t = f">= {th}" if th > -1000 else "兜底"
        _out(f"    {lv:<4} {t:<8} {note}")
    _out()
    return 0


def cmd_ocr(args) -> int:
    ok, why = ocr_mod.available()
    if ok:
        _out(f"\n  截图识别可用。系统 OCR 语言包：{why}\n")
        _out("  用法：python -m mcd_genesis hatch --image 你的账单.png\n")
        return 0
    _out(f"\n  截图识别不可用：{why}")
    _out("  改用文本输入：python -m mcd_genesis hatch \"巨无霸 x2, 麦乐鸡\"\n")
    return 1


def build() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mcd_genesis",
        description="麦麦创世纪：用一张麦当劳账单捏一只宠物。每次都不一样。",
    )
    sub = p.add_subparsers(dest="command")

    h = sub.add_parser("hatch", help="捏一只（默认命令）")
    h.add_argument("text", nargs="*", help="账单文本，或菜品列表")
    h.add_argument("--image", "-i", help="麦当劳账单截图（Windows 系统 OCR）")
    h.add_argument("--seed", "-s", type=int, help="固定种子以复现同一只")
    h.set_defaults(func=cmd_hatch)

    m = sub.add_parser("menu", help="查看饲料库")
    m.add_argument("--cat", help="按类别筛（鸡/牛肉/甜品/饮料/薯条/鱼/早餐/沙拉）")
    m.add_argument("--keyword", "-k", help="按名字筛")
    m.add_argument("--limit", type=int, default=30)
    m.set_defaults(func=cmd_menu)

    sub.add_parser("forms", help="查看所有可能的出生结果").set_defaults(func=cmd_forms)
    sub.add_parser("ocr", help="检查截图识别是否可用").set_defaults(func=cmd_ocr)

    return p


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv or argv[0].startswith("-") or argv[0] not in (
            "hatch", "menu", "forms", "ocr"):
        argv = ["hatch"] + argv

    p = build()
    args = p.parse_args(argv)
    if not getattr(args, "func", None):
        p.print_help()
        return 1
    return args.func(args)
