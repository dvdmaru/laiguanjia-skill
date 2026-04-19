---
title: 診所護理師小惠 — 賴管家預約情境案例
persona: 小惠
industry: clinic
case_id: 05
reminder_window: 預約看診前一天傍晚
source_url: https://lineoa.batmobile.com.tw/blogs/clinic
source_file: 賴管家 - 預約.md
source_line_range: 394-431
last_updated: 2026-04-19
feature_refs:
  - booking
  - push_messaging
  - member_management
---

# 診所護理師小惠

## 官網原文情境

> 小型診所的護理師小惠有一個「LINE 官方帳號」，專門分享衛教知識和醫療資訊給病患。小惠希望病患可以透過「LINE 官方帳號」預約看診時間，但自己對寫程式一竅不通，因此決定向「賴管家」求助。
>
> 「賴管家」為小惠量身打造了一個預約網頁，病患只要透過小惠的 LINE 官方帳號點選預約網頁，就可以輕鬆預約看診時間。預約過程快速便捷，病患可以選擇適合自己的時間和醫生，例如內科、兒科、家醫科等，還可以填寫症狀描述或特殊需求，如藥物過敏、身體不適等，讓小惠能夠提供更有針對性的服務。
>
> 病患完成預約後，「賴管家」會即時通知小惠，並將病患的預約資料整理成清晰的後台介面，方便小惠安排診所的看診進度。小惠可以快速掌握每個病患的預約狀態，並在後台進行確認、取消等管理操作。
>
> 病患在完成預約後也會收到成功通知；**預約看診前一天傍晚**，病患還會收到「賴管家」的貼心提醒，有效降低誤診率。
>
> 藉由「賴管家」的協助，小惠的診所預約服務變得更加流暢和專業，實現了診所與病患的雙贏局面。

## 情境痛點摘要

| 痛點 | 賴管家功能對應 |
|---|---|
| 病患選醫生／科別（內科／兒科／家醫科） | 服務項目自訂（科別 + 醫生） |
| 藥物過敏、慢性病歷等需事前紀錄 | 預約備註欄 |
| 慢性病回診、定期追蹤易忘 | 預約看診**前一天傍晚**提醒 |
| 衛教資訊需持續觸及病患 | 推播訊息 + 圖文訊息 |

> **⚠️ 醫療法規考量**：診所類應用涉及病患個資與醫療廣告法，實際導入前建議向 `@batmobile` 顧問確認合規使用邊界（例如不可在推播中做療效保證、個資蒐集需符合《個資法》與《醫療法》）。Skill 在診所相關情境應主動加註此類合規提醒，不應假裝自己是法規顧問。

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

回傳 `case_studies[4]` 含 `reminder_window=「預約看診前一天傍晚」`。與零售服務業「當天早上 7 點」不同，診所提醒時機貼合「前一晚調整用藥／飲食」的醫療節奏。

### Step 2 — 方案判斷：`check_plan_suitability`

```json
{
  "tool": "check_plan_suitability",
  "args": {
    "user_profile": {
      "business_type": "clinic",
      "friend_count_estimate": "5000_to_20000",
      "needs": ["booking", "push_messaging", "smart_customer_service"]
    }
  }
}
```

診所好友量通常較高（5,000–20,000 範圍），且病患常有重複性衛教問題（掛號流程、營業時間、停診通知）。Skill 應建議：

- **進階版**（更多標籤、分群、推播額度）
- 加購 **`smart_customer_service`**（AI 客服自動回應常見衛教問題，每月 100 萬 Token 額度可支援 2 萬好友、每人每天 3–5 題）

### Step 3 — 合規加註

若使用者在 Skill 對話中提到「想推療效見證」「保證治癒」等違反醫療廣告法的敘述，Skill 應：

1. 不生成違法廣告文案
2. 引導使用者改走「衛教資訊 + 專業定位」敘事
3. 在 `initiate_trial_contact` 前提醒請直接與顧問討論合規邊界

### Step 4 — 試用：`initiate_trial_contact`

```json
{
  "tool": "initiate_trial_contact",
  "args": {
    "prefilled_intent": "general_inquiry",
    "target_oa": "@batmobile",
    "user_consent": true
  }
}
```

（診所建議走 `general_inquiry` 而非 `trial_personal`，因為需人工確認合規邊界後再開通試用）

## 延伸連結

- 素材檔：`賴管家 - 預約.md`（line 394–431）
- 官網長文：<https://lineoa.batmobile.com.tw/blogs/clinic>
- 相關 feature：`booking` / `push_messaging` / `smart_customer_service` / `member_management`
