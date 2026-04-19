---
title: 賴管家 Skill — 技術白皮書索引（繁體中文）
type: index
last_updated: 2026-04-19
audience: 外部技術審查者（資安／法務／AI 倫理窗口）
source:
  - server.py
  - mcp-spec.md
  - data/feature-routes.json
  - data/pricing.json
  - data/faq.json
  - tests/*.py
  - memory/decisions/2026-04-17-laiguanjia-X+Z-strategy.md
category: whitepaper
feature: all
language: zh-TW
counterpart: ./README.en.md
---

# 賴管家 Skill — 技術白皮書索引

## 這份文件是給誰看的

這份白皮書是為「**不打算直接安裝或使用本 Skill**、但需要判斷『是否可以信任這個 Skill 被他們的員工／客戶使用』的技術審查者」而寫。典型讀者包含：

- **資安窗口（Security）**：想確認這個 MCP server 的攻擊面、資料外流風險、LLM hallucination 造成的誤觸發風險
- **法務窗口（Legal）**：想確認個資法、消費者保護法、醫療廣告法（如診所情境）在本 Skill 的資料流中是否合規
- **AI 倫理／風控窗口（AI Governance）**：想確認「使用者是否有明確同意」「AI 是否會自主代使用者送出任何行動」「是否有審計紀錄」

如果您是「想開始用賴管家做預約、推播、集點」的店家使用者，這份文件不適合您 — 請直接到 [官方網站（lineoa.batmobile.com.tw）](https://lineoa.batmobile.com.tw/) 或 [免費試用入口](https://line.batmobile.com.tw/)。

## 四章節架構

本白皮書拆為四份子檔（index + 4），每章獨立可讀，之間有明確交叉引用：

| 章節 | 檔名 | 主題 | 建議讀者 |
|---|---|---|---|
| 01 | [01-mcp-architecture.md](./01-mcp-architecture.md) | MCP 架構總覽：FastMCP、stdio transport、6 個唯讀工具的設計 | 全部三類讀者 |
| 02 | [02-data-layer-separation.md](./02-data-layer-separation.md) | 資料層 + 路由邏輯 + I/O 委派三段分離：為何 `get_feature_detail` 只回 metadata | 資安、AI 倫理 |
| 03 | [03-consent-gate-pattern.md](./03-consent-gate-pattern.md) | Consent Gate + bool-is-int guard：`initiate_trial_contact` 的反幻覺／反濫用設計 | 資安、法務、AI 倫理 |
| 04 | [04-dual-layer-validation.md](./04-dual-layer-validation.md) | 雙層 diff 驗證工作流：VM Python × Mac MCP Inspector 三分支 bonus 方法論 | 資安（驗證完整度佐證）、AI 倫理 |

英文版對照檔：同目錄下 `README.en.md` / `01-mcp-architecture.en.md` / `02-data-layer-separation.en.md` / `03-consent-gate-pattern.en.md` / `04-dual-layer-validation.en.md`，內容一對一對照但非逐字翻譯。以繁中版為權威版本，英文版遇到歧義以繁中為準。

## 一頁摘要（TL;DR）

賴管家 Skill 是「**賴管家（Laiguanjia）— 個人工作室／中小商家 LINE OA 經營工具**」的 LLM 代理層。它透過 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 曝露 6 個**唯讀（read-only）**工具給任何支援 MCP 的 host agent（Claude Desktop、Cowork mode、Claude Code 等），協助該 agent 回答「這個店家適不適合賴管家？哪個方案？費用多少？功能怎麼用？」等決策問題。

三個設計選擇構成本 Skill 的可信度基礎：

1. **三段分離**（見 [02](./02-data-layer-separation.md)）：資料在 JSON、邏輯在 Python handler、I/O（外部連線、訊息送出）完全委派給 host agent。MCP server 自己不打網路、不呼任何外部 API、不主動推播。
2. **Consent Gate 先行檢查 + bool-is-int 防線**（見 [03](./03-consent-gate-pattern.md)）：唯一會產出「建議 host agent 送訊息」的工具 `initiate_trial_contact` 用**第一個 check** 攔截無使用者同意的呼叫；`user_consent=1`（Python `bool is int`）也被拒絕，確保 LLM 或攻擊者不能用 truthy 值旁路。
3. **雙層 diff 驗證**（見 [04](./04-dual-layer-validation.md)）：每個工具在 release 前會跑兩層驗證 —— VM Python 內對 6 個工具產出做 JSON canonical diff（bytes 級比對）+ Mac 端 MCP Inspector 對同一組 payload 做 UI spot check（catches JSON-RPC layer 問題）。這兩層的交集才算通過。

6 個工具的介面（完整 schema 見 [mcp-spec.md](../../mcp-spec.md)）：

| 工具 | 動詞 | 最昂貴副作用 |
|---|---|---|
| `get_pricing` | GET | 無 |
| `get_faq` | GET | 無 |
| `check_plan_suitability` | GET（計算） | 無 |
| `get_feature_detail` | GET | 無（回 metadata + 附 `case_study_file`/`blog_slug` 讓 host agent 自行 Read/fetch 展開內容） |
| `get_contact_and_trial` | GET | 無 |
| `initiate_trial_contact` | GET（計畫）| **回傳一個 host agent 應該問使用者「要不要幫你開 LINE？」的 payload**，但 MCP server 自己不開任何連結、不送訊息。與 [pricing.json 公開聯絡資料](../../data/pricing.json) 本質相同，差異在於 consent gate + audit metadata |

**沒有任何工具 destructive（不會刪資料、不會扣款、不會覆寫店家設定）**，這點在每個工具的 `ToolAnnotations(destructiveHint=False)` 明確標示，見 [01](./01-mcp-architecture.md) 第 3 節。

## 與 ADR（架構決策紀錄）的對應

本白皮書的每一章有對應的 ADR（Architecture Decision Record），ADR 記錄「做這個決定的當下評估了哪些選項、為什麼不選另一個」，白皮書則說明「最終決定在實作上長什麼樣」。兩者互補：

| 白皮書章節 | 對應 ADR |
|---|---|
| 01-mcp-architecture | [2026-04-17-laiguanjia-X+Z-strategy.md](../../../memory/decisions/2026-04-17-laiguanjia-X+Z-strategy.md)（決定做 MCP Skill 的上游決策）|
| 02-data-layer-separation | [2026-04-19-laiguanjia-three-segment-separation.md](../../../memory/decisions/2026-04-19-laiguanjia-three-segment-separation.md) |
| 03-consent-gate-pattern | [2026-04-19-laiguanjia-consent-gate-pattern.md](../../../memory/decisions/2026-04-19-laiguanjia-consent-gate-pattern.md) |
| 04-dual-layer-validation | [2026-04-19-laiguanjia-dual-layer-validation.md](../../../memory/decisions/2026-04-19-laiguanjia-dual-layer-validation.md) |

## 範圍外

以下議題**不在本白皮書範圍內**，若審查者需要可另案提供：

- **賴管家產品本身的後端架構**（LINE OA Messaging API 串接、推播排程引擎、店家後台） — 本 Skill 是**外部代理層**，不觸及產品後端
- **LINE OA 個資合規細節**（LINE 平台自己的 ToS、台灣個資法在 LINE OA 上的實作細節） — 屬於 LINE Corp 與賴管家產品的合約層
- **案例研究的客戶真實資訊**（6 位產業主角皆來自 [官網 blog](https://lineoa.batmobile.com.tw/blogs/) 公開內容，非客戶真實個資）
- **徽章系統（P1.5）、示範影片（P1.6）** — 屬於 Z 軌後續階段，本白皮書只涵蓋 Skill 核心技術

## 版本與維護

- **本版本**：2026-04-19 P1.3b 初版
- **維護方**：Charlie Chien（[charlie.chien@gmail.com](mailto:charlie.chien@gmail.com)）
- **Repo**：[github.com/dvdmaru/laiguanjia-skill](https://github.com/dvdmaru/laiguanjia-skill)
- **LICENSE**：本 Skill 程式碼以 MIT 授權；資料（`data/*.json` 含官方定價、FAQ）版權屬「賴管家 / Batmobile」，Skill 使用者必須透過 `get_contact_and_trial` 導向官方正式渠道，不得私下轉售或以誤導方式引用
- **更新觸發條件**：當 `server.py`、`data/*.json`、或 `mcp-spec.md` 任一有變動時，對應章節必須在同一個 commit 更新；若牽涉三段分離、consent 流程、驗證方法的**設計變動**，同時新增 ADR

## 建議閱讀順序

- **資安窗口**：01 → 02 → 03 → 04（由淺入深，每章都針對資安視角補充）
- **法務窗口**：01（跳過 FastMCP 技術細節）→ 03（重點：Consent Gate、個資法、醫療廣告法）→ 02（輔助理解資料邊界）
- **AI 倫理／風控窗口**：03（Consent 是否真的是 informed consent？）→ 04（驗證是否獨立可重現？）→ 02 → 01

## 疑問提出管道

審查過程中如有疑問，請在 [Issues 頁](https://github.com/dvdmaru/laiguanjia-skill/issues) 開 issue，並標記 `whitepaper-review` label，我會在 **2 個工作天內**首次回覆。涉及敏感內容（例如揭露特定客戶資料疑慮）可寄 charlie.chien@gmail.com 私下討論，回覆承諾相同。
