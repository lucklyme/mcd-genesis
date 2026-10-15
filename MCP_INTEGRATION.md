# MCP 集成说明

## 接入的麦当劳 MCP 能力

本项目基于麦当劳官方 MCP Server（`https://mcp.mcd.cn`）构建，使用了以下工具：

| MCP Tool | 用途 |
|---|---|
| `list-nutrition-foods` | 获取 158 个真实在售餐品的营养数据 |
| `now-time-info` | 仅用于端到端连通性验证（可选） |

## 认证方式

- MCP Token 通过 **环境变量** `MCD_MCP_TOKEN` 传入
- 仓库内不出现真实 Token；仅提供 `mcp-config.example.json` 占位模板
- 本地 WorkBuddy 配置位于 `~/.workbuddy/mcp.json`

## 两种运行模式

### 离线模式（默认）

使用内置快照 `data/foods.json`（2026-10-15 从 `list-nutrition-foods` 真实接口保存）。

```bash
python demo.py
python -m mcd_genesis hatch "巨无霸 x2, 麦乐鸡"
```

离线模式**不需要任何 Token**，适合新用户 clone 后直接体验。

### 实时模式

从麦当劳 MCP 拉取最新营养数据。

```bash
set MCD_MCP_TOKEN=你的Token
python demo.py --live
```

实时模式仅刷新饲料库，账单解析、捏人逻辑与离线模式完全一致。

## 数据流

```
麦当劳账单截图 / 手输文本
        ↓
OCR 识别（Windows 内置引擎）/ 文本解析
        ↓
菜品名模糊匹配 → 158 个真实餐品之一
        ↓
营养字段（kcal/protein/fat/carb/sodium/calcium）
        ↓
基因映射 + 随机浮动 + 翻车事件
        ↓
属性面板 / ASCII 立绘 / 稀有度 / 命运判词
```

## 合规说明

- 不存储、不上传用户账单图片；OCR 在本地完成
- 所有 MCP Token 仅走环境变量，不落盘、不进仓库
- 参赛仓库中不存在任何真实凭证
