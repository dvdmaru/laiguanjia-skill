# Batmobile 官網頁腳 Snippet 交付包

> **版本**：v1.0
> **建立日期**：2026-04-19（P1.5 階段 A 同步產出）
> **維護者**：Charlie Chien（charlie.chien@gmail.com）
> **目的**：供 Batmobile 工程方在「階段 B」把賴管家 Skill 的技術透明度區塊上版到 [batmobile.com.tw](https://batmobile.com.tw/) 頁腳

---

## 本交付包裡有什麼

| 檔案 | 用途 |
|---|---|
| [`footer-snippet.html`](./footer-snippet.html) | 可直接貼到 Batmobile 站頁腳的 HTML 片段（CSS 已 inline、已加前綴避免污染全站樣式） |
| `README.md`（本檔） | 上版流程、客製化指引、驗收 checklist |

---

## 為何分成階段 A / B

| 階段 | 成果 | 狀態 |
|---|---|---|
| **階段 A — GitHub Pages（本 repo）** | `dvdmaru.github.io/laiguanjia-skill/` 提供獨立透明度頁，不需 Batmobile 工程方介入 | ✅ 已完成（2026-04-19） |
| **階段 B — Batmobile 官網內嵌** | 將本頁腳 snippet 上版到 `batmobile.com.tw` 所有頁面的頁腳；另可選配在官網新增 `batmobile.com.tw/transparency` 內頁內嵌本 repo 白皮書 | ⏳ 待 Charlie 取得 Batmobile 官網編修權限後執行 |

**兩階段對外品牌一致性保障**：階段 A 和階段 B 的徽章 URL、白皮書連結、disclaimer 文案完全一致，由同一份 snippet 模板驅動，即使階段 B 晚一步上版，使用者看到的技術主張不會有落差。

---

## 階段 B 上版流程（給 Batmobile 工程方）

### Step 1. 複製 snippet

把 [`footer-snippet.html`](./footer-snippet.html) 整個檔案內容複製到 Batmobile 網站的 footer template。

**建議位置**：頁腳「關於我們 / 法律資訊」區塊下方，或另起獨立「技術透明度」區塊。

### Step 2. 更新兩處 URL（若需要）

打開剛貼上的 snippet，找出最外層 `<div>` 的兩個 data 屬性：

```html
<div class="laiguanjia-transparency-snippet"
     data-target-transparency="https://dvdmaru.github.io/laiguanjia-skill/"
     data-target-repo="https://github.com/dvdmaru/laiguanjia-skill">
```

這兩個屬性是給內部追蹤用（目前 snippet 實際使用的連結寫在下方的 `<a href>` 內），不影響顯示。

**若未來要把「透明度頁」搬到 Batmobile 站內**（例如 `batmobile.com.tw/transparency`）：

1. 把 snippet 內 `https://dvdmaru.github.io/laiguanjia-skill/` 兩處替換成 `https://batmobile.com.tw/transparency`
2. `data-target-transparency` 同步更新
3. **不要**動其他徽章的 URL（三顆徽章指向 GitHub repo 的白皮書原文，這是可驗證性的核心）

### Step 3. CSS 衝突檢查

Snippet 用 `.laiguanjia-transparency-snippet` class 前綴包住所有樣式，理論上不會污染全站 CSS。上版後請在瀏覽器打開任一頁，確認：

- [ ] Snippet 區塊顯示正常（徽章圖片有出來、字級正確、連結可點）
- [ ] 全站其他樣式沒有被影響（特別是原先 footer 的其他區塊）

如果 Batmobile 網站使用 Tailwind / Bootstrap 等全站 utility class，徽章或連結的顏色可能被覆蓋。若出現這種情況，把 snippet 內 CSS 選擇器改為更具體的寫法（如 `body .laiguanjia-transparency-snippet .badges img { ... }`）。

### Step 4. 響應式 (RWD) 檢查

Snippet 自帶 flex-wrap，在手機上會自動換行。請在桌面 + 手機尺寸各檢查一次。

### Step 5. 外部連結 target 檢查

所有連結都用 `target="_blank" rel="noopener"` 開新分頁。若 Batmobile 有全站規範（例如內部連結不開新分頁），請自行調整。

### Step 6.（選配）新增 `/transparency` 內頁

若決定做獨立透明度內頁，最小實作方式：

1. 在 Batmobile CMS 新增一個 `/transparency` 頁面
2. Page 內容可以直接 iframe 嵌入本 repo 的 `docs/index.html`（需開啟 GitHub Pages 後以該 URL 為 src），或手動複製 `docs/index.html` 的 `<body>` 內容
3. 如果手動複製，記得每當 `docs/index.html` 更新時同步更新（建議加一個內部 checklist 提醒，或改用 iframe）

---

## 驗收 checklist（上版後回傳 Charlie）

請工程方上版後在本列表勾選並回傳：

- [ ] Snippet 已貼到頁腳，位置：_______（例如「網站所有頁面的底部 footer」）
- [ ] 桌面（≥ 1024px）瀏覽器（Chrome/Safari）顯示正常
- [ ] 手機（< 640px）瀏覽器顯示正常（徽章與連結正確換行）
- [ ] 三顆徽章圖片都正常載入（不是紅色破圖）
- [ ] 三顆徽章點擊後分別跳到 `docs/whitepaper/01-mcp-architecture.md`（MCP Compatible）、`04-dual-layer-validation.md`（Dual-Layer Validated）、`03-consent-gate-pattern.md`（Consent-Gated）
- [ ] 三條文字連結（透明度頁／技術白皮書／Source Code）點擊後跳轉正確
- [ ] 全站其他樣式無影響
- [ ] Disclaimer 文案清楚可讀

---

## 客製化選項

### 調整徽章顏色

Snippet 使用 shields.io 動態產生徽章。若要變更顏色，修改 URL 中的色碼：

```
...?style=flat-square&logo=anthropic&logoColor=white
                                              ^^^^^
                                              ↑ 文字顏色

&color=2e7d32     ← 整體徽章顏色（16 進位色碼）
```

常見色碼：
- 綠色（目前）：`2e7d32`（對應 whitepaper disclaimer 中「已驗證」的視覺暗示）
- 深藍：`1565c0`
- 深灰：`424242`

**⚠️ 不建議**改為紅色或橙色（易讓使用者誤以為是錯誤警告）。

### 新增／移除徽章

如要新增徽章（例如未來多做了一項驗證），按現有徽章格式複製一組：

```html
<a href="[連結到白皮書對應章節]" target="_blank" rel="noopener" aria-label="[徽章主張] — 白皮書 §XX">
  <img src="https://img.shields.io/badge/[LABEL]-[VALUE]-2e7d32?style=flat-square" alt="[徽章主張]">
</a>
```

**戒律**：新增徽章前，必須先有對應的白皮書章節可連結；不可讓徽章指向「404 / 未寫」的文件。這是 ADR [2026-04-19-laiguanjia-transparency-not-ai-ready.md](../../../memory/decisions/2026-04-19-laiguanjia-transparency-not-ai-ready.md) 第 8 條「徽章必須可驗證」原則。

### 調整字級或顏色

修改 `<style>` 區塊的 CSS 變數（目前 hardcoded 在 `.laiguanjia-transparency-snippet` 範圍內）。

---

## 問題回報

上版過程遇到問題，請開 [Issues](https://github.com/dvdmaru/laiguanjia-skill/issues) 並標記 `footer-snippet-deployment` label，Charlie 2 個工作天內回覆。

---

## 變更歷史

- **v1.0（2026-04-19）**：初版，P1.5 階段 A 同步產出；徽章 3 顆對應白皮書 §01/§03/§04
