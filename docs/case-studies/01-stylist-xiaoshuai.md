---
title: 髮型設計師小帥 — 賴管家預約情境案例
persona: 小帥
industry: hair_salon
case_id: 01
reminder_window: 預約日當天早上 7 點
source_url: https://lineoa.batmobile.com.tw/blogs/stylist
source_file: 賴管家 - 預約.md
source_line_range: 250-298
last_updated: 2026-04-19
feature_refs:
  - booking
  - push_messaging
  - member_management
---

# 髮型設計師小帥

## 官網原文情境

> 美髮師小帥有一個「LINE 官方帳號」，專門分享髮型設計和髮色推薦給客人。小帥想要讓客人可以透過「LINE 官方帳號」預約美髮服務，但是自己不太懂技術，因此決定尋求「賴管家」的協助。
>
> 「賴管家」為小帥打造了一個預約網頁，客人只要透過小帥的「LINE 官方帳號」點選這個預約網頁，就可以輕鬆完成美髮預約。預約流程十分簡便，客人可以選擇理想的時間和髮型設計，還可以填寫特殊需求，如髮質調理、頭皮護理等，讓小帥能夠提供更個人化的服務。
>
> 客人完成預約後，「賴管家」會即時通知小帥，並將客人的預約資料整理成清晰的後台介面，方便小帥安排時間與項目。小帥可以快速掌握每個客人的預約狀態，並在後台進行確認、取消等管理操作。
>
> 客人在完成預約後也會收到成功通知；**預約日當天早上 7 點**，客人還會收到貼心提醒，有效降低爽約率。
>
> 藉由「賴管家」的協助，小帥的美髮預約服務變得更加流暢和專業，實現了美髮師與客人的雙贏局面。

### 小帥的使用步驟（官網列）

1. 申請「LINE 官方帳號」、LINE 開發者帳號 & 賴管家帳號，發送美髮資訊
2. 透過賴管家用官方帳號接收客人預約
3. 用 LIFF 製作預約網頁，讓客人透過 LINE 預約
4. 用 LINE Login 取得客人資料，方便聯繫

## 情境痛點摘要

| 痛點 | 賴管家功能對應 |
|---|---|
| 不懂技術，無法自建預約網頁 | 預約管理內建 LIFF 預約頁（5 分鐘建立，不需開發） |
| 客人填特殊需求（髮質、頭皮護理）易漏接 | 預約備註欄 + 後台統一檢視 |
| 爽約率影響排程 | 預約日當天 07:00 自動提醒 |
| 要對新髮色/熱門造型做推廣 | 推播訊息 / 圖文訊息 + 會員標籤分群 |

## 賴管家 Skill 如何回應這個情境

當使用者透過小帥的角色切入（例如詢問「我是美髮設計師，能用賴管家做什麼？」），Skill 預期的多步回應如下：

### Step 1 — 確認功能適用：`get_feature_detail`

```json
{
  "tool": "get_feature_detail",
  "args": {
    "feature": "booking",
    "include_case_study": true
  }
}
```

回傳含 `booking.summary`（預約管理 + 自動提醒）與 `case_studies[0]`（小帥的 persona/industry/blog_slug/reminder_window）。LLM 得以引用小帥作為具名案例，而非泛泛而談。

### Step 2 — 對應方案：`check_plan_suitability`

```json
{
  "tool": "check_plan_suitability",
  "args": {
    "user_profile": {
      "business_type": "personal_studio",
      "friend_count_estimate": "under_5000",
      "needs": ["booking", "push_messaging", "tagging"]
    }
  }
}
```

髮型工作室通常好友量在 5,000 人以下，個人版（NT$99/月）即可涵蓋預約 + 推播 + 30 組標籤。Skill 應回覆「個人版方案已足夠」，並附 `get_pricing` 的明細。

### Step 3 — 想要實際試用：`get_contact_and_trial` → `initiate_trial_contact`

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

回傳官方預填訊息與 `@batmobile` OA 連結，讓小帥可以一鍵帶著需求進入諮詢，不需重打「我想試用預約功能」。

## 延伸連結

- 素材檔：`賴管家 - 預約.md`（line 250–298）
- 官網長文：<https://lineoa.batmobile.com.tw/blogs/stylist>
- 相關 feature：`booking` / `push_messaging` / `member_management`
