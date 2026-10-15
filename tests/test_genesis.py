"""核心单元测试：覆盖 OCR 解析、基因映射、翻车、形态判定。"""

from __future__ import annotations

import random
import unittest

from mcd_genesis import accident as acc_mod
from mcd_genesis import foods as foods_mod
from mcd_genesis import forge as forge_mod
from mcd_genesis import forms as forms_mod
from mcd_genesis import genes as genes_mod
from mcd_genesis.receipt import parse_text


class TestReceipt(unittest.TestCase):
    def test_comma_separated_hand_input(self):
        r = parse_text("巨无霸 x2, 麦乐鸡, 大薯条", match_fn=foods_mod.match)
        self.assertEqual(len(r.items), 3)
        self.assertEqual(r.items[0].qty, 2)
        self.assertEqual(r.items[0].matched, "巨无霸")
        self.assertEqual(r.items[1].matched, "麦乐鸡5块")
        self.assertEqual(r.items[2].matched, "大薯条")

    def test_ocr_column_major(self):
        """OCR 常按列输出：先菜名、后数量/价格，按顺序对齐。"""
        text = (
            "麦当劳 上海人民广场餐厅\n"
            "巨无霸\n麦乐鸡5块\n大薯条\n"
            "×2 51.00\n13.00\n12.00\n"
        )
        r = parse_text(text, match_fn=foods_mod.match)
        names = [it.matched for it in r.items]
        qtys = [it.qty for it in r.items]
        self.assertEqual(names, ["巨无霸", "麦乐鸡5块", "大薯条"])
        self.assertEqual(qtys, [2, 1, 1])

    def test_noise_filter(self):
        r = parse_text(
            "合计 118.00\n实付 118.00\n2026-10-16 12:41 堂食\n巨无霸 x1",
            match_fn=foods_mod.match,
        )
        self.assertEqual(len(r.items), 1)
        self.assertEqual(r.items[0].matched, "巨无霸")


class TestFoods(unittest.TestCase):
    def test_exact_and_fuzzy_match(self):
        self.assertEqual(foods_mod.match("巨无霸")["name"], "巨无霸")
        self.assertEqual(foods_mod.match("麦乐鸡")["name"], "麦乐鸡5块")
        self.assertEqual(foods_mod.match("大薯条")["name"], "大薯条")
        self.assertIsNone(foods_mod.match("不存在的菜"))


class TestGenes(unittest.TestCase):
    def test_fixed_seed_repeatable(self):
        f = foods_mod.match("巨无霸")
        g1 = genes_mod.express(f, 1, random.Random(7))
        g2 = genes_mod.express(f, 1, random.Random(7))
        self.assertEqual(g1.delta, g2.delta)

    def test_randomness_between_seeds(self):
        f = foods_mod.match("巨无霸")
        g1 = genes_mod.express(f, 1, random.Random(7))
        g2 = genes_mod.express(f, 1, random.Random(8))
        # 在 1/100 概率下才可能相等，这里直接断言大概率不同
        self.assertNotEqual(g1.delta, g2.delta)

    def test_weight_is_caloric_truth(self):
        """体重 = kcal / 7700 * 1000，不随随机系数浮动。"""
        f = foods_mod.match("巨无霸")
        g1 = genes_mod.express(f, 1, random.Random(1))
        g2 = genes_mod.express(f, 1, random.Random(2))
        self.assertEqual(g1.delta["weight"], g2.delta["weight"])
        self.assertAlmostEqual(g1.delta["weight"], f["kcal"] / 7.7, places=1)


class TestAccident(unittest.TestCase):
    def test_fries_spill_changes_stats(self):
        rng = random.Random(1)
        a = next(x for x in acc_mod.ACCIDENTS if x.key == "fries_spill")
        stats = {"charm": 50, "vitality": 50, "bp": 100, "wisdom": 0, "weight": 0}
        changes, tag, blood, logs = acc_mod.resolve(a, stats, rng)
        self.assertTrue(any("颜值" in ln for ln in logs) or "charm" in str(logs))
        self.assertEqual(tag, "满地金黄")
        self.assertEqual(blood, "薯条精")


class TestForms(unittest.TestCase):
    def test_sugar_demon(self):
        stats = {"charm": 10, "wisdom": 10, "vitality": 10, "bp": 100, "weight": 1000, "luck": 50}
        f = forms_mod.judge(stats, {"甜品": 3, "饮料": 0}, 6, 0)
        self.assertEqual(f.name, "糖分恶魔")

    def test_hypertension_cat(self):
        stats = {"charm": 10, "wisdom": 10, "vitality": 10, "bp": 200, "weight": 1000, "luck": 50}
        f = forms_mod.judge(stats, {"牛肉": 2}, 2, 0)
        self.assertEqual(f.name, "高血压猫")


class TestForge(unittest.TestCase):
    def test_end_to_end(self):
        r = parse_text("巨无霸 x2, 麦乐鸡5块, 大薯条, 草莓麦旋风, 可乐中杯",
                       match_fn=foods_mod.match)
        b = forge_mod.forge(r, seed=7, quiet=True)
        self.assertIn(b.form.name, forms_mod.ART)
        self.assertIn("charm", b.stats)
        self.assertIn("luck", b.stats)
        self.assertGreaterEqual(b.stats["bp"], 40)
        self.assertGreaterEqual(b.stats["weight"], 500)
        # 翻车词条去重
        self.assertEqual(len(b.tags), len(set(b.tags)))

    def test_different_seeds_different_pets(self):
        r = parse_text("巨无霸 x2, 麦乐鸡5块, 大薯条, 草莓麦旋风, 可乐中杯",
                       match_fn=foods_mod.match)
        b1 = forge_mod.forge(r, seed=1, quiet=True)
        b2 = forge_mod.forge(r, seed=2, quiet=True)
        self.assertTrue(
            b1.form.name != b2.form.name or b1.stats != b2.stats
        )


if __name__ == "__main__":
    unittest.main()
