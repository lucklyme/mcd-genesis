"""mcd-genesis · 麦麦创世纪

上传一张麦当劳账单，上帝用上面的菜捏一只宠物。
每次捏出来的都不一样——基因表达有随机系数，中途还可能把托盘打翻。

所有营养数据来自麦当劳官方 MCP 的 list-nutrition-foods 接口。
"""

from . import foods, genes, accident, forms, receipt, forge, ocr
from .forge import forge as hatch
from .forge import panel, Birth
from .receipt import parse_text, Receipt, Item

__version__ = "1.0.0"
__all__ = [
    "foods", "genes", "accident", "forms", "receipt", "forge", "ocr",
    "hatch", "panel", "Birth", "parse_text", "Receipt", "Item",
]
