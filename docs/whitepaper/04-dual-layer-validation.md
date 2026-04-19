---
title: 04 雙層 diff 驗證工作流
type: whitepaper-chapter
chapter: 04
last_updated: 2026-04-19
audience: 外部技術審查者（資安／AI 倫理）
source:
  - server.py
  - tests/test_day4.py
  - tests/test_day6_consent_gate.py
  - tests/test_all_tools_smoke.py
category: whitepaper
language: zh-TW
counterpart: ./04-dual-layer-validation.en.md
related_adr: ../../../memory/decisions/2026-04-19-laiguanjia-dual-layer-validation.md
---

# 04. 雙層 Diff 驗證工作流

## 4.1 為什麼「單層驗證」不夠

常見的 MCP server 測試做法有兩類：

- **Type A：只跑 Python unit test**。優點：快、可自動化、CI 友善。缺點：**測不到 MCP 協定層（JSON-RPC 格式、stdio framing、tool schema 序列化）**。程式碼邏輯對，但 MCP client 收到的可能是壞 JSON
- **Type B：只跑 MCP Inspector（官方 UI 工具）**。優點：能看到 host agent 實際會收到的東西。缺點：手動、難 CI、容易 drift（今天手工點過、明天改了程式碼忘了重點）

本 Skill 採用**雙層 diff 驗證**（Dual-Layer Diff Validation）同時解決兩邊限制。核心概念：

> 在 Python 層產生一組「canonical JSON」，在 MCP Inspector 手動 spot check 同一組 payload，兩層做**bytes 級**比對。
> 任一層跟基準不同 = 不通過。

## 4.2 第一層：VM Python 內的 JSON Canonical Diff

**流程**：

1. 定義一組 **fixture 參數**（共 6 組，每個工具一組）
2. 在 Python 裡直接呼叫 6 個 handler，把回傳 dict 轉成 canonical JSON：
   ```python
   json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2)
   ```
3. 與 `tests/fixtures/golden/*.json` 裡的 **golden file** 做 bytes 級 `==` 比對

**關鍵參數**：

- `sort_keys=True`：鍵名排序，避免 Python dict 插入順序變動造成假 diff
- `ensure_ascii=False`：保留中文原字元而非 `\uXXXX` escape，方便人工閱讀 golden file
- `indent=2`：固定縮排，讓 golden file 在 git diff 中可讀

**Golden file 的更新規則**：

- golden file 只能**透過 PR 人工審核**更新。規則：任何 `tests/fixtures/golden/*.json` 的變動必須在 PR description 中說明「為什麼」
- 若因官方定價變動等合理原因需更新，PR 同時改 `data/pricing.json` 與 golden file，reviewer 看到「兩份同步」才能 merge
- 若有人**只改 golden file 但不改 `data/*.json`**，代表企圖繞過驗證 —— 這在 PR review 中會被擋下

**測試執行方式（本地 VM）**：

```bash
cd /sessions/.../laiguanjia-skill
.venv/bin/python -m pytest tests/test_all_tools_smoke.py -v
```

CI 可設為 GitHub Actions 跑同一條命令。目前 repo 尚無 GitHub Actions（P1.3b 後會補 CI workflow，屬 P2 範圍）。

## 4.3 第二層：Mac MCP Inspector Spot Check

**MCP Inspector 是什麼**：Anthropic 官方提供的 MCP server debugger（`npx @modelcontextprotocol/inspector`），以瀏覽器 UI 形式與本地 MCP server 通訊，顯示 JSON-RPC 級別的完整訊息流。

**為什麼需要這層**：

- Python handler 回 dict 很容易對，但從 dict → JSON-RPC response 的序列化由 MCP SDK 負責。若 SDK 有 bug（例如某個欄位名被自動 camelCase 化、某些 Unicode 邊界被 escape 壞），Python 單測抓不到
- Inspector 顯示的是 host agent 實際會收到的 JSON-RPC payload，這是「最接近終端真實情況」的驗證點

