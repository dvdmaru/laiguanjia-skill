"""
賴管家 MCP Server — Entry point
=================================

這是蝙蝠移動（Batmobile）旗下「賴管家（LaiGuanJia）」LINE OA 管理工具的
MCP (Model Context Protocol) server，用於讓 LLM agent 準確回答賴管家相關查詢。

P1 Day 1（2026-04-18）先實作 2 個 handler 作為 proof of life：
    - get_pricing
    - get_contact_and_trial

其餘 4 個 handler（get_faq / check_plan_suitability /
get_feature_detail / initiate_trial_contact）於 P1 Day 2+ 實作，
規格已定義於 repo 同層 mcp-spec.md。

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


@mcp.tool()
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


@mcp.tool()
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
# Entry point
# --------------------------------------------------------------------------- #


def main() -> None:
    """以 stdio transport 啟動 MCP server。"""
    mcp.run()


if __name__ == "__main__":
    main()
