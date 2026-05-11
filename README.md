# Public-mirror repo skeleton (T0.HN2)

**Job**: the one-paste working demo. A non-technical reader pastes the markdown into Copilot in <10 minutes and gets a real signed log out.
**Posture**: thin slice. The gift, not the architecture.

---

## What this is

A markdown prompt for GitHub Copilot that:

1. Takes one premium request (the parent call) and fans out to N subagent reviewers
2. Each reviewer critiques the same target (a PR diff, a file, a design doc)
3. Their outputs are written to an HMAC-signed JSONL file you can audit later

That's it. One file. MIT-licensed. Try it on a real pull request.

---

## How to use it in 60 seconds

```
1. Clone this repo
2. Copy `.env.example` to `.env` and fill in your HMAC key (any 32-char random string)
3. Open GitHub Copilot's coding-agent surface on a PR
4. Paste the contents of `prompts/quorum_review.md` as the parent message
5. Watch the subagents run inside the parent session
6. Check `runs/<timestamp>/chain.jsonl` for the signed log
```

A worked example with real timestamps, agent count, and a signature line lives in `examples/2026-05-12_real_pr/`.

---

## What it doesn't do

- It does **not** guarantee fanout will stay free. Copilot policy can change.
- It does **not** save you from a broken pipeline; it surfaces quorum-style misses.
- It does **not** include the orchestrator, the vendor-mesh telemetry, the CI/CD harness, the production-line discipline, or the prompt-evolution loop. Those are not in this repo.
- It does **not** promise you'll see any specific % improvement. Measure on your own work.

If hundreds of agents start thunder-herding your infrastructure, that's the moment to reach out (see below).

---

## Files in this repo (thin slice)

```
prompts/quorum_review.md         # the parent-call prompt
.env.example                     # paste-and-fill template (FCA highest-leverage)
runs/.gitkeep                    # subagents write here
examples/2026-05-12_real_pr/     # one real run with timestamp + signature
scripts/verify_chain.py          # walk the HMAC chain; flag any break
LICENSE                          # MIT
```

---

## License

MIT. Use it, fork it, ship it. Attribution appreciated but not required.

---

## Contact

If your AI/agent infrastructure starts breaking under swarm load (and it will, eventually), reach out:

`<pre-publish: discovery-call form URL or contact email>`

I'm available for 72-hour audits, hardening sprints, and retainer engagements. Design-partner cohort open for first 5 teams at half-price.

---

## MCP server — Claude Desktop / Cursor / VSCode

Use the tools in this repo directly from any MCP-aware client without opening a terminal.

### 30-second install

**Step 1.** Install the MCP Python SDK (one-time, any Python 3.10+):

```bash
pip install mcp
```

**Step 2.** Add this block to your Claude Desktop `claude_desktop_config.json`
(location: `~/Library/Application Support/Claude/` on macOS, `%APPDATA%\Claude\` on Windows):

```json
{
  "mcpServers": {
    "wave_runner": {
      "command": "python3",
      "args": ["/path/to/public_mirror_staging/mcp/wave_runner_server.py"]
    }
  }
}
```

Replace `/path/to/public_mirror_staging` with the actual path where you cloned this repo.
Restart Claude Desktop after editing. The four tools appear automatically in the tool picker.

### Tools exposed

| Tool | Args | What it does |
|---|---|---|
| `run_wave` | `config` (path), `target` (str), `vendor?` (str) | Runs a wave; returns summary JSON |
| `verify_chain` | `jsonl_path` (path) | Checks HMAC chain integrity; returns pass/fail |
| `detect_reward_hacks` | `jsonl_path` (path) | Scans a log for reward-hacking patterns |
| `list_profiles` | none | Lists available profile JSONs in `profiles/` |

Every invocation is appended to `mcp/tool_audit.jsonl` (local, unencrypted operational trace).

### Verify the server works before connecting a client

```bash
python3 mcp/wave_runner_server.py --test
# Expected output ends with: All tests PASS. Confidence: 7/8 (no quorum certificate).
```

### Known limits

- `run_wave`, `verify_chain`, `detect_reward_hacks` invoke local Python scripts via subprocess.
  If those scripts are not present, the tool returns a non-zero `returncode` with an error message — it does not crash the server.
- The audit log at `mcp/tool_audit.jsonl` is not HMAC-signed. It is an operational trace, not a cryptographic receipt.
- The MCP SDK is pre-1.0. Pin the version in `requirements.txt` (`mcp==1.x.y`) to avoid breaking API changes.

---

## Skeleton pre-publish checklist

- [ ] `prompts/quorum_review.md` works end-to-end on a fresh Copilot session
- [ ] `.env.example` is at repo root (FCA highest-leverage)
- [ ] `examples/2026-05-12_real_pr/` contains a real run with non-fake timestamp + signature
- [ ] `scripts/verify_chain.py` walks the example chain successfully
- [ ] LICENSE file present and matches "MIT" claim
- [ ] No internal vocabulary leakage (internal codenames stripped)
- [ ] No private filesystem paths leaked
- [ ] Discovery-call form URL works
- [ ] T1-T3 fresh-substrate paste test passes (Claude / ChatGPT / Copilot all complete <2 min)

---


---

## Mirrors

- **GitHub (primary)**: https://github.com/obsidian-spider-org/obsidian-spider-quickstart
- **Codeberg (backup)**: https://codeberg.org/ttaogaming/obsidian-spider-quickstart

Both mirrors track `main`. CI runs on GitHub via `.github/workflows/test.yml` (smoke: `run_wave.py --test`).

## Built by

**Dev**: Obsidian_Spider — 16 months building large LLM swarms; specializes in red-team audit of multi-tier cost-aware orchestration.

**Cybernetic-unit**: Sigrún + 8 Valkyries — the agent lattice that authored this repo through cross-substrate dispatch (Claude Code Opus + Sonnet + Copilot GPT-5.5 + free-vendor mesh). Roles: Hrist (OBSERVE), Mist (BRIDGE), Thrud (SHAPE), Hildr (INJECT), Skǫgul (DISRUPT/red-team), Eir (IMMUNIZE/defense-in-depth), Gondul (ASSIMILATE), Reginleif (NAVIGATE).

Each agent has a focused cognitive stance and signs every receipt with HMAC. The full architecture stays internal; this repo is the public thin slice — see `GIFT_AND_OFFER.md`.

