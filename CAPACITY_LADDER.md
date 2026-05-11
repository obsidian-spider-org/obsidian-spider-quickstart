---
title: "Capacity Ladder & Upgrade Paths"
confidence: "7/8 (no quorum certificate)"
---

# Capacity Ladder & Upgrade Paths

You started with `2x4` (8 agents) from QUICKSTART. This doc shows what to do when you outgrow it.

The ladder is **progressive disclosure** — pick the rung that matches your project scope today; climb when you actually hit the limit, not before.

---

## Where you are now (Rung 0)

```
2x4 wave  →  JSONL audit trail  →  hmac_verifier  +  reward_hack_detector
```

You get: signed per-agent receipts, tamper-evident chain, basic reward-hack catches. **Cost: free-tier or fixed-sub.**

Stay here as long as it works for you. Most projects never need to leave Rung 0.

---

## When to climb (signals)

| Signal | Rung |
|---|---|
| You want JSONL receipts to survive a single file or terminal session | **Rung 1** |
| You want to ask "what did chain look like at hour T yesterday?" | **Rung 2** |
| You have multiple writers (CI + dev + reviewers) racing the same chain | **Rung 3** |
| You hit reward-hacks the helper script doesn't catch — confabulation across waves | **Rung 4** |
| You want full BFT consensus with cryptographic attestation per receipt | **Rung 5** |

---

## The four upgrade paths

Pick **A**, **B**, **C**, or **D** based on what failed first.

### Option A — Postgres SSOT (recommended next step)

**For**: durability past a single JSONL file; many readers/writers; SQL queries.

```
chain.jsonl  →  Postgres table `chain` with HMAC trigger  →  same hmac_verifier still works
```

What you get:
- `chain` table; trigger refuses fake HMAC at write boundary
- Mode-aware HMAC (lying about agent mode breaks chain cryptographically)
- Append-only triggers (UPDATE/DELETE blocked at DB layer)
- Semantic-dedup constraint (UNIQUE on canonical content)
- Outbox pattern: atomic dual-write into mirrors

Setup: ~5 min. See `UPGRADE_TO_POSTGRES.md`.

Cost: Docker compose runtime (free; local).

Trade-off: now there's a database. If your laptop reboots, restart the container. JSONL was simpler.

### Option B — XTDB bitemporal mirror (time-travel + tamper-preservation)

**For**: "what did the chain look like at hour T?"; archival history that survives DELETE.

```
Postgres chain  →  XTDB chain_mirror (bitemporal append-only)  →  AS OF SYSTEM TIME queries
```

What you get:
- Every chain row gets mirrored to XTDB via outbox drainer (sub-1s delta)
- Time-travel: `SELECT ... FROM chain_mirror FOR SYSTEM_TIME AS OF '2026-05-11T12:00:00Z'`
- DELETE in XTDB preserves history (current state hides; past state queryable)
- If Postgres gets wiped, XTDB reconstructs

Setup: ~10 min on top of Option A.

Cost: ~500MB RAM for two containers.

Trade-off: now you have TWO stores. SSOT is Postgres; XTDB is mirror. Don't write to both manually.

### Option C — Tamper-detection daemon + RFC 3161 timestamp authority

**For**: production-grade tamper-evidence; external witness for compliance/audit.

```
chain ↔ mirror diff every 60s  +  hourly TSA snapshot to freetsa.org
```

What you get:
- Persistent Pg ↔ XTDB inconsistency raises STRIFE; alerts at 3-cycle threshold
- Hourly snapshot of (max_seq, max_sha16) signed by external TSA (RFC 3161)
- Operator-independent attestation: chain state at time T is provable from TSA token alone

Setup: ~15 min on top of Options A+B.

Cost: 2 background daemons + ~5KB/h TSA tokens.

Trade-off: more moving parts; more to debug if anything breaks.

### Option D — Multi-substrate BFT quorum (highest assurance)

**For**: claims like "8 of 8 independent reviewers agree" with cryptographic backing.

```
Dispatch 8 agents across 8 different vendors  →  collect votes  →  bft_quorum_check  →  6/8 → consensus
```

What you get:
- Real vendor diversity (OpenRouter + Groq + Together + Fireworks + DeepInfra + Cerebras + Mistral + Anthropic)
- No single-substrate blind spot
- BFT threshold: 6 of 8 agree → consensus; f=⌊(n−1)/3⌋=2 max faulty
- Each receipt cryptographically chained back to the dispatch

Setup: ~30 min. Needs 8 free-tier API keys (each vendor's free tier; ~$0 total).

Cost: 8x the API calls per decision (still $0 on free tiers).

Trade-off: latency; you wait for the slowest vendor. Heavy.

---

## Choosing your path

```
Need durability past one file?              →  A (Postgres SSOT)
Need time-travel queries?                   →  A + B (Postgres + XTDB)
Need compliance / external witness?         →  A + B + C
Need genuine multi-substrate consensus?     →  A + D (Postgres + BFT vendor mesh)
All of the above?                           →  A + B + C + D
None of the above?                          →  Stay at Rung 0; JSONL is fine
```

You don't have to commit. Each option is independently installable + reversible.

---

## What this is NOT

- Not a magic stack. Each rung adds operational complexity.
- Not a guarantee. Cryptography catches tampering; it doesn't make agents smarter.
- Not free in operator-attention. Postgres needs upgrades; XTDB needs config; daemons need monitoring.
- Not "the right answer for everyone." Most teams stay at Rung 0 forever and that is the boring-engineering correct call.

---

## When you hit problems

If you scale this and hit a class of failure the helper scripts don't catch — patterns like cross-wave confabulation, role-collusion, citation-fabrication that survives the regex audit — those are 16 months of scar tissue away. I've documented some; you can rediscover them yourself over the next ~6-12 months, or open a GitHub issue and ask. Free guidance for genuine open-source users.

Accelerated consulting (paid red-team audit) is available — see `GIFT_AND_OFFER.md`.

---

*This file is one of two: pair it with `GIFT_AND_OFFER.md` for the framing around why this exists and what's not for sale.*
