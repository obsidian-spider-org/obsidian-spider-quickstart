---
title: "Cost model — measure your own savings"
date: 2026-05-11
confidence: "7/8 (no quorum certificate)"
---

# Cost model

This document shows the math behind the "100× to 1000× cheaper than raw API" range you'll see referenced in the README and HN post. Every $-figure is cited with a URL and date-stamped. Every assumption is shown as a variable you can change. Plug in your own numbers and check.

## Headline

- Verified range under reasonable assumptions: **~100×–1000× cheaper than the same work done as raw API calls**, depending on which frontier model you'd otherwise pay for and how heavy your tool-call loops run.
- I land at ~425× on my normal workflow (40 GPT-5.5-class subagents on one Copilot Pro+ parent call) and ~961× on heavy-Opus 11×8 max-burn days. The 100× floor is what you'd see if you compared against GPT-5 across-the-board, which is itself an unusual choice.
- The cost-aware routing swarm pattern also works on free vendor mesh (OpenRouter / Groq / Together / Cerebras) and on Claude Code's Agent tool. The Copilot-specific savings multiplier is the largest right now; the routing pattern is portable.

## What this is and isn't

This is **not** a billing bypass. The parent call against a premium model (Copilot Pro+ GPT-5.5 in my case) is charged in full: 7.5 premium requests × $0.04 overage = $0.30 per parent call, debited against my paid plan.

What this **is**: paying for premium, then using the subagent fan-out feature Copilot advertised to maximize what one paid premium request does. The savings multiplier below compares my paid-parent-call cost against doing the same work as 40 separate raw-API calls — not against any free or unbilled call on Copilot's side.

