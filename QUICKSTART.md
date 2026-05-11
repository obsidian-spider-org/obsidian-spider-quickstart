---
title: "10-Minute Quickstart"
confidence: "7/8 (no quorum certificate)"
---

# 10-Minute Quickstart

## What you'll have after 10 minutes

A JSONL audit trail of N subagents independently processing the same input from different angles, plus one synthesis line where the parent gathers them. Each line is one subagent's signed receipt. Two included scripts verify the cryptographic chain and flag common reward-hacking patterns.

**Multi-platform.** The prompt works on:

- **GitHub Copilot Pro+** — current pricing window; one parent premium request fans out to many subagents inside the same message
- **Free vendor mesh** — OpenRouter / Groq / Together / Cerebras with backoff/retry/durable-workflow wrapper
- **Claude Code** — Agent tool subagents
- **Anywhere a parent agent can launch subagents** — the cost-tier routing is the load-bearing value-prop, not vendor-specific

This is a general-purpose scatter-gather: code review is one example; so are batch image-prompt generation, markdown drafting, refactor exploration, decision rooms, schema design, A/B copy, and test-case brainstorming. The prompt template stays the same; only your TARGET and GATHER_INSTRUCTION change.

### What is cost-aware routing?

One parent call dispatches N subagents inside the same message. Each subagent is routed to the cheapest model that does the job — cheap reasoning tier for "read this file, extract these names, run this small check," and a frontier model only for the final synthesis pass that gathers everything. Multi-tier cost awareness yields much better $/token than running a frontier model on every step; the routing-LLM literature (RouteLLM, Aviary, Mixture of Agents) benchmarks this pattern and finds it consistently better than frontier-on-everything by a comfortable margin. The exact multiplier depends on your task mix and which baseline you're comparing against.

---

## Minute 1–2: get the template

Clone or download this repo. The only file you need right now is `PROMPT.md`.

```bash
git clone <this-repo-url>
cd <repo-name>
```

Open `PROMPT.md` and copy the block that starts with `## ORCHESTRATOR SYSTEM PROMPT`. That block is the parent-prompt template. It has three `FILL_ME` slots: FORMATION, TARGET, and TIER_MIX. (GATHER_INSTRUCTION goes inside TARGET — see examples below.)

---

## Two paths from here

**Path A — Zero-install (paste-into-Claude/Copilot)**: continue reading below. Fastest; ~3 min.

**Path B — Programmatic (CLI driver)**: skip ahead to "Path B" section near the end of this doc. Requires Python 3.10+ + one API key in `.env` + `pip install requests`. Best if you want JSONL auto-emitted to disk for verification by `hmac_verifier.py` / `reward_hack_detector.py` without copy-paste. ~5 min.

---

## Path A — Minute 2–4: fill in the three slots and send

Open your AI tool of choice — GitHub Copilot agent mode, Claude Projects, a GPT-4o assistant, or any system that accepts a long system prompt. Paste the copied block as the system or first-user message.

Fill in the three `FILL_ME` values before sending:

```
FORMATION=2x4          # 2 waves × 4 subagents = 8 total perspectives
TARGET=<your input + a gather instruction; see examples below>
TIER_MIX=all-frontier  # or: multi-tier
```

`2x4` is the recommended starting point. Wave 1 produces N perspectives. Wave 2 sees Wave 1's output and either disputes, refines, or builds on it. That sequential structure is why you get more signal than a single call.

Send the prompt. The model will spawn subagents internally and stream back JSONL lines — one per subagent, one summary at the end.

**No API key required on your end.** The model you pasted into handles the calls. If you want to run this headlessly (without a chat UI), any OpenAI-compatible endpoint works — see `PROMPT.md`'s Appendix for environment setup.

---

## Example TARGETs (showing variety)

The same prompt template handles all of these. The only thing that changes is what you put in `TARGET` and what gather you ask for.

### Example 1 — Fan-out PR review

```
TARGET=Review the following PR diff. Each subagent: pick a different role
(security, logic, style, performance, completeness, consistency, edge-cases,
integration) and find <=3 issues with file:line citations. Gather: produce
one merged review ordered by severity, dedup-ed across waves.

<paste PR diff here>
```

### Example 2 — Fan-out batch image-prompt generation

```
TARGET=Generate 8 alt-art prompt variations for a product page hero image.
Each subagent: pick a different visual stance (minimalist, maximalist,
photoreal, illustrative, isometric, monochrome, retro, futuristic) and
produce one image-generation prompt with a one-sentence rationale.
Gather: a comparison sheet ranking by suitability for an e-commerce hero.

<product description + brand constraints here>
```

