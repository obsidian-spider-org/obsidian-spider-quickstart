---
title: "obsidian-spider-quickstart"
date: 2026-05-11
confidence: "7/8 (no quorum certificate)"
---

# obsidian-spider-quickstart

> Cost-aware routing swarm for LLMs: one parent call dispatches N subagents, each routed to the cheapest model that does the job, and one synthesis pass gathers them. Signed-log audit. Multi-platform.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Built with Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![MCP-compatible](https://img.shields.io/badge/MCP-compatible-purple)](https://modelcontextprotocol.io/)
[![GitHub mirror](https://img.shields.io/badge/GitHub-obsidian--spider--org-181717?logo=github)](https://github.com/obsidian-spider-org/obsidian-spider-quickstart)

I built a markdown prompt that implements a cost-aware routing swarm: one parent call dispatches N independent subagents, each producing one perspective on whatever input you hand it, and the parent gathers them into a single synthesis. Cheap models handle cheap work; frontier models only run the synthesis pass. Every subagent's output is written to an HMAC-signed JSONL log you can audit later. Two stdlib-only Python helpers verify the cryptographic chain and flag common reward-hacking patterns. MIT-licensed, no telemetry.

**Multi-platform.** The pattern works on any host where a parent agent can launch subagents:

- **GitHub Copilot Pro+** — the current pricing window; one parent premium request fans out to many subagents inside the same message (highest leverage)
- **Free vendor mesh** — OpenRouter / Groq / Together / Cerebras free tiers, with backoff/retry/durable-workflow wrapper
- **Claude Code** — Agent tool subagents
- **Anywhere a parent agent can launch subagents** — the cost-tier routing is the load-bearing value-prop, not any one vendor

The pattern is general across use cases too. Code review is one example; so are batch image-prompt generation, markdown drafting variants, decision-room quorums, refactor exploration, schema design, A/B copy generation, and test-case brainstorming. You decide what to fan out and what to gather.

---

## Use cases at a glance

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

The prompt template doesn't hardcode any one use case. You write what you want fanned out and how you want it gathered.

---

## Quick Start

```
1. git clone https://github.com/obsidian-spider-org/obsidian-spider-quickstart
2. cp .env.example .env   # then fill in any 32-char random string for HMAC_KEY
3. Open GitHub Copilot's coding-agent surface (or Claude, or GPT-4o)
4. Paste the contents of PROMPT.md as the parent message
5. Fill FORMATION + TARGET (your input) + GATHER_INSTRUCTION (what synthesis to produce)
6. Read the signed log at the path run_wave.py prints (./run_<ts>.jsonl by default)
```

A sample run output lives at `examples/sample_1x4_pr_review.jsonl` — pass it through `python3 hmac_verifier.py examples/sample_1x4_pr_review.jsonl` to see chain verification on real data.

---

## What you get after 10 minutes

- A JSONL audit trail of N subagents independently working on the same input from different angles
- HMAC-signed receipts you can re-verify later with one stdlib Python script
- One parent call fans out to N subagents inside the same message, which on Copilot Pro+ today runs an order of magnitude or two cheaper than the same work as raw API calls. The measured ratio sits around 100x to 1000x depending on which frontier model you'd otherwise pay for; **measure your own** with the calculator and four worked examples in [`docs/COST_MODEL.md`](docs/COST_MODEL.md)
- A reward-hack pattern detector that flags common LLM failure modes (consensus theater, citation-shape gaming, mode-drift)
- Three profile sizes to pick from (2x2 demo, 4x4 recommended-start, 8x8 stress-test) — see `profiles/`
- An optional MCP server stub for Claude Desktop, Cursor, and VSCode-MCP clients

To be clear about pricing: the parent call is fully paid premium (Copilot Pro+ at $39/mo plus the premium-request multiplier — ~$0.30 per call on GPT-5.5 at 7.5×). The savings ratio is paid-parent vs same-work-as-raw-API, not parent-vs-nothing. GitHub announced [usage-based Copilot billing effective June 1, 2026](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/); the current Copilot subagent pricing window is closing — measure your own savings before then. The pattern keeps working after the transition on Copilot, on free vendor mesh, and on Claude Code — the cost-savings multiplier compresses on Copilot, the routing pattern does not. See [GIFT_AND_OFFER.md](GIFT_AND_OFFER.md) for paid tiers (audits, hardening sprints, retainers).

---

## What it doesn't do

- The cost-savings number is a ratio, not an absolute. If you weren't going to pay for raw API anyway, you aren't "saving" anything — measure your own with the calculator
- Inside-parent-message subagent counting on Copilot is current pricing-window behavior; multipliers and behaviors shift with [GitHub's June 1, 2026 billing transition](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/)
- It surfaces quorum-style misses; it does not fix a broken pipeline for you
- It does not include the orchestrator, vendor-mesh telemetry, CI/CD harness, or prompt-evolution loop — those stay internal
- It does not promise any specific quality improvement; measure on your own work

---

## Files in this repo

```
PROMPT.md                        # the parent-call prompt template (use-case-agnostic)
.env.example                     # rename to .env and fill in your HMAC key
profiles/                        # 2x2, 4x4, 8x8 wave configurations + critic_lite_example.md
examples/sample_1x4_pr_review.jsonl  # a sample run output you can verify
run_wave.py                      # programmatic CLI driver; writes ./run_<ts>.jsonl
hmac_verifier.py                 # stdlib chain integrity check (the chain verifier)
reward_hack_detector.py          # pattern scan for common LLM failure modes
mcp/                             # MCP server stub (optional)
docs/COST_MODEL.md               # the math behind the 100x–1000x range + calculator
LICENSE                          # MIT
```

---

## Profiles

Pick the profile that matches your scope. Most projects stay at `2x2` and never need to climb. `Subagent` is generic — it's whatever you ask each agent to do (review, draft, propose, generate, critique, etc.).

| Profile | Waves × Subagents | Total | When to use |
|---|---|---|---|
| `2x2` | 2 waves, 2 subagents | 4 calls | Solo run; fastest path |
| `4x4` | 4 waves, 4 subagents | 16 calls | Recommended start; refinement built in |
| `8x8` | 8 waves, 8 subagents | 64 calls | Stress test; free-tier rate-limit risk; burns context fast |

Profile JSONs live in `profiles/`. Default config in `QUICKSTART.md` uses `2x2`.

---

## MCP server (optional)

Use the tools in this repo from any MCP-aware client without opening a terminal.

```bash
pip install mcp
```

Add this block to your Claude Desktop `claude_desktop_config.json` (location: `~/Library/Application Support/Claude/` on macOS, `%APPDATA%\Claude\` on Windows):

```json
{
  "mcpServers": {
    "wave_runner": {
      "command": "python3",
      "args": ["/path/to/obsidian-spider-quickstart/mcp/wave_runner_server.py"]
    }
  }
}
```

Restart Claude Desktop. The four tools (`run_wave`, `verify_chain`, `detect_reward_hacks`, `list_profiles`) appear in the tool picker.

Verify the server works before connecting a client:

```bash
python3 mcp/wave_runner_server.py --test
```

Known limits: the MCP audit log at `mcp/tool_audit.jsonl` is an operational trace, not a cryptographic receipt. Pin the SDK version in `requirements.txt` (`mcp==1.x.y`) to avoid pre-1.0 API churn.

---

## Upgrade paths

- `CAPACITY_LADDER.md` — when you outgrow JSONL, what to climb to next (Postgres, bitemporal mirror, RFC 3161 timestamps, multi-vendor BFT quorum)
- `BOOTSTRAP_NOTE.md` — what "BFT consensus" actually means at each rung; honest about the limits of single-substrate scatter-gather
- `UPGRADE_TO_POSTGRES.md` — the 5-minute path from one JSONL file to a real database

---

## License

MIT — free, no strings, no attribution required (attribution welcome but not required).

---

## Mirrors

- **GitHub (primary)**: https://github.com/obsidian-spider-org/obsidian-spider-quickstart

Both mirrors track `main`. CI runs on GitHub via `.github/workflows/test.yml` (smoke: `run_wave.py --test`).

---

## Built by

Built by Obsidian_Spider — 16 months building multi-agent LLM swarms.

For the framing around what's gift and what's paid offer, see [GIFT_AND_OFFER.md](GIFT_AND_OFFER.md).

---

## Contact

General questions: `contact@obsidianspider.org` · Paid work: `audit@obsidianspider.org` · Or [open a GitHub issue](https://github.com/obsidian-spider-org/obsidian-spider-quickstart/issues).

See [GIFT_AND_OFFER.md](GIFT_AND_OFFER.md) for the engagement ladder and refund terms.
