---
title: Laiguanjia Skill — Technical Whitepaper Index (English)
type: index
last_updated: 2026-04-19
audience: External technical reviewers (Security / Legal / AI ethics)
source:
  - server.py
  - mcp-spec.md
  - data/feature-routes.json
  - data/pricing.json
  - data/faq.json
  - tests/*.py
  - memory/decisions/2026-04-17-laiguanjia-X+Z-strategy.md
category: whitepaper
feature: all
language: en
counterpart: ./README.md
---

# Laiguanjia Skill — Technical Whitepaper Index

## Who this is for

This whitepaper is written for **technical reviewers who are not going to install or use the Skill themselves** but need to judge "is this Skill safe to be used by our employees or customers?" Typical readers:

- **Security contact**: concerned about MCP server attack surface, data exfiltration, LLM-hallucination-triggered unintended actions
- **Legal contact**: concerned about Taiwan Personal Data Protection Act, Consumer Protection Act, Medical Advertisement Regulations compliance (e.g. clinic case)
- **AI governance / risk contact**: concerned about "is user consent truly informed?", "can the AI take any action on its own?", "is there an audit trail?"

If you are a business owner looking to **use** Laiguanjia for booking / push notifications / loyalty programs, this document is not for you. Please visit the [official site](https://lineoa.batmobile.com.tw/) or the [free trial entry](https://line.batmobile.com.tw/) instead.

## Four-chapter architecture

The whitepaper is split into one index + four sub-chapters. Each chapter is self-contained with explicit cross-references:

| # | Filename | Topic | Recommended reader |
|---|---|---|---|
| 01 | [01-mcp-architecture.en.md](./01-mcp-architecture.en.md) | MCP architecture overview: FastMCP, stdio transport, six read-only tools | All three reader types |
| 02 | [02-data-layer-separation.en.md](./02-data-layer-separation.en.md) | Data + routing + I/O three-segment separation: why `get_feature_detail` only returns metadata | Security, AI governance |
| 03 | [03-consent-gate-pattern.en.md](./03-consent-gate-pattern.en.md) | Consent Gate + bool-is-int guard: anti-hallucination / anti-abuse design in `initiate_trial_contact` | Security, Legal, AI governance |
| 04 | [04-dual-layer-validation.en.md](./04-dual-layer-validation.en.md) | Dual-layer diff validation workflow: VM Python × Mac MCP Inspector with triple-branch bonus | Security (validation completeness), AI governance |

Traditional Chinese counterparts live next to each English file (e.g. `README.md`, `01-mcp-architecture.md`). Content is 1:1 but not word-for-word. **The Traditional Chinese version is the canonical source**; when ambiguity arises, defer to the zh-TW version.

## One-page TL;DR

Laiguanjia Skill is the LLM-agent layer of **Laiguanjia (賴管家) — a LINE Official Account management tool for independent professionals and small businesses** in Taiwan. It exposes **six read-only tools** via [Model Context Protocol (MCP)](https://modelcontextprotocol.io) to any MCP-capable host agent (Claude Desktop, Cowork mode, Claude Code, etc.), helping that agent answer questions like "Is this business a good fit for Laiguanjia? Which plan? How much? How does feature X work?"

Three design choices form the trust foundation:

1. **Three-segment separation** (see [02](./02-data-layer-separation.en.md)): data lives in JSON, logic lives in Python handlers, and I/O (network calls, message sending) is fully delegated to the host agent. The MCP server itself does not call the network, does not invoke any external API, and does not push any message.
2. **Consent gate first + bool-is-int guard** (see [03](./03-consent-gate-pattern.en.md)): the only tool that produces a "suggest host agent to send a message" payload, `initiate_trial_contact`, uses a **first-check** to reject calls without explicit user consent. `user_consent=1` (Python `bool is int`) is also rejected, preventing LLMs or attackers from bypassing with truthy values.
3. **Dual-layer diff validation** (see [04](./04-dual-layer-validation.en.md)): every tool is validated two ways before release — VM Python-side canonical JSON diff (byte-level) + Mac-side MCP Inspector UI spot check (catches JSON-RPC-layer issues). Only their intersection passes.

Six-tool interface (full schema in [mcp-spec.md](../../mcp-spec.md)):

| Tool | Verb | Most expensive side effect |
|---|---|---|
| `get_pricing` | GET | None |
| `get_faq` | GET | None |
| `check_plan_suitability` | GET (compute) | None |
| `get_feature_detail` | GET | None (returns metadata + `case_study_file`/`blog_slug` pointers for host to `Read` or fetch) |
| `get_contact_and_trial` | GET | None |
| `initiate_trial_contact` | GET (plan) | **Returns a payload instructing host agent to ask the user "want to open LINE?"**, but the MCP server itself opens no link and sends no message. Functionally identical to [public contact info in pricing.json](../../data/pricing.json); the difference is the consent gate + audit metadata |

**No tool is destructive** (no data deletion, no payment charge, no overwrite of business settings). This is declared via `ToolAnnotations(destructiveHint=False)` on every tool, see [01](./01-mcp-architecture.en.md) §3.

## Mapping to ADRs

Each whitepaper chapter has a corresponding ADR (Architecture Decision Record). ADRs record "what options were evaluated at decision time and why one was chosen over another"; the whitepaper explains "what the final decision looks like in code". The two complement each other:

| Whitepaper chapter | Corresponding ADR |
|---|---|
| 01-mcp-architecture | [2026-04-17-laiguanjia-X+Z-strategy.md](../../../memory/decisions/2026-04-17-laiguanjia-X+Z-strategy.md) (upstream decision to build a Skill) |
| 02-data-layer-separation | [2026-04-19-laiguanjia-three-segment-separation.md](../../../memory/decisions/2026-04-19-laiguanjia-three-segment-separation.md) |
| 03-consent-gate-pattern | [2026-04-19-laiguanjia-consent-gate-pattern.md](../../../memory/decisions/2026-04-19-laiguanjia-consent-gate-pattern.md) |
| 04-dual-layer-validation | [2026-04-19-laiguanjia-dual-layer-validation.md](../../../memory/decisions/2026-04-19-laiguanjia-dual-layer-validation.md) |

## Out of scope

The following are **not covered** in this whitepaper. Reviewers who need these can request them separately:

- **Laiguanjia product backend** (LINE OA Messaging API integration, push scheduler, business dashboard) — this Skill is an **external agent layer** and does not touch product backend
- **LINE OA personal data compliance details** (LINE platform ToS, implementation of Taiwan PDPA on LINE OA) — that's between LINE Corp and the Laiguanjia product
- **Real customer identities in case studies** (the six persona profiles are all from [public blog](https://lineoa.batmobile.com.tw/blogs/) content, not actual PII)
- **Badge system (P1.5), demo video (P1.6)** — later Z-track phases; this whitepaper only covers Skill core technicals

## Version & maintenance

- **This version**: 2026-04-19 P1.3b initial
- **Maintainer**: Charlie Chien ([charlie.chien@gmail.com](mailto:charlie.chien@gmail.com))
- **Repo**: [github.com/dvdmaru/laiguanjia-skill](https://github.com/dvdmaru/laiguanjia-skill)
- **License**: Skill source code is MIT-licensed. Data (`data/*.json` containing official pricing and FAQ) belongs to Laiguanjia / Batmobile; Skill users must route users to the official channel via `get_contact_and_trial`, and may not resell or misleadingly quote the data
- **Update trigger**: when `server.py`, `data/*.json`, or `mcp-spec.md` changes, the corresponding chapter must be updated in the same commit. When the change affects three-segment separation / consent flow / validation method **design**, a new ADR must also be added

## Suggested reading order

- **Security**: 01 → 02 → 03 → 04 (progressively deeper; each chapter has a security-focused subsection)
- **Legal**: 01 (skip FastMCP internals) → 03 (focus: Consent Gate, PDPA, Medical Advertisement Regulations) → 02 (data boundaries)
- **AI governance / risk**: 03 (is consent truly informed?) → 04 (is validation independently reproducible?) → 02 → 01

## How to raise questions

During review, please open an issue on the [Issues page](https://github.com/dvdmaru/laiguanjia-skill/issues) tagged `whitepaper-review`. I commit to a first response **within 2 business days**. For sensitive content (e.g. concerns that disclose specific customer data), email charlie.chien@gmail.com with the same response commitment.
