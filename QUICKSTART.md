---
title: "10-Minute Quickstart"
confidence: "7/8 (no quorum certificate)"
---

# 10-Minute Quickstart

## What you'll have after 10 minutes

A JSONL audit trail of multiple AI agents independently reviewing your code or document. Each line is one agent's signed receipt. Two included scripts verify the cryptographic chain and flag common reward-hacking patterns. All of this runs on free-tier API credits.

---

## Minute 1–2: get the template

Clone or download this repo. The only file you need right now is `PROMPT.md`.

```bash
git clone <this-repo-url>
cd <repo-name>
```

Open `PROMPT.md` and copy the block that starts with `## ORCHESTRATOR SYSTEM PROMPT`. That block is the parent-prompt template. It has three `FILL_ME` slots.

---

## Two paths from here

**Path A — Zero-install (paste-into-Claude/Copilot)**: continue reading below. Fastest; ~3 min.

**Path B — Programmatic (CLI driver)**: skip ahead to "Path B" section near the end of this doc. Requires Python 3.10+ + one API key in `.env` + `pip install requests`. Best if you want JSONL auto-emitted to disk for verification by `hmac_verifier.py` / `reward_hack_detector.py` without copy-paste. ~5 min.

---

## Path A — Minute 2–4: fill in the three slots and send

Open your AI tool of choice — GitHub Copilot agent mode, Claude Projects, a GPT-4o assistant, or any system that accepts a long system prompt. Paste the copied block as the system or first-user message.

Fill in the three `FILL_ME` values before sending:

```
FORMATION=2x4          # 2 waves × 4 agents = 8 total reviewers
TARGET=<paste PR diff or document text here>
TIER_MIX=all-frontier  # or: multi-tier
```

`2x4` is the recommended starting point. Wave 1 finds issues. Wave 2 sees Wave 1's output and either disputes or builds on it. That sequential structure is why you get more signal than a single call.

Send the prompt. The model will spawn subagents internally and stream back JSONL lines — one per agent, one summary at the end.

**No API key required on your end.** The model you pasted into handles the calls. If you want to run this headlessly (without a chat UI), any OpenAI-compatible endpoint works — see `PROMPT.md`'s Appendix for environment setup.

---

## Minute 4–6: save and read the output

Copy the JSONL lines out of the chat response and save them:

```bash
# paste the JSONL lines into a file
cat > run_001.jsonl   # paste, then Ctrl-D
```

Each line is one agent's review:

```bash
head -3 run_001.jsonl
```

You'll see fields like `agent`, `role`, `wave`, `claim`, and `evidence.location`. The `evidence.location` field should cite a file path and line number (e.g., `src/db.py:87`) or a direct quote from your target text. If it's a vague assertion with no citation, that's a finding worth flagging.

---

## Minute 6–8: verify the chain and run the reward-hack check

Two scripts ship in this repo. Both are stdlib-only Python — no install needed.

**Verify the HMAC chain** (confirms nothing was edited after the fact):

```bash
python3 hmac_verifier.py run_001.jsonl
```

Exit 0 means the chain is intact. Exit 1 prints the specific row that broke the link. The default key matches the key baked into the template; if you rotated `HMAC_KEY` in the parent prompt, pass it:

```bash
CHAIN_HMAC_KEY=your-key python3 hmac_verifier.py run_001.jsonl
```

