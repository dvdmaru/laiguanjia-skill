---
title: 04 Dual-Layer Diff Validation Workflow
type: whitepaper-chapter
chapter: 04
last_updated: 2026-04-19
audience: External technical reviewers (Security / AI governance)
source:
  - server.py
  - tests/test_day4.py
  - tests/test_day6_consent_gate.py
  - tests/test_all_tools_smoke.py
category: whitepaper
language: en
counterpart: ./04-dual-layer-validation.md
related_adr: ../../../memory/decisions/2026-04-19-laiguanjia-dual-layer-validation.md
---

# 04. Dual-Layer Diff Validation Workflow

## 4.1 Why single-layer validation isn't enough

Common MCP server testing approaches:

- **Type A: Python unit tests only**. Pros: fast, automated, CI-friendly. Cons: **does not catch the MCP protocol layer** (JSON-RPC format, stdio framing, tool schema serialization). Code logic correct, but MCP client might receive malformed JSON
- **Type B: MCP Inspector only (official UI)**. Pros: shows what host will actually receive. Cons: manual, not CI-friendly, prone to drift (you clicked yesterday, edited code today, forgot to re-click)

The Skill uses **Dual-Layer Diff Validation** to cover both gaps. The core idea:

> Produce a "canonical JSON" at the Python layer; spot-check the same payloads in MCP Inspector; **byte-level** compare.
> If either layer deviates from baseline, it fails.

## 4.2 Layer 1: VM Python JSON Canonical Diff

**Flow**:

1. Define a set of **fixture params** (six groups, one per tool)
2. Call the six handlers directly in Python, dump returns to canonical JSON:
   ```python
   json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2)
   ```
3. Byte-level `==` compare against **golden files** in `tests/fixtures/golden/*.json`

**Key parameters**:

- `sort_keys=True`: key ordering — avoids false diffs from Python dict insertion order changes
- `ensure_ascii=False`: keeps Chinese characters as-is rather than `\uXXXX` — easier human review
- `indent=2`: fixed indentation — readable in git diff

**Golden file update rules**:

- Golden files can only be updated via **human-reviewed PR**. Rule: any change to `tests/fixtures/golden/*.json` must include a "why" in the PR description
- If official pricing change warrants an update, the PR updates both `data/pricing.json` and golden files together — reviewer only merges when they're synchronized
- If someone changes **only the golden file without touching `data/*.json`**, that's an attempt to bypass validation and will be blocked at PR review

**Local run (VM)**:

```bash
cd /sessions/.../laiguanjia-skill
.venv/bin/python -m pytest tests/test_all_tools_smoke.py -v
```

CI can run the same on GitHub Actions. The repo has no GitHub Actions yet (CI workflow will be added in P2, post-P1.3b).

## 4.3 Layer 2: Mac MCP Inspector Spot Check

**What is MCP Inspector**: Anthropic's official MCP server debugger (`npx @modelcontextprotocol/inspector`), a browser UI that talks to a local MCP server and displays the full JSON-RPC message stream.

**Why this layer is needed**:

- Python handler returning the right dict is easy to verify, but dict → JSON-RPC response serialization is the MCP SDK's job. If the SDK has a bug (some field name auto-camelCased, some Unicode boundary escape mishandled), Python unit tests won't catch it
- Inspector shows exactly what the host agent will receive — the validation point closest to real-world conditions

**Spot-check flow**:

1. On Mac terminal: `npx @modelcontextprotocol/inspector python3 server.py`
2. Inspector opens browser UI; Charlie manually clicks each of the six tools with **identical** fixture params
3. Compare Inspector's JSON-RPC response against Layer 1 golden files
4. Identical → pass; any diff → record diff type and diagnose (MCP SDK / Python handler / golden file)

**Why spot check instead of full coverage**: six tools × one call covers the serialization path sufficiently; full coverage lives in Layer 1 (automated). This layer only catches what automation misses.

## 4.4 Triple-Branch Bonus Methodology

`check_plan_suitability`'s `friend_count` input decides three branches (`starter / pro / enterprise`). Its golden files have **three** — one per branch — and fixture params straddle boundaries:

| Fixture | `friend_count` | Expected branch |
|---|---|---|
| A | 0 | starter |
| B | 200 | starter (on boundary) |
| C | 201 | pro |
| D | 2000 | pro (on boundary) |
| E | 2001 | enterprise |

These five cases cover all branches plus two boundaries — "**branch coverage + boundary value analysis mix**". Python unit tests run all five; Layer 2 Inspector spot-checks only A/C/E (three branches, no duplicate boundary runs). That's the "triple-branch bonus" naming.

**Generalization**: any branching tool (e.g. `get_faq` by category) uses the same pattern. Branch-less tools (`get_pricing` with no params) use one fixture at Layer 1 and one matching run at Layer 2.

## 4.5 Coverage table

As of 2026-04-19 (post-P1.3a):