The bug report at [microsoft/vscode#292452](https://github.com/microsoft/vscode/issues/292452) describes free-model-parent calling premium-model-subagents, which is a different pattern from this workflow. This workflow uses a premium parent calling a mix of paid and free subagents.

The June 1 billing transition will change the multiplier math; it does not change the legitimacy of the pattern. Multi-tier cost-aware routing works on Copilot, on free vendor mesh, on Claude Code, and on anywhere a parent agent can launch subagents.

## Pricing inputs (as of 2026-05-11)

### Raw API list prices

| Model | Input $/Mtok | Output $/Mtok | Source |
|---|---|---|---|
| GPT-5 | $1.25 | $10.00 | [artificialanalysis.ai/models/gpt-5](https://artificialanalysis.ai/models/gpt-5) |
| GPT-5.5 (xhigh) | $5.00 | $30.00 | [artificialanalysis.ai/models/gpt-5-5](https://artificialanalysis.ai/models/gpt-5-5) |
| Claude Sonnet 4.6 | $3.00 | $15.00 | [claude.com/platform/api](https://claude.com/platform/api) |
| Claude Opus 4.7 | $5.00 | $25.00 | [claude.com/platform/api](https://claude.com/platform/api) |

Note: prompt caching reduces these materially (Claude cached reads $0.30/Mtok Sonnet / $0.50/Mtok Opus; OpenAI cached input $0.125/Mtok GPT-5 / $0.50/Mtok GPT-5.5). The calculator below treats input as uncached to keep the comparison conservative.

### GitHub Copilot Pro+ — what one parent call actually costs

| Item | Value | Source |
|---|---|---|
| Pro+ monthly fee | $39 / user / month | [github.com/features/copilot/plans](https://github.com/features/copilot/plans) |
| Included premium requests | 1,500 / month | same |
| Overage rate | $0.04 / additional premium request | same |
| GPT-5.5 multiplier | 7.5× | [docs.github.com/.../copilot-requests](https://docs.github.com/en/copilot/concepts/billing/copilot-requests) |
| Claude Opus 4.7 multiplier | 15× | same |
| Claude Sonnet 4.6 multiplier | 1× | same |
| GPT-5 mini / GPT-4o / GPT-4.1 multiplier | 0× (included; no premium consumption on paid plans) | same |

One parent call on GPT-5.5 = 7.5 premium requests = $0.30 of overage budget. For Opus 4.7 (15×) the per-parent-call cost is $0.60; for Sonnet 4.6 (1×) it is $0.04.

GitHub [announced usage-based Copilot billing effective 2026-06-01](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/). The current pricing window is closing — measure your own savings before the transition.

## Work envelope per parent call

| Variable | Default | Notes |
|---|---|---|
| Parent input tokens | 200,000 | maxes prompt + context rehydration |
| Parent output tokens | 50,000 | conservative default |
| Subagents per parent | 40 | typical workflow on Pro+ |
| Tool calls per subagent | 25 | midpoint of 10–40 range |
| Tokens per tool-call loop iteration | 5,000 | tool I/O round-trips + observation re-context |
| Subagent input tokens | 200,000 | subagents inherit parent context |
| Subagent output tokens | 50,000 | conservative default |

Derived totals for one parent-call's worth of work (normal workflow):
- Total input tokens = `200k + (40 × 200k) + (40 × 25 × 5k)` = **13.2M**
- Total output tokens = `50k + (40 × 50k)` = **2.05M**

## Raw API cost across scenarios

| Scenario | Input cost | Output cost | Total raw API cost |
|---|---|---|---|
| All GPT-5 ($1.25/$10) | $16.50 | $20.50 | **$37.00** |
| All Sonnet 4.6 ($3/$15) | $39.60 | $30.75 | **$70.35** |
| All Opus 4.7 ($5/$25) | $66.00 | $51.25 | **$117.25** |
| All GPT-5.5 xhigh ($5/$30) | $66.00 | $61.50 | **$127.50** |

Heavy-Opus 11×8 max-burn case (88 subagents, 40 tool calls each):
- Total input = `200k + 88×200k + 88×40×5k` = **35.4M**
- Total output = `50k + 88×50k` = **4.45M**
- Opus raw = `35.4 × $5 + 4.45 × $25` = **$288.25**

## The ratio

Parent-call cost on Copilot Pro+ at 7.5× multiplier × $0.04 = $0.30.

| Scenario | Raw API cost | Operator cost | Savings multiplier |
|---|---|---|---|
| All GPT-5 (cheapest current frontier) | $37.00 | $0.30 | **~123×** |
| All Sonnet 4.6 | $70.35 | $0.30 | **~234×** |
| All Opus 4.7 (40 subagents) | $117.25 | $0.30 | **~391×** |
| All GPT-5.5 xhigh | $127.50 | $0.30 | **~425×** |
| Heavy-Opus 11×8 max-burn (88 subagents) | $288.25 | $0.30 | **~961×** |

Range across plausible scenarios: **~123×–961×**. Public-facing language uses **"100× to 1000× depending on which frontier model you'd otherwise pay for"** — honest at both ends.

## Multi-tier mix — the real workflow (Copilot is one angle)

Most real workflows don't run all-Opus or all-GPT-5. They mix tiers: cheap models for cheap work (extracting names, summarizing one paragraph, generating one variant), frontier only for the synthesis pass that needs reasoning across the whole gather.

Example mix (the 4×4 default, 32 cheap subagents + 8 frontier synthesis):

```
Parent (Opus 4.7):     200k × $5/M  + 50k × $25/M               = $2.25
32 × Sonnet 4.6:       32 × (325k × $3/M + 50k × $15/M)         = $55.20
8  × Opus 4.7:         8  × (325k × $5/M + 50k × $25/M)         = $23.00
                                                                  ──────────
                                                                    $80.45
```

| Scenario | Raw API | Operator cost | Ratio | Notes |
|---|---|---|---|---|
| All Opus 4.7 (40 subagents) | $117.25 | $0.30 | ~391× | every subagent runs frontier; expensive |
| **Multi-tier mix** (32 Sonnet + 8 Opus + 1 Opus parent) | **$80.45** | $0.30 | **~268×** | mix saves ~32% on raw vs all-Opus |
| Multi-tier mix on free vendor mesh (32 free + 8 Sonnet synth + 1 Opus parent) | ~$16 | ~$0 (rate-limited) | undefined | cheap tier costs nothing; only synthesis is paid |

**Two things matter here**:

1. **The multi-tier mix saves ~32% on raw API regardless of harness.** Whether you run on raw API, Copilot, or Claude Code, mixing tiers is cheaper than all-frontier. The Copilot per-parent-call billing model is one specific cost-aware routing path layered on top — not the whole story.

2. **On free vendor mesh** (OpenRouter free-tier / Groq free / Together free), the 32 cheap subagents run at $0. Only the synthesis layer costs anything. The savings ratio against raw all-frontier API approaches infinite as your free-tier quota holds.

The 100×–1000× headline includes Copilot's per-parent-call billing model. The ~32% mix-saving is what holds **before any vendor-specific savings on top**.

## Measure your own savings

You don't have to believe these numbers. Plug in yours and check.

```
Variables (defaults reflect my actual workflow on Copilot Pro+ with ~40
GPT-5.5-class subagents per parent call; replace any with your numbers):

  INPUT_TOKENS_PER_SUBAGENT   = 200,000   (I max prompt + context rehydration)
  OUTPUT_TOKENS_PER_SUBAGENT  = 50,000
  SUBAGENTS_PER_PARENT        = 40
  TOOL_CALLS_PER_SUBAGENT     = 25        (midpoint of my 10–40 range)
  TOKENS_PER_TOOL_CALL_LOOP   = 5,000     (input re-context per tool round-trip)
  INPUT_PRICE_PER_MTOK_USD    = 5.00      (Claude Opus 4.7 or GPT-5.5)
  OUTPUT_PRICE_PER_MTOK_USD   = 25.00     (Claude Opus 4.7; use 30.00 for GPT-5.5)
  YOUR_PARENT_CALL_COST_USD   = 0.30      (Copilot Pro+ GPT-5.5: 7.5 × $0.04;
                                           Claude Code on a Max plan: depends;
                                           free-tier vendor mesh: ~$0)

Raw API cost of one parent-call's worth of work:

  total_input_tokens =
      INPUT_TOKENS_PER_SUBAGENT * SUBAGENTS_PER_PARENT
    + TOKENS_PER_TOOL_CALL_LOOP * TOOL_CALLS_PER_SUBAGENT * SUBAGENTS_PER_PARENT
    + 200_000

  total_output_tokens =
      OUTPUT_TOKENS_PER_SUBAGENT * SUBAGENTS_PER_PARENT
    + 50_000

  raw_api_cost_usd =
      (total_input_tokens  / 1_000_000) * INPUT_PRICE_PER_MTOK_USD
    + (total_output_tokens / 1_000_000) * OUTPUT_PRICE_PER_MTOK_USD

Cost ratio (the savings multiplier):

  savings_multiplier = raw_api_cost_usd / YOUR_PARENT_CALL_COST_USD
```

That last line is the whole point: pick a model, plug in your real numbers, divide. If the ratio is much smaller than mine, you're either running a cheaper alternative model or you have less fan-out than I do. If it's larger, you're running heavier tool loops than I am or using a more expensive comparison baseline.

## Worked examples

**Example 1 — normal workflow (40 subagents on GPT-5.5 via Copilot Pro+):**
- total_input = `200k × 40 + 5k × 25 × 40 + 200k` = 13.2M
- total_output = `50k × 40 + 50k` = 2.05M
- raw_api_cost = `(13.2 × $5) + (2.05 × $30)` = **$127.50**
- savings_multiplier = `$127.50 / $0.30` = **~425×**

**Example 2 — same fan-out priced against Claude Opus 4.7 raw API:**
- raw_api_cost = `(13.2 × $5) + (2.05 × $25)` = **$117.25**
- savings_multiplier = `$117.25 / $0.30` = **~391×**

**Example 3 — 11×8 all-frontier max-burn day, priced against Opus raw:**
- total_input = `200k × 88 + 5k × 40 × 88 + 200k` = 35.4M
- total_output = `50k × 88 + 50k` = 4.45M
- raw_api_cost = `(35.4 × $5) + (4.45 × $25)` = **$288.25**
- savings_multiplier = `$288.25 / $0.30` = **~961×**

**Example 4 — pessimistic floor (40 subagents priced against GPT-5 everywhere):**
- raw_api_cost = `(13.2 × $1.25) + (2.05 × $10)` = **$37**
- savings_multiplier = `$37 / $0.30` = **~123×**

The four examples bracket the public-facing range. "100× to 1000× depending on what you'd otherwise be running" is the honest framing.

## What this doc does NOT establish

- **Token-counting defaults are estimates.** The "5,000 tokens per tool-call loop" and "50,000 tokens output per subagent" are conservative defaults, not measured. A reader who logs actual token usage will get a sharper ratio.
- **Copilot policy is unilateral.** The 2026-06-01 billing transition is publicly announced; specifics of in-message subagent behavior may change at that point. The free-vendor-mesh path and Claude Code path stay open with smaller multipliers.
- **The $0.30 figure assumes overage.** If you stay inside the 1,500/month allowance, your incremental per-parent-call cost is closer to $0 (amortized into the $39 fee). The "$0.30" treats every parent call as if it spent overage, which is conservative.
- **Pricing pages move.** All URLs in this doc were fetched on 2026-05-11. OpenAI's marketing page returned 403 for unauthenticated fetch; GPT-5 / GPT-5.5 numbers come from `artificialanalysis.ai`, a third-party mirror. Cross-check on `platform.openai.com` once signed in.

## Words to avoid when citing this

- "1000× cheaper" as a bald claim. Always pair with the range and the "depends on what you'd otherwise be running" hedge.
- "Free" without "current policy, not a guarantee" right next to it.
- "Saves you $X" as an absolute. The number is a ratio against a hypothetical raw-API baseline; if you were never going to pay for raw API, you aren't "saving" anything.

---

*Pair this doc with `CAPACITY_LADDER.md` (the technical upgrade map) and `GIFT_AND_OFFER.md` (the framing).*