**Spot check 流程**：

1. Mac 終端機跑 `npx @modelcontextprotocol/inspector python3 server.py`
2. Inspector 開啟瀏覽器 UI，Charlie 手動點 6 個工具各一次，用**同樣**的 fixture 參數
3. 對比 Inspector 顯示的 JSON-RPC response 與第一層 golden file
4. 若 bytes 完全一致 → 通過；若有任何差異，記錄差異類型並排查是 MCP SDK、Python handler、還是 golden file 的問題

**為什麼是「spot check」而非全覆蓋**：6 個工具每個跑一次已經足夠涵蓋序列化路徑；全覆蓋放在第一層（自動化），這層負責抓「自動化抓不到的」。

## 4.4 三分支 Bonus 方法論

`check_plan_suitability` 的輸入 `friend_count` 決定 3 個分支（`starter / pro / enterprise`）。這個工具的 golden file 有 **3 份**，每個分支一份，fixture 參數跨越邊界：

| Fixture | `friend_count` | 預期分支 |
|---|---|---|
| A | 0 | starter |
| B | 200 | starter（邊界上） |
| C | 201 | pro |
| D | 2000 | pro（邊界上） |
| E | 2001 | enterprise |

這 5 個 case 用最少參數覆蓋所有分支 + 兩個邊界，屬於「**branch coverage + boundary value analysis 混搭**」。Python 單測跑完這 5 個 fixture，第二層 Inspector 只挑 A/C/E 三個（跨三個分支、不重複跑邊界）做 spot check —— 這就是「三分支 bonus」命名的由來。

**這個方法論的通用性**：對任何帶 branch 的工具（例如 `get_faq` 根據 category 分流），皆採同樣模式。對 branch-less 工具（例如 `get_pricing` 無參數），第一層跑 1 個 fixture 即可，第二層同步跑一次。

## 4.5 驗證覆蓋表

截至 2026-04-19 P1.3a 完成時的覆蓋：

| 工具 | 分支數 | 第一層 fixtures | 第二層 spot check |
|---|---|---|---|
| `get_pricing` | 1 | 1 | 1 |
| `get_faq` | 8 (category) | 8 | 3（熱門 category） |
| `check_plan_suitability` | 3 | 5（含邊界） | 3 |
| `get_feature_detail` | 3 (feature) | 3 | 3 |
| `get_contact_and_trial` | 1 | 1 | 1 |
| `initiate_trial_contact` | 2（consent=True/False 歧路）+ 6 guard cases | 8 | 2（True/False）+ 1（bool-is-int `1`）|
| **合計** | — | **26** | **13** |

**重點**：consent gate 與 bool-is-int guard 是 **Python 單測 + Inspector 雙重驗證**。單測覆蓋 8 種輸入（True/False/1/0/"true"/"yes"/None/未帶），Inspector 抽 3 個 high-signal case 再跑一次，確保協定層無 drift。

## 4.6 Consent Gate 的專屬驗證

針對 `initiate_trial_contact` 我們還有額外驗證：

```python
# tests/test_day6_consent_gate.py 節錄
def test_consent_gate_blocks_integer_one():
    result = initiate_trial_contact(user_consent=1)
    assert result.get("error") == "consent_required", (
        f"bool-is-int guard 失守：user_consent=1 不應通過 consent gate，實際回傳 {result}"
    )

def test_consent_gate_blocks_string_true():
    result = initiate_trial_contact(user_consent="true")
    assert result.get("error") == "consent_required"

def test_consent_gate_passes_real_true():
    result = initiate_trial_contact(user_consent=True)
    assert result.get("action") == "suggest_open_line"
    assert result["trial_url"].startswith("https://line.batmobile.com.tw/")
```

assertion message 不只說「失敗了」而是說「**失守了**」—— 用詞刻意，提醒 reviewer 這是安全界線而非功能測試。

## 4.7 回歸（Regression）防線

每次 `server.py` 或 `data/*.json` 修改後，流程是：

