---
title: "Fan-out Subagent Review Prompt"
license: MIT
version: "1.0.0"
target_substrate: "GitHub Copilot Pro+ / Claude / GPT-4o"
confidence: "7/8 (no quorum certificate)"
---

# Fan-out Subagent Review Prompt

**One parent call. Multiple independent reviewers. Cryptographically signed log.**

---

## What this is

I built a markdown prompt that turns one GitHub Copilot premium request into a small fan-out of subagent reviewers. You paste it into Copilot's coding-agent surface (or Claude, or GPT-4o with tools). The parent call delegates to N subagents who each critique your PR, document, or design independently. Their outputs land in a JSONL file with an HMAC chain so you can audit who said what and confirm nothing was tampered with afterward.

The key insight: Copilot's current billing model counts the *parent* message as one premium request. Subagents spawned inside that message inherit the context without each billing separately. I run 4–8 reviewers this way on every non-trivial PR. In my experience the independent-critique pattern catches things a single pass misses — not because the model is smarter, but because you get multiple independent angles with different role assignments.

The HMAC chain is optional but cheap. Each reviewer emits one signed JSONL line. The chain links `prev_sha16 → this_sha16` so you can verify order and detect post-hoc edits. If you never care about tamper-evidence, ignore it. If you do, it costs nothing extra.

---

## Quick start (30 seconds)

1. Open GitHub Copilot agent mode (or Claude Projects, or a GPT-4o assistant).
2. Paste the **parent-prompt template** below into the system or first-user message.
3. Fill in `FORMATION`, `TARGET`, and (optionally) `TIER_MIX`.
4. Send. Read the JSONL lines that come back.

```
FORMATION=2x4          # X waves × Y subagents
TARGET=<paste PR diff or doc excerpt here>
TIER_MIX=all-frontier  # or: multi-tier
```

That's it. The rest of this document explains the formation contract, templates, and output format.

---

## The X_Y wave formation contract

`FORMATION=X_Y` means **X sequential waves of Y subagents each**.

| Formation | Waves | Agents/wave | Total agents | When to use |
|-----------|-------|-------------|--------------|-------------|
| `1x1`     | 1     | 1           | 1            | Quick sanity check |
| `1x4`     | 1     | 4           | 4            | Single broad review pass |
| `1x8`     | 1     | 8           | 8            | Maximum breadth, one pass |
| `2x4`     | 2     | 4           | 8            | **Recommended start** — first wave finds, second wave verifies |
| `4x8`     | 4     | 8           | 32           | Sustained adversarial review |
| `8x8`     | 8     | 8           | 64           | Heavy red-team; burns context fast |

**Waves are sequential.** Wave 2 sees Wave 1's JSONL output before it starts. This lets later waves dispute or build on earlier findings rather than repeat them.

**Tier-mix knob** (set in the parent prompt):
- `--all-frontier`: every subagent uses the same tier as the parent (default).
- `--multi-tier`: first subagent per wave is frontier-class; remaining subagents use a cheaper reasoning tier. Useful when you want one "anchor" reviewer per wave and cost is a concern.

You decide which formation fits your risk tolerance. Measure your own results.

---

## Parent-prompt template

Copy this block as-is. Fill the three `FILL_ME` slots.

````markdown
## ORCHESTRATOR SYSTEM PROMPT

You are the parent orchestrator for a fan-out review run.

### Configuration (fill before sending)
```
FORMATION=FILL_ME        # e.g. 2x4
TARGET=FILL_ME           # PR diff, document excerpt, or design text
TIER_MIX=all-frontier    # or: multi-tier
HMAC_KEY=default-public-key-rotate-yours
```

### Your job
1. Parse FORMATION into X waves of Y subagents.
2. For each wave (1 through X):
   a. Spawn Y subagents sequentially, each with the SUBAGENT TEMPLATE below.
   b. Assign each subagent a unique `agent_id` (e.g. `reviewer-w1-a1`).
   c. Assign role from this rotation: security, logic, style, performance, completeness, consistency, edge-cases, integration.
   d. Collect each subagent's JSON receipt (one line per agent).
3. If TIER_MIX is `multi-tier`: subagent index 0 per wave is frontier; remaining use a cheaper reasoning call.
4. After all waves: emit a `SUMMARY` receipt with `verb: "SUMMARIZE"`, listing all finding IDs and any consensus flags.
5. Write all receipts (including SUMMARY) as newline-delimited JSON to stdout.