| Tool | Branches | Layer 1 fixtures | Layer 2 spot-check |
|---|---|---|---|
| `get_pricing` | 1 | 1 | 1 |
| `get_faq` | 8 (category) | 8 | 3 (popular categories) |
| `check_plan_suitability` | 3 | 5 (with boundaries) | 3 |
| `get_feature_detail` | 3 (feature) | 3 | 3 |
| `get_contact_and_trial` | 1 | 1 | 1 |
| `initiate_trial_contact` | 2 (consent True/False branches) + 6 guard cases | 8 | 2 (True/False) + 1 (bool-is-int `1`) |
| **Total** | — | **26** | **13** |

**Note**: the consent gate + bool-is-int guard is verified by **both Python unit tests and Inspector**. Unit tests cover 8 input variants (True/False/1/0/"true"/"yes"/None/omitted); Inspector runs 3 high-signal cases to ensure protocol-layer no drift.

## 4.6 Consent Gate dedicated tests

Additional checks for `initiate_trial_contact`:

```python
# tests/test_day6_consent_gate.py excerpt
def test_consent_gate_blocks_integer_one():
    result = initiate_trial_contact(user_consent=1)
    assert result.get("error") == "consent_required", (
        f"bool-is-int guard FAILED: user_consent=1 should not pass the consent gate; got {result}"
    )

def test_consent_gate_blocks_string_true():
    result = initiate_trial_contact(user_consent="true")
    assert result.get("error") == "consent_required"

def test_consent_gate_passes_real_true():
    result = initiate_trial_contact(user_consent=True)
    assert result.get("action") == "suggest_open_line"
    assert result["trial_url"].startswith("https://line.batmobile.com.tw/")
```

The assertion message deliberately says "**FAILED**", not just "failure" — reminding reviewers this is a security boundary, not a feature test.

## 4.7 Regression barrier

After any `server.py` or `data/*.json` change:

1. Charlie runs Layer 1 pytest in VM → **must be green**
2. If Layer 1 passes, run Mac MCP Inspector spot check
3. Commit only if both layers pass
4. Commit message includes `[dual-validated]` tag

**Historical validation events (high value)**:

- **P0 first integration validation (2026-04-12)**: discovered `get_faq`'s `answer` field appeared double-escaped in Inspector (`\\n` → `\\\\n`) while Python unit tests were all green. Root cause: a fixture used raw string `r"..."` — stored literal `\\n`, not newline. Fixed → both layers pass
- **P1 Day 4 six-tool validation (2026-04-18)**: first complete dual-layer run; Python 3 seconds, Inspector ~6 minutes manual
- **P1.3a case study correction (2026-04-19)**: `feature-routes.json` `case_studies` array corrected from erroneous 8 to correct 6 items; golden files synced; dual-layer validation passed; commit `2d94a53`

## 4.8 Independent reproducibility

External reviewers may reproduce validation themselves:

### Prereqs
```bash
# Mac, preferably python.org 3.13 installer
# (miniconda's symlink binding breaks venvs when base Python breaks;
#  python.org installer venvs are Mach-O universal binary, independent copies)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Layer 1
```bash
.venv/bin/python -m pytest tests/ -v
```
Expected: **26 passed** in ~3 seconds

### Layer 2
```bash
npx @modelcontextprotocol/inspector .venv/bin/python server.py
```
After Inspector opens:
1. On the Tools tab, click each of the six tools
2. Manually fill fixture params (refer to `tests/fixtures/`)
3. Compare responses against `tests/fixtures/golden/*.json`

**If Layer 1 and Layer 2 disagree**: almost certainly an MCP SDK serialization issue (we've hit this 3 times — 2 escape issues, 1 Unicode normalization). Issues and PRs are enthusiastically welcomed.

## 4.9 Why no property-based / fuzz testing

Reviewers may ask: why not Hypothesis or AFL? Three pragmatic reasons:

1. **MCP server input domain is narrow**: six tools, <10 input fields total, mostly enums (`industry` limited to 6 strings) or small integers (`friend_count` 0–10,000 range). Branch coverage + boundary values exhaust it
2. **External world dependency = 0**: no fs write, no network, no DB. Fuzzing typically finds "weird interactions between input and external world"; Skill has no external world — low fuzz ROI
3. **Return on investment**: Charlie is solo developer; time is better spent on the 8 consent-gate cases + 3 branch boundaries than Hypothesis. Future tool set expansion (especially write actions) will re-evaluate

This tradeoff is recorded in [ADR: 2026-04-19-laiguanjia-dual-layer-validation.md](../../../memory/decisions/2026-04-19-laiguanjia-dual-layer-validation.md).

## 4.10 Chapter recap

1. **Dual layer = Python-side JSON canonical diff + Mac-side MCP Inspector spot check**; both must pass
2. **`json.dumps(sort_keys=True, ensure_ascii=False)`** is the technical foundation of canonical form
3. **Triple-branch bonus** = branch coverage + boundary value analysis mix; fewest fixtures, maximum surface
4. **Consent gate 8 cases + Inspector 3 cases** together cover both functionality and protocol layers
5. **Independent reproducibility**: external reviewers can fully re-run via pytest + MCP Inspector on Mac
6. **End of whitepaper**. Return to [index](./README.en.md) to read other chapters
