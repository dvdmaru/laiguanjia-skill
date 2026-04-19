"""
P1 Day 4 雙工具 Python-level 驗證腳本（VM × Mac 雙層）。

新增 2 個工具：
  * get_feature_detail        — 手冊路由查詢
  * initiate_trial_contact    — LINE OA deep link 生成（不金流、不自動送出）

目的：以「12 組輸入 → JSON 輸出」的形式跑過兩工具的所有關鍵分支。
  * VM 端：`python3 tests/test_day4_handlers.py vm` → tests/outputs/day4-vm.json
  * Mac 端：`python3 tests/test_day4_handlers.py mac` → tests/outputs/day4-mac.json
  * 對齊方式：`diff tests/outputs/day4-vm.json tests/outputs/day4-mac.json`
    （除了 runtime 欄位外應完全相同，預期 diff 僅 1 行）

測試群組涵蓋（延用 Day 3 設計原則）：
  * Happy path（標準路徑）
  * 邊界（case_study 開關 / section_id 精準過濾 / 備用 OA）
  * 防禦性（不合法 feature / section_id / intent / target_oa / bool-is-int 陷阱）

⚠️  此腳本只驗 Python 邏輯層；MCP 協定包裝（ToolAnnotations / JSON schema /
    stdio transport）需在 Mac 端開 `mcp dev server.py` 透過 Inspector 測 3-4 組
    代表性 payload（spot check）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 允許直接 `python3 tests/test_day4_handlers.py`
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import get_feature_detail, initiate_trial_contact  # noqa: E402


# --------------------------------------------------------------------------- #
# 測試組（12 組）
# --------------------------------------------------------------------------- #


GROUPS: list[dict] = [
    # ---- get_feature_detail（6 組） --------------------------------------- #
    {
        "name": "feature_detail | booking 預設（不含 case_study）",
        "fn": "get_feature_detail",
        "args": {"feature": "booking"},
    },
    {
        "name": "feature_detail | booking + include_case_study=True（8 個產業案例）",
        "fn": "get_feature_detail",
        "args": {"feature": "booking", "include_case_study": True},
    },
    {
        "name": "feature_detail | event_management + section_id=event_supplement_full + case_study",
        "fn": "get_feature_detail",
        "args": {
            "feature": "event_management",
            "section_id": "event_supplement_full",
            "include_case_study": True,
        },
    },
    {
        "name": "feature_detail | smart_customer_service（單一 section，含 Token 額度）",
        "fn": "get_feature_detail",
        "args": {"feature": "smart_customer_service"},
    },
    {
        "name": "feature_detail | feature=unknown_feature（防禦性 - 不合法 feature）",
        "fn": "get_feature_detail",
        "args": {"feature": "unknown_feature"},
    },
    {
        "name": "feature_detail | booking + section_id=nonexistent（防禦性 - section 不屬於此 feature）",
        "fn": "get_feature_detail",
        "args": {"feature": "booking", "section_id": "nonexistent_section"},
    },

    # ---- initiate_trial_contact（6 組） ---------------------------------- #
    {
        "name": "trial_contact | happy path：consent=True + trial_personal + @batmobile",
        "fn": "initiate_trial_contact",
        "args": {
            "prefilled_intent": "trial_personal",
            "target_oa": "@batmobile",
            "user_consent": True,
        },
    },
    {
        "name": "trial_contact | 備用 OA：consent=True + general_inquiry + @639sfpzz",
        "fn": "initiate_trial_contact",
        "args": {
            "prefilled_intent": "general_inquiry",
            "target_oa": "@639sfpzz",
            "user_consent": True,
        },
    },
    {
        "name": "trial_contact | 活動模組加購：consent=True + trial_event_module + 預設 OA",
        "fn": "initiate_trial_contact",
        "args": {
            "prefilled_intent": "trial_event_module",
            "user_consent": True,
        },
    },
    {
        "name": "trial_contact | 缺同意（預設 False）→ consent_required",
        "fn": "initiate_trial_contact",
        "args": {"prefilled_intent": "trial_personal"},
    },
    {
        "name": "trial_contact | bool-is-int 陷阱：consent=1（int 非 bool）→ consent_required",
        "fn": "initiate_trial_contact",
        "args": {"prefilled_intent": "trial_personal", "user_consent": 1},
    },
    {
        "name": "trial_contact | 不合法 intent：consent=True + UNKNOWN_INTENT",
        "fn": "initiate_trial_contact",
        "args": {"prefilled_intent": "UNKNOWN_INTENT", "user_consent": True},
    },
]


DISPATCH = {
    "get_feature_detail": get_feature_detail,
    "initiate_trial_contact": initiate_trial_contact,
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
    layer = sys.argv[1] if len(sys.argv) > 1 else "vm"
    if layer not in {"vm", "mac"}:
        print(f"❌ 不合法 layer={layer}，請用 vm 或 mac", file=sys.stderr)
        return 2

    bundle = run()
    bundle["runtime"] = f"{layer}_python"
    out_path = ROOT / "tests" / "outputs" / f"day4-{layer}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"✅ Wrote {out_path}")
    for g in bundle["groups"]:
        tag = "OK" if g["ok"] else "EX"
        print(f"  [{tag}] {g['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
