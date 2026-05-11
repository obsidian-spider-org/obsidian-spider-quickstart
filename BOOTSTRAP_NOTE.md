---
title: "Bootstrap vs Real Vendor Mesh"
date: 2026-05-11
confidence: "7/8 (no quorum certificate)"
---

# Bootstrap vs Real Vendor Mesh

A short note on what "BFT consensus" actually means in this repo at each rung of the capacity ladder. I want to be honest about the difference between persona fanout inside one model and real multi-vendor consensus.

## The current state (Rung 0–2): bootstrap

When you run `run_wave.py --config 2x2` or paste `PROMPT.md` into a single Copilot, Claude, or GPT-4 session, the "8 reviewers" are 8 personae spawned by ONE underlying model. They share training weights, context window, and reward function. That is **bootstrap reasoning**, not Byzantine fault tolerance.

What you get from bootstrap:
- ✅ Structural diversity (different roles ask different questions)
- ✅ Sequential refinement (wave 2 sees wave 1's output)
- ✅ Cryptographic receipt chain (HMAC-linked JSONL)
- ✅ Reward-hack pattern detection on the output

What bootstrap does NOT give you:
- ❌ Independence from the substrate's blind spots
- ❌ Failure modes that don't transfer across the 8 personae
- ❌ Real Byzantine fault tolerance against a malicious-or-faulty model

This is **fine for most projects**. Most reviews don't need cryptographic certainty across distinct substrates — they just need more than one perspective.

## The upgrade (Rung 4–5): real free-vendor mesh

Real Byzantine fault tolerance requires distinct substrates. The Option D upgrade in `CAPACITY_LADDER.md` dispatches across 8 different vendor families on their respective free tiers:

```
reviewer 1  → OpenRouter   (rotate model family per free-tier slot)
reviewer 2  → Groq
reviewer 3  → Together
reviewer 4  → Fireworks
reviewer 5  → DeepInfra
reviewer 6  → Cerebras
reviewer 7  → Mistral
reviewer 8  → Anthropic
```

When 8 vendors with independent training data and independent reward functions all converge on the same finding, that's a real BFT-class signal. If 6 of 8 agree (threshold = ⌈2n/3⌉ for n=8), the consensus is durable against any 2 faulty or colluding nodes (f = ⌊(n−1)/3⌋ = 2).

Setup time for the upgrade: ~30 min. Cost: each vendor has a free tier; total $0 marginal cost per decision if you stay within free-tier quotas.

## Why this matters for your interpretation

If `reward_hack_detector.py` flags `L-CONSENSUS-THEATER` on a bootstrap run because all 8 personae agreed too easily, that flag is *correct*. Bootstrap consensus IS theater compared to real-vendor-mesh consensus. The detector isn't bugged; it's surfacing a real limit of the bootstrap mode.

To make BFT-attested claims, climb to Rung 4 or 5.

## Practical guidance

| Your project | Stay at bootstrap? | Climb to vendor-mesh? |
|---|---|---|
| Solo PR reviews; rapid prototyping | YES (Rung 0–2 is plenty) | not needed |
| Internal code review at a 3–10 person team | YES (HMAC chain catches tampering) | not needed |
| Production decision-gate (auto-merge, release approval) | maybe | recommended (Option A + D) |
| Compliance / regulatory audit trail | NO (bootstrap is single-witness) | YES (real BFT + RFC 3161 TSA) |
| Security review of safety-critical code | NO | YES (real BFT) |

## What this repo is honest about

The `PROMPT.md` template tells the parent model to "spawn N subagents." On a single-substrate run, those subagents are personae — useful, but not Byzantine-fault-tolerant. The HMAC chain catches *output* tampering; it does NOT make the personae independent.

The `confidence: "7/8 (no quorum certificate)"` cap on every receipt reflects this: a real 8/8 quorum certificate requires multi-substrate attestation (Option D in `CAPACITY_LADDER.md`). I designed bootstrap reasoning to max out at 7/8 by design.

This isn't a weakness; it's a labelling discipline. Pay attention to the cap.

---

*Pair this note with `CAPACITY_LADDER.md` (the technical upgrade map) and `GIFT_AND_OFFER.md` (the framing).*
