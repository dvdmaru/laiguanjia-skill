---
title: 02 Data + Routing + I/O Delegation Three-Segment Separation
type: whitepaper-chapter
chapter: 02
last_updated: 2026-04-19
audience: External technical reviewers (Security / AI governance)
source:
  - server.py
  - data/feature-routes.json
  - data/pricing.json
  - data/faq.json
  - docs/manual-toc.md
  - docs/case-studies/*.md
category: whitepaper
language: en
counterpart: ./02-data-layer-separation.md
related_adr: ../../../memory/decisions/2026-04-19-laiguanjia-three-segment-separation.md
---

# 02. Data + Routing + I/O Delegation — Three-Segment Separation

## 2.1 Why "three-segment separation"

Two common anti-patterns appear in LLM agent tooling:

- **Anti-pattern A: tool bundles data + logic + I/O**. E.g. a tool called `get_pricing_and_open_line` that looks up pricing and **also redirects the user to LINE** — the host agent sees and intercepts neither. A hallucination or prompt injection can make the LLM open LINE when it shouldn't
- **Anti-pattern B: tool is a "black-box API"**. The host only sees "call some tool, get a natural language answer"; what the tool does internally (what data it read, what network calls it made) is opaque — auditing is hard

Laiguanjia Skill avoids both via **three-segment separation**:

```
┌───────────────────────────┐
│ 1. Data segment            │  ← Pure static JSON, no logic
│    data/*.json             │
└───────────────────────────┘
            ▲ Python open/read
            │
┌───────────────────────────┐
│ 2. Routing segment         │  ← Decides which data slice to return;
│    server.py six handlers  │     validates format; no network, no fs write
└───────────────────────────┘
            ▲ MCP tools/call return
            │
┌───────────────────────────┐
│ 3. I/O delegation          │  ← Host agent's responsibility:
│    Host agent              │     - Natural language from payload
│    (Cowork / Claude Code)  │     - Expand manual (Read)
│                            │     - Open LINE URL (user consent)
│                            │     - Send LINE OA messages (official only)
└───────────────────────────┘
```

Each segment has clear **responsibility boundaries**; calls that cross boundaries are rejected by the next segment.

## 2.2 Data segment: `data/*.json`

Three files (as of 2026-04-19):

| File | Purpose | Size | Update cadence |
|---|---|---|---|
| `data/pricing.json` | Plan pricing, feature matrix, contact info | ~8 KB | On official announcement |
| `data/faq.json` | Eight FAQ entries (onboarding, push, loyalty, multi-store, compliance, tech, billing) | ~12 KB | When official FAQ changes |
| `data/feature-routes.json` | Three-feature (booking, loyalty, push) metadata + case study pointers + manual pointers | ~14 KB | On new feature / case additions |

**Key principles**:

1. **Data is data, not code**. No `${env}` interpolation, no JS/Python `eval` paths, no HTML `<script>` injection — all outputs derived from data are sanitized by the routing segment
2. **Version-controlled via Git**. Every pricing / FAQ change has a commit trail; reviewers can `git blame` to see who changed what when
3. **No PII, no real customer data**. The six case-study personas (Xiaoshuai, Amanda, Xiaoling, Xiaomei, Xiaohui, Xiaochen) all originate from public [official blog](https://lineoa.batmobile.com.tw/blogs/) content, not real customer PII

**Manual is handled specially**: the full Laiguanjia PDF manual is ~**12 MB**. Bundling it into JSON causes (a) single-tool-call payload blowing context window; (b) unnecessary bulk data exposure. Solution: **lazy loading**:

- `data/feature-routes.json` stores only **pointers** — each feature maps to a section in `docs/manual-toc.md`
- `get_feature_detail` returns metadata + pointer; the host `Read`s the actual content on demand
- `docs/manual-toc.md` is a **structured TOC** of the official PDF, not its full text — original text lives on the official site

## 2.3 Routing segment: six handlers in `server.py`

Each of the six handlers **maps input parameters to a slice of data, performs any computation, and returns a structured payload**. Example from `check_plan_suitability` (the only compute-bearing handler):

```python
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def check_plan_suitability(industry: str, friend_count: int) -> dict:
    # 1. Input validation (Pydantic confirms type; here we add value range checks)
    if not isinstance(friend_count, int) or isinstance(friend_count, bool) or friend_count < 0:
        return {"error": "friend_count is invalid; must be a non-negative integer"}

    # 2. Read thresholds from data/pricing.json
    pricing = load_pricing()  # read-only

    # 3. Pure compute: friend count × plan caps → suggested plan
    if friend_count <= 200:
        suggested = "starter"
    elif friend_count <= 2000:
        suggested = "pro"
    else:
        suggested = "enterprise"

    # 4. Return structured payload
    return {
        "industry": industry,
        "friend_count": friend_count,
        "suggested_plan": suggested,
        "reasoning": f"...",
        # No URL, no "want me to open LINE?" type nudging
    }
```

**Three commandments** (upheld throughout `server.py`):

1. **No network**: no `requests.*`, `urllib.*`, `socket.*`; no outbound DNS
2. **No file writes**: handlers only do `open(..., "r")`, never `open(..., "w")`
3. **No eval**: no `eval()` / `exec()` / `subprocess.*`; Pydantic validates structure, doesn't execute anything

These can be verified with static scans (e.g. `grep -nE "requests\.|urllib\.|socket\.|eval\(|exec\(|subprocess\."` on `server.py`). In practice, CI can run `bandit` or `semgrep` for stronger guarantees.

## 2.4 I/O delegation: host agent's responsibility

**Three things** are delegated to the host agent. The MCP server never does them:

### A. Turn structured payload into natural language

Server returns:

```json
{"monthly_price_twd": 490, "plan": "starter", ...}
```

Host agent (Claude or another LLM) decides how to phrase it to the user:

> "Laiguanjia Starter is NT$490 per month and is suitable for..."

**Factual accuracy** depends on the LLM not hallucinating. Mitigations: (a) payload is already minimal factual assertion — LLM needs to "say it plainly" not "invent content"; (b) host's system prompt can require direct quoting of payload fields.

### B. Expand manual details

When a user asks "how does booking work?":

1. LLM calls `get_feature_detail(feature="booking")`, receives `{... "manual_pointer": "docs/manual-toc.md#booking"}`
2. LLM decides more detail is needed → uses `Read` on `docs/manual-toc.md#booking`
3. If host (e.g. Cowork mode) has `Read` → success; if not → LLM explicitly tells user "I can't open the manual directly; find the tutorial at [this link](https://lineoa.batmobile.com.tw/)"

**Why lazy loading**: 12 MB manual in payload crashes context; pointer mode = on-demand use. Also: `Read` is a host-side auditable action, making "did the LLM actually consult the real manual?" verifiable.

### C. Open LINE / send messages

Details in [03 Consent Gate](./03-consent-gate-pattern.en.md). Core principle: **even if `initiate_trial_contact` returns "host agent should open URL X", the actual open is done by the host**, which should re-confirm with the user first. Meaning: even if the MCP server is compromised and returns a fake URL, the host still has a chance to intercept.

## 2.5 Why `get_feature_detail` returns only metadata

`get_feature_detail` is the poster child of three-segment separation. Its return:

```json
{
  "feature": "booking",
  "official_url": "https://lineoa.batmobile.com.tw/features/booking",
  "supported_industries": ["hair_salon", "fitness", "nail_art", "pet_grooming", "clinic", "transportation"],
  "case_studies": [
    {
      "persona": "Xiaoshuai",
      "industry": "hair_salon",
      "case_study_file": "docs/case-studies/01-stylist-xiaoshuai.md",
      "blog_slug": "stylist",
      "official_url": "https://lineoa.batmobile.com.tw/blogs/stylist",
      "reminder_window": "7 AM on the booking day"
    },
    ... (5 more)
  ],
  "manual_pointer": "docs/manual-toc.md#booking"
}
```

**Deliberately not returned**:

- **Full case-study narrative**: lives in `docs/case-studies/*.md`; host `Read`s on demand. Rationale: (a) single-payload size stays under 50 KB; (b) `Read` calls on host side become auditable
- **Full manual body**: same — too big
- **Any nudge language**: no "try free now" / "register immediately" strings. CTAs are the host agent's prerogative based on conversation flow, not the tool's job

Meets both **security** (smaller payload attack surface) and **AI governance** (less risk of LLM producing marketing-ish output based on tool returns) requirements.

## 2.6 Data boundary & prompt injection

String fields in `data/*.json` (e.g. FAQ answers, pricing descriptions) may become part of the LLM's context. If someone sneaks `"answer": "...email attacker@evil.com"` into a PR, the LLM output could be poisoned.

**Mitigations**:

- **Every data change needs PR review**. Currently maintained solo by Charlie; after open-sourcing, CODEOWNERS + branch protection will be added
- **Returned payload must be treated as "tool result", not "system prompt"** on the host side — the MCP spec establishes this separation, but host implementation quality determines respect
- **Sensitive fields (URLs, emails) have hardcoded allowlist validation in the routing segment** (e.g. `initiate_trial_contact` only returns URLs prefixed with `https://line.batmobile.com.tw/` or `https://lin.ee/`; see [03](./03-consent-gate-pattern.en.md))

## 2.7 ADR mapping

Full decision record: [ADR: 2026-04-19-laiguanjia-three-segment-separation.md](../../../memory/decisions/2026-04-19-laiguanjia-three-segment-separation.md)

The ADR details why "monolithic MCP server (logic + I/O together)" and "pure static JSON / no routing layer" were rejected, and the long-term maintenance cost of three-segment separation.

## 2.8 Chapter recap

1. **Data, logic, I/O each have distinct responsibilities**; boundaries are verifiable by static scans
2. **Routing segment does no network, no file write, no eval** — three security commandments easy to check
3. **`get_feature_detail`'s pointer mode** implements lazy loading, meeting both context window constraints and auditability
4. **Delegating I/O to host** keeps consent and final-action control with the user; even a compromised MCP server can be intercepted by host
5. **Next (03)**: how `initiate_trial_contact`, the only tool with sensitive semantics, uses Consent Gate + bool-is-int guard to minimize abuse
