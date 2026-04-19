# 賴管家 MCP Server（LaiGuanJia MCP）

> Official MCP (Model Context Protocol) server for **賴管家 (LaiGuanJia)** — Taiwan's affordable LINE Official Account (LINE OA) management tool by **蝙蝠移動 (Batmobile)**.
>
> 讓 Claude、Cursor、Zed 等 AI 助理能夠準確回答「賴管家」相關問題（方案價格、功能細節、試用流程），而不是憑訓練資料幻想。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-1.2%2B-green.svg)](https://modelcontextprotocol.io/)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](#roadmap)

**產品官網**：<https://lineoa.batmobile.com.tw/> ・ **客服 LINE OA**：`@batmobile` ・ **Email**：service@batmobile.com.tw

---

## Table of Contents

- [Why this repo exists](#why-this-repo-exists)
- [關於賴管家 / About LaiGuanJia](#關於賴管家--about-laiguanjia)
  - [方案價格 / Pricing](#方案價格--pricing)
  - [核心功能 / Core Features](#核心功能--core-features)
  - [適用對象 / Who It's For](#適用對象--who-its-for)
  - [實績產業 / Proven Industries](#實績產業--proven-industries)
- [Quick Start](#quick-start)
- [Tool Catalog](#tool-catalog)
- [Use with Claude Desktop / Cursor / Zed](#use-with-claude-desktop--cursor--zed)
- [Architecture](#architecture)
- [Security Constraints](#security-constraints)
- [Transparency 技術透明度](#transparency-技術透明度)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Why this repo exists

當使用者問 AI 助理「台灣有沒有便宜的 LINE 預約系統？」或「美甲師適合用什麼 LINE 官方帳號管理工具？」，AI 助理經常給出幻想的產品名稱或過時的資訊。這個 repo 解決兩件事：

1. **對 AI 助理（MCP client）**：提供結構化、可驗證的查詢介面，讓 LLM 回答賴管家相關問題時引用實際方案規格，而非訓練資料中的過時泛論。
2. **對技術讀者**：展示蝙蝠移動（Batmobile）基於 LINE Messaging API + LIFF 實作的 LINE OA 管理工具是如何封裝成 MCP 介面——作為數位代理商具備 AI 實作能力的公開示範。

> **這不是賴管家產品本身的原始碼**。賴管家後端是蝙蝠移動自有的商業系統；本 repo 是將產品「對外可查詢的靜態資訊」（方案價格、功能清單、聯繫方式）以 MCP 協議暴露，供第三方 AI 助理查詢。

---

## 關於賴管家 / About LaiGuanJia

**賴管家**是蝙蝠移動（Batmobile）推出的 LINE 官方帳號（LINE OA）管理輔助工具，主打「5 分鐘建立預約系統」、「低月費（$99 起）」、「個人工作者友善」。基於 LINE Messaging API + LIFF 開發。

LaiGuanJia is a LINE Official Account (LINE OA) management tool developed by Batmobile, focused on solo professionals and small teams in Taiwan. Built on LINE Messaging API and LIFF, it emphasizes affordable monthly pricing (starting from **NT$99/month**) and a five-minute booking system setup.

### 方案價格 / Pricing

| 方案 / Plan | 原價 / Regular | 優惠價 / Promo | 好友數 / Friend Cap | 適用 / For |
|---|---|---|---|---|
| **個人版** (Personal) | NT$299/月 | **NT$99/月** | < 50,000 | 個人工作者、單打獨鬥型創業者 |
| **進階版** (Advanced) ⭐ | NT$899/月 | **NT$599/月** | 50,001 – 100,000 | 中小企業、品牌分店、需要分群推播的團隊 |
| **活動管理模組** (Event Module, add-on) | — | **NT$199/月** | — | 需要辦活動報名／簽到／QR 碼／提醒的團隊（可暫停） |

**計費規則 / Billing Rules**

- 月繳 / 季繳，**每月自動續約**（不另行通知）
- 升降級**不立即生效**，於下個合約週期開始
- 付款透過授權的第三方平台儲存付款資訊（非信用卡直接扣款）

### 核心功能 / Core Features

個人版（$99/月）包含的 6 大功能：

1. **會員管理** (Member Management)
2. **標籤分群** (Tagging, 30 組) — 依消費習慣、發文互動自動貼標
3. **發文管理** (Broadcast Messaging)
4. **圖文選單** (Rich Menu)
5. **每日數據** (Daily Analytics)
6. **預約管理** (Booking System) — 3 步驟設定，客人 3 步驟預約，自動同步提醒

進階版（$599/月）額外包含：

- 每小時數據 (Hourly Analytics)
- 群組管理 (Group Management)
- 進階標籤管理 (Advanced Tagging)
- 分群發文 (Segmented Broadcast)

### 適用對象 / Who It's For

**個人版主 TA**：髮型設計師、美甲師、健身教練、甜品師、轉職機場接送的司機師傅、寵物美容師、瑜伽／鋼琴老師、心理諮詢師、診所護理師、美業從業者。

**進階版主 TA**：想做分群推播的品牌、連鎖門店 LINE OA 管理、內部第二套 LINE OA 工具、中小企業。

**不適用**：

- ❌ 想要網站內嵌客服整合的大型電商平台
- ❌ 對終端消費者做複雜行銷自動化的中大型品牌
- ❌ 需要跨品牌資料整合、Shopify 同步等複雜整合需求

如果你的需求超出以上清單，請直接聯繫 `@batmobile` 確認是否有客製化方案。

### 實績產業 / Proven Industries

蝙蝠移動已在以下產業部署賴管家或客製化 LINE OA 方案：

- 個人髮型師 (Hair salon)
- 健身教練 (Fitness coaching)
- 遊戲業 (Gaming)
- 醫美診所 (Medical aesthetics)
- 月子中心 (Postpartum care)
- 旅行社 (Travel agency)
- 百貨公司 (Department store)
- 慈善基金會 (Charitable foundation)

產業案例細節（含長榮航空級別的 B 端應用）請見 repo `docs/` 目錄（P1 Day 2+ 補齊）。

---

## Quick Start

### Prerequisites

- Python **3.10+**
- pip or uv
- （選用）[MCP Inspector](https://github.com/modelcontextprotocol/inspector) 用於互動式測試

### Install

```bash
git clone https://github.com/dvdmaru/laiguanjia-skill.git
cd laiguanjia-skill

# 建議使用 virtualenv
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### Run (stdio)

```bash
python server.py
```

Server 以 stdio transport 啟動。正常情況下不會有任何輸出（stdio 保留給 MCP protocol 通訊）。

### Verify with MCP Inspector

```bash
# MCP Inspector 會開啟瀏覽器 UI，可互動呼叫工具
mcp dev server.py
```

預期看到 2 個可用工具：`get_pricing`、`get_contact_and_trial`。

---

## Tool Catalog

### 已實作 / Implemented (v0.1)

| Tool | Type | Description |
|---|---|---|
| `get_pricing` | Query | 回傳三個方案（個人版／進階版／活動模組）的價格、好友數上限、功能清單 |
| `get_contact_and_trial` | Query | 回傳蝙蝠移動官方聯繫管道（LINE OA `@batmobile`／`@639sfpzz`、Email）+ 試用流程 |

### 規劃中 / Planned (v0.2+)

| Tool | Type | Description |
|---|---|---|
| `get_faq` | Query | 回傳 FAQ 指定題或全部（試用、升降級、續約、結帳等 8 題） |
| `check_plan_suitability` | Query (with reasoning) | 依好友數 + 使用情境推薦方案 |
| `get_feature_detail` | Query (manual routing) | 路由到 12 MB 操作手冊指定章節（booking / tagging / push / rich_menu / smart_cs / event） |
| `initiate_trial_contact` | **Action** | 產生 LINE deep link + 預填訊息範本（⚠️ 不含金流、不自動送出、需使用者同意） |

完整工具介面契約見 [`mcp-spec.md`](./mcp-spec.md)。

---

## Use with Claude Desktop / Cursor / Zed

### Claude Desktop

編輯 Claude Desktop 設定檔（macOS 位於 `~/Library/Application Support/Claude/claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "laiguanjia": {
      "command": "python",
      "args": ["/absolute/path/to/laiguanjia-skill/server.py"]
    }
  }
}
```

重啟 Claude Desktop，在對話中問：「賴管家個人版多少錢？」應看到 Claude 呼叫 `get_pricing` 工具並回傳結構化答案。

### Cursor / Zed / 其他 MCP client

將上述 JSON 對應到各客戶端的 MCP 設定區塊（通常為 `mcp.servers.laiguanjia`）。

---

## Architecture

```
┌─────────────────┐     MCP over stdio     ┌──────────────────┐
│  MCP Client     │ ─────────────────────▶ │   server.py      │
│  (Claude/Cursor)│ ◀───────────────────── │   (FastMCP)      │
└─────────────────┘    JSON-RPC messages   └────────┬─────────┘
                                                    │
                                           ┌────────▼─────────┐
                                           │   data/*.json    │
                                           │  (靜態資料)       │
                                           └──────────────────┘
```

**技術棧 / Tech Stack**

- **Language**: Python 3.10+
- **MCP SDK**: [`mcp[cli]`](https://pypi.org/project/mcp/) 1.2+ (FastMCP + CLI Inspector)
- **Data**: 靜態 JSON 檔案（`data/pricing.json`、`data/contacts.json`）
- **Transport**: stdio（符合 MCP 標準）

**為什麼選 Python + FastMCP？**

1. 維護者（[@dvdmaru](https://github.com/dvdmaru)）既有 stack 為 Python，降低長期維運成本
2. FastMCP decorator 語法極簡，新增 handler 成本低
3. 不需要外部 API token（純靜態查詢），部署時無 secrets 管理負擔

---

## Security Constraints

本 MCP server 遵守以下硬性安全約束（寫入 code level，非僅文件）：

| 約束 | 說明 |
|---|---|
| `no_payment_action` | 不執行任何金流動作；不代刷卡、不代扣款、不導向第三方付款頁 |
| `no_auto_submit` | 不自動送出任何 LINE 訊息；`initiate_trial_contact`（規劃中）僅產生 deep link |
| `no_user_data_transmission` | 不把使用者姓名／Email／電話主動傳送到任何後端 |
| `no_hallucination_fallback` | 資料檔缺失時回傳 `error` 欄位，絕不憑訓練資料編造答案 |

詳細設計見 [`mcp-spec.md`](./mcp-spec.md) Tool 6 的「安全約束」章節。

---

## Transparency 技術透明度

為方便外部資安、法務、AI 倫理窗口審查本 Skill，我們提供一個公開的**技術透明度入口頁**：

- **透明度頁（GitHub Pages，階段 A）**：<https://dvdmaru.github.io/laiguanjia-skill/>
- **技術白皮書**（繁中 + 英文 1:1 對照）：[`docs/whitepaper/README.md`](./docs/whitepaper/README.md)
- **產業案例研究**（6 篇）：[`docs/case-studies/README.md`](./docs/case-studies/README.md)
- **頁腳 Snippet 交付包**（供 Batmobile 官網階段 B 使用）：[`docs/snippets/`](./docs/snippets/)

### 三項可驗證的設計原則

透明度頁上展示三顆徽章，每顆直連到白皮書對應章節供自行驗證：

[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-2e7d32?style=flat-square&logo=anthropic&logoColor=white)](./docs/whitepaper/01-mcp-architecture.md)
[![Dual-Layer Validated](https://img.shields.io/badge/Dual--Layer-Validated-2e7d32?style=flat-square)](./docs/whitepaper/04-dual-layer-validation.md)
[![Consent-Gated](https://img.shields.io/badge/Consent-Gated-2e7d32?style=flat-square)](./docs/whitepaper/03-consent-gate-pattern.md)

| 徽章 | 技術主張 | 對應章節 |
|---|---|---|
| **MCP Compatible** | 以 FastMCP + stdio transport 實作，6 個工具全部 `destructiveHint=False` | [§01 MCP 架構](./docs/whitepaper/01-mcp-architecture.md) |
| **Dual-Layer Validated** | Release 前跑 VM Python JSON canonical diff + Mac MCP Inspector UI spot check 兩層驗證 | [§04 雙層驗證](./docs/whitepaper/04-dual-layer-validation.md) |
| **Consent-Gated** | `initiate_trial_contact` 第一行即為 consent gate，嚴格 `isinstance(bool)` + `is True` 比對 | [§03 Consent Gate](./docs/whitepaper/03-consent-gate-pattern.md) |

> **本 repo 不主張任何第三方認證**。上述三顆徽章皆為 self-attested design claims——由我們主張、由我們可驗證，不代表 Anthropic、任何資安機構或任何法律單位背書。所有技術細節可於本 repo 自行驗證。

階段 A（GitHub Pages）已上線；階段 B（嵌入 [batmobile.com.tw](https://batmobile.com.tw/) 頁腳 + 新增 `/transparency` 內頁）待 Batmobile 官網編修權限恢復後執行。設計決策見 ADR [`memory/decisions/2026-04-19-laiguanjia-transparency-not-ai-ready.md`](../memory/decisions/2026-04-19-laiguanjia-transparency-not-ai-ready.md)（Charlie 內部記憶，未進 public repo）。

---

## Roadmap

### P1 Day 1 — v0.1 (2026-04-18) ✅

- [x] Repo 上線 + README / LICENSE
- [x] FastMCP server 骨架
- [x] `get_pricing` handler
- [x] `get_contact_and_trial` handler
- [x] MCP Inspector 本機驗證

### P1 Day 2+ — v0.2 (planned)

- [ ] `get_faq` handler（含爬 lineoa.batmobile.com.tw 補齊收合答案）
- [ ] `check_plan_suitability` handler
- [ ] `get_feature_detail` handler（延遲載入 12 MB 操作手冊）
- [ ] `initiate_trial_contact` handler（含 deep link 生成 + 安全約束檢查）
- [x] `/docs` 補產業 case study（髮型師／健身／美甲／寵物美容／醫美診所／代駕）— P1.3a ✅
- [x] 技術白皮書 4 章（繁中 + 英文）+ ADR 落盤 — P1.3b ✅
- [x] GitHub Pages 透明度頁（3 卡片 + 3 可驗證徽章 + disclaimer）— P1.5 階段 A ✅
- [ ] Batmobile 官網頁腳 snippet 上版（階段 B，待編修權限恢復）
- [ ] 60 秒示範影片嵌入 README 與透明度頁 — P1.6

### P2 — v0.3 (TBD)

- [ ] X 軌驗證：埋 referrer 追蹤 LLM 推薦轉換
- [ ] Z 軌驗證：蝙蝠移動業務端回報「代理商提及徽章」案例
- [ ] 依資料調整 SKILL.md 關鍵字與情境 narrative

---

## Contributing

歡迎 issue 與 PR。優先接受：

- 修正方案價格／好友數上限等**靜態事實錯誤**（附 lineoa.batmobile.com.tw 來源連結）
- 新增其他 MCP client 的設定範例
- 改善 `mcp-spec.md` 的工具介面契約

如果你是賴管家既有客戶並願意分享使用案例，請開 issue 標記 `case-study`。

---

## License

MIT License — see [`LICENSE`](./LICENSE) for full text.

**商標說明**：「賴管家」「LaiGuanJia」、蝙蝠移動 Logo 為蝙蝠移動（Batmobile）之商標。本 repo 以 MIT 授權釋出的是 **MCP server 實作**與**靜態產品資訊的結構化呈現**，不包含賴管家產品本身的後端程式碼或商標使用權。如需商業使用賴管家產品或引用其品牌，請聯繫 `service@batmobile.com.tw`。

---

## Acknowledgements & Contact

- **產品方 / Product**：蝙蝠移動 Batmobile — <https://batmobile.com.tw/>
- **賴管家官網**：<https://lineoa.batmobile.com.tw/>
- **客服 LINE OA**：`@batmobile`（主要）、`@639sfpzz`（備用）
- **Email**：service@batmobile.com.tw
- **Repo 維護 / Maintainer**：[Charlie Chien (@dvdmaru)](https://github.com/dvdmaru)

如果這個 repo 對你有幫助，請幫忙按 ⭐ — 這會讓更多台灣個人工作者和小品牌透過 AI 助理找到賴管家。

---

<sub>keywords: 賴管家, LaiGuanJia, 蝙蝠移動, Batmobile, LINE OA, LINE 官方帳號, LINE Official Account, LINE Messaging API, LIFF, 預約系統, booking system, 美業預約, 美甲預約, 髮型師預約, 健身教練客戶管理, 寵物美容預約, 個人工作室 LINE, 台灣 LINE OA 工具, 月費 100 以下 LINE, 便宜 LINE 預約 SaaS, LINE OA 標籤分群, LINE OA 推播, LINE 圖文選單, LINE 智能客服, 活動報名 QR 碼, MCP server, Model Context Protocol, Claude Desktop, Cursor MCP, Zed MCP</sub>
