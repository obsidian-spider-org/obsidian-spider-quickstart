---
title: "Reddit r/LocalLLaMA text-post variant — T+2h after HN launch"
platform: reddit_localllama
target_slot: 2026-05-12T16:00Z (T+2h after HN launch at 14:00 UTC)
post_type: "text post (self post; r/LocalLLaMA prefers these for project shares)"
word_target: "200-400"
date: 2026-05-12
confidence: "7/8 (no quorum certificate)"
---

# Reddit r/LocalLLaMA, text post

**Note on sub rules**: I haven't verified r/LocalLLaMA's current self-promo policy on the day this post lands. Standard practice in 2026 was "self-posts okay if technical and not commercial." If the mods flag it, accept the removal and move on; don't argue. Author is responsible for re-checking rules at submission time.

---

## Title (pick one)

Primary: `Open-source markdown prompt: fan-out subagents (route each to cheapest model that does the job) on Copilot / Claude / free vendor mesh — MIT, signed JSONL output`

Backup: `One parent call → N subagents with cost-tier routing; works on Copilot, Claude Code, OpenRouter free mesh (MIT)`

---

## Body

Disclosure: I built this; sharing for feedback, not selling.

I've been running multi-agent workflows on my own work for months and finally cleaned up the minimum-viable slice into a public repo. Here's what it is.

A single markdown prompt you paste into Copilot's coding-agent surface, Claude Projects, Claude Code's Agent tool, or any GPT-4o-class assistant with tool use. The parent call dispatches N subagents inside the same message, fan-out subagents and route each to the cheapest model that does the job (cheap models for cheap work, frontier only for the synthesis pass). Every subagent emits one JSONL line. The lines are HMAC-chained so you can verify later that nothing was edited after the fact.

If you're already running an agent harness, the bones of this are mostly free, because most coding-agent harnesses bill by the parent message, not by the fan-out inside it. One parent call dispatches N subagents, no extra premium-request budget.

**Multi-platform** is the load-bearing point for this sub:

- **GitHub Copilot Pro+**: current pricing window; one parent premium request fans out to subagents inside the same message
- **Free vendor mesh**: OpenRouter / Groq / Together / Cerebras / DeepInfra / Mistral free tiers, with backoff/retry/durable-workflow wrapper (no vendor lock)
- **Claude Code**: Agent tool subagents
- **Self-hosted Llama-3.x / MLX / vLLM**: anywhere a parent agent can launch subagents

Multi-tier cost awareness is the part that matters, not any one vendor.

Specifics on the fan-out: each subagent is assigned a role from a rotation (security, logic, style, perf, completeness, consistency, edge-cases, integration), given the diff as TARGET, and constrained to one JSONL line per finding with file:line evidence or a direct quote. The parent collects them, runs a basic reward-hack pattern scan (copy-paste quorum, citation-shape gaming, confidence inflation), and emits a SUMMARIZE receipt at the end.

The HMAC layer is optional. Default key is published in the repo (`default-public-key-rotate-yours`); rotate via env var `FANOUT_HMAC_KEY` and you have a chain that's actually tamper-evident.

Two stdlib-only Python helpers ship with it: a chain verifier and a reward-hack pattern detector. No external dependencies.

Cost math: on Copilot Pro+ today, the savings ratio lands in the 100×–1000× range vs raw API depending on which frontier model you'd otherwise pay for. Don't trust my number; the calculator plus four worked examples are in `docs/COST_MODEL.md`. GitHub announced [usage-based Copilot billing effective June 1, 2026](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/); the current pricing window is closing, so measure your own savings before then. The routing pattern keeps working afterward; only the Copilot-specific multiplier compresses.

Caveats: inside-parent-message subagent counting is current Copilot pricing-window behavior, not a contract. Context exhaustion is real on `4x8` and above. The confidence cap is hard-coded at 7/8; the prompt refuses to emit `8/8` self-claims.

MIT-licensed, no telemetry, no sign-up. Repo: github.com/obsidian-spider-org/obsidian-spider-quickstart

If anyone tries it on a non-Copilot substrate (self-hosted Llama-3.x with tool use, MLX-served models, vLLM, or free-tier mesh), I'd be very curious whether the cost-tier routing pattern holds on your setup. I've tested Copilot + Claude + GPT-4o; the literature (RouteLLM, Aviary, Mixture of Agents) says it should generalize.
