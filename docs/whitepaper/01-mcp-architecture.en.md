---
title: 01 MCP Architecture Overview
type: whitepaper-chapter
chapter: 01
last_updated: 2026-04-19
audience: External technical reviewers (Security / Legal / AI ethics)
source:
  - server.py
  - mcp-spec.md
category: whitepaper
language: en
counterpart: ./01-mcp-architecture.md
---

# 01. MCP Architecture Overview

## 1.1 Why MCP instead of REST API

The Skill's core goal is to let LLM agents (Claude Desktop, Cowork mode, Claude Code) **autonomously call tools during reasoning** to answer questions about Laiguanjia usage, plan fit, and pricing, and — on explicit user consent — help open a LINE trial entry. This implies:

- LLM must call tools dynamically, not force the user to pre-fetch data
- Tools must be typed, have schemas, and have descriptions (so LLMs interpret them correctly without hallucinating parameters)
- Tool calls must be auditable (every call, params, and response can be host-logged)
- Must not bind to a single LLM vendor (today Claude, tomorrow any MCP-capable agent)

Three options were compared:

| Option | Pros | Cons |
|---|---|---|
| A. REST API + hand-written prompt tool descriptions | Low barrier; familiar | Different prompts per LLM; no standard schema; host must build its own audit |
| **B. MCP server (chosen)** | Open standard (Anthropic + community); built-in typing and annotations; host gets audit for free; portable across LLMs | Spec still evolving (v2025-03-26 current); ecosystem smaller than REST |
| C. Anthropic "Claude Skill" folder directly | Lowest barrier (pure Markdown) | Only works in Claude ecosystem; no structured tool calls; no consent gate |

Chose B. The Skill is **dual-distributed** as both a Claude Skill (for Claude ecosystem loading) and an MCP server (for any MCP host). Both share the same `data/*.json` and `server.py`.

Full decision log: [2026-04-17-laiguanjia-X+Z-strategy.md](../../../memory/decisions/2026-04-17-laiguanjia-X+Z-strategy.md).

## 1.2 MCP tech stack

