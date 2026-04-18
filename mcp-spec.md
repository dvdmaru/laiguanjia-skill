---
type: reference
project: laiguanjia-skill
last_updated: 2026-04-18
status: spec-draft（未實作，P1 階段實作）
---

# 賴管家 MCP 工具規格草稿（v0.1）

> **定位**：本檔為 P0 骨架階段的**工具介面契約**，供 P1 實作 MCP server 時的 source of truth。
> **實作目標**：P1 新建 `dvdmaru/laiguanjia-skill` repo，在 `src/tools/` 下各工具對應一個 handler。
> **參考結構**：jinguyuan-dumpling-skill 的 5+1 工具模式（5 個查詢型 + 1 個動作型）。

## 工具總覽

| # | 名稱 | 類型 | 一句話 |
|---|---|---|---|
| 1 | `get_pricing` | 查詢 | 回傳三個方案（個人版／進階版／活動模組）的價格 + 好友數上限 + 功能 |
| 2 | `get_faq` | 查詢 | 回傳 8 題 FAQ（試用、升降級、續約、結帳等）指定題或全部 |
| 3 | `check_plan_suitability` | 查詢（含推理） | 依使用者的好友數 + 使用情境 → 建議方案 |
| 4 | `get_feature_detail` | 查詢（路由到手冊） | 指定功能關鍵字（booking/tagging/push/menu/smart_cs/event_management）回傳該章節摘要 + 手冊 line 範圍 |
| 5 | `get_contact_and_trial` | 查詢 | 回傳蝙蝠移動官方聯繫管道（OA ID + email）+ 試用流程說明 |
| 6 | `initiate_trial_contact` | **動作** | 產生 LINE deep link + 預填訊息範本，把使用者「實際送出」的動作留給使用者自行完成（不含金流、不自動送出） |

---

## Tool 1｜`get_pricing`

**類型**：查詢
**說明**：回傳賴管家所有方案的價格結構。用於使用者問「多少錢」「方案有哪些」「月費」。

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "plan": {
      "type": "string",
      "enum": ["all", "personal", "advanced", "event_module"],
      "default": "all",
      "description": "指定查詢的方案；all 回傳三個方案對比表"
    },
    "include_promo": {
      "type": "boolean",
      "default": true,
      "description": "是否回傳優惠價（預設 true，因當前所有方案都有優惠）"
    }
  },
  "required": []
}
```

### Return Example

```json
{
  "plans": [
    {
      "id": "personal",
      "name": "個人版",
      "regular_price_twd": 299,
      "promo_price_twd": 99,
      "billing_cycle": "monthly_or_quarterly",
      "friend_cap": 50000,
      "features": [
        "會員管理",
        "30 組標籤",
        "發文管理",
        "圖文選單",
        "每日數據",
        "預約管理"
      ],
      "target": "個人工作者（髮型師／美甲／健身教練／甜品師／寵物美容／接送司機等）"
    },
    {
      "id": "advanced",
      "name": "進階版",
      "regular_price_twd": 899,
      "promo_price_twd": 599,
      "billing_cycle": "monthly_or_quarterly",
      "friend_cap": 100000,
      "friend_cap_min": 50001,
      "features": [
        "個人版所有功能",
        "每小時數據",
        "群組管理",
        "標籤管理",
        "分群發文"
      ],
      "target": "中小企業、品牌分店 LINE OA、需要進階分群推播的團隊",
      "note": "最多人使用的方案"
    },
    {
      "id": "event_module",
      "name": "活動管理模組（加購）",
      "regular_price_twd": null,
      "promo_price_twd": 199,
      "billing_cycle": "monthly",
      "features": [
        "報名表單自訂",
        "報名人數上限控制",
        "自動確認訊息",
        "活動前 48 小時提醒",
        "QR 碼簽到"
      ],
      "is_addon": true,
      "pausable": true,
      "note": "不舉辦活動的月份可暫停，隨時可啟用"
    }
  ],
  "source": "賴管家 - 費用.md + 賴管家 - 活動模組.md"
}
```

---

## Tool 2｜`get_faq`

**類型**：查詢
**說明**：回傳 FAQ 指定題或全部。資料源：`賴管家 - FAQ.md`（8 題，P1 需爬原站補齊收合內容）。

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "question_id": {
      "type": "string",
      "enum": ["Q01", "Q02", "Q03", "Q04", "Q05", "Q06", "Q07", "Q08", "all"],
      "default": "all"
    },
    "keywords": {
      "type": "array",
      "items": { "type": "string" },
      "description": "替代 question_id 的關鍵字搜尋，例如 ['試用', '退費']"
    }
  }
}
```