**Check for reward hacks** (catches agents claiming consensus they didn't earn, fake HMAC values, missing citations, etc.):

```bash
python3 reward_hack_detector.py run_001.jsonl
```

Exit 0 means no patterns triggered. Non-zero exit prints exactly which rows triggered which pattern and why. The patterns are named (e.g., `citation-missing`, `fake-hmac`) so you can trace the failure to a specific agent and wave.

---

## Minute 8–9: try a heavier formation or a lighter one

You decide how much to spend:

| Formation | Agents | Typical compute time | When to use |
|-----------|--------|---------------------|-------------|
| `1x4`     | 4      | ~30s                | Quick sanity check |
| `2x4`     | 8      | ~60s                | **Recommended start** |
| `4x8`     | 32     | ~4–5 min            | Sustained adversarial review |
| `8x8`     | 64     | ~10+ min            | Heavy red-team; burns session limits on most plans |

Change `FORMATION=2x4` to whatever fits your task and paste again. The JSONL schema is identical across formations — your downstream tooling doesn't need to change.

---

## Minute 9–10: decide what to do next

Three forks:

- **Just want the receipt log?** You're done. JSONL is portable. Import it into your own pipeline, grep it, or open it in any JSON viewer.
- **Want tamper-evidence with stronger durability guarantees?** See `UPGRADE_TO_POSTGRES.md` — adds a Postgres + XTDB bitemporal mirror so receipts survive beyond a single file.
- **Want to change the agent roles?** Edit `FORMATION` and `TIER_MIX` in the parent prompt, or fork the subagent template and assign different roles. The role rotation list is in `PROMPT.md` — security, logic, style, performance, completeness, consistency, edge-cases, integration.

---

## What this isn't

- **Not a model.** The reviewers are whatever LLM you pasted the prompt into. Quality depends on that model and your target text. A vague or large target produces vague findings.
- **Not a guarantee.** The HMAC chain catches tampering after the fact, not before. If the model never computed a real HMAC (it emitted `NO_HMAC`), the chain has a gap — the verifier will flag it.
- **Not a replacement for human review.** Treat the output as triage. Cite specific agent findings with their `evidence.location`. Do not quote the agents as authority.
- **Not free-tier-stable.** Free-tier rate limits change. If a formation times out or a vendor goes unreachable mid-run, you'll get a partial JSONL. The verifier handles partial files — it reports how many rows verified and where the chain broke.

---

## Glossary

- **JSONL**: one JSON object per line in a file. Each line is one agent's receipt.
- **HMAC**: a cryptographic signature computed from the receipt content and a shared key. The chain links each receipt to the previous one — tamper a row and the next row's `prev_sha16` stops matching.
- **Wave**: a batch of agents called in parallel from one parent prompt. Wave 2 sees Wave 1's output before starting.
- **2x4**: 2 waves × 4 agents per wave = 8 total agents. The first number is waves; the second is agents per wave.
- **Reward hack**: a pattern where an agent produces output that looks correct without doing the actual work — e.g., claiming a file:line citation without quoting anything real, or asserting consensus that no prior receipt supports.
- **`verb: PASS`**: an agent found nothing in its role scope. A legitimate result; not a failure.

---

## Path B — Programmatic CLI driver

If you want the JSONL emitted to disk automatically (so `hmac_verifier.py` and `reward_hack_detector.py` can run unattended), use the included `run_wave.py` driver instead of pasting:

```bash
# Setup (one time, ~1 min)
cp .env.example .env                 # fill ONE vendor key (OpenRouter is easiest free tier)
pip install requests                 # only non-stdlib dep

# Run with default 2x2 profile
python3 run_wave.py --config simple_trio --target "<your PR diff or task>"

# Output lands in ./run_<ts>.jsonl
# Verify integrity:
python3 hmac_verifier.py run_<ts>.jsonl

# Check for reward-hacks:
python3 reward_hack_detector.py run_<ts>.jsonl
```

Profiles available (auto-discovered from `profiles/*.json`):
- `simple_trio` — 2 waves × 2 agents = 4 reviewers (default; recommended start)
- `standard_4x4` — 4 waves × 4 agents = 16 reviewers (SPIN cycle)
- `defense_in_depth_8x8` — 8 waves × 8 agents = 64 reviewers (heavy; may exceed session limits)

Add `--dry-run` to see the plan without making API calls.

**MCP variant**: if you use Claude Desktop / VSCode-MCP, the `mcp/wave_runner_server.py` exposes `run_wave`, `verify_chain`, `detect_reward_hacks`, and `list_profiles` as MCP tools. See `README.md` for the 30-second install snippet.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Model returns prose instead of JSONL | System prompt wasn't set as the first message | Move the template block to the system/context slot, not the user message |
| `HMAC mismatch` on every row | Writer key and verifier key differ | Check `HMAC_KEY` in the parent prompt matches `CHAIN_HMAC_KEY` env var |
| `prev_sha16_mismatch` on row 2 | Agent skipped a receipt or mis-ordered output | Check for missing rows; re-run with a fresh file |
| Many `CITATION-MISSING` flags | Model made capability claims without citing receipts | This is the detector doing its job — review those rows manually |
| `NO_HMAC` in `this_sha16` field | Model couldn't compute HMAC (common on constrained hosts) | Expected behavior; verifier flags it; not a chain break |
| Empty or very short output | Target text was too large or too vague | Split the target into smaller chunks; use `1x4` formation first |

---

## Self-redteam: what a skeptical 10-minute trial user will complain about

The workflow depends on the model executing the parent prompt faithfully. A model that shortcuts — skipping waves, faking HMAC values, reusing the same claim across agents — produces a JSONL that looks complete but isn't. The reward-hack detector catches several of these patterns, but not all of them. A model can produce syntactically valid, HMAC-correct JSONL with substantively empty findings and the tooling will exit 0. The only real check is reading the `claim` and `evidence.detail` fields yourself and asking whether they describe something real in your target text. The tooling is a floor, not a ceiling. Your judgment is still required.

---

## Try it now

```
1. Copy the ORCHESTRATOR SYSTEM PROMPT block from PROMPT.md
2. Open your AI tool
3. Paste as system message; fill FORMATION=2x4 and TARGET=<your text>
4. Send
5. Save the JSONL lines to run_001.jsonl
6. python3 hmac_verifier.py run_001.jsonl
7. python3 reward_hack_detector.py run_001.jsonl
```