- **MCP spec version**: 2025-03-26 (latest stable as of 2026-04-19)
- **Server impl**: Python [`mcp`](https://pypi.org/project/mcp/) package, `FastMCP` high-level decorator API
- **Transport**: `stdio` — host agent spawns the server as a subprocess, exchanging JSON-RPC over stdin/stdout
- **Python version**: 3.13 (from python.org installer, not conda)
- **Dependency management**: `requirements.txt` + project-local `.venv`

Why stdio over HTTP+SSE transport? stdio is the MCP spec's first choice, and gives three benefits:

1. **No listening port**: even if the host machine runs other services, this server doesn't open a port or expose itself to external scans. Attack surface = 0
2. **Lifecycle bound to host**: when the host agent exits, the server subprocess terminates automatically. No zombies
3. **No auth burden**: since the host spawns the subprocess, the host is the trust boundary. No need for API keys

HTTP+SSE transport is recommended only for "server and host on different machines". Laiguanjia Skill runs fully on the user's local machine; no cross-machine requirement; stdio is the clear winner.

## 1.3 Six-tool interface

Full Input/Output schemas live in [`mcp-spec.md`](../../mcp-spec.md) (429 lines). Summary:

| # | Tool | Verb | Reads user PII? | External I/O? | `ToolAnnotations` |
|---|---|---|---|---|---|
| 1 | `get_pricing` | lookup | No | No | readOnly ✅ destructive ❌ idempotent ✅ openWorld ❌ |
| 2 | `get_faq` | lookup | No | No | readOnly ✅ destructive ❌ idempotent ✅ openWorld ❌ |
| 3 | `check_plan_suitability` | compute | No (input = `industry` + `friend_count`, no PII) | No | readOnly ✅ destructive ❌ idempotent ✅ openWorld ❌ |
| 4 | `get_feature_detail` | lookup-with-pointer | No | No | readOnly ✅ destructive ❌ idempotent ✅ openWorld ❌ |
| 5 | `get_contact_and_trial` | lookup | No | No | readOnly ✅ destructive ❌ idempotent ✅ openWorld ❌ |
| 6 | `initiate_trial_contact` | plan-with-consent | No (`user_consent` is a bool, not PII) | **No** (plan-only; host agent sends anything if needed) | readOnly ✅ destructive ❌ idempotent ✅ openWorld ❌ |

**Three takeaways**:

1. **No tool reads user PII** (no name, phone, email, LINE ID, address)
2. **No tool produces external I/O** (no HTTP, no file write, no DB write, no message send — all delegated to host)
3. **Every tool is `destructiveHint=False`** (no delete, overwrite, or charge side effects)

Sample `server.py` implementation (tool 6 shown; other five share the same annotation shape):

```python
@mcp.tool(
    annotations=ToolAnnotations(
        title="Start trial — only suggest host agent open link after explicit user consent",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
)
def initiate_trial_contact(user_consent: bool = False) -> dict:
    # Consent gate first-check — detailed in Chapter 03
    if not isinstance(user_consent, bool) or user_consent is not True:
        return {"error": "consent_required", ...}
    ...
```

Per MCP spec, `ToolAnnotations` tells the host agent:

- `readOnlyHint=True`: tool doesn't modify external state → host may safely retry and call concurrently
- `destructiveHint=False`: side effects are reversible (in our case, there are no side effects, a stronger guarantee)
- `idempotentHint=True`: same inputs produce the same output → host may retry safely
- `openWorldHint=False`: tool does not interact with the outside world (no network, no fs writes) → host needs no "allow external access" prompt

Security reviewers can treat this table as "the claimed side effect surface"; independent verification is covered in [04 Dual-layer diff validation](./04-dual-layer-validation.en.md).

## 1.4 Startup and call flow (end-to-end)

Here's the full path from user asking "How much is Laiguanjia monthly?" in Cowork mode to receiving an answer:

```
┌──────────┐   ① spawn server subprocess    ┌──────────────────┐
│ Host      │ ─────────────────────────────> │ laiguanjia-skill │
│ Agent     │         (stdio pipe)           │  MCP server     │
│ (Cowork)  │                                │  (Python 3.13)  │
└──────────┘                                └──────────────────┘
     │                                              │
     │ ② "initialize" JSON-RPC                      │
     ├─────────────────────────────────────────────>│
     │                                              │
     │           ③ capabilities returned            │
     │<─────────────────────────────────────────────┤
     │                                              │
     │ ④ "tools/list"                               │
     ├─────────────────────────────────────────────>│
     │                                              │
     │        ⑤ schemas for 6 tools returned        │
     │<─────────────────────────────────────────────┤
     │                                              │
     │ [User message: "How much is Laiguanjia?"]    │
     │                                              │
     │ ⑥ LLM decides to call `get_pricing`          │
     │   via "tools/call"                            │
     ├─────────────────────────────────────────────>│
     │                                              │
     │             ⑦ Python handler runs            │
     │            (reads data/pricing.json,         │
     │             builds payload)                  │
     │                                              │
     │            ⑧ pricing payload returned        │
     │<─────────────────────────────────────────────┤
     │                                              │
     │ ⑨ LLM turns payload into natural language    │
     │                                              │
     └─> User sees "Laiguanjia starts at NT$490..."
```

**Key facts**:

- **Step ⑦'s Python handler does not hit the network**. Data is read from local `data/*.json`
- **Step ⑧'s payload is structured JSON**, not natural language. Natural language is generated only at step ⑨ by the LLM from the payload. The LLM-to-payload relationship is traceable (host records tool calls)
- **Manual content is not returned directly in step ⑧**. `get_feature_detail` returns a pointer to `docs/case-studies/XX-xxx.md`, which the host `Read`s on demand. This is "lazy loading" to avoid the 12 MB manual blowing up context; see [02](./02-data-layer-separation.en.md)

## 1.5 Attack surface (security view)

Under MCP + stdio, the Skill's attack surface looks like:

| Attack surface | Risk | Mitigation |
|---|---|---|
| **RCE via MCP** | None | stdio transport does not listen on a port; no remote reach |
| **Privilege escalation via MCP** | None | Server runs with host agent's user permissions; does not request elevation |
| **Data exfiltration via MCP** | Very low | Server does not hit network. If the host itself is compromised, that's a host problem, not a Skill problem |
| **Supply chain (PyPI)** | Low | Deps: `mcp` (official) + `pydantic` (built into MCP). `requirements.txt` pins versions; CI can run `pip-audit` |
| **Prompt injection via `data/*.json`** | Medium | Data is version-controlled; attacker needs a PR to change it; see Chapter 02 "data boundary" |
| **LLM hallucinating tool calls with malicious args** | Low (medium for `initiate_trial_contact`) | All tools use Pydantic type validation; the sole sensitive tool has consent gate + bool-is-int guard; see [03](./03-consent-gate-pattern.en.md) |

Each row is revisited with concrete implementation details in subsequent chapters.

## 1.6 Portability & lock-in risk

- **MCP spec is open** (Anthropic-led but not Claude-dependent). Any MCP-capable host (Claude Desktop, Cowork, Cursor, Continue) can load this Skill
- **No Claude-only MCP extensions are used** (neither `resources/read` nor `prompts/get` — only core `tools/call`)
- **Data format is JSON** — not bound to any DB or service
- **LLM vendor migration cost**: 0 (Skill is vendor-independent)

## 1.7 Chapter recap

1. Skill is **MCP server + Claude Skill dual-distributed**, using stdio to expose 6 tools
2. **All 6 tools are readOnly / non-destructive / idempotent / closed-world**, collect no PII, do no network I/O
3. **MCP-layer attack surface is minimal**; main risks are host-side compromise and `data/*.json` supply chain — the former is out of Skill control; the latter is mitigated by version control
4. **Next (02)**: how "data / routing / I/O" separation further reduces risk
