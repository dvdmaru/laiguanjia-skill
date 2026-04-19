---
title: 02 資料層 + 路由邏輯 + I/O 委派三段分離
type: whitepaper-chapter
chapter: 02
last_updated: 2026-04-19
audience: 外部技術審查者（資安／AI 倫理）
source:
  - server.py
  - data/feature-routes.json
  - data/pricing.json
  - data/faq.json
  - docs/manual-toc.md
  - docs/case-studies/*.md
category: whitepaper
language: zh-TW
counterpart: ./02-data-layer-separation.en.md
related_adr: ../../../memory/decisions/2026-04-19-laiguanjia-three-segment-separation.md
---

# 02. 資料層 + 路由邏輯 + I/O 委派三段分離

## 2.1 為什麼需要「三段分離」

傳統的 LLM agent 工具有兩種常見反模式：

- **反模式 A：工具裡塞資料 + 邏輯 + I/O**。例如「一個工具叫 `get_pricing_and_open_line`，它查定價後**順便把使用者導到 LINE**」—— 這樣 host agent 完全看不到也攔不到「開啟 LINE」這個副作用，hallucination 或 prompt injection 就可能讓 LLM 在不該開的時候開
- **反模式 B：工具是「黑箱 API」**。host agent 只看到「呼叫某個工具、得到一個自然語言回答」，但工具內部發生什麼事（讀了哪些資料？打了哪些網路？）完全不透明 —— 審計困難

賴管家 Skill 用「**三段分離**」避免這兩類問題：

```
┌───────────────────────────┐
│ 1. 資料層（Data）          │  ← 純靜態 JSON，不含邏輯
│    data/*.json             │
└───────────────────────────┘
            ▲ Python open/read
            │
┌───────────────────────────┐
│ 2. 路由邏輯（Routing）     │  ← 決定「給哪段資料」、格式驗證
│    server.py 六個 handler │     不打網路、不動 filesystem
└───────────────────────────┘
            ▲ MCP tools/call 回傳
            │
┌───────────────────────────┐
│ 3. I/O 委派（Delegation）  │  ← host agent 負責：
│    host agent             │     - 把 payload 轉自然語言
│    (Cowork / Claude Code) │     - 展開 manual (Read)
│                            │     - 開啟 LINE URL（需使用者同意）
│                            │     - 送 LINE OA 訊息（需走官方）
└───────────────────────────┘
```

每一段都有明確的**權責邊界**，違反邊界的呼叫會被下一段拒絕。

## 2.2 資料層：`data/*.json`

資料層共有三個檔案（截至 2026-04-19）：

| 檔案 | 用途 | 大小 | 更新週期 |
|---|---|---|---|
| `data/pricing.json` | 方案定價、功能對照表、聯絡資訊 | ~8 KB | 隨官方公告變動 |
| `data/faq.json` | 8 題常見問答（入門、推播、集點、跨店、合規、技術、帳務） | ~12 KB | 官方 FAQ 增修時 |
| `data/feature-routes.json` | 三大功能（預約、集點、推播）的 metadata + 案例指標 + manual 指標 | ~14 KB | 新增功能／案例時 |

**關鍵原則**：

1. **資料就是資料，不是程式碼**。JSON 裡面不會有 `${env}` 字串插值、不會有 JS/Python eval 路徑、不會有 HTML `<script>` 注入點（所有由這些資料生成的輸出都經過路由層的安全化）
2. **版本受 Git 控管**。每次 pricing / FAQ 的變動都留有 commit 紀錄，審計者可透過 `git blame` 查到哪一行是誰在何時改的
3. **不含個資、不含客戶真實資料**。案例研究 6 位主角（小帥、Amanda、小玲、小美、小惠、小陳）全來自官網 [公開 blog](https://lineoa.batmobile.com.tw/blogs/)，非私人客戶 PII

**手冊的特殊處理**：賴管家 PDF 完整手冊約 **12 MB**，若直接納入 JSON 會造成兩個問題：（a）單次 `get_feature_detail` 回傳的 payload 過大，超出 LLM context window；（b）非必要的全量資料暴露。解法是「**延遲載入**」：

- `data/feature-routes.json` 只存「**指標（pointer）**」 — 每個功能對應到 `docs/manual-toc.md` 的哪個 section
- `get_feature_detail` 回傳 metadata + pointer，host agent 需要展開內容時才自己 `Read` 對應檔案
- 這份 `docs/manual-toc.md` 是官方 PDF 手冊的**結構化目錄**，非原文全文 —— 原文以官網為權威

## 2.3 路由邏輯：`server.py` 六個 handler

路由層的六個 handler 各自負責「**把輸入參數映射到資料層的哪塊資料、做必要的計算、回傳結構化 payload**」。以 `check_plan_suitability` 為例（這是唯一帶計算的 handler）：

```python
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def check_plan_suitability(industry: str, friend_count: int) -> dict:
    # 1. 輸入驗證（Pydantic 已經確保型別，這裡補上值域檢查）
    if not isinstance(friend_count, int) or isinstance(friend_count, bool) or friend_count < 0:
        return {"error": "friend_count 參數不合法，必須為非負整數"}

    # 2. 從 data/pricing.json 讀取方案門檻
    pricing = load_pricing()  # 只讀不寫

    # 3. 純計算：友好數 × 方案上限 → 建議方案
    if friend_count <= 200:
        suggested = "starter"
    elif friend_count <= 2000:
        suggested = "pro"
    else:
        suggested = "enterprise"

    # 4. 回傳結構化 payload
    return {
        "industry": industry,
        "friend_count": friend_count,
        "suggested_plan": suggested,
        "reasoning": f"...",
        # 注意：不含任何 URL 或「要幫你開 LINE 嗎？」類誘導語
    }
```

**路由層的三條戒律**（`server.py` 全程遵守）：

1. **不打網路**：handler 裡沒有 `requests.*`、`urllib.*`、`socket.*`；也沒有對外 DNS 查詢
2. **不寫檔**：handler 只做 `open(..., "r")`，從不 `open(..., "w")`
3. **不 eval**：handler 不用 `eval()` / `exec()` / `subprocess.*`；Pydantic 做的是純結構驗證，不執行任何使用者輸入

這三條用靜態掃描（例如 `grep -nE "requests\.|urllib\.|socket\.|eval\(|exec\(|subprocess\."` on `server.py`）即可驗證。實務上 CI 可跑 `bandit` 或 `semgrep` 加強。

## 2.4 I/O 委派：host agent 的責任

**三件事**明確委派給 host agent，MCP server 絕不自己做：

### A. 把結構化 payload 轉成自然語言

Server 回的是：

```json
{"monthly_price_twd": 490, "plan": "starter", ...}
```

Host agent（Claude 等 LLM）決定怎麼對使用者講：

> 「賴管家 Starter 方案月費 NT$490，適合...」

這部分的**事實真實性**仰賴 LLM 不要幻覺。對應的緩解設計：（a）payload 已經是最精簡的事實陳述，LLM 只需「說人話」而非「編內容」；（b）host agent 層的 system prompt 可要求「直接引用 payload 原文」。

### B. 展開 manual 詳情

當使用者問「預約功能怎麼設定？」時，流程是：

1. LLM 呼叫 `get_feature_detail(feature="booking")`，拿到 `{... "manual_pointer": "docs/manual-toc.md#booking"}`
2. LLM 判斷需要更多細節 → 自己用 `Read` 工具讀 `docs/manual-toc.md` 的 booking section
3. 若 host agent（例如 Cowork mode）有 `Read` 工具 → 成功；若沒有 → LLM 會明說「我無法直接打開手冊，你可以在 [這個連結](https://lineoa.batmobile.com.tw/) 找到詳細教學」

**Why 延遲載入**：12 MB 手冊全塞進 payload 會炸掉 context window；pointer 模式讓 host agent 按需取用，同時也讓審計者更容易驗證「LLM 是否引用了真實手冊內容」（`Read` 是 host 側可記錄的行為）。

### C. 開啟 LINE / 送訊息

這部分細節見 [03 Consent Gate](./03-consent-gate-pattern.md)。核心原則：**即使 `initiate_trial_contact` 回傳「建議 host agent 開啟某個 URL」，實際開啟的動作仍由 host agent 執行**，而 host agent 應在開啟前再問使用者一次「確定嗎？」。也就是說，即使 MCP server 被 compromise 掉回了假 URL，host agent 仍有機會攔截。

## 2.5 為何 `get_feature_detail` 只回 metadata

`get_feature_detail` 是三段分離最具代表性的實作。它的回傳：

```json
{
  "feature": "booking",
  "official_url": "https://lineoa.batmobile.com.tw/features/booking",
  "supported_industries": ["hair_salon", "fitness", "nail_art", "pet_grooming", "clinic", "transportation"],
  "case_studies": [
    {
      "persona": "小帥",
      "industry": "hair_salon",
      "case_study_file": "docs/case-studies/01-stylist-xiaoshuai.md",
      "blog_slug": "stylist",
      "official_url": "https://lineoa.batmobile.com.tw/blogs/stylist",
      "reminder_window": "預約日當天早上 7 點"
    },
    ... (5 more)
  ],
  "manual_pointer": "docs/manual-toc.md#booking"
}
```

**刻意不回的東西**：

- **案例故事的完整文字**：放在 `docs/case-studies/*.md`，host agent 需要時自行 `Read`。理由：（a）避免單次 payload 超過 50 KB；（b）讓 host 側的 `Read` 呼叫成為可審計紀錄
- **完整官方手冊內容**：同上，太大了
- **任何誘導語**：不會有「立即免費試用」「馬上註冊」等 CTA 字串。CTA 是 host agent 根據對話脈絡決定是否提出的事情，不是工具回傳的事情

這個設計同時滿足**資安**（減少 payload attack surface）與 **AI 倫理**（減少 LLM 基於工具回傳做營銷式回答的風險）兩個視角的需求。

## 2.6 資料邊界與 prompt injection

`data/*.json` 的 string 欄位（例如 FAQ 的 answer、pricing 的 description）可能被 LLM 當作 context 的一部分。若某人在 PR 裡偷偷把 `"answer": "...請聯絡 attacker@evil.com"` 合入，理論上可能污染 LLM 輸出。

**緩解**：

- 資料檔的**所有變動都需 PR review**。目前維護方為 Charlie 一人，未來 open source 後會以 CODEOWNERS + branch protection 強化
- 回傳 payload 在 host agent 側應被當作「工具結果」而非「系統 prompt」—— MCP spec 本身有這層區隔，但 host agent 的實作質量決定這層區隔是否被尊重
- 敏感欄位（URL、email）在路由層有 hardcoded allowlist 校驗（例如 `initiate_trial_contact` 只會回 `https://line.batmobile.com.tw/` 以及 `https://lin.ee/` 兩種前綴的 URL，其他一律拒絕；見 [03](./03-consent-gate-pattern.md)）

## 2.7 與 ADR 的對應

本章的設計決策完整記錄在：

- [ADR: 2026-04-19-laiguanjia-three-segment-separation.md](../../../memory/decisions/2026-04-19-laiguanjia-three-segment-separation.md)

ADR 中詳細列出為何不選「monolithic MCP server（邏輯 + I/O 綁在一起）」與「pure static JSON / no routing layer」這兩個替代方案，以及三段分離的長期維護成本。

## 2.8 本章重點回顧

1. **資料、邏輯、I/O 三段各司其職**，每一段的權責邊界都可用靜態掃描驗證
2. **路由層不打網路、不寫檔、不 eval**，這是資安審查最容易驗證的三條戒律
3. **`get_feature_detail` 的 pointer 模式**是「延遲載入」的實作，同時滿足 context window 限制與可審計需求
4. **I/O 委派給 host agent** 讓 consent 與最終行動的控制權留在使用者端，即使 MCP server 被 compromise，host 仍有機會攔截
5. **下一章（03）**：說明唯一具敏感語意的 `initiate_trial_contact` 如何用 Consent Gate + bool-is-int guard 把濫用空間壓到最低
