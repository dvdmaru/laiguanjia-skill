---
title: 賴管家 Skill — 產業情境案例索引
type: index
last_updated: 2026-04-19
source:
  - 賴管家 - 預約.md
  - https://lineoa.batmobile.com.tw/blogs/*
category: case-study
feature: booking
---

# 賴管家 Skill — 產業情境案例索引

本資料夾收錄賴管家（Laiguanjia）**預約功能**在六個具名產業主角身上的實際應用情境。每一篇 case study 都包含官網原文案例敘事 + 「賴管家 Skill 如何回應這個情境」段落，對應 MCP 工具呼叫範例。

## 設計原則

- **來源優先**：所有情境敘事以官網 `https://lineoa.batmobile.com.tw/blogs/*` 部落格文章為權威來源，`docs/case-studies/` 下的每篇 case 都是這些長文的結構化抽取版
- **真實主角**：6 位主角皆來自官網 blog 長文，並非自行編造。官網首頁 `/stories/*` 另有 4 位短見證主角（甜甜、阿管、奈奈、Lily），兩套敘事分工不同——短見證走行銷節奏，長文走產業情境
- **Skill 對接**：每篇 case 末段列出在同樣情境下，賴管家 Skill 會如何透過 MCP 工具（`get_feature_detail`、`get_pricing`、`check_plan_suitability`、`get_contact_and_trial`、`initiate_trial_contact`）幫使用者決策
- **資料一致**：本索引與 `data/feature-routes.json` 的 `features.booking.case_studies` 陣列同步維護（6 項，非 P0 誤寫的 8 項）

## 案例一覽

| 編號 | 主角 | 產業 | 官方提醒時機 | 檔案 |
|---|---|---|---|---|
| 01 | 小帥 | 髮型設計（hair_salon） | 預約日當天早上 7 點 | [01-stylist-xiaoshuai.md](./01-stylist-xiaoshuai.md) |
| 02 | Amanda | 健身教練（fitness） | 預約日當天早上 7 點 | [02-fitness-amanda.md](./02-fitness-amanda.md) |
| 03 | 小玲 | 美甲師（nail_art） | 預約日前一天傍晚 | [03-manicure-xiaoling.md](./03-manicure-xiaoling.md) |
| 04 | 小美 | 寵物美容師（pet_grooming） | 預約日當天早上 7 點 | [04-petgrooming-xiaomei.md](./04-petgrooming-xiaomei.md) |
| 05 | 小惠 | 診所護理師（clinic） | 預約看診前一天傍晚 | [05-clinic-xiaohui.md](./05-clinic-xiaohui.md) |
| 06 | 小陳 | 職業駕駛／機場接送（transportation） | 預約出發時間前 30 分鐘 | [06-driver-xiaochen.md](./06-driver-xiaochen.md) |

## 延伸閱讀（通用 blog）

這兩篇不聚焦單一主角，適合拿來理解「預約功能」的整體定位與入門門檻：

- [讓預約不再是煩惱：賴管家預約功能如何讓您掌握時間、贏得客戶](https://lineoa.batmobile.com.tw/blogs/line-official-account-appointment-booking-system-for-individuals-professionals)（個人專業工作者切入）
- [使用賴管家，5 分鐘就能建立自己的預約服務](https://lineoa.batmobile.com.tw/blogs/lineoa_reservation)（五分鐘快速建立）

兩篇完整文字已收錄在本專案的 `賴管家 - 預約.md`（line 1–168）。

## 與 feature-routes.json 的關聯

| docs/case-studies/ | data/feature-routes.json |
|---|---|
| 01-stylist-xiaoshuai.md | `booking.case_studies[0]`（`case_study_file` 指向此檔、`blog_slug=stylist`） |
| 02-fitness-amanda.md | `booking.case_studies[1]`（`blog_slug=lineoa_personaltrainer`） |
| 03-manicure-xiaoling.md | `booking.case_studies[2]`（`blog_slug=manicure`） |
| 04-petgrooming-xiaomei.md | `booking.case_studies[3]`（`blog_slug=petgrooming`） |
| 05-clinic-xiaohui.md | `booking.case_studies[4]`（`blog_slug=clinic`） |
| 06-driver-xiaochen.md | `booking.case_studies[5]`（`blog_slug=uber`） |

欄位語意：`case_study_file`＝repo 內此資料夾的相對路徑（宿主 agent 用 `Read` 取敘事內容時使用）；`blog_slug`＝官網 blog URL 最末段（與 `official_url` 搭配產生對外連結）；兩欄位分工，不可混用。

Skill 執行 `get_feature_detail(feature="booking", include_case_study=True)` 時，handler 從 `feature-routes.json` 抓 `case_studies` 陣列，回傳 6 項 `persona` + `industry` + `case_study_file` + `blog_slug` + `official_url` + `reminder_window` 的結構化資料。LLM 需要具體情境敘事時，再讀對應的 case study 檔案（`case_study_file` 指向）。

## 維護指引

- 官網 blog 若有增修，先更新 `賴管家 - 預約.md`（素材檔），再同步本資料夾對應 case
- 若官網新增第 7 位以上的具名主角：① 在 `feature-routes.json.booking.case_studies` 追加項目 ② 新增 `07-xxx.md` ③ 更新本 README 的一覽表與關聯表
- 不要把首頁 `/stories/*` 的 4 位短見證主角混入本資料夾——它們屬於行銷節奏，不適合作為產業情境範本
