"""账单解析：把一段 OCR 文本（或手输文本）拆成「菜名 + 数量 + 金额」。

麦当劳小票的常见噪声行——合计、优惠、会员、订单号、门店、时间——在这里被拦掉。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

# 噪声行关键词：命中即丢弃
NOISE = (
    "合计", "小计", "总计", "共", "应付", "实付", "应收", "找零", "优惠", "折扣", "减免",
    "会员", "积分", "余额", "支付方式", "支付", "微信", "支付宝", "银行卡", "现金",
    "订单", "单号", "流水", "交易", "商户", "门店", "餐厅", "地址", "电话",
    "时间", "日期", "时段", "取餐", "堂食", "外送", "外卖", "取单", "排队", "桌号",
    "谢谢", "惠顾", "欢迎", "光临", "发票", "税率", "税额",
    "麦乐送", "配送", "服务费", "包装", "餐具",
    "数量", "单价", "金额", "品名", "商品",
)

_DATE_RE = re.compile(r"20\d{2}[-/—一][01]\d[-/—一][0123]\d")
_TIME_RE = re.compile(r"\d{1,2}\s*[:：]\s*\d{2}")

# 数量：x2 / ×2 / *2 / 2份 / 2个
# 注意：量词里刻意不含「块」——「麦乐鸡5块」的 5 是品名的一部分（5 块装），
# 若当成数量会把钠直接乘 5 倍。份/个/件/杯/盒 才是真正的购买量词。
_QTY_RE = re.compile(r"(?:[xX×*]\s*(\d{1,2})|([\d]{1,2})\s*(?:份|个|件|杯|盒))")
# 金额：¥25.5 / ￥25.5 / 25.50元 / 25.5
_PRICE_RE = re.compile(r"[¥￥]\s*(\d+(?:\.\d{1,2})?)|(\d+(?:\.\d{1,2})?)\s*元")
_TOTAL_RE = re.compile(r"(?:合计|总计|实付|应付|应收)[^\d]{0,6}(\d+(?:\.\d{1,2})?)")


@dataclass
class Item:
    raw: str
    name: str = ""
    qty: int = 1
    price: Optional[float] = None
    matched: Optional[str] = None   # 匹配到的真实餐品名
    food: Optional[dict] = None

    @property
    def ok(self) -> bool:
        return self.food is not None


@dataclass
class Receipt:
    items: List[Item] = field(default_factory=list)
    total: Optional[float] = None
    raw_text: str = ""
    unmatched: List[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.items)


# 中文账单常用分隔符。数字后的千位逗号（1,180.00）不能切，故加 (?!\d) 保护。
_SPLIT_RE = re.compile(r"(?<=[\u4e00-\u9fa5)\d])\s*[,，、;；]\s*(?!\d)")


def _clean(line: str) -> str:
    return line.replace("\u3000", " ").strip()


def _split_items(text: str) -> List[str]:
    """把一行里的多个菜名切开：「巨无霸 x2, 麦乐鸡」-> 两行。"""
    return [ln for ln in _SPLIT_RE.sub("\n", text).splitlines() if ln.strip()]


def _is_noise(line: str) -> bool:
    if not line:
        return True
    if len(line) > 80:              # OCR 把整段糊在一起的长行，不可信
        return True
    # OCR 喜欢在字间加空格，如「合 计 6 件」；去掉空格后再过滤
    compact = line.replace(" ", "").replace("\u3000", "")
    if any(k in compact for k in NOISE):
        return True
    # 日期+时间行是门店信息，不是菜
    if _DATE_RE.search(compact) and _TIME_RE.search(compact):
        return True
    return False


def parse_text(text: str, match_fn=None) -> Receipt:
    """解析账单文本。

    同时支持两种输入：
      1. 手输：巨无霸 x2, 麦乐鸡
      2. OCR 列优先：先识别出所有菜名，再识别出所有数量/价格
    match_fn 由调用方注入（foods.match），避免循环 import。
    """
    r = Receipt(raw_text=text or "")

    m = _TOTAL_RE.search(text or "")
    if m:
        try:
            r.total = float(m.group(1))
        except ValueError:
            pass

    foods_found: List[Item] = []
    qty_prices: List[Tuple[int, Optional[float]]] = []

    for line in _split_items(text or ""):
        line = _clean(line)
        # OCR 常见全角符号统一：全角小数点→半角，中文逗号→半角
        line = line.replace("．", ".").replace("，", ",")
        if _is_noise(line):
            continue

        qty = 1
        qm = _QTY_RE.search(line)
        if qm:
            qty = int(qm.group(1) or qm.group(2) or 1)
            qty = max(1, min(qty, 20))

        price = None
        pm = _PRICE_RE.search(line)
        if pm:
            try:
                price = float(pm.group(1) or pm.group(2))
            except ValueError:
                pass

        # 去掉数量/金额片段，剩下的就是菜名
        name = _QTY_RE.sub("", line)
        name = _PRICE_RE.sub("", name)
        name = re.sub(r"[\s,，、|]+$", "", name).strip(" |·-—")
        name = name.replace(" ", "").replace("\u3000", "")

        # 只剩数字/价格残留 → 这是数量/价格列
        if not name or len(name) < 2 or re.fullmatch(r"[\d\s.,·°℃]+", name):
            qty_prices.append((qty, price))
            continue

        it = Item(raw=line, name=name, qty=qty, price=price)
        if match_fn is not None:
            hit = match_fn(name)
            if hit:
                it.matched = hit.get("name")
                it.food = hit
            else:
                r.unmatched.append(name)
        foods_found.append(it)

    # 对齐：OCR 列优先时，数量/价格行数与菜品行数相同，按顺序一一对应
    if qty_prices and len(qty_prices) == len(foods_found):
        for it, (q, p) in zip(foods_found, qty_prices):
            if q != 1:
                it.qty = q
            if p is not None:
                it.price = p
    else:
        # 兜底：向后归并（数量行紧跟在菜名之后时）
        j = 0
        for it in foods_found:
            while j < len(qty_prices) and qty_prices[j] != (1, None):
                q, p = qty_prices[j]
                if q != 1:
                    it.qty = q
                if p is not None:
                    it.price = p
                j += 1
                break

    r.items = foods_found
    return r
