---
title: "HN first-comment reply (pasted within 5 min of submission)"
date: 2026-05-11
launch_slot: 2026-05-12T14:00Z (Tuesday HN peak per wave-1 timing research)
confidence: "7/8 (no quorum certificate)"
---

# First-comment reply

*Pasted by the author within 5 min of submission. Plain-prose; no LLM polish.*

---

Hey, author here. I'm TTao (Obsidian_Spider is the org name on GitHub).

Quick context: the scatter-gather pattern is a small clean piece lifted out of a bigger personal workflow. The bigger version isn't for sale and isn't in the repo. This part stands on its own, so I figured I'd hand it out before GitHub's June 1 billing transition lands.

### Measure your own cost savings

Don't trust my "100×–1000×". Plug in your numbers. Variables (defaults reflect my workflow on Copilot Pro+ with ~40 GPT-5.5-class subagents per parent call; replace any with your numbers):

```
INPUT_TOKENS_PER_SUBAGENT   = 200,000   (I max prompt + context rehydration)
OUTPUT_TOKENS_PER_SUBAGENT  = 50,000
SUBAGENTS_PER_PARENT        = 40
TOOL_CALLS_PER_SUBAGENT     = 25        (midpoint of my 10–40 range)
TOKENS_PER_TOOL_CALL_LOOP   = 5,000     (input re-context per tool round-trip)
INPUT_PRICE_PER_MTOK_USD    = 5.00      (Claude Opus 4.7 or GPT-5.5; check your model)
OUTPUT_PRICE_PER_MTOK_USD   = 25.00     (Opus 4.7; use 30.00 for GPT-5.5)
YOUR_PARENT_CALL_COST_USD   = 0.30      (Copilot Pro+ GPT-5.5: 7.5 × $0.04 overage;
                                         Claude Code on a Max plan: depends on plan;
                                         free-tier vendor mesh: ~$0)

total_input  = INPUT_TOKENS_PER_SUBAGENT * SUBAGENTS_PER_PARENT
             + TOKENS_PER_TOOL_CALL_LOOP * TOOL_CALLS_PER_SUBAGENT * SUBAGENTS_PER_PARENT
             + 200,000
total_output = OUTPUT_TOKENS_PER_SUBAGENT * SUBAGENTS_PER_PARENT + 50,000
raw_api_cost = (total_input/1M * INPUT_PRICE) + (total_output/1M * OUTPUT_PRICE)
savings      = raw_api_cost / YOUR_PARENT_CALL_COST_USD
```

My normal workflow: 40 GPT-5.5 subagents on Copilot Pro+ → raw API equivalent ~$127 → my cost ~$0.30 → ~425×. The 1000× end of the range is a heavy-Opus 11×8 day. The 100× end is GPT-5 across the board. Four bracketed examples are in `docs/COST_MODEL.md`.

### Note on pricing posture

I pay the full Copilot Pro+ premium-request multiplier on every parent call (7.5× for GPT-5.5 = $0.30/call). This isn't a billing bypass; Copilot advertised the subagent feature and I built on it. The June 1 transition shifts the multiplier math; the routing pattern still works on free vendor mesh and Claude Code afterward.

### If you're on an annual Copilot plan

Separately useful (saw a few people asking): if the new usage-based pricing doesn't work for you, GitHub is offering a self-serve cancel-and-refund through May 20, 2026. Billing settings → GitHub Copilot → Manage subscription → "Cancel and refund subscription." Canceling is not reversible for non-students; refund is prorated for time remaining. Source: [docs.github.com/en/copilot/concepts/billing/billing-for-individuals](https://docs.github.com/en/copilot/concepts/billing/billing-for-individuals).

### Sources (all fetched 2026-05-11)

- [Copilot premium-request multipliers](https://docs.github.com/en/copilot/concepts/billing/copilot-requests) — GPT-5.5 at 7.5×, Claude Opus 4.7 at 15×, Sonnet 4.6 at 1×
- [Copilot Pro+ plan](https://github.com/features/copilot/plans) — $39/mo, 1500 included premium requests, $0.04/req overage
- [GitHub usage-based billing announcement](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/) — June 1, 2026
- [Copilot billing-for-individuals (refund policy)](https://docs.github.com/en/copilot/concepts/billing/billing-for-individuals)
- [Anthropic pricing](https://claude.com/platform/api) — Opus 4.7 $5/$25 per Mtok, Sonnet 4.6 $3/$15
- [GPT-5.5 pricing mirror](https://artificialanalysis.ai/models/gpt-5-5) — OpenAI's marketing page returned 403 unauth on 2026-05-11; cross-check on platform.openai.com when signed in

### Caveats

- Copilot billing is opaque from outside. My numbers are mine; measure yours.
- 7/8 confidence cap means I treat human review as still required.

### Aside from the gift

I also take paid audits on AI-agent workflows. 7-tier ladder + refund-on-no-finding on the focused audit. Details in [GIFT_AND_OFFER.md](https://github.com/obsidian-spider-org/obsidian-spider-quickstart/blob/main/GIFT_AND_OFFER.md). First 5 at design-partner half-price. Not pitching here — just leaving the link if it ever fits.

Happy to answer questions for the next few hours. Contact: `contact@obsidianspider.org` (or just reply in-thread).
