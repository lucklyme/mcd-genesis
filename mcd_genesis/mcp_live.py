"""实时模式：直接从麦当劳 MCP Server 拉取真实营养数据。

零第三方依赖（只用标准库 urllib）。
Token 从环境变量 MCD_MCP_TOKEN 读取，**绝不硬编码**。

用到的是 MCP 工具 `list-nutrition-foods`，它返回 160 个真实在售餐品的
能量 / 蛋白质 / 脂肪 / 碳水 / 钠 / 钙。McLang 的每条指令都能在这里找到原型，
所以小票上的每一个数字都是真的。
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

MCP_URL = "https://mcp.mcd.cn"
DEFAULT_TIMEOUT = 25


class MCPError(RuntimeError):
    pass


def _token() -> str:
    tok = os.environ.get("MCD_MCP_TOKEN", "").strip()
    if not tok:
        raise MCPError(
            "未检测到环境变量 MCD_MCP_TOKEN。\n"
            "  获取方式：登录 https://open.mcd.cn/mcp -> 控制台 -> 激活 -> 复制 MCP Token\n"
            "  设置方式：export MCD_MCP_TOKEN=你的Token   （Windows: set MCD_MCP_TOKEN=你的Token）\n"
            "  不配置也能玩：python demo.py 会用内置快照（真实数据）演示。"
        )
    return tok


def _json_from(text: str, start: int) -> Any:
    dec = json.JSONDecoder()
    return dec.raw_decode(text[start:])[0]


def _parse_payload(raw: str) -> Any:
    """MCP 响应可能是裸 JSON / SSE，payload 本身还可能是 Markdown 包着的。"""
    raw = raw.strip()
    if raw.startswith("{"):
        obj = json.loads(raw)
    else:
        obj = None
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                body = line[len("data:"):].strip()
                if body:
                    obj = json.loads(body)
                    break
        if obj is None:
            raise MCPError(f"无法解析 MCP 响应：{raw[:200]}")

    result = obj.get("result", obj)
    if isinstance(result, dict) and isinstance(result.get("structuredContent"), dict):
        return result["structuredContent"]

    contents = result.get("content") if isinstance(result, dict) else None
    if isinstance(contents, list):
        for item in contents:
            text = item.get("text", "") if isinstance(item, dict) else ""
            if not text:
                continue
            marker = text.find("## Original Response")
            search = text[marker:] if marker >= 0 else text
            idx = search.find("{")
            if idx >= 0:
                try:
                    return _json_from(search, idx)
                except ValueError:
                    continue
    return result


def call_tool(tool: str, arguments: Optional[Dict[str, Any]] = None,
              url: str = MCP_URL) -> Any:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments or {}},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {_token()}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise MCPError("401 未授权：MCP Token 无效或已过期，请重新申请。") from exc
        if exc.code == 429:
            raise MCPError("429 限流：单 Token 每分钟最多 600 次请求，请降低频率。") from exc
        raise MCPError(
            f"MCP 调用失败 HTTP {exc.code}：{exc.read().decode('utf-8', 'ignore')[:200]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise MCPError(f"网络错误：{exc.reason}") from exc
    return _parse_payload(raw)


# ---------------------------------------------------------------------------
# list-nutrition-foods 的返回是一个自定义文本表格，需要专门解析
# ---------------------------------------------------------------------------

_HEADER_RE = re.compile(r"\{([^}]*)\}")


def parse_nutrition_text(text: str) -> List[Dict[str, Any]]:
    """解析形如：

        [160]{productName,nutritionDescription,energyKj,energyKcal,...}:
          猪柳麦满分,null,1288,308,16,16,24,781,213
          ...

    的自定义表格文本，返回结构化的餐品列表。
    """
    if not isinstance(text, str):
        raise MCPError("营养数据格式异常：期望字符串")

    m = _HEADER_RE.search(text)
    if not m:
        raise MCPError("营养数据格式异常：找不到字段头")
    fields = [f.strip() for f in m.group(1).split(",")]

    rows: List[Dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("[") or "{" in line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < len(fields):
            continue
        row: Dict[str, Any] = {}
        for i, key in enumerate(fields):
            val = parts[i]
            if key == "productName" or key == "nutritionDescription":
                row[key] = "" if val in ("null", "None", "") else val
            else:
                try:
                    row[key] = float(val)
                except ValueError:
                    row[key] = 0.0
        if row.get("productName"):
            rows.append(row)
    return rows


def fetch_nutrition() -> List[Dict[str, Any]]:
    """调用 MCP 拉取真实餐品营养数据。"""
    payload = call_tool("list-nutrition-foods", {})
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, str):
            return parse_nutrition_text(data)
        if isinstance(data, list):
            return data
    if isinstance(payload, str):
        return parse_nutrition_text(payload)
    return []
