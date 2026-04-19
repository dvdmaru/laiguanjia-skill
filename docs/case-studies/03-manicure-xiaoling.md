---
title: 美甲師小玲 — 賴管家預約情境案例
persona: 小玲
industry: nail_art
case_id: 03
reminder_window: 預約日前一天傍晚
source_url: https://lineoa.batmobile.com.tw/blogs/manicure
source_file: 賴管家 - 預約.md
source_line_range: 353-391
last_updated: 2026-04-19
feature_refs:
  - booking
  - push_messaging
---

# 美甲師小玲

## 官網原文情境

> 美甲師小玲有一個 LINE 官方帳號，專門分享美甲設計和色彩搭配給客人。小玲希望客人可以透過 LINE 官方帳號預約美甲服務，但自己對程式設計一竅不通，因此決定尋求「賴管家」的協助。
>
> 「賴管家」為小玲量身打造了一個預約網頁，客人只要透過小玲的 LINE 官方帳號點選預約網頁，就可以輕鬆預約美甲服務。預約過程簡單明瞭，客人可以選擇理想的時間和美甲款式，例如法式指甲、凝膠指甲、手繪藝術等，還可以上傳指甲照片或填寫特殊需求，如皮膚過敏、指甲脆弱等，讓小玲能夠提供更個人化的服務。
>
> 客人完成預約後，「賴管家」會即時通知小玲，並將客人的預約資料整理成條理分明的後台介面，方便小玲安排美甲的時間與項目。小玲可以一目了然地掌握每個客人的預約狀況，並在後台進行確認、取消等操作。
>
> 客人在完成預約後也會收到成功通知；**預約日前一天傍晚**，客人還會收到「賴管家」貼心的預約提醒，有效降低爽約率。
>
> 在「賴管家」的協助下，小玲的美甲預約服務變得更加流暢和專業，實現了美甲師與客人的雙贏局面。

## 情境痛點摘要

| 痛點 | 賴管家功能對應 |
|---|---|
| 美甲款式多樣（法式／凝膠／手繪） | 服務項目可自訂 + 時長差異化設定 |
| 客人可能皮膚過敏、指甲脆弱，需事前告知 | 預約備註欄 |
| 美甲師需提前一天準備材料、工具 | 預約日**前一天傍晚**提醒（與其他多數產業「當天早上 7 點」不同，貼合備料節奏） |
| 客人可能想看看其他人的美甲作品 | 圖文訊息分享作品集、圖文選單綁定 Instagram / 作品頁 |

> **⚡ 小玲案例的獨特點**：官網 blog 特別標註「預約日前一天傍晚」而非通用的當天早上 7 點提醒，可能是因為美甲師常需要**前一天備料**（挑凝膠顏色、準備客人指定的款式材料）。這個提醒時機差異是實際業務節奏的反映，Skill 回覆時若使用者描述類似業務（需備料／備材），可建議對照小玲的情境。

## 賴管家 Skill 如何回應這個情境

### Step 1 — 功能＋案例：`get_feature_detail`

```json
{
  "tool": "get_feature_detail",
  "args": {
    "feature": "booking",
    "include_case_study": true
  }
}
```

`case_studies[2]` 回傳小玲的 persona + `reminder_window=「預約日前一天傍晚」`。LLM 可明確告訴使用者「這個情境下的提醒時機與通用預設不同，需要根據實際產業節奏調整」。

### Step 2 — 考慮要不要加活動模組：`get_pricing`

若小玲有**開課教學**或**主題美甲活動**（例如聖誕系列報名、婚禮美甲限定場），可考慮額外加購**活動模組（NT$199/月）**：

```json
{
  "tool": "get_pricing",
  "args": {
    "include_add_ons": true
  }
}
```

Skill 回覆應區分：
- 日常一對一預約 → 只需個人版 `booking`
- 主題活動／課程招生 → 加購 `event_management`（48 小時前提醒 + QR 碼簽到）

### Step 3 — 想試試看：`initiate_trial_contact`

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

- 素材檔：`賴管家 - 預約.md`（line 353–391）
- 官網長文：<https://lineoa.batmobile.com.tw/blogs/manicure>
- 相關 feature：`booking` / `push_messaging` / 進階可加購 `event_management`