### Return Example

```json
{
  "faqs": [
    {
      "id": "Q04",
      "question": "方案升降級何時生效？",
      "answer": "升降級不立即生效，於下個合約週期開始",
      "category": "billing"
    },
    {
      "id": "Q05",
      "question": "續約規則？",
      "answer": "每月自動續約，系統不再另行發出續約通知",
      "category": "billing"
    }
  ],
  "source": "賴管家 - FAQ.md",
  "warning": "目前 FAQ 多為收合狀態，P1 階段需爬 lineoa.batmobile.com.tw 補齊完整答案"
}
```

---

## Tool 3｜`check_plan_suitability`

**類型**：查詢（含推理）
**說明**：依使用者輸入的好友數 + 使用情境 → 建議方案。核心邏輯以好友數為主、功能需求為輔。

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "friend_count": {
      "type": "integer",
      "description": "預期或現有的 LINE OA 好友數"
    },
    "use_cases": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "booking",
          "mass_messaging",
          "tagging_segmentation",
          "rich_menu",
          "smart_customer_service",
          "event_registration",
          "hourly_analytics",
          "group_management"
        ]
      }
    },
    "industry": {
      "type": "string",
      "description": "使用者產業（例如：hair_salon / fitness / medical / retail / travel）"
    }
  },
  "required": ["friend_count"]
}
```

### Return Example

```json
{
  "recommended_plan": "personal",
  "reason": "好友數 < 50,000 符合個人版上限；使用情境 booking + rich_menu 皆在個人版功能清單內",
  "monthly_cost_twd": 99,
  "alternatives": [
    {
      "plan": "advanced",
      "upgrade_if": "好友數成長到 50,001 以上，或需要每小時數據 / 群組管理"
    }
  ],
  "addons": [
    {
      "plan": "event_module",
      "relevant": false,
      "reason": "使用情境未包含 event_registration"
    }
  ],
  "caveats": [
    "升降級不立即生效，下個合約週期才生效（FAQ Q04）"
  ]
}
```

---

## Tool 4｜`get_feature_detail`

**類型**：查詢（路由到手冊章節）
**說明**：指定功能關鍵字 → 回傳摘要 + 手冊 line 範圍，供 Agent 後續用 `Read` offset/limit 精準讀取（避免整檔 12 MB 讀入）。

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "feature": {
      "type": "string",
      "enum": [
        "booking",
        "member_management",
        "tagging",
        "push_messaging",
        "tracking_link",
        "rich_menu",
        "smart_customer_service",
        "event_management",
        "registration_and_login",
        "oa_connection"
      ]
    },
    "include_case_study": {
      "type": "boolean",
      "default": false,
      "description": "是否附帶產業案例（true 時回傳賴管家 - 預約.md 或手冊 lines 351-451 的案例）"
    }
  },
  "required": ["feature"]
}
```

### Return Example

```json
{
  "feature": "booking",
  "summary": "預約管理功能：店家資訊設定 → 管理服務項目（名稱／簡述／價格／時長）→ 行事曆（月／週／日三視圖）→ 預約列表 → 消費者端一鍵預約。預約確認訊息同步發送給店家與客人，預約當天 07:00 自動提醒客人。",
  "sources": [
    {
      "file": "賴管家 - 預約.md",
      "size_bytes": 23852,
      "recommend_full_read": true
    },
    {
      "file": "賴管家 - 操作手冊.md",
      "lines": "291-350",
      "note": "後台設定介面截圖 + 步驟說明，含 base64 圖片建議用 grep -v '^!\\[\\]' 過濾"
    }
  ],
  "case_studies": [
    {
      "persona": "小帥（髮型設計師）",
      "industry": "hair_salon",
      "source_file": "賴管家 - 預約.md"
    },
    {
      "persona": "Amanda（美甲師）",
      "industry": "nail_art",
      "source_file": "賴管家 - 預約.md"
    }
  ],
  "routing_table_source": "docs/manual-toc.md"
}
```

---

## Tool 5｜`get_contact_and_trial`