### Example 3 — Fan-out markdown drafting

```
TARGET=Draft 8 different intro paragraphs for the blog post described below.
Each subagent: pick a different opening rhetorical move (anecdote, statistic,
contrarian claim, question, scene, definition, analogy, direct address) and
write ~120 words. Gather: pick the best three with one-sentence rationale
each; flag any that buried the lede.

<blog post outline + target audience here>
```

### Example 4 — Fan-out code-change exploration

```
TARGET=Propose 8 different refactor strategies for the function below.
Each subagent: pick a different optimization axis (readability, performance,
testability, type-safety, error-handling, API surface, dependency reduction,
state-machine clarity) and propose one refactor with a code sketch and
tradeoff note. Gather: a tradeoff matrix and one recommended strategy with
reasoning.

<function source here>
```

### Example 5 — Fan-out decision room

```
TARGET=Analyze the decision below from 8 stance-driven angles. Each subagent:
pick a different stance (proponent, skeptic, cost-cutter, growth-maximizer,
risk-officer, customer-voice, ops-reality, long-horizon) and produce a
one-paragraph analysis + a recommended vote (proceed / hold / oppose).
Gather: a quorum verdict with vote tally and dissent summary.

<decision context + options here>
```

### Example 6 — Fan-out test generation

```
TARGET=Generate 8 test-case ideas for the function below. Each subagent:
pick a different test-design axis (happy path, boundary, adversarial input,
concurrency, error path, performance, integration, regression). For each:
one test name + one-sentence setup + expected assertion. Gather: a
consolidated test plan with priority order.

<function source + existing tests here>
```

The pattern is the same every time: scatter on a different axis per subagent, gather according to the synthesis you actually want.

---

## Minute 4–6: save and read the output

Copy the JSONL lines out of the chat response and save them:

```bash
# paste the JSONL lines into a file
cat > run_001.jsonl   # paste, then Ctrl-D
```

Each line is one subagent's output:

```bash
head -3 run_001.jsonl
```

You'll see fields like `agent`, `role`, `wave`, `claim`, and `evidence.location`. For review-style tasks, `evidence.location` should cite a file path and line number (e.g., `src/db.py:87`) or a direct quote. For generative tasks (drafts, image prompts, schema proposals), it carries the generated artifact and a one-line rationale. If it's a vague assertion with no anchor, that's a finding worth flagging.

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

