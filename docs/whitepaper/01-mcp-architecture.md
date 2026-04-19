---
title: 01 MCP 架構總覽
type: whitepaper-chapter
chapter: 01
last_updated: 2026-04-19
audience: 外部技術審查者（資安／法務／AI 倫理窗口）
source:
  - server.py
  - mcp-spec.md
category: whitepaper
language: zh-TW
counterpart: ./01-mcp-architecture.en.md
---

# 01. MCP 架構總覽

## 1.1 為什麼這個 Skill 用 MCP 而不是 REST API

賴管家 Skill 的核心目標是讓 LLM agent（Claude Desktop、Cowork mode、Claude Code 等）**在對話中自主查詢**店家使用情境、方案適配、定價等資訊，並在使用者明確同意後代為開啟 LINE 試用入口。對應的技術需求是：

- **LLM 要能在推理過程中動態呼叫工具**（而不是使用者手動查完資料再貼給 LLM）
- **工具介面要有型別、有 schema、有描述**（讓 LLM 能正確理解、不要幻覺參數）
- **工具呼叫要可審計**（每次 call、參數、回傳 payload 都能被 host 側記錄）
- **不綁特定 LLM 廠商**（今天是 Claude，未來可能是其他支援 MCP 的 agent）

比較過的三個選項：

| 選項 | 優勢 | 劣勢 |
|---|---|---|
| A. REST API + 自寫 Prompt 工具描述 | 技術門檻低、開發者最熟悉 | 不同 LLM 要寫不同 prompt；工具描述無標準 schema；host 側需自建 audit trail |
| **B. MCP server（本選擇）** | 開放標準（Anthropic + 社群）；型別與 annotations 內建；host agent 自動有 audit；跨 LLM 可攜 | Spec 仍在演進（v2025-03-26 目前版本）；社群工具生態比 REST 小 |
| C. 直接做成 Anthropic「Claude Skill」資料夾 | 門檻最低（純 Markdown） | 只能在 Claude 生態使用；無結構化工具呼叫；無法做 consent gate |

選 B。本 Skill **同時**以 Claude Skill 形式（讓 Claude 讀 `SKILL.md` 載入 prompt）與 MCP server 形式（讓任何支援 MCP 的 host 使用 6 個工具）雙形式發布 —— Claude Skill 是對 Claude 生態最友善的載入包裝、MCP 是跨生態的工具介面。兩者共用同一組 `data/*.json` 真實資料與同一個 `server.py`。

選擇的完整決策紀錄見 [2026-04-17-laiguanjia-X+Z-strategy.md](../../../memory/decisions/2026-04-17-laiguanjia-X+Z-strategy.md)。

## 1.2 MCP 技術棧

