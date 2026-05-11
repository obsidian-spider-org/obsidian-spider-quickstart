---
title: "Show HN: Cost-aware routing swarm — one parent call, N subagents (MIT)"
date: 2026-05-11
launch_slot: 2026-05-12T14:00Z (Tuesday HN peak per wave-1 timing research)
confidence: "7/8 (no quorum certificate)"
---

# Show HN: Cost-aware routing swarm — one parent call, N subagents (MIT)

I've been running this pattern privately for a few months and figured I'd write it up before someone else does. If you already pay for Claude Code or Copilot, the bones of this are mostly free: most coding-agent harnesses bill by the parent message, not by the fanout inside it. One parent call dispatches N subagents, no extra premium-request budget.

The repo is a single markdown prompt plus two stdlib-only Python helpers. MIT, no telemetry, no signup. You paste the prompt as the parent message, fill in TARGET and GATHER_INSTRUCTION, and each subagent writes one HMAC-signed JSONL line so you can audit later. Cheap models handle cheap work; frontier only runs the final gather.

What you can fan out: code review, image-prompt batches, markdown drafts, decision-room quorums, refactor exploration, schema design, test-case ideas. The template doesn't hardcode the use case; you fill in what to scatter and what to gather.

The savings ratio sits around 100×–1000× vs running the same work as raw API calls, depending on which frontier model you'd otherwise pay for. The multi-tier mix itself (cheap subagents for cheap work; frontier only for the final gather) saves ~30% on raw API cost vs all-frontier, before any vendor-specific savings on top. Copilot is one angle, free vendor mesh is another, Claude Code is a third. Don't trust my number. The calculator and four worked examples are in `docs/COST_MODEL.md`; plug in your own variables.

If you don't already use an LLM agent harness, this won't matter to you today; it's a tool for people already paying for one. On Copilot Pro+ specifically, GitHub's [June 1 billing transition](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/) shifts the multiplier math, so now is the moment to measure your own savings. The routing pattern keeps working afterward on free vendor mesh, Claude Code, and anywhere a parent agent can launch subagents.

What this isn't: an orchestrator, a vendor-mesh telemetry stack, or a magic quality booster. It surfaces quorum-style misses; it doesn't fix a broken pipeline. Human review is still required.

Repo + 10-min quickstart: https://github.com/obsidian-spider-org/obsidian-spider-quickstart

If you try it on a real input, I'd be curious what ratio you measure.
