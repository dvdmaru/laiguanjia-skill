"""
P1 Day 3 雙工具 Python-level 驗證腳本（VM × Mac 雙層）。

目的：以「n 組輸入 → JSON 輸出」的形式跑過 get_faq + check_plan_suitability
的所有關鍵分支。
  * VM 端：`python3 tests/test_day3_handlers.py vm` → tests/outputs/day3-vm.json
  * Mac 端：`python3 tests/test_day3_handlers.py mac` → tests/outputs/day3-mac.json
  * 對齊方式：`diff tests/outputs/day3-vm.json tests/outputs/day3-mac.json`
    （除了 runtime 欄位外應完全相同）

測試群組定義原則：
  * 每個群組 = {name, fn_name, args} 三元組
  * 涵蓋 happy path + 邊界 + 升級 + 加購 + escalate + 防禦性
  * 輸出必須可被 `json.dumps(..., sort_keys=True, ensure_ascii=False)` 序列化

⚠️  此腳本只驗 Python 邏輯層；要驗證 MCP 協定包裝（ToolAnnotations / JSON schema /
    stdio transport）還是需要在 Mac 端開 `mcp dev server.py` 透過 Inspector 測
    2-3 組代表性 payload（spot check）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 允許直接 `python3 tests/test_day3_handlers.py`
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import check_plan_suitability, get_faq  # noqa: E402


# --------------------------------------------------------------------------- #
# 測試組
# --------------------------------------------------------------------------- #


GROUPS: list[dict] = [
    # ---- get_faq ---------------------------------------------------------- #
    {
        "name": "get_faq | question_id=Q04（full 答案）",
        "fn": "get_faq",
        "args": {"question_id": "Q04"},
    },
    {
        "name": "get_faq | question_id=all（全部 8 題）",
        "fn": "get_faq",
        "args": {"question_id": "all"},
    },
    {
        "name": "get_faq | keywords=[試用]（應落在 Q01 以外，若無命中回 0 題）",
        "fn": "get_faq",
        "args": {"keywords": ["試用"]},
    },
    {
        "name": "get_faq | keywords=[續約]（應命中 Q05）",
        "fn": "get_faq",
        "args": {"keywords": ["續約"]},
    },
    {
        "name": "get_faq | question_id=Q99（防禦性 - 不合法 id）",
        "fn": "get_faq",
        "args": {"question_id": "Q99"},
    },

    # ---- check_plan_suitability ----------------------------------------- #
    {
        "name": "plan | 1000 好友 + booking → personal",
        "fn": "check_plan_suitability",
        "args": {"friend_count": 1000, "use_cases": ["booking"]},
    },
    {
        "name": "plan | 80000 好友 + hourly_analytics → advanced",
        "fn": "check_plan_suitability",
        "args": {"friend_count": 80000, "use_cases": ["hourly_analytics"]},
    },
    {
        "name": "plan | 150000 好友 → escalate_to_sales",
        "fn": "check_plan_suitability",
        "args": {"friend_count": 150000},
    },
    {
        "name": "plan | 30000 好友 + event_registration → personal + event_module 加購",
        "fn": "check_plan_suitability",
        "args": {"friend_count": 30000, "use_cases": ["event_registration"]},
    },
    {
        "name": "plan | 20000 好友 + industry=hair_salon → personal + industry_hint",
        "fn": "check_plan_suitability",
        "args": {
            "friend_count": 20000,
            "use_cases": ["booking", "tagging_segmentation"],
            "industry": "hair_salon",
        },
    },
    {
        "name": "plan | 1000 好友 + group_management → 升級 advanced",
        "fn": "check_plan_suitability",
        "args": {"friend_count": 1000, "use_cases": ["group_management"]},
    },
    {
        "name": "plan | friend_count=-1（防禦性 - 非負整數）",
        "fn": "check_plan_suitability",
        "args": {"friend_count": -1},
    },
    {
        "name": "plan | use_cases=[UNKNOWN_UC]（防禦性 - 不合法 use_case）",
        "fn": "check_plan_suitability",
        "args": {"friend_count": 1000, "use_cases": ["UNKNOWN_UC"]},
    },
    {
        "name": "plan | industry=unknown（防禦性 - 不合法 industry）",
        "fn": "check_plan_suitability",
        "args": {"friend_count": 1000, "industry": "unknown_industry"},
    },
]


DISPATCH = {
    "get_faq": get_faq,
    "check_plan_suitability": check_plan_suitability,
}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def run() -> dict:
    results = []
    for group in GROUPS:
        fn = DISPATCH[group["fn"]]
        try:
            output = fn(**group["args"])
            results.append({
                "name": group["name"],
                "fn": group["fn"],
                "args": group["args"],
                "ok": True,
                "output": output,
            })
        except Exception as exc:  # noqa: BLE001
            results.append({
                "name": group["name"],
                "fn": group["fn"],
                "args": group["args"],
                "ok": False,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            })
    return {"runtime": "vm_python", "count": len(results), "groups": results}


def main() -> int:
    # 支援 `python3 tests/test_day3_handlers.py vm` / `... mac` 以區分雙層輸出
    layer = sys.argv[1] if len(sys.argv) > 1 else "vm"
    if layer not in {"vm", "mac"}:
        print(f"❌ 不合法 layer={layer}，請用 vm 或 mac", file=sys.stderr)
        return 2

    bundle = run()
    bundle["runtime"] = f"{layer}_python"
    out_path = ROOT / "tests" / "outputs" / f"day3-{layer}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    # 同步印出「小摘要」以便肉眼快速掃描
    print(f"✅ Wrote {out_path}")
    for g in bundle["groups"]:
        tag = "OK" if g["ok"] else "EX"
        print(f"  [{tag}] {g['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
