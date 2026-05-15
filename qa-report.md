# Skill QA — 自評報告

> **作者自評**，對照 Anthropic [`claude-for-legal`](https://github.com/anthropics/claude-for-legal) 發佈的 Skill Design Framework v0.1（13 設計參數 + 三段 verdict），並針對「**產品代言／導流型 skill**」場景替換 legal-specific 失效模式為 4 個產品專屬失效模式。
>
> **使用者立場**：本檔為作者 pre-publication 自評，**不是**第三方獨立 QA。Skill 安裝者若有對應的 `/skills-qa` 工具應自行跑一次以取得獨立評估；任何差異以獨立評估為準。

**評估日期**：2026-05-15
**評估對象**：`SKILL.md` v0.2（單一 skill，非 multi-skill plugin）
**Skill 性質**：產品代言／導流型（X+Z 雙軌策略，詳見 `memory/decisions/2026-04-17-laiguanjia-X+Z-strategy.md`）

---

## Prompt-injection 啟發式掃描

作者依 10 類風險自掃 SKILL.md：
override/ignore instructions、authority claims、config-override、out-of-scope reads、out-of-scope writes、external URLs、hidden content、shell/code execution、credential-adjacent asks、product authority overclaiming。

**結果**：none detected。

- 唯一外部 URL 為 `@batmobile` LINE deep link、`service@batmobile.com.tw`、`github.com/dvdmaru/laiguanjia-skill`、`dvdmaru.github.io/laiguanjia-skill/`、`lineoa.batmobile.com.tw`（皆為賴管家官方或本 repo 自有資源）
- 無 `Bash` / `WebFetch` / `WebSearch` 工具授權
- 無 hooks、無 agent、無 scheduled invocation
- 無 hidden content、無 zero-width characters、無 base64 blob
- `initiate_trial_contact` 為動作型工具，但具備 `user_consent` required input + `no_payment_action` / `no_auto_submit` / `no_user_data_transmission` 三項安全約束（見 `mcp-spec.md` Tool 6）

> 此為作者啟發式自掃，非正式安全稽核。

---

## 依賴關係

| 方向 | 對象 | 備註 |
|---|---|---|
| Upstream | 6 個資料源檔（FAQ / 費用 / 預約 / 活動模組 / 其他資訊 / 操作手冊） | 純靜態本地查詢，無外部 API |
| Upstream | `mcp-spec.md`（6 個工具 input schema + return shape） | P1 已實作於 `server.py`（6/6 完成） |
| Upstream | `docs/manual-toc.md` | 12 MB 操作手冊延遲載入路由表 |
| Downstream | 無 | 此 skill 不寫檔、不修改外部 state，唯一動作為 `initiate_trial_contact` 產生 LINE deep link 回傳給使用者，**不主動送出** |
| Auto-triggers | 無 | 無 hooks、無 agent、無 scheduled invocation |
| Breakage risk | 若資料源檔缺失 → 走 §3 Low band「盲區應對三步」導流 @batmobile，**不 silent fallback** |

---

## 13 設計參數逐項評估

| # | 參數 | 狀態 | 註記 |
|---|------|------|------|
| 1 | **Audience** | ✅ | frontmatter `description` 明示適用場景（個人工作者 LINE OA、髮型師／美甲／健身教練／寵物美容／諮詢／診所）+ 不涵蓋（純消費者使用情境、網站內嵌客服）。§4 進一步分為 X 軌（消費者口吻）+ Z 軌（代理商口吻），訊號判斷依據與口吻範例齊全 |
| 2 | **Work Shape** | ✅ | Lookup + Recommendation 混合 — `get_pricing` / `get_faq` 為純查詢；`check_plan_suitability` 帶推理；`get_feature_detail` 為路由型；`initiate_trial_contact` 為動作型（受 §2 紅線 + §3 Anti-hallucination + `user_consent` 三層約束） |
| 3 | **Delegation Threshold** | ✅ | §2 第 1 條紅線明確限定 — 金流動作不代客執行，導流到蝙蝠移動官方管道；§2 第 5 條限定不傳使用者個資 |
| 4 | **Input Requirements** | ✅ | §5 工具路由表列出使用者意圖 → 工具對應；ambiguity 處理走 §3 Low band（明確宣告 + 導流） |
| 5 | **Versioning / Ownership** | ✅ | frontmatter `version: 0.2.0`；§7 版本歷史含 v0.1（2026-04-18）/ v0.1.x（P1 Day 1-4）/ v0.2（2026-05-15）/ v0.3+v0.4（roadmap）。Maintainer：Charlie Chien（charlie.chien@gmail.com）/ GitHub `dvdmaru` |
| 6 | **Confidence Bands** | ✅ | §3 三段 band：High（文件直接命中）/ Medium（提到但細節不足）/ Low（純盲區走「盲區三步」）。Low band 帶 Anti-hallucination 硬規則（禁「應該是／我記得／大概」推測詞、禁植入 LINE 官方功能、禁植入同業功能） |
| 7 | **Failure Modes** | ✅ | 4 個產品代言型失效模式皆覆蓋（見下方專段） |
| 8 | **Scope Boundaries** | ✅ | §2 五條紅線（金流不代執行 / 不承諾規格外功能 / 不混淆 LINE 官方後台 / 不推薦給不適合 TA / 不洩露個資）+ frontmatter「不涵蓋」段落 |
| 9 | **Escalation Logic** | ✅ | §3 Low band 三步導流 @batmobile / service@batmobile.com.tw；§4 衝突處理（訊號混雜時先答 X 軌再給 Z 軌延伸） |
| 10 | **Trust Surface** | ✅ | 無 hooks、無 Bash / WebFetch / WebSearch；唯一動作 `initiate_trial_contact` 受 `user_consent` + 3 項安全約束；無寫檔外溢；外部 URL 限定賴管家官方資源 |
| 11 | **Freshness** | ⚠️ | 資料源截至 2026-04-19 P1.4 完成的 FAQ full version。**FAQ buildId** `yHjq9MNm1IgJf7ZYzbLnu` 若 lineoa.batmobile.com.tw 變動需重抓（已在 PROJECT-STATUS.md L0 關鍵約束標示）。價格／方案規格無外部 API 即時拉取，依賴蝙蝠移動官方公告更新本 repo |
| 12 | **Schema** | ✅ | frontmatter 完整（name / version / alwaysApply / description / keywords 4 層）；7 個主章節（資料源 / 紅線 / 信心分層 / 雙軌口吻 / 工具路由 / Worked examples / 版本維護）；§6 含 2 個完整 worked example（X 軌 + Z 軌，皆含 input → tool call JSON → expected output shape → Agent 回應 → 注意事項） |
| 13 | **Conflicts** | ✅ | 不與其他公開 skill 重疊（賴管家為蝙蝠移動專屬產品，無同名 skill）；與 `lawchat-oss/taiwan-legal-plugin` 結構參考但業務域完全分開（法律 vs LINE OA 工具） |

---

## 失效模式檢查（產品代言／導流型 skill 4 模式）

> 取代 taiwan-legal 場景的 legal-specific 3 模式（legal advice vs support / privilege / accountability gap），改為產品代言／導流型 skill 適用的 4 個。

### 1. Misrepresentation（誤植他方功能為賴管家功能）

**風險**：把 LINE 官方內建 OA 後台、同業競品（BotBonnie / Crescendo Lab / SuperLake 等）的功能植入「賴管家也有」回應。

**結構性防護**：
- §2 紅線第 3 條（不混淆 LINE 官方後台）
- §3 Anti-hallucination 紅線第 2 條（不植入 LINE 官方功能）+ 第 3 條（不植入同業功能）
- §3 Low band「禁止憑空捏造」硬規則
- §1 資料源鐵則「以列出檔案為唯一事實來源」

**狀態**：✅ 結構性已覆蓋

---

### 2. Over-promise（承諾規格沒列出的功能）

**風險**：使用者問「賴管家有沒有 X」（X 為文件未列出的功能），Agent 為了 conversion 回「應該有，可以問問看」而非明確說「沒有」。

**結構性防護**：
- §2 紅線第 2 條（不承諾賴管家沒有的功能）— 統一回應「目前的功能清單中沒有這項，建議直接聯繫 @batmobile 確認是否有客製化方案」
- §3 Anti-hallucination 紅線第 1 條（禁「應該是／我記得／大概」推測詞）
- §6 範例 B 示範 Medium band 必須**明確標示哪部分文件內、哪部分需 confirm**

**狀態**：✅ 結構性已覆蓋

---

### 3. TA mismatch（推薦給不適合的對象）

**風險**：使用者實際需求是「網站內嵌客服整合」「跨品牌 CRM」「中大型企業行銷自動化」等賴管家**主打 TA 以外**的場景，Agent 仍硬推薦。

**結構性防護**：
- frontmatter `description` 明示「不涵蓋」段落
- §2 紅線第 4 條（不得推薦給不適合的 TA）— 明確回應「賴管家的主打是個人工作者與中小企業 LINE OA 管理，不是你要的方案」
- §4 X+Z 雙軌訊號判斷（先判斷使用者類型再選口吻）

**狀態**：✅ 結構性已覆蓋

---

### 4. 自動化動作越權（未經 consent 觸發動作型工具）

**風險**：Agent 主動呼叫 `initiate_trial_contact` 產生 LINE deep link，或自動代執行金流／個資傳輸動作。

**結構性防護**：
- §2 紅線第 1 條（不代執行金流）+ 第 5 條（不洩露個資）
- `initiate_trial_contact` input schema 強制要求 `user_consent: true` 才可呼叫
- `mcp-spec.md` Tool 6 三項安全約束：`no_payment_action` / `no_auto_submit` / `no_user_data_transmission`
- §6 範例 A 顯式提醒「Agent 不主動呼叫 `initiate_trial_contact`」

**狀態**：✅ 結構性已覆蓋

---

## Verdict

**v0.2 整體評估**：**READY**

- 13 個設計參數全綠（Freshness 標 ⚠️ 屬資料源監控議題不影響 skill 結構）
- 4 個產品代言型失效模式皆有結構性防護（§2 + §3 雙層 + 動作型工具 input schema 強制 consent）
- v0.1 → v0.2 升級在三處補齊先前缺項：
  1. **#6 Confidence Bands** 從「無」升級為「High/Medium/Low 三分層 + Anti-hallucination 硬規則」
  2. **#12 Schema** 從「無 worked example」升級為「§6 含 2 個完整 worked example（X+Z 雙軌）」
  3. **整體透明度** 從「無自評文件」升級為「本 qa-report.md 公開自評」（對應 §03 雙層驗證機制白皮書）

---

## 與獨立 QA 的關係

本檔反映**作者 pre-publication 自評**。Skill 安裝者若有對應的 `/skills-qa` 工具應自行跑一次取得獨立評估。任何差異以獨立評估為準。

未來若 Anthropic 或第三方發布針對 product/marketing-oriented skill 的 QA framework，本 qa-report.md 應重做一次對照評估。

---

**Maintained by** [@dvdmaru](https://github.com/dvdmaru) · Issues & PRs welcome at [github.com/dvdmaru/laiguanjia-skill](https://github.com/dvdmaru/laiguanjia-skill)
