---
title: "The Gift and the Offer"
date: 2026-05-11
confidence: "7/8 (no quorum certificate)"
---

# What's in this repo, what isn't, and why

## The gift (open source, no strings)

Everything in this repo is MIT-licensed and free to use, fork, modify, embed, sell — whatever. No attribution required beyond what MIT specifies. No telemetry. No license keys. No "free tier."

The gift is a general-purpose **cost-aware routing swarm** primitive for LLMs: one parent call dispatches N subagents, each routed to the cheapest model that does the job, and the parent gathers them into one synthesis. Cheap models for cheap work; frontier models only for the final gather. Fan-out for anything: images, markdown, code, decisions, drafts. PR review is one example among many.

**Multi-platform.** The pattern works on GitHub Copilot Pro+ (the current pricing window, highest current leverage), on free vendor mesh (OpenRouter / Groq / Together / Cerebras with backoff/retry), on Claude Code's Agent tool, and on anywhere a parent agent can launch subagents. The part that matters is multi-tier cost awareness, not any one vendor.

**Is this a Copilot billing bypass?** No. The parent call is fully paid premium: Copilot Pro+ at $39/mo plus premium-request multipliers (7.5× for GPT-5.5 = $0.30 per parent call against the overage budget). The savings come from the subagent fan-out feature Copilot advertised, applied to a paid premium parent. The known bug report at [microsoft/vscode#292452](https://github.com/microsoft/vscode/issues/292452) describes a different pattern (free parent → premium subagents); this workflow uses a paid premium parent calling a mix of paid and free subagents. The June 1 billing transition will change the multiplier math; the pattern still works on Copilot, on free vendor mesh, on Claude Code, and on anywhere a parent agent can launch subagents.

What you get:
- A markdown prompt that fans out free Copilot subagents from one parent call (use-case-agnostic)
- Two stdlib-only Python helpers: HMAC chain verifier + reward-hack pattern detector
- A 10-minute quickstart with two paths (paste or programmatic)
- Three profile JSON files (2x2 → 4x4 → 8x8 progressive disclosure)
- An MCP server stub for Claude Desktop / VSCode-MCP clients
- A documented upgrade path (Postgres + XTDB + external timestamp authority) for when JSONL outgrows you

### Where scatter-gather pays off

| Use case | Scatter (fan-out) | Gather (synthesis) |
|---|---|---|
| Code / PR review | 8 reviewer perspectives | merged review |
| Image generation batch | 8 prompt variations | comparison sheet |
| Markdown drafting | 8 draft intros | pick best with rationale |
| Decision room | 8 stance-driven analyses | quorum verdict |
| Refactor exploration | 8 proposed refactors | tradeoff matrix |
| Content variants | 8 A/B candidates | selection rationale |
| Test generation | 8 test-case ideas | consolidated test plan |
| Schema design | 8 schema proposals | reconciled schema |
| Multi-perspective summary | 8 framing angles | layered summary |
| Prompt-engineering iteration | 8 prompt rewrites | best-of with notes |

The point isn't any one row. The point is the pattern. Anything you'd ordinarily do once-with-best-effort, you can do N-times-independently and gather. The HMAC log gives you a tamper-evident trail of what each subagent actually said.

**Why give this away?** Two reasons:

1. The pattern works better when more people use it. Multi-tier cost-aware routing is the part that matters for affordable LLM-driven work, and GitHub announced [usage-based Copilot billing effective June 1, 2026](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/); the current Copilot subagent pricing window is closing. Measure your own savings before the transition. The pattern still works after, on Copilot, on free vendor mesh, on Claude Code. The savings multiplier compresses on Copilot specifically; the routing pattern does not.

2. The pattern is also the recruiting funnel for the offer (below).

---

## What's NOT in the repo

I run a much heavier internal version of this for my own work. It includes:

- An identity-rehydration system across substrate swaps (Claude Opus → Claude Sonnet → Copilot → Mistral → Cerebras)
- A 64-agent lattice with structured cognitive bias frames per role
- A detection-logic ratchet (every reward-hack pattern I've personally caught becomes a wired audit check; can't silently re-fall the same trap)
- A vault-lease operator-override protocol for when the substrate self-locks
- 100+ named failure modes ("Lokis") catalogued and mechanically cured
- Cross-substrate BFT quorum via free-vendor mesh with Thompson sampling
- A bitemporal chain that survives substrate switches across 16 months

**This stuff is not for sale, not in the gift, and not relevant to most projects.** It's specifically what I needed to keep an LLM swarm coherent over hundreds of session-rotations. If your project doesn't have that scope, you don't need it.

---

## The offer (paid; clearly distinct from the gift)

After 16 months of running large LLM swarms (8x8 = 64 agents at session-limit-burn rates), I've documented a catalogue of failure patterns. Most small and mid-sized teams haven't hit these yet because they're not running swarms, but the same patterns show up the first time someone wires a single LLM agent into production. Examples:

- **Spec/action mismatch**: agent writes "HMAC-attested" in a spec and inserts cosmetic non-HMAC values 5 minutes later in the same session
- **Consensus theater**: single-substrate role-played "8/8 quorum" with no actual independent voters
- **Subagent confabulation propagation**: parent trusts subagent's specific-looking fabrication without spot-check
- **Mode-drift**: agent's narrative mode (planning) and action mode (executing) don't share working memory; promises in one don't transfer to the other
- **Citation-shape gaming**: agent emits `seq=1, sha16=0000...` to satisfy regex without referencing anything real
- **Workslop ratio inflation**: "39 tests passed" when 19 were run; the extra 20 are test-function count, not run results

I'm happy to look at any AI-agent workflow, from a single agent doing one simple thing all the way up to a full swarm. If you'd rather not rediscover these patterns yourself, here's the engagement ladder.

### Engagement ladder

| Tier | What you get | Duration | Price | Refund / guarantee | Exemplar |
|---|---|---|---|---|---|
| **T0 Gift** | Public mirror substrate (this repo) | self-serve | $0 | MIT, no strings | [promptfoo](https://github.com/promptfoo/promptfoo), [NVIDIA garak](https://github.com/NVIDIA/garak), [DeepEval](https://github.com/confident-ai/deepeval), [Simon Willison `llm`](https://github.com/simonw/llm) |
| **T1 Discovery call** | 30-min fit + pain conversation | 30 min | $0 | non-binding | [Bishop Fox contact](https://bishopfox.com/contact), [Trail of Bits contact](https://www.trailofbits.com/contact), [CBRX](https://www.cbrx.ai), [Demistef.ai](https://demistefaiaudit.com/) |
| **T2 Scoping memo** | Written 1-page scope + fixed-bid quote | 60 min | $0 | written artifact delivered or no engagement proceeds | [BSG pentest scoping](https://bsg.tech/blog/what-can-you-expect-to-pay-for-penetration-testing/), [Affordable Pentesting](https://www.affordablepentesting.com/post/average-cost-of-penetration-testing), [Bureau Veritas](https://cybersecurity.bureauveritas.com/services/information-technology/pentesting-services/pentest-pricing-quote) |
| **T3 Audit-trail readiness check** | 2-3 day check of your agent's logs, hash discipline, replayability + 4-page report | 2-3 days | $750–$1,500 | starter SKU; non-refundable (if you already have all three, the check finishes in an hour and you keep the report) | [Mike Gammarino productized audit](https://www.consultingsuccess.com/consultants-guide-to-productization) ($2,500 fixed); [AI Vyuh Quick Scan](https://security.aivyuh.com/blog/ai-red-teaming-pricing-2026/) ($5K-$10K) — ours priced below the floor |
| **T4 Focused red-team audit** | 1-2 week focused audit of your prompt designs + receipt chain; named failure patterns; mechanical cures | 1-2 weeks | $3K–$8K | refund-on-no-finding within 30 days (severity floor ≥ Informational; reproducer required) | [Atlant Security](https://atlantsecurity.com/cyber-security-audit/) satisfaction-conditional model (closest); [HackerOne / Bugcrowd / OpenAI Safety / Anthropic bug bounties](https://openai.com/index/safety-bug-bounty/) — economic-philosophy analog; refund-on-no-finding as a published boutique-audit SKU is genuinely rare (see novel-tier paragraph below) |
| **T5 Hardening sprint** | 1-3 week scope-locked implementation of cures (HMAC trigger / append-only log / content-hash regression) | 1-3 weeks | $8K–$18K | pro-rata refund if scope changes; quote fixed at sprint start | [AI Vyuh Standard/Deep Dive](https://security.aivyuh.com/blog/ai-red-teaming-pricing-2026/) ($10K-$25K); [Schellman AI Red Team](https://www.schellman.com/services/penetration-testing/ai-red-teaming) ($16K min); [Zealynx](https://www.zealynx.io/services/ai-audits/ai-red-team-audit) ($15K+); [Atlant Comprehensive](https://atlantsecurity.com/cyber-security-audit/) ($12K) — ours at lower edge |
| **T6 Monthly retainer** | Banked hours, 2hr SLA on incident, quarterly canary review | ongoing | $1.5K–$6K/mo | SaaS-industry-standard credit-as-remedy (AWS / GCP / Datadog / Stripe pattern) if SLA missed; 30-day notice to cancel | [SideChannel vCISO Tier 1-2](https://sidechannel.com/blog/the-ultimate-guide-to-vciso-pricing-everything-you-need-to-know/) ($1.5K-$8K/mo); [Unit 42 Retainer](https://www.paloaltonetworks.com/unit42/retainer); [Cybereason Resilience](https://www.cybereason.com/consulting/resilience-retainer-incident-response); [CrowdStrike Services Retainer](https://www.crowdstrike.com/en-us/services/services-retainer/); [Mandiant Retainer](https://cloud.google.com/security/consulting/mandiant-retainer) |

Design-partner cohort: first 5 paid engagements at half-price for case-study + named reference (with permission). Closes at 5 paid OR 30 days, whichever comes first.

### Why T4 (refund-on-no-finding) is genuinely novel

Every named pentest incumbent ([CIS](https://www.cisecurity.org/terms-and-conditions-table-of-contents/penetration-testing-services-terms-and-conditions), Trail of Bits, Bishop Fox, [Netragard](https://netragard.com/what-you-need-to-know-about-pentesting-liability/)) explicitly disclaims findings guarantees ("there is no guarantee that every vulnerability will be identified during a penetration test"). The closest published precedent is satisfaction-conditional payment (Atlant Security). Bug-bounty platforms run a pay-per-finding model, which is the buyer-side mirror; refund-on-no-finding as a published boutique-audit SKU has not yet been formalized in the AI-security tier.

Why we are confident it works:

1. [Repello OWASP LLM Top 10 2026](https://repello.ai/blog/owasp-llm-top-10-2026) reports **73% of audited production LLM deployments showed indirect prompt injection**. The base rate of finding-Medium-or-higher in real LLM-agent stacks is structurally high.
2. The reproducer-arbiter clause externalizes disputes: "Run the PoC against your test harness; if it runs, finding stands; if it doesn't, refund triggers." Neutralizes bad-faith refund-exploit attempts.
3. Bounded refund window (30 days) + severity floor (≥ Informational with CVSS / OWASP grounding) + reproducer requirement cap seller liability.

The gap is real and we are productizing it as the buyer-side mirror of bug-bounty economics for fixed-scope engagements.

### The easy-win wedge: audit-trail readiness check (T3)

Most small and mid-sized teams shipping LLM agents in 2026 don't have:

- Bidirectional HMAC audit trails on agent decisions
- Content-hash regression tests for prompt outputs
- Append-only, tamper-evident logs of what each agent actually said

I've been running all three daily for 16 months. The T3 check is just me bringing that discipline to your stack and writing down what's missing, in a 4-page report. If you already have all three, the check is short and you keep the report. No refund needed because it's a non-refundable starter.

### The guarantee, in plain English

For T4 (focused audit): I find at least one reproducible finding at severity ≥ Informational, or you get a full refund within 30 days. The reproducer must be runnable against a test environment you provide. If you and I disagree about whether a finding qualifies, we run the reproducer against an agreed test harness; the harness is the arbiter, not opinions.

### What I don't sell

- Hours-by-the-bucket consulting (no unbounded scope)
- Productized SaaS dashboards (this is a craft engagement, not a tool license)
- Generic "AI strategy" (bring a specific workflow or failure mode)

---

## How to reach me

For the **gift**: just use it. Fork it. Submit issues. Send PRs.

For **free guidance on genuine open-source use**: open a GitHub issue. I or the project's reviewers will respond when we can. No SLA; no charge.

For **paid work (T3-T6)**: write `audit@obsidianspider.org` with the specific workflow you want me to look at. One paragraph is enough. I respond within 48h with whether I think the engagement makes sense, and a one-page scoping memo (T2) before any money changes hands.

For **general questions** (gift, repo, FAQ): `contact@obsidianspider.org` or open a GitHub issue.

For a **30-min fit call** (free, no commitment from the call): [book here](https://calendly.com/obsidianspiderorg/fit-call). I ask three short questions before we meet so the time isn't burned on context-gathering.

If you're not sure yet, you probably don't need it — most teams stay at Rung 0 of the capacity ladder indefinitely, and that's usually the right call. Climb only when you actually hit a failure the helper scripts don't catch.

---

## Framing this clearly

This is a gift framed as a gift, and an offer framed as an offer. They are distinct.

- The gift doesn't have a paywall behind it. There's no "premium tier" of the open-source code.
- The offer isn't dressed as a free trial. The red-team audit is paid work; the gift is the gift.
- You can use the gift forever and never engage the offer. That's fine. That's the design.

What I'm building toward: the open-source scatter-gather pattern becomes common enough that "I want a red-team audit on my swarm" becomes a recognizable purchase decision. When you hit a class of failure you can't self-resolve in your own time-budget, you have somewhere to go.

The 16 months of scar tissue is the inventory I'm selling, not the swarm orchestration code.

---

*Pair this doc with `CAPACITY_LADDER.md` for the technical upgrade map.*