1. Charlie 在 VM 跑第一層 pytest → **必須全綠**
2. 若第一層通過，Mac 端跑 MCP Inspector spot check
3. 若兩層同步通過才 commit
4. commit 訊息加 tag `[dual-validated]` 標記「已跑雙層」

**歷史驗證紀錄**（高價值事件）：

- **P0 第一次整合驗證（2026-04-12）**：發現 `get_faq` 回傳的 `answer` 欄位在 Inspector 看到的是雙重 escape（`\\n` → `\\\\n`），Python 單測卻全綠。追查發現是某個 fixture 中用了 raw string r`"..."`，導致 Python 層存的就是 `\\n` 字面值、不是換行。改正後雙層通過
- **P1 Day 4 驗證 6 個工具（2026-04-18）**：首次完整雙層跑通 6 個工具，耗時 Python 層 3 秒、Inspector 手動約 6 分鐘
- **P1.3a case study 修正（2026-04-19）**：`feature-routes.json` 的 `case_studies` 陣列從錯誤 8 項改為正確 6 項，golden file 同步更新；雙層驗證通過；commit `2d94a53`

## 4.8 獨立可重現性

外部審查者若要自行重現驗證：

### 前置
```bash
# Mac 端，建議用 python.org 3.13 的 installer
# （miniconda 的 symlink 綁定會在 base Python 壞掉時連動壞掉 venv，
#  python.org installer 建的 venv 是 Mach-O universal binary 獨立複本）
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 第一層
```bash
.venv/bin/python -m pytest tests/ -v
```
預期：**26 passed** in ~3 秒

### 第二層
```bash
npx @modelcontextprotocol/inspector .venv/bin/python server.py
```
Inspector 開啟後：
1. 於 Tools 分頁逐一點擊 6 個工具
2. 手動填入 fixture 參數（參見 `tests/fixtures/`）
3. 對比 response 與 `tests/fixtures/golden/*.json` 是否一致

**若第一層與第二層不一致**：幾乎可確定是 MCP SDK 層面序列化問題（我們追過 3 次，2 次是 escape、1 次是 Unicode normalization）。歡迎開 issue，PR 會被熱烈歡迎。

## 4.9 為何不上 property-based testing / fuzz testing

審查者可能會問：為何不用 Hypothesis 或 AFL 做 property-based / fuzz？三個務實原因：

1. **MCP server 的輸入域極窄**：6 個工具輸入欄位總共 < 10 個，大部分是 enum（`industry` 限定 6 個字串）或小整數（`friend_count` 0-10000 量級）。branch coverage + boundary values 已足以窮盡
2. **外部世界依賴 = 0**：沒有 filesystem write、沒有網路、沒有 db。fuzz 通常是找「輸入 vs 外部世界的互動」的 weird case，本 Skill 沒有外部世界，fuzz ROI 低
3. **投資報酬率**：Charlie 是單人開發者，時間放在 consent gate 的 8 個明確 case + 3 分支邊界案更划算。未來若擴充工具集（例如新增寫入動作），再評估導入 Hypothesis

這個權衡記錄在 [ADR: 2026-04-19-laiguanjia-dual-layer-validation.md](../../../memory/decisions/2026-04-19-laiguanjia-dual-layer-validation.md) 中。

## 4.10 本章重點回顧

1. **雙層 = Python 層 JSON canonical diff + Mac 端 MCP Inspector spot check**，兩層同步通過才算驗證
2. **`json.dumps(sort_keys=True, ensure_ascii=False)`** 是 canonical form 的技術基礎
3. **三分支 bonus** = branch coverage + boundary value 混搭，對帶分支工具用最少 fixture 覆蓋最大面
4. **Consent gate 8 個 case + Inspector 3 case** 同時守住功能與協定兩層
5. **獨立可重現**：外部審查者用 pytest + MCP Inspector 即可在 Mac 端完整重跑
6. **整個白皮書到此告一段落**。回 [index](./README.md) 可重新選讀其他章節
