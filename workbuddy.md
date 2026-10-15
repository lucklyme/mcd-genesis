# WorkBuddy 使用说明

## 已配置的 MCP

本机 `~/.workbuddy/mcp.json` 中已配置：

```json
{
  "mcd-mcp": {
    "type": "streamablehttp",
    "url": "https://mcp.mcd.cn",
    "headers": {
      "Authorization": "Bearer ${MCD_MCP_TOKEN}"
    }
  }
}
```

需要在 WorkBuddy 左侧栏【专家·技能·连接器】→【连接器】中启用 `mcd-mcp`。

## 如何与 WorkBuddy 配合使用

1. 用户在 WorkBuddy 中上传麦当劳账单截图
2. 调用 `python -m mcd_genesis hatch --image <截图路径>`
3. WorkBuddy 将终端输出以卡片形式展示给用户
4. 用户可复制 ASCII 出生公告或 `--seed` 复现自己的那只宠物

## 示例对话

```
用户：这是我今天的麦当劳账单，捏一只看看
AI：python -m mcd_genesis hatch --image /tmp/receipt.png
AI：<展示出生公告>

用户：这只太丑了，重新捏
AI：python -m mcd_genesis hatch --image /tmp/receipt.png
AI：<展示新的出生公告>
```

## 注意事项

- Windows OCR 依赖系统简体中文语言包，识别失败时退回文本输入
- `--seed` 可复现同一只宠物，适合在 WorkBuddy 中固定展示
- 离线模式无需 Token，新用户零配置即可运行