### HMAC chain rule
- Wave 1, Agent 1: `prev_sha16 = "0000000000000000"`.
- Each subsequent receipt: `prev_sha16 = this_sha16` of the immediately preceding receipt.
- `this_sha16 = HMAC-SHA256(key=HMAC_KEY, msg=f"{seq}|{ts}|{verb}|{claim}")[0:16]`.
- Default key is `default-public-key-rotate-yours`. Rotate via env var `FANOUT_HMAC_KEY`.
- If you cannot compute HMAC: emit `this_sha16: "NO_HMAC"` and note it — do not silently omit.

### Reward-hacking check (run before emitting SUMMARY)
For each claim in the JSONL output, verify:
- [ ] Evidence includes a file:line reference OR a direct quote from TARGET — not a vague assertion.
- [ ] No two agents from the same wave made identical claims with identical evidence (copy-paste quorum).
- [ ] No agent marked `confidence: "8/8"` — that requires external sign-off; cap at `"7/8"`.
- [ ] HMAC chain is unbroken: `prev_sha16` of receipt N matches `this_sha16` of receipt N-1.
Flag any violation in the SUMMARY receipt's `rh_flags` array.

---
## SUBAGENT TEMPLATE

You are `{{agent_id}}`, role: `{{role}}`.

TARGET is the text below the `---TARGET---` line.

Your job:
1. Read TARGET.
2. Find ≤3 concrete issues within your role scope.
3. For each issue: cite file:line OR direct quote. No vague assertions.
4. Emit exactly one JSON line matching this schema (no extra prose):

```json
{
  "seq": {{seq}},
  "ts": "{{iso8601}}",
  "prev_sha16": "{{prev_sha16}}",
  "this_sha16": "{{this_sha16}}",
  "verb": "OBSERVE",
  "agent": "{{agent_id}}",
  "wave": {{wave_number}},
  "role": "{{role}}",
  "task_id": "{{parent_task_id}}",
  "claim": "one-sentence summary of finding",
  "evidence": {
    "location": "file:line or quote",
    "detail": "what exactly is wrong and why"
  },
  "severity": "high|medium|low|info",
  "confidence": "7/8"
}
```

If you find nothing in your scope, emit `verb: "PASS"` with `claim: "no issues found in role scope"`.

---TARGET---
{{TARGET}}
````

---

## Output schema (JSONL)

Each line is self-describing. Full field reference:

```json
{
  "seq":        1,
  "ts":         "2026-05-12T12:00:00Z",
  "prev_sha16": "0000000000000000",
  "this_sha16": "a3f7c2d1e8b94f05",
  "verb":       "OBSERVE",
  "agent":      "reviewer-w1-a1",
  "wave":       1,
  "role":       "security",
  "task_id":    "pr-42",
  "claim":      "SQL query on line 87 is unparameterized.",
  "evidence": {
    "location": "src/db.py:87",
    "detail":   "f-string interpolation directly into cursor.execute(); exploitable via search input"
  },
  "severity":   "high",
  "confidence": "7/8",
  "rh_flags":   []
}
```

