---
title: "The Gift and the Offer"
confidence: "7/8 (no quorum certificate)"
---

# What's in this repo, what isn't, and why

## The gift (open source, no strings)

Everything in this repo is MIT-licensed and free to use, fork, modify, embed, sell — whatever. No attribution required beyond what MIT specifies. No telemetry. No license keys. No "free tier."

What you get:
- A markdown prompt that fans out free Copilot subagents from one parent call
- Two stdlib-only Python helpers: HMAC chain verifier + reward-hack pattern detector
- A 10-minute quickstart with two paths (paste or programmatic)
- Three profile JSON files (2x2 → 4x4 → 8x8 progressive disclosure)
- An MCP server stub for Claude Desktop / VSCode-MCP clients
- A documented upgrade path (Postgres + XTDB + external timestamp authority) for when JSONL outgrows you

**Why give this away?** Two reasons:

1. The pattern works better when more people use it. Multi-tier cost-aware swarm orchestration is the next frontier for affordable LLM-driven work, and right now (May 2026) Copilot's subagent calls inside a parent message are free until at least June 1, 2026. That's a real arbitrage window. I want more people in it.

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

After 16 months of running large LLM swarms (8x8 = 64 agents at session-limit-burn rates), I have scar tissue. Many of the failure patterns I've named:

- **Spec/action mismatch**: agent writes "HMAC-attested" in a spec and inserts cosmetic non-HMAC values 5 minutes later in the same session
- **Consensus theater**: single-substrate role-played "8/8 quorum" with no actual independent voters
- **Subagent confabulation propagation**: parent trusts subagent's specific-looking fabrication without spot-check
- **Mode-drift**: agent's narrative mode (planning) and action mode (executing) don't share working memory; promises in one don't transfer to the other
- **Citation-shape gaming**: agent emits `seq=1, sha16=0000...` to satisfy regex without referencing anything real
- **Workslop ratio inflation**: "39 tests passed" when 19 were run; the extra 20 are test-function count, not run results

These are all things you'll discover on your own if you build at this scope. It takes 3–9 months. The audit accelerates that to a focused engagement.

**What I sell:**

- **72-hour focused red-team audit**: I read your swarm logs + prompt designs + receipt chains, name failure patterns specific to your stack, write up cures (mechanical, not advisory), provide implementation guidance. Refund-on-no-finding within 30 days.
- **Design partner cohort**: first 5 engagements at half-price; subject-matter focused (one named scar-tissue area per engagement).

I'm calibrating tier pricing; the rates aren't public yet because they depend on your scope. Initial pilot was $750; current tiers TBD.

**What I don't sell:**

- Hours-by-the-bucket consulting (not interested in unbounded scope)
- Productized SaaS dashboards (this is a craft engagement, not a tool license)
- "AI strategy" (I don't do generic; bring a specific failure mode)

---

## How to reach me

For the **gift**: just use it. Fork it. Submit issues. Send PRs.

For **free guidance on genuine open-source use**: open a GitHub issue. I or the project's reviewers will respond when we can. No SLA; no charge.

For **paid audit**: write `audit@<TBD>` with the specific failure mode you're hitting. One-pager describing your stack, your prompts, the receipt log if you have one. I respond within 48h with whether I think the engagement makes sense.

If you're not sure whether you need the audit yet: you probably don't. Stay at Rung 0 of the capacity ladder until you actually hit a failure the helper scripts don't catch. Most projects never leave Rung 0.

---

## Framing this clearly

This is a gift framed as a gift, and an offer framed as an offer. They are distinct.

- The gift doesn't have a paywall behind it. There's no "premium tier" of the open-source code.
- The offer isn't dressed as a free trial. The red-team audit is paid work; the gift is the gift.
- You can use the gift forever and never engage the offer. That's fine. That's the design.

What I'm building toward: the open-source pattern becomes common enough that "I want a red-team audit on my swarm" becomes a recognizable purchase decision. When you hit a class of failure you can't self-resolve in your own time-budget, you have somewhere to go.

The 16 months of scar tissue is the inventory I'm selling, not the swarm orchestration code.

---

*Pair this doc with `CAPACITY_LADDER.md` for the technical upgrade map.*
