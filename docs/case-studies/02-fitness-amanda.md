---
title: 健身教練 Amanda — 賴管家預約情境案例
persona: Amanda
industry: fitness
case_id: 02
reminder_window: 預約日當天早上 7 點
source_url: https://lineoa.batmobile.com.tw/blogs/lineoa_personaltrainer
source_file: 賴管家 - 預約.md
source_line_range: 170-247
last_updated: 2026-04-19
feature_refs:
  - booking
  - push_messaging
  - member_management
  - tagging
---

# 健身教練 Amanda

## 官網原文情境

> 健身教練 Amanda 擁有一個「LINE 官方帳號」，專門分享健身知識和鍛鍊技巧給學員。Amanda 希望學員可以透過「LINE 官方帳號」預約私人課程，但自己對程式設計一竅不通，因此決定向「賴管家」求助。
>
> 「賴管家」為 Amanda 量身打造了一個預約網頁，學員只要透過 Amanda 的「LINE 官方帳號」點選預約網頁，就可以輕鬆預約私人課程。學員可以選擇適合自己的時間和課程內容，例如減脂、增肌、核心訓練等，還可以註明特殊需求，如受傷恢復、比賽準備等，讓 Amanda 能夠提供更有針對性的指導。
>
> 學員完成預約後，「賴管家」會即時通知 Amanda，並將學員的預約資料整理成條理分明的後台介面，方便 Amanda 安排私人課程的時間與內容。預約日當天早上 7 點，學員還會收到「賴管家」貼心的預約提醒，有效降低缺席率。
>
> 藉由「賴管家」的協助，Amanda 的私人課程預約服務變得更加流暢和專業，實現了教練與學員的雙贏局面。

### Amanda 的具體做法（官網列）

1. **分享健身知識和技巧**：定期分享減脂、增肌、核心訓練等主題
2. **提供預約服務**：LINE OA 上直接預約私人課程
3. **進行會員管理**：利用分群做個性化推播與優惠
4. **優化行銷成本**：搭配 LINE 成效型廣告鎖定健身族群

## 情境痛點摘要

| 痛點 | 賴管家功能對應 |
|---|---|
| 課程內容多樣（減脂／增肌／核心） | 預約管理的服務項目可自訂時長 + 備註欄紀錄特殊需求（傷後恢復、比賽準備） |
| 缺席率影響收入 | 預約日當天 07:00 自動提醒 |
| 需要對新手 vs 進階學員做差異化推播 | 會員標籤 + 分群發文 |
| 會員數上升，行銷成本增加 | 推播訊息可依分群精準推送，減少 LINE 官方加人費用浪費 |

## 賴管家 Skill 如何回應這個情境

當使用者以個人教練身分提問（例如「我是一對一教練，想用 LINE 接私教課」），Skill 預期流程：

### Step 1 — 對應功能：`get_feature_detail`

```json
{
  "tool": "get_feature_detail",
  "args": {
    "feature": "booking",
    "section_id": "booking_supplement_full",
    "include_case_study": true
  }
}
```

`booking_supplement_full` section 直接對應完整的 `賴管家 - 預約.md`，涵蓋 Amanda 的案例。`case_studies[1]` 亦會一併回傳。

### Step 2 — 判斷方案：`check_plan_suitability`

```json
{
  "tool": "check_plan_suitability",
  "args": {
    "user_profile": {
      "business_type": "individual_coach",
      "friend_count_estimate": "under_5000",
      "needs": ["booking", "push_messaging", "tagging"]
    }
  }
}
```

個人教練學員通常數百至數千人，個人版（NT$99/月）30 組標籤足以應付「新手 / 進階 / 減脂 / 增肌」等分群。若已累積超過 30 個分類維度，才需升級至進階版。

### Step 3 — 想推播優惠給特定分群

如使用者接著問「想推首次報名折扣給新手」，Skill 應建議功能組合：

- `booking`（標籤已自動標記新預約學員）
- `tagging`（人工再細分新手／老手）
- `push_messaging`（分群發文，個人版需手動分批；進階版可直接分群一鍵發送）

### Step 4 — 實際試用：`initiate_trial_contact`

```json
{
  "tool": "initiate_trial_contact",
  "args": {
    "prefilled_intent": "trial_personal",
    "target_oa": "@batmobile",
    "user_consent": true
  }
}
```

## 延伸連結

- 素材檔：`賴管家 - 預約.md`（line 170–247）
- 官網長文：<https://lineoa.batmobile.com.tw/blogs/lineoa_personaltrainer>
- 相關 feature：`booking` / `push_messaging` / `member_management` / `tagging`