`verb` values: `OBSERVE` (finding), `PASS` (nothing in scope), `DISPUTE` (wave N+1 disagreeing with wave N), `SUMMARIZE` (parent's final receipt).

---

## What it doesn't do

- **Not magic.** Free fanout is a current Copilot policy artifact, not a contractual guarantee. Measure whether it still works on your account before building a pipeline around it.
- **Not a substitute for a broken pipeline.** If your tests don't run, no number of reviewer agents will catch a runtime regression.
- **HMAC default key is published here.** Anyone who has read this file can forge a valid chain using `default-public-key-rotate-yours`. Rotate your key. It takes 30 seconds: set `FANOUT_HMAC_KEY=<your-secret>` in your environment.
- **Confidence is capped at 7/8.** The eighth point requires a human quorum certificate. Do not ship AI-only reviewed code to production and call it `8/8` confidence.
- **Context length burns.** A `4x8` run on a large diff can exhaust the parent context window before Wave 4 finishes. Start with `2x4` and measure.

---

## Cost model

Copilot Pro+ is $39/mo with 1500 premium requests; each parent call costs 1 premium request; subagents spawned inside that call are intra-message and do not each bill separately — in my experience and as of the current Copilot policy at time of writing.

---

## Upgrade path

If you want durable bidirectional records — queryable history, bitemporal audit, rollback — the next step is Postgres with an append-only receipt table and an XTDB-style bitemporal layer on top. That infrastructure is what I actually run. The markdown prompt above is the minimal public slice.

See `UPGRADE_TO_POSTGRES.md` (separate doc, forthcoming) for the schema and migration path.

---

## Try it

```bash
# 1. Copy PROMPT.md to your clipboard.
# 2. Open Copilot agent / Claude Projects / GPT-4o assistant.
# 3. Set FORMATION=1x4, paste a short PR diff as TARGET, send.

# Expected: 4 JSONL lines + 1 SUMMARIZE line to stdout, e.g.:
{"seq":1,"ts":"2026-05-12T12:00:01Z","prev_sha16":"0000000000000000","this_sha16":"a3f7c2d1e8b94f05","verb":"OBSERVE","agent":"reviewer-w1-a1","wave":1,"role":"security","task_id":"pr-demo","claim":"Unparameterized query at db.py:87.","evidence":{"location":"db.py:87","detail":"f-string in cursor.execute"},"severity":"high","confidence":"7/8","rh_flags":[]}
{"seq":2,"ts":"2026-05-12T12:00:02Z","prev_sha16":"a3f7c2d1e8b94f05","this_sha16":"b8e3a1c0f2d74e91","verb":"PASS","agent":"reviewer-w1-a2","wave":1,"role":"logic","task_id":"pr-demo","claim":"no issues found in role scope","evidence":{},"severity":"info","confidence":"7/8","rh_flags":[]}
```

Real output will vary by model, target, and formation. Measure your own hit rate.

---

## Self red-team: what could go wrong

In my experience, the failure modes to watch for are:

1. **Model collapses to one answer.** The parent sometimes assigns all subagents the same implicit framing, producing a quorum of identical findings with cosmetically different wording. The reward-hacking check (copy-paste quorum flag) catches the obvious form, but subtle alignment collapse is harder to detect. Mitigation: mandate different roles per agent; read receipts critically.
2. **HMAC chain silently omitted.** Some models refuse to compute HMAC or emit `NO_HMAC` without flagging it. Always verify the chain is present before treating output as tamper-evident.
3. **Context exhaustion mid-wave.** Large diffs + many waves = truncated output. The parent may stop mid-JSONL. Set a lower FORMATION first; scale up only after a baseline run.
4. **Billing policy change.** Copilot Pro+ fanout behavior is a policy artifact. If Microsoft changes billing semantics, the cost model in this doc becomes wrong immediately. Measure your own account.
5. **False confidence in 7/8.** The confidence cap exists to remind you this is AI output. "7/8" is not a guarantee; it is a machine-readable signal that human review is still required.

You decide whether these risks are acceptable for your use case.

---

## License

MIT. Use it, fork it, modify it. Attribution appreciated but not required.

---

## Glossary

- **HMAC**: Hash-based Message Authentication Code. A way to sign a piece of text with a secret key so you can later verify it hasn't been changed. If the key is secret, an attacker can't forge a valid signature.
- **JSONL**: JSON Lines. One JSON object per line. Easy to append, easy to stream, easy to parse one line at a time.
- **Quorum**: Agreement among multiple independent reviewers. When ≥ half agree on a finding, it is a quorum finding. Mentioned here in "quorum-style misses" — things a single reviewer skips that multiple independent reviewers catch.
- **BFT (Byzantine Fault Tolerance)**: A computer-science term for a system that keeps working even if some participants lie or fail arbitrarily. This prompt does not implement full BFT — it is a lightweight tamper-evidence layer, not a distributed consensus protocol.
- **Bitemporal**: A database design where every record carries two timestamps — when something was true in the world, and when the database learned about it. Useful for audit trails. Mentioned in the upgrade path; not part of the minimal prompt.
- **Premium request**: GitHub Copilot's billing unit for high-quality model calls (GPT-4o / Claude-tier). As of writing, Copilot Pro+ includes 1500/month.
- **Fan-out**: Spawning multiple parallel (or sequential) workers from a single parent call. The parent is the orchestrator; the workers are the subagents.
- **Subagent**: In this context, a reviewer spawned by the parent orchestrator within the same conversation context. Not a separate API call in the current Copilot billing model.
- **Reward hacking**: When an AI agent finds a way to score well on a metric without actually doing the underlying task. Example: copy-pasting the same finding with minor word changes to produce a longer-looking review.
- **XTDB**: An open-source database with built-in bitemporal semantics. Used in the upgrade path for durable, auditable receipt storage.