- **MCP spec 版本**：2025-03-26（截至 2026-04-19 仍為最新 stable）
- **Server 實作**：Python [`mcp`](https://pypi.org/project/mcp/) 套件之 `FastMCP`（高階裝飾器 API）
- **Transport**：`stdio`（標準輸入輸出）—— host agent 以子程序方式啟動本 server，彼此透過 stdin/stdout 交換 JSON-RPC 訊息
- **Python 版本**：3.13（python.org 官方 installer 版本，非 conda）
- **依賴管理**：`requirements.txt` + 專案本地 `.venv`

為什麼選 `stdio` 而不是 HTTP + SSE transport？`stdio` 是 MCP spec 的首選，它有三個好處：

1. **沒有監聽 port**：即使 host 機器上跑著其他服務，本 server 不會開 port、不會被外部掃描到 → 攻擊面 = 0
2. **生命週期跟 host 綁定**：host agent 結束，server 子程序自動收掉，不會有殭屍程序
3. **沒有認證負擔**：既然是 host 啟動的子程序，host 本身就是 trust boundary，不需要額外設計 API key

HTTP + SSE transport 目前僅建議用於「server 與 host 跨機器部署」情境。賴管家 Skill 是完全在使用者本機運作的工具，不需要跨機器，stdio 是正解。

## 1.3 六個工具的介面

完整 Input / Output schema 寫在 [`mcp-spec.md`](../../mcp-spec.md)（共 429 行），本章只列介面摘要：

| # | 工具名稱 | 動詞分類 | 是否讀取使用者資料 | 是否產生外部 I/O | `ToolAnnotations` |
|---|---|---|---|---|---|
| 1 | `get_pricing` | lookup | 否 | 否 | readOnly ✅ destructive ❌ idempotent ✅ openWorld ❌ |
| 2 | `get_faq` | lookup | 否 | 否 | readOnly ✅ destructive ❌ idempotent ✅ openWorld ❌ |
| 3 | `check_plan_suitability` | compute | 否（輸入 = `industry` + `friend_count`，無個資） | 否 | readOnly ✅ destructive ❌ idempotent ✅ openWorld ❌ |
| 4 | `get_feature_detail` | lookup-with-pointer | 否 | 否 | readOnly ✅ destructive ❌ idempotent ✅ openWorld ❌ |
| 5 | `get_contact_and_trial` | lookup | 否 | 否 | readOnly ✅ destructive ❌ idempotent ✅ openWorld ❌ |
| 6 | `initiate_trial_contact` | plan-with-consent | 否（`user_consent` 為 bool，不是個資） | **否**（只回計畫 payload，送訊息是 host agent 的工作） | readOnly ✅ destructive ❌ idempotent ✅ openWorld ❌ |

**三個結論**：

1. **沒有任何工具讀取使用者個資**（姓名、電話、email、LINE ID、地址皆不收）
2. **沒有任何工具產生外部 I/O**（HTTP、file write、db write、message send 全部交由 host agent 處理）
3. **所有工具都是 `destructiveHint=False`**（無任何會刪除、覆寫、扣款的副作用）

對應 `server.py` 實作（節錄第 6 號工具，其他五個結構相同，只是 `readOnlyHint` 等欄位值一致）：

```python
@mcp.tool(
    annotations=ToolAnnotations(
        title="啟動試用 — 僅在使用者明確同意後建議 host agent 開啟連結",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
)
def initiate_trial_contact(user_consent: bool = False) -> dict:
    # consent gate 首檢查 — 詳見第 03 章
    if not isinstance(user_consent, bool) or user_consent is not True:
        return {"error": "consent_required", ...}
    ...
```

`ToolAnnotations` 的四個欄位對 host agent 的意義（摘自 MCP spec）：

- `readOnlyHint=True`：工具不修改外部狀態 → host 可以放心併發呼叫、可以 retry
- `destructiveHint=False`：工具的副作用可逆（在我們這裡是「沒有副作用」，更強的保證）
- `idempotentHint=True`：同樣輸入多次呼叫等於一次呼叫 → host 可以安全 retry
- `openWorldHint=False`：工具不與外部世界互動（無網路、無 filesystem write）→ host 知道不需要給使用者「允許存取外部」的授權提示

資安審查可以把這張表當作「本 Skill 宣稱的副作用範圍」，實際驗證方式寫在 [04 雙層 diff 驗證](./04-dual-layer-validation.md)。

## 1.4 啟動與呼叫流程（端到端）

以下是使用者在 Cowork mode 問「賴管家月費多少？」到最終收到回答的完整流程：

```
┌──────────┐   ①啟動 server 子程序    ┌──────────────────┐
│ Host      │ ─────────────────────> │ laiguanjia-skill │
│ Agent     │      （stdio pipe）      │  MCP server     │
│ (Cowork)  │                         │  (Python 3.13)  │
└──────────┘                         └──────────────────┘
     │                                        │
     │ ②「initialize」JSON-RPC                │
     ├───────────────────────────────────────>│
     │                                        │
     │                ③ 回傳 capabilities    │
     │<───────────────────────────────────────┤
     │                                        │
     │ ④「tools/list」                        │
     ├───────────────────────────────────────>│
     │                                        │
     │        ⑤ 回傳 6 個工具的 schema       │
     │<───────────────────────────────────────┤
     │                                        │
     │【使用者訊息：「賴管家月費多少？」】     │
     │                                        │
     │ ⑥ LLM 決定呼叫 `get_pricing`           │
     │   「tools/call」                        │
     ├───────────────────────────────────────>│
     │                                        │
     │              ⑦ Python handler 跑       │
     │              （讀 data/pricing.json    │
     │               組 payload）              │
     │                                        │
     │        ⑧ 回傳 pricing payload          │
     │<───────────────────────────────────────┤
     │                                        │
     │ ⑨ LLM 把 payload 轉成自然語言回答      │
     │                                        │
     └─> 使用者看到「賴管家月費 NT$490 起...」
```

**關鍵事實**：

- **第 ⑦ 步的 Python handler 不打網路**。所有資料從 `data/*.json` 本地讀取
- **第 ⑧ 步的 payload 是結構化 JSON**，不是自然語言。自然語言只在第 ⑨ 步由 LLM 基於 payload 生成，LLM 與 payload 的關係可追溯（host agent 會把 tool call 記錄下來）
- **手冊內容（manual）不在第 ⑧ 步直接回傳**。`get_feature_detail` 回傳的是「指向 `docs/case-studies/XX-xxx.md` 的檔案路徑」，讓 host agent 在需要時自己 `Read`。這是「延遲載入」設計，避免單次工具回傳 12 MB manual 內容撐爆 context，見 [02](./02-data-layer-separation.md)

## 1.5 資安視角的攻擊面

在 MCP + stdio 架構下，本 Skill 對資安審查者關心的攻擊面如下：

| 攻擊面 | 風險等級 | 緩解 |
|---|---|---|
| **Remote code execution via MCP** | 不存在 | stdio transport 不監聽 port，無法遠端連入 |
| **Privilege escalation via MCP** | 不存在 | server 以 host agent 的使用者權限執行，不要求任何提升 |
| **Data exfiltration via MCP** | 極低 | server 自己不打網路。若 host agent 本身被 compromise，那是 host 的問題、不是 Skill 的問題 |
| **Supply chain (pypi 套件)** | 低 | 依賴只有 `mcp` 官方套件 + `pydantic`（MCP 內建）；`requirements.txt` 鎖死版本，CI 可跑 `pip-audit` |
| **Prompt injection in `data/*.json`** | 中 | 資料來源是 repo 內受版控的 JSON，攻擊者要 PR 才能改；見第 02 章的「資料邊界」 |
| **LLM hallucinate tool call with malicious args** | 低（`initiate_trial_contact` 中等） | 所有工具 Pydantic 驗證型別；唯一有敏感語意的 `initiate_trial_contact` 有 consent gate + bool-is-int 防線，見 [03](./03-consent-gate-pattern.md) |

這份表格的每一列會在後續章節中以具體實作細節展開驗證。

## 1.6 可攜性與鎖定風險

- **MCP spec 是開放標準**（Anthropic 主導，但 protocol 本身不依賴 Claude）。理論上任何支援 MCP 的 host（Claude Desktop、Cowork、Cursor、Continue 等）都可載入本 Skill
- **本 Skill 不使用任何 Claude-only 的 MCP 擴充**（例如 `resources/read`、`prompts/get` 皆未使用 —— 只用 `tools/call` 一類核心 RPC）
- **資料格式是 JSON**，不依賴特定 database 或 service
- **切換 LLM 供應商的遷移成本**：0（因為 Skill 本身不依賴 LLM 供應商）

## 1.7 本章重點回顧

1. 本 Skill 是 **MCP server + Claude Skill 雙形式發布**，以 stdio transport 對 host agent 曝露 6 個工具
2. **6 個工具皆 readOnly / non-destructive / idempotent / closed-world**，且不收個資、不打網路
3. **攻擊面在 MCP 層面上極小**，主要風險是 host agent 本身的 compromise 以及 `data/*.json` 的 supply chain — 前者不在 Skill 控制範圍，後者透過 repo 版控緩解
4. **下一章（02）**：說明「資料層 / 路由邏輯 / I/O 委派」如何進一步把風險壓縮到最低
