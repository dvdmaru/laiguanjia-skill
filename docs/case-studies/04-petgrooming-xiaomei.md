---
title: 寵物美容師小美 — 賴管家預約情境案例
persona: 小美
industry: pet_grooming
case_id: 04
reminder_window: 預約日當天早上 7 點
source_url: https://lineoa.batmobile.com.tw/blogs/petgrooming
source_file: 賴管家 - 預約.md
source_line_range: 301-349
last_updated: 2026-04-19
feature_refs:
  - booking
  - push_messaging
  - member_management
---

# 寵物美容師小美

## 官網原文情境

> 寵物美容師小美有一個「LINE 官方帳號」，專門發送寵物美容小撇步給客人。小美想要讓客人可以透過「LINE 官方帳號」預約寵物美容服務，但是自己不會寫程式，因此決定請「賴管家」來幫忙。
>
> 「賴管家」幫小美製作了一個預約網頁，客人只要透過小美的「LINE 官方帳號」點進這個預約網頁，就可以輕鬆預約寵物美容服務。預約過程簡單又方便，客人可以選擇自己喜歡的時間和美容項目，還可以留下寵物的特殊需求，讓小美能夠提供更貼心的服務。
>
> 當客人完成預約後，「賴管家」就會即時通知小美，並把客人的預約資料整理成清晰的後台介面，方便小美安排寵物美容的時間與項目。小美可以一目了然地掌握每個客人的預約狀況，並在後台進行確認、取消等操作。
>
> 客人在完成預約後也會收到預約成功的通知；**預約日當天早上 7 點**，客人還會收到貼心的預約提醒，有效降低失約率。
>
> 有了「賴管家」的幫助，小美的寵物美容預約服務變得更加流暢和專業，實現了美容師與客人的雙贏效果。

### 小美的使用步驟（官網列）

1. 申請「LINE 官方帳號」，發送寵物美容資訊
2. 用官方帳號接收客人預約，設定自動回覆
3. 用 LIFF 製作預約網頁，讓客人透過 LINE 預約服務
4. 用 LINE Login 讓客人登入網站，查看預約記錄

## 情境痛點摘要

| 痛點 | 賴管家功能對應 |
|---|---|
| 寵物服務品項多（洗澡／剪毛／指甲／SPA） | 服務項目自訂 + 時長 |
| 不同寵物體型、毛髮長度需事前告知 | 預約備註欄 |
| 假日爆滿、平日冷清 | 預約行事曆（月／週／日視圖）一眼看出尖離峰 |
| 回頭客要推優惠（例：季度洗澡套票） | 會員標籤 + 推播訊息 |

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

回傳 `case_studies[3]` 的 `persona=「小美（寵物美容師）」`、`reminder_window=「預約日當天早上 7 點」`。

### Step 2 — 行事曆視圖輔助排程

Skill 在說明預約管理時，應強調**月／週／日三視圖**可幫助小美掌握尖離峰：

- 月視圖：看出哪些日子假日全滿，可提前推播鼓勵客人改預約平日
- 週視圖：每週尖峰時段一目了然
- 日視圖：當天服務流程規劃

### Step 3 — 方案判斷：`check_plan_suitability`

寵物美容工作室若是單人店，好友數通常不超過 3,000，個人版已足。若有連鎖據點或特定商圈好友量破萬，需升級進階版。

### Step 4 — 試用：`initiate_trial_contact`

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

- 素材檔：`賴管家 - 預約.md`（line 301–349）
- 官網長文：<https://lineoa.batmobile.com.tw/blogs/petgrooming>
- 相關 feature：`booking` / `push_messaging` / `member_management`