**Check for reward hacks** (catches subagents claiming consensus they didn't earn, fake HMAC values, missing citations, near-duplicate outputs across agents, etc.):

```bash
python3 reward_hack_detector.py run_001.jsonl
```

Exit 0 means no patterns triggered. Non-zero exit prints exactly which rows triggered which pattern and why. The patterns are named (e.g., `citation-missing`, `fake-hmac`, `copy-paste-quorum`) so you can trace the failure to a specific subagent and wave.

---

## Minute 8–9: try a heavier formation or a lighter one

You decide how much to spend:

| Formation | Subagents | Typical compute time | When to use |
|-----------|-----------|---------------------|-------------|
| `1x4`     | 4         | ~30s                | Quick sanity check |
| `2x4`     | 8         | ~60s                | **Recommended start** |
| `4x8`     | 32        | ~4–5 min            | Sustained scatter |
| `8x8`     | 64        | ~10+ min            | Heavy run; burns session limits on most plans |

Change `FORMATION=2x4` to whatever fits your task and paste again. The JSONL schema is identical across formations — your downstream tooling doesn't need to change.

---

## Minute 9–10: decide what to do next

Three forks:

- **Just want the receipt log?** You're done. JSONL is portable. Import it into your own pipeline, grep it, or open it in any JSON viewer.
- **Want tamper-evidence with stronger durability guarantees?** See `UPGRADE_TO_POSTGRES.md` — adds a Postgres + XTDB bitemporal mirror so receipts survive beyond a single file.
- **Want to change the subagent roles?** Edit `FORMATION` and `TIER_MIX` in the parent prompt, or fork the subagent template and assign different roles. The role rotation list is in `PROMPT.md` — pick whatever axes make sense for your use case.

---

## What this isn't

- **Not a model.** The subagents are whatever LLM you pasted the prompt into. Quality depends on that model and your input. A vague or very large input produces vague outputs.
- **Not a guarantee.** The HMAC chain catches tampering after the fact, not before. If the model never computed a real HMAC (it emitted `NO_HMAC`), the chain has a gap — the verifier will flag it.
- **Not a replacement for human judgment.** Treat the output as triage. Cite specific subagent findings with their `evidence.location` or generated artifact. Do not quote the subagents as authority.
- **Not free-tier-stable.** Free-tier rate limits change. If a formation times out or a vendor goes unreachable mid-run, you'll get a partial JSONL. The verifier handles partial files — it reports how many rows verified and where the chain broke.

---

## Glossary

- **JSONL**: one JSON object per line in a file. Each line is one subagent's receipt.
- **HMAC**: a cryptographic signature computed from the receipt content and a shared key. The chain links each receipt to the previous one — tamper a row and the next row's `prev_sha16` stops matching.
- **Wave**: a batch of subagents called in parallel from one parent prompt. Wave 2 sees Wave 1's output before starting.
- **Scatter-gather**: fan out N subagents on different axes, then gather their outputs into one synthesis.
- **2x4**: 2 waves × 4 subagents per wave = 8 total subagents. The first number is waves; the second is subagents per wave.
- **Reward hack**: a pattern where a subagent produces output that looks correct without doing the actual work — e.g., claiming a file:line citation without quoting anything real, or asserting consensus that no prior receipt supports.
- **`verb: PASS`**: a subagent found nothing in its scope (or has nothing to add). A legitimate result; not a failure.

---

## Path B — Programmatic CLI driver

If you want the JSONL emitted to disk automatically (so `hmac_verifier.py` and `reward_hack_detector.py` can run unattended), use the included `run_wave.py` driver instead of pasting:

```bash
# Setup (one time, ~1 min)
cp .env.example .env                 # fill ONE vendor key (OpenRouter is easiest free tier)
pip install requests                 # only non-stdlib dep

# Run with default 2x2 profile
python3 run_wave.py --config 2x2 --target "<your input + gather instruction>"

# Output lands in ./run_<ts>.jsonl
# Verify integrity:
python3 hmac_verifier.py run_<ts>.jsonl

# Check for reward-hacks:
python3 reward_hack_detector.py run_<ts>.jsonl
```

Profiles available (auto-discovered from `profiles/*.json`):
- `2x2` — 2 waves × 2 subagents = 4 outputs (default; recommended start)
- `4x4` — 4 waves × 4 subagents = 16 outputs (SPIN cycle)
- `8x8` — 8 waves × 8 subagents = 64 outputs (heavy; may exceed session limits)

Add `--dry-run` to see the plan without making API calls.

**MCP variant**: if you use Claude Desktop / VSCode-MCP, the `mcp/wave_runner_server.py` exposes `run_wave`, `verify_chain`, `detect_reward_hacks`, and `list_profiles` as MCP tools. See `README.md` for the 30-second install snippet.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Model returns prose instead of JSONL | System prompt wasn't set as the first message | Move the template block to the system/context slot, not the user message |
| `HMAC mismatch` on every row | Writer key and verifier key differ | Check `HMAC_KEY` in the parent prompt matches `CHAIN_HMAC_KEY` env var |
| `prev_sha16_mismatch` on row 2 | Subagent skipped a receipt or mis-ordered output | Check for missing rows; re-run with a fresh file |
| Many `CITATION-MISSING` flags | Model made capability claims without citing receipts | This is the detector doing its job — review those rows manually |
| `NO_HMAC` in `this_sha16` field | Model couldn't compute HMAC (common on constrained hosts) | Expected behavior; verifier flags it; not a chain break |
| Empty or very short output | Input was too large or too vague | Split the input into smaller chunks; use `1x4` formation first |
| All 8 subagents produce near-identical outputs | Scatter axis wasn't specified per agent | Add an explicit per-agent stance/role list to your TARGET |

---

## Self-redteam: what a skeptical 10-minute trial user will complain about

The workflow depends on the model executing the parent prompt faithfully. A model that shortcuts — skipping waves, faking HMAC values, reusing the same claim across subagents — produces a JSONL that looks complete but isn't. The reward-hack detector catches several of these patterns, but not all of them. A model can produce syntactically valid, HMAC-correct JSONL with substantively empty findings and the tooling will exit 0. The only real check is reading the `claim` and `evidence.detail` (or the generated artifact) yourself and asking whether it describes something real about your input. The tooling is a floor, not a ceiling. Your judgment is still required.

---

## Try it now

```
1. Copy the ORCHESTRATOR SYSTEM PROMPT block from PROMPT.md
2. Open your AI tool
3. Paste as system message; fill FORMATION=2x4 and TARGET=<your input + gather instruction>
4. Send
5. Save the JSONL lines to run_001.jsonl
6. python3 hmac_verifier.py run_001.jsonl
7. python3 reward_hack_detector.py run_001.jsonl
```
