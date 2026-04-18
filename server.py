"""
賴管家 MCP Server — Entry point
=================================

這是蝙蝠移動（Batmobile）旗下「賴管家（LaiGuanJia）」LINE OA 管理工具的
MCP (Model Context Protocol) server，用於讓 LLM agent 準確回答賴管家相關查詢。

P1 Day 1（2026-04-18）先實作 2 個 handler 作為 proof of life：
    - get_pricing
    - get_contact_and_trial

P1 Day 3（2026-04-18）新增：
    - get_faq
    - check_plan_suitability

其餘 2 個 handler（get_feature_detail / initiate_trial_contact）
於 P1 Day 4+ 實作，規格已定義於 repo 同層 mcp-spec.md。

Usage:
    python server.py                # 以 stdio transport 啟動
    mcp dev server.py               # 使用 MCP Inspector 開發模式

Requirements:
    pip install 'mcp[cli]>=1.2.0'
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

# --------------------------------------------------------------------------- #
# Server 初始化
# --------------------------------------------------------------------------- #

mcp = FastMCP(
    "laiguanjia",
    instructions=(
        "賴管家（LaiGuanJia）LINE OA 管理工具的查詢 MCP server。"
        "可查詢方案價格、官方聯繫管道、試用流程。"
        "僅回傳靜態查詢結果，不執行金流、不自動送出訊息、不傳送使用者個資。"
    ),
)

DATA_DIR = Path(__file__).parent / "data"


def _load_json(filename: str) -> dict[str, Any]:
    """載入 data/ 下的 JSON 檔，失敗時回傳包含 error 欄位的 dict。"""
    path = DATA_DIR / filename
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"error": f"資料檔不存在：{filename}", "path": str(path)}
    except json.JSONDecodeError as exc:
        return {"error": f"資料檔格式錯誤：{filename}", "detail": str(exc)}


# --------------------------------------------------------------------------- #
# Tool 1 | get_pricing
# --------------------------------------------------------------------------- #


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def get_pricing(plan: str = "all", include_promo: bool = True) -> dict[str, Any]:
    """
    回傳賴管家方案價格。

    Args:
        plan: 指定方案。可選值：
            - "all"（預設）：回傳三個方案
            - "personal"：個人版 $99/月（優惠價）
            - "advanced"：進階版 $599/月（優惠價）
            - "event_module"：活動管理模組 $199/月（加購）
        include_promo: 是否包含優惠價（預設 True，因當前所有方案都有優惠）。

    Returns:
        dict，包含 plans 清單、billing_rules、source。
    """
    data = _load_json("pricing.json")
    if "error" in data:
        return data

    valid_plans = {"all", "personal", "advanced", "event_module"}
    if plan not in valid_plans:
        return {
            "error": "plan 參數不合法",
            "valid_values": sorted(valid_plans),
            "received": plan,
        }

    plans = data.get("plans", [])
    if plan != "all":
        plans = [p for p in plans if p.get("id") == plan]

    # 依 include_promo 決定是否去除 promo_price_twd
    if not include_promo:
        plans = [
            {k: v for k, v in p.items() if k != "promo_price_twd"}
            for p in plans
        ]

    return {
        "plans": plans,
        "billing_rules": data.get("billing_rules", {}),
        "source": data.get("source"),
        "last_updated": data.get("last_updated"),
    }


# --------------------------------------------------------------------------- #
# Tool 2 | get_contact_and_trial
# --------------------------------------------------------------------------- #


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def get_contact_and_trial(channel: str = "all") -> dict[str, Any]:
    """
    回傳蝙蝠移動（賴管家母公司）的官方聯繫管道 + 試用流程說明。

    Args:
        channel: 指定管道。可選值：
            - "all"（預設）：回傳所有管道（LINE OA + Email + website）
            - "line_oa"：只回傳 LINE 官方帳號資訊
            - "email"：只回傳 email

    Returns:
        dict，包含 contacts（管道資訊）、trial_flow（試用流程）、
        prefilled_messages（預填訊息範本，供下一階段 initiate_trial_contact 使用）、
        constraints（安全約束：不金流、不自動送出、不傳使用者個資）、source。

    Security Notes:
        此工具僅為靜態查詢，不執行任何對外動作。若使用者已明確同意要發起試用，
        應由 initiate_trial_contact 工具（P1 Day 2+ 實作）處理 deep link 生成，
        且使用者本人仍須手動點擊、複製、貼上、送出訊息。
    """
    data = _load_json("contacts.json")
    if "error" in data:
        return data

    valid_channels = {"all", "line_oa", "email"}
    if channel not in valid_channels:
        return {
            "error": "channel 參數不合法",
            "valid_values": sorted(valid_channels),
            "received": channel,
        }

    contacts = data.get("contacts", {})

    # 依 channel 過濾
    if channel == "line_oa":
        filtered = {
            "line_oa_basic": contacts.get("line_oa_basic"),
            "line_oa_dedicated": contacts.get("line_oa_dedicated"),
        }
    elif channel == "email":
        filtered = {"email": contacts.get("email")}
    else:
        filtered = contacts

    return {
        "contacts": filtered,
        "trial_flow": data.get("trial_flow", []),
        "prefilled_messages": data.get("prefilled_messages", {}),
        "constraints": data.get("constraints", {}),
        "source": data.get("source"),
        "last_updated": data.get("last_updated"),
    }


# --------------------------------------------------------------------------- #
# Tool 3 | get_faq
# --------------------------------------------------------------------------- #


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def get_faq(
    question_id: str = "all",
    keywords: list[str] | None = None,
) -> dict[str, Any]:
    """
    回傳賴管家 FAQ。資料源為 `賴管家 - FAQ.md`，共 8 題（其中 2 題 full、
    4 題 partial、2 題 collapsed_on_source）。

    Args:
        question_id: 指定題號。可選值：
            - "all"（預設）：回傳全部 8 題
            - "Q01" ~ "Q08"：指定單題
        keywords: 關鍵字陣列（選填）。若提供，將在 question_id 過濾後的結果
            再以關鍵字交集過濾（關鍵字在 question 或 answer 欄位出現即算命中）。

    Returns:
        dict，包含：
            - faqs: list，每題含 id / question / answer / category /
              completeness / source_note / source_url
            - matched_count: int
            - completeness_legend: dict（提醒 LLM 如何處理 partial / collapsed）
            - data_quality_note: str（整體資料品質提示，建議 LLM 引用給使用者）
            - source, last_updated

    Completeness Notes:
        - "full"：答案完整，可直接回覆
        - "partial"：僅有片段，回覆時須附「建議至官網或 @batmobile 詢問」
        - "collapsed_on_source"：無答案，必須導流至官網或 @batmobile
    """
    data = _load_json("faq.json")
    if "error" in data:
        return data

    faqs = data.get("faqs", [])
    valid_ids = {f["id"] for f in faqs} | {"all"}

    if question_id not in valid_ids:
        return {
            "error": "question_id 參數不合法",
            "valid_values": sorted(valid_ids),
            "received": question_id,
        }

    # 1. 依 question_id 過濾
    if question_id != "all":
        faqs = [f for f in faqs if f["id"] == question_id]

    # 2. 若有 keywords，再做交集過濾（question 或 answer 任一命中即算）
    if keywords:
        kw_lower = [k.lower() for k in keywords if isinstance(k, str)]

        def _hit(faq: dict[str, Any]) -> bool:
            q = (faq.get("question") or "").lower()
            a = (faq.get("answer") or "").lower()
            return any(kw in q or kw in a for kw in kw_lower)

        faqs = [f for f in faqs if _hit(f)]

    return {
        "faqs": faqs,
        "matched_count": len(faqs),
        "completeness_legend": data.get("completeness_legend", {}),
        "data_quality_note": data.get("data_quality_note"),
        "categories": data.get("categories", []),
        "source": data.get("source"),
        "last_updated": data.get("last_updated"),
    }


# --------------------------------------------------------------------------- #
# Tool 4 | check_plan_suitability
# --------------------------------------------------------------------------- #


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def check_plan_suitability(
    friend_count: int,
    use_cases: list[str] | None = None,
    industry: str | None = None,
) -> dict[str, Any]:
    """
    依使用者的 LINE OA 好友數、使用情境、產業，建議適合的賴管家方案。

    邏輯順序：
        1. friend_count → base_plan（personal / advanced / escalate_to_sales）
        2. 若 > 100,000 → 回傳 escalate 分支，引導至 @batmobile 客服
        3. 依 use_cases 檢查是否需從 personal 升級到 advanced
           （例如 hourly_analytics / group_management 只在 advanced）
        4. 依 use_cases 檢查是否觸發加購（event_registration → event_module）
        5. 合計 monthly_cost_twd（base + addons）
        6. industry 僅作為輔助提示，不影響主要決策

    Args:
        friend_count: 預期或現有的 LINE OA 好友數（必填，須為非負整數）
        use_cases: 使用情境陣列（選填）。合法值見 feature_to_min_base_plan
            的 keys：booking / tagging_segmentation / rich_menu /
            mass_messaging / smart_customer_service / event_registration /
            hourly_analytics / group_management
        industry: 產業代碼（選填）。合法值見 industry_hints 的 keys：
            hair_salon / nail_art / fitness / pet_grooming / confectionery /
            medical / retail / travel

    Returns:
        dict，包含 recommended_plan / reason / monthly_cost_twd /
        alternatives / addons / industry_hint / caveats / source。
        若 friend_count 不合法或 use_cases 含不合法值，回傳 error 物件。
    """
    rules = _load_json("plans-suitability-rules.json")
    if "error" in rules:
        return rules

    # --- 輸入驗證 --------------------------------------------------------- #
    # Python 的 bool 是 int 的子類，要排除掉
    if not isinstance(friend_count, int) or isinstance(friend_count, bool) or friend_count < 0:
        return {
            "error": "friend_count 參數不合法（須為非負整數）",
            "received": friend_count,
            "expected": "int >= 0",
        }

    use_cases = use_cases or []
    valid_use_cases = set(rules.get("feature_to_min_base_plan", {}).keys())
    invalid_use_cases = [uc for uc in use_cases if uc not in valid_use_cases]
    if invalid_use_cases:
        return {
            "error": "use_cases 含不合法值",
            "invalid": invalid_use_cases,
            "valid_values": sorted(valid_use_cases),
        }

    valid_industries = set(rules.get("industry_hints", {}).keys())
    if industry is not None and industry not in valid_industries:
        return {
            "error": "industry 參數不合法",
            "valid_values": sorted(valid_industries),
            "received": industry,
        }

    # --- 1. friend_count → base_plan -------------------------------------- #
    base_plan: str | None = None
    base_cost: int | None = None
    for threshold in rules.get("friend_count_thresholds", []):
        lower = threshold["min"]
        upper = threshold["max"]  # None 代表無上限
        if friend_count >= lower and (upper is None or friend_count <= upper):
            base_plan = threshold["recommended_plan"]
            base_cost = threshold.get("base_monthly_cost_twd")
            break

    if base_plan is None:
        # 理論上不應該發生（thresholds 已涵蓋 0 到 infinity）
        return {
            "error": "friend_count 未落在任何 threshold 內",
            "received": friend_count,
            "thresholds": rules.get("friend_count_thresholds"),
        }

    # --- 2. > 100,000 escalate 分支 --------------------------------------- #
    if base_plan == "escalate_to_sales":
        escalate_threshold = next(
            (t for t in rules["friend_count_thresholds"]
             if t["recommended_plan"] == "escalate_to_sales"),
            {},
        )
        return {
            "recommended_plan": "custom_enterprise",
            "reason": (
                f"好友數 {friend_count} 超過現有公開方案（進階版上限 100,000）"
                "，需透過 @batmobile 客服客製化議價"
            ),
            "monthly_cost_twd": None,
            "next_action": {
                "channel": "line_oa",
                "target_oa": "@batmobile",
                "prefilled_text": (
                    f"你好，我的 LINE OA 好友數約 {friend_count} 人"
                    "，想詢問賴管家是否有客製方案"
                ),
                "fallback_email": "service@batmobile.com.tw",
            },
            "caveats": rules.get("caveats", []),
            "escalate_note": escalate_threshold.get("note"),
            "source": rules.get("source"),
        }

    # --- 3. use_cases 升級 base_plan -------------------------------------- #
    plan_rank: dict[str, int] = rules.get("plan_rank", {})
    feature_map: dict[str, str] = rules.get("feature_to_min_base_plan", {})
    upgrade_triggered_by: list[str] = []
    for uc in use_cases:
        required = feature_map.get(uc)
        if required and plan_rank.get(required, 0) > plan_rank.get(base_plan, 0):
            base_plan = required
            upgrade_triggered_by.append(uc)

    # 升級後可能改變 base_cost，從 thresholds 取新方案對應的價格
    if upgrade_triggered_by:
        for threshold in rules.get("friend_count_thresholds", []):
            if threshold["recommended_plan"] == base_plan:
                base_cost = threshold.get("base_monthly_cost_twd")
                break

    # --- 4. addons 觸發 --------------------------------------------------- #
    addon_triggers: dict[str, dict[str, Any]] = rules.get("addon_triggers", {})
    addons: list[dict[str, Any]] = []
    for uc in use_cases:
        if uc in addon_triggers:
            info = addon_triggers[uc]
            addons.append({
                "addon_id": info["addon_id"],
                "addon_name": info.get("addon_name"),
                "triggered_by_use_case": uc,
                "monthly_cost_twd": info["addon_monthly_cost_twd"],
                "note": info.get("note"),
            })

    # --- 5. 合計成本 ------------------------------------------------------ #
    addon_cost_total = sum(a["monthly_cost_twd"] for a in addons)
    total_cost = (base_cost or 0) + addon_cost_total

    # --- 6. reason / alternatives / industry_hint ------------------------- #
    reason_parts = [f"好友數 {friend_count} 人落在 {base_plan} 方案範圍"]
    if upgrade_triggered_by:
        reason_parts.append(
            f"使用情境 {', '.join(upgrade_triggered_by)} 需升級至 {base_plan}"
        )
    elif use_cases:
        reason_parts.append(
            f"使用情境 {', '.join(use_cases)} 皆涵蓋於 {base_plan} 方案功能"
        )
    if addons:
        addon_names = [a["addon_id"] for a in addons]
        reason_parts.append(f"觸發加購：{', '.join(addon_names)}")

    alternatives: list[dict[str, Any]] = []
    if base_plan == "personal":
        alternatives.append({
            "plan": "advanced",
            "upgrade_if": (
                "好友數成長到 50,001 以上，或需要每小時數據 / 群組管理 / 分群發文"
            ),
        })

    industry_hint = None
    if industry:
        industry_hint = rules.get("industry_hints", {}).get(industry)

    return {
        "recommended_plan": base_plan,
        "reason": "；".join(reason_parts),
        "monthly_cost_twd": {
            "base": base_cost,
            "addons": addon_cost_total,
            "total": total_cost,
        },
        "alternatives": alternatives,
        "addons": addons,
        "industry_hint": industry_hint,
        "caveats": rules.get("caveats", []),
        "source": rules.get("source"),
    }


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def main() -> None:
    """以 stdio transport 啟動 MCP server。"""
    mcp.run()


if __name__ == "__main__":
    main()