**類型**：查詢
**說明**：回傳蝙蝠移動官方聯繫管道 + 試用流程。

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "channel": {
      "type": "string",
      "enum": ["line_oa", "email", "all"],
      "default": "all"
    }
  }
}
```

### Return Example

```json
{
  "contacts": [
    {
      "type": "line_oa",
      "oa_id_basic": "@639sfpzz",
      "oa_id_dedicated": "@batmobile",
      "deep_link_template": "https://line.me/R/ti/p/%40{oa_id_url_encoded}",
      "note": "@batmobile 為蝙蝠移動專屬 OA，@639sfpzz 為基礎 OA，兩者皆可聯繫客服"
    },
    {
      "type": "email",
      "address": "service@batmobile.com.tw"
    }
  ],
  "trial_flow": [
    "1. 加入 @batmobile 或 @639sfpzz",
    "2. 透過 LINE 對話告知欲試用的方案（個人版 / 進階版）",
    "3. 完成 LINE OA 串接（手冊 Part 3 lines 84-102）",
    "4. 客服協助開通"
  ],
  "source": "賴管家 - 其他資訊.md + FAQ.md"
}
```

---

## Tool 6｜`initiate_trial_contact`（動作型）

**類型**：動作
**說明**：當使用者明確表示「好我要試用／我要加好友／幫我聯繫客服」時呼叫。產生 LINE deep link + 預填訊息文字，由使用者自行點開 LINE app 完成最後送出。

### ⚠️ 安全約束（符合 CLAUDE.md 全域約束）

| 約束 | 說明 |
|---|---|
| `no_payment_action` | 不執行任何金流動作，不引導到第三方信用卡頁面 |
| `no_auto_submit` | 不自動送出訊息，只產生 deep link 讓使用者**自己**點擊 |
| `no_user_data_transmission` | 不主動傳送使用者姓名／Email／電話到任何後端，只把 LINE deep link 還給使用者 |
| `consent_required` | 呼叫此工具前，Agent 必須先取得使用者明確同意（例如「我要試用」「幫我聯繫」） |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "target_oa": {
      "type": "string",
      "enum": ["@batmobile", "@639sfpzz"],
      "default": "@batmobile",
      "description": "@batmobile 為專屬 OA（主要），@639sfpzz 為基礎 OA（備用）"
    },
    "prefilled_intent": {
      "type": "string",
      "enum": ["trial_personal", "trial_advanced", "trial_event_module", "general_inquiry"],
      "description": "依使用者情境產生不同預填訊息"
    },
    "user_consent": {
      "type": "boolean",
      "description": "使用者是否已明確同意發起聯繫；false 時 Agent 不應呼叫此工具"
    }
  },
  "required": ["prefilled_intent", "user_consent"]
}
```

### Return Example

```json
{
  "action": "deep_link_generated",
  "target_oa": "@batmobile",
  "deep_link": "https://line.me/R/ti/p/%40batmobile",
  "prefilled_text": "你好，我想試用賴管家個人版，請問怎麼開始？",
  "instructions_for_user": [
    "1. 點擊上方連結或複製到瀏覽器開啟",
    "2. 系統會跳轉到 LINE app 並加入 @batmobile 官方帳號",
    "3. 將預填文字複製貼上並送出（這一步由你自己完成）"
  ],
  "constraints": {
    "no_payment_action": true,
    "no_auto_submit": true,
    "no_user_data_transmission": true
  },
  "fallback": {
    "if_line_app_not_installed": "改用 email: service@batmobile.com.tw"
  }
}
```

---

## 實作備忘（供 P1 參考）

1. **Token 管理**：賴管家後端呼叫 LINE Messaging API 時會用 Channel Access Token，但**本 MCP server 本身不需要 LINE token**（只是靜態查詢 + 產生 deep link）。P1 實作時可純本地檔案查詢，不需外部 API 金鑰。
2. **與 notify-system 的關聯**：notify-system Day 1 決策檔（`memory/decisions/2026-04-15-notify-system-day1-line-oa.md`）有處理 LINE OA OAuth 流程的 lesson learned，若 P2 擴充賴管家 MCP 支援「查詢使用者的 OA 後台資料」時可參考。
3. **測試策略**：P1 先針對 `get_pricing` / `get_faq` / `check_plan_suitability` 寫 unit test（可純 JSON fixture），`get_feature_detail` 需整合測試（依賴 manual-toc.md 路由 + 實際讀手冊檔）。
4. **錯誤處理**：所有工具應處理三種錯誤 —— 資料檔缺失、input schema 不符、盲區查詢（回傳標準「導流到 @batmobile」回應）。
