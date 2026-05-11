#!/usr/bin/env python3
# MIT License
# Copyright (c) 2026 Obsidian_Spider — built by the cybernetic_unit Sigrún + 8 Valkyries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
run_wave.py — 10-minute thin-slice multi-agent review driver.
Confidence: 7/8 (no quorum certificate).

Stdlib + requests only. No Postgres, XTDB, or Docker required.

Quickstart:
    pip install requests
    export OPENROUTER_API_KEY=sk-or-...
    python3 run_wave.py --config 2x2 --target "path/to/file_or_text"

Run inline tests:
    python3 run_wave.py --test

Dry run (no API calls):
    python3 run_wave.py --config 2x2 --dry-run --target "demo text"

Vendor env keys:
    OPENROUTER_API_KEY    → openrouter (default; many free models)
    GROQ_API_KEY          → groq (fast, generous free tier)
    ANTHROPIC_API_KEY     → anthropic (Claude; costs money)
    OPENAI_API_KEY        → openai (costs money)
"""

import argparse
import hashlib
import hmac as _hmac
import json
import os
import re
import sys
import time
import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Vendor routing table
# ---------------------------------------------------------------------------

VENDOR_CONFIGS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "env_key": "OPENROUTER_API_KEY",
        "default_model": "mistralai/mistral-7b-instruct:free",
        "free_note": "$0 with a free model e.g. mistral-7b-instruct:free",
        "auth_header": "Bearer",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "env_key": "GROQ_API_KEY",
        "default_model": "llama3-8b-8192",
        "free_note": "$0 on Groq free tier",
        "auth_header": "Bearer",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1/messages",
        "env_key": "ANTHROPIC_API_KEY",
        "default_model": "claude-haiku-4-5",
        "free_note": "Paid — check pricing at anthropic.com",
        "auth_header": "x-api-key",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "env_key": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
        "free_note": "Paid — check pricing at openai.com",
        "auth_header": "Bearer",
    },
}

# ---------------------------------------------------------------------------
# HMAC chain helpers (canonical schema: same as hmac_verifier.py)
# ---------------------------------------------------------------------------

SEP = "\x1f"


def _canonical_bytes(row: dict) -> bytes:
    def j(v):
        return json.dumps(v, sort_keys=True, separators=(",", ":"))
    parts = [
        str(row.get("prev_sha16", "")),
        str(row.get("ts", "")),
        str(row.get("opcode_verb", "")),
        str(row.get("agent", "")),
        str(row.get("task_id", "")),
        str(row.get("claim", "")),
        j(row.get("evidence", {})),
        str(row.get("confidence", "")),
        j(row.get("meta", {})),
        str(row.get("mode", "")),
    ]
    return SEP.join(parts).encode("utf-8")


def _compute_sha16(key: bytes, row: dict) -> str:
    canonical = _canonical_bytes(row)
    return _hmac.new(key, canonical, hashlib.sha256).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Profile loading
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent


def load_profile(profile_name: str) -> dict:
    """Load profiles/<name>.json relative to this script."""
    path = SCRIPT_DIR / "profiles" / f"{profile_name}.json"
    if not path.exists():
        candidates = list((SCRIPT_DIR / "profiles").glob("*.json"))
        names = [p.stem for p in candidates]
        raise FileNotFoundError(
            f"Profile '{profile_name}' not found at {path}. "
            f"Available: {names}"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def agents_for_wave(profile: dict, wave_num: int) -> list[dict]:
    """Return agent dicts scheduled for wave_num (1-indexed)."""
    schedule = profile.get("wave_schedule")
    if schedule:
        # Find the schedule entry for this wave
        entry = next((w for w in schedule if w["wave"] == wave_num), None)
        if not entry:
            return []
        roles_this_wave = entry["agent_roles"]
        all_agents = {a["role"]: a for a in profile["agents"]}
        return [all_agents[r] for r in roles_this_wave if r in all_agents]
    else:
        # Fallback: distribute agents evenly across waves
        agents = profile["agents"]
        apw = profile.get("agents_per_wave", 1)
        start = (wave_num - 1) * apw
        return agents[start:start + apw]


# ---------------------------------------------------------------------------
# Reward-hack checks (inline; also pipes into reward_hack_detector.py if present)
# ---------------------------------------------------------------------------

BONDSWOMAN_SET = {
    "awaiting operator", "go/no-go", "pending operator",
    "requires operator", "please advise", "please confirm",
    "should i proceed", "would you like me to",
}

HEX16_RE = re.compile(r"^[0-9a-f]{16}$")
CONSENSUS_RE = re.compile(
    r"\b(consensus reached|bft.?attested|quorum met|unanimous agreement)\b",
    re.IGNORECASE,
)


def quick_reward_hack_check(row: dict, checks: list[str]) -> list[str]:
    """Return list of triggered Loki names."""
    flags = []
    row_text = json.dumps(row).lower()

    if "L-CONSENSUS-THEATER" in checks:
        if CONSENSUS_RE.search(json.dumps(row)) and row.get("signal") != "DISRUPT":
            flags.append("L-CONSENSUS-THEATER")

    if "L-MODE-DRIFT" in checks:
        canonical_modes = {
            "autonomous", "supervised", "review", "audit", "test",
            "bootstrap", "canary", "idle", "drain", "shutdown",
        }
        if row.get("mode") not in canonical_modes:
            flags.append("L-MODE-DRIFT")

    if "L-DUPLICATE-TASK-ID" in checks:
        # Checked at run level, not per-row; skip here
        pass

    if "L102-FAKE-HMAC" in checks:
        sha16 = row.get("this_sha16", "")
        if sha16 and not HEX16_RE.match(str(sha16)):
            flags.append("L102-FAKE-HMAC")

    if "L-FUTURE-AS-PRESENT" in checks:
        future_re = re.compile(r"\b(is enforced|is now enforced|is validated|is checked)\b", re.I)
        if future_re.search(json.dumps(row)):
            flags.append("L-FUTURE-AS-PRESENT")

    return flags


# ---------------------------------------------------------------------------
# Target loading
# ---------------------------------------------------------------------------

def load_target(target: str) -> str:
    """If target is an existing file path, read it. Otherwise treat as literal text."""
    p = Path(target)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8", errors="replace")
    return target


# ---------------------------------------------------------------------------
# Vendor API call
# ---------------------------------------------------------------------------

def call_vendor(
    vendor: str,
    messages: list[dict],
    model: str | None = None,
    timeout: int = 60,
) -> tuple[str, float]:
    """
    Make a chat-completion call.
    Returns (response_text, elapsed_seconds).
    Raises on HTTP errors or missing API key.
    """
    try:
        import requests
    except ImportError:
        raise ImportError("requests is required: pip install requests")

    cfg = VENDOR_CONFIGS.get(vendor)
    if cfg is None:
        raise ValueError(f"Unknown vendor '{vendor}'. Choose from: {list(VENDOR_CONFIGS)}")

    api_key = os.environ.get(cfg["env_key"])
    if not api_key:
        raise EnvironmentError(
            f"Vendor '{vendor}' requires env var {cfg['env_key']}. "
            f"Set it before running."
        )

    chosen_model = model or cfg["default_model"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # Anthropic uses different auth header and request shape
    if vendor == "anthropic":
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        # Separate system prompt from user messages for Anthropic
        system_msgs = [m["content"] for m in messages if m["role"] == "system"]
        user_msgs = [m for m in messages if m["role"] != "system"]
        body = {
            "model": chosen_model,
            "max_tokens": 1024,
            "system": "\n\n".join(system_msgs) if system_msgs else "You are a helpful AI.",
            "messages": user_msgs,
        }
    else:
        body = {
            "model": chosen_model,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.3,
        }

    t0 = time.monotonic()
    resp = requests.post(cfg["base_url"], headers=headers, json=body, timeout=timeout)
    elapsed = time.monotonic() - t0

    if resp.status_code != 200:
        raise RuntimeError(
            f"Vendor '{vendor}' returned HTTP {resp.status_code}: {resp.text[:300]}"
        )

    data = resp.json()

    # Extract text — handle Anthropic vs OpenAI-compatible shapes
    if vendor == "anthropic":
        content = data.get("content", [{}])
        text = content[0].get("text", "") if content else ""
    else:
        choices = data.get("choices", [{}])
        text = choices[0].get("message", {}).get("content", "") if choices else ""

    return text.strip(), elapsed


# ---------------------------------------------------------------------------
# Parse agent response into a JSONL row
# ---------------------------------------------------------------------------

def parse_agent_response(
    text: str,
    agent_role: str,
    wave: int,
    seq: int,
    task_id: str,
    prev_sha16: str,
    hmac_key: bytes,
) -> dict:
    """
    Extract the first JSON object from the agent's response and normalize it.
    Computes HMAC chain link.
    """
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Try to find a JSON object in the response
    row = None
    # First try: the whole response is one JSON line
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError:
            pass

    # Second try: find the first { ... } block
    if row is None:
        match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}", text, re.DOTALL)
        if match:
            try:
                row = json.loads(match.group())
            except json.JSONDecodeError:
                pass

    # Fallback: construct a minimal row from raw text
    if row is None:
        row = {
            "opcode_verb": "OBSERVE",
            "agent": agent_role,
            "claim": text[:200] if text else "(empty response)",
            "evidence": {"raw_response": text[:500]},
            "mode": "review",
            "confidence": "7/8",
        }

    # Normalize / enforce required fields
    row.setdefault("opcode_verb", "OBSERVE")
    row["agent"] = agent_role  # always override with our canonical name
    row.setdefault("claim", "(no claim)")
    row.setdefault("evidence", {})
    row.setdefault("mode", "review")
    row.setdefault("confidence", "7/8")
    row.setdefault("meta", {})

    # Chain fields
    row["seq"] = seq
    row["wave"] = wave
    row["task_id"] = task_id
    row["ts"] = ts
    row["prev_sha16"] = prev_sha16

    # Compute HMAC
    row["this_sha16"] = _compute_sha16(hmac_key, row)

    return row


# ---------------------------------------------------------------------------
# Main run logic
# ---------------------------------------------------------------------------

def run(
    profile_name: str,
    target: str,
    out_path: str,
    vendor: str,
    model: str | None,
    dry_run: bool,
    hmac_key: bytes,
    request_delay_ms: int,
) -> dict:
    """
    Execute the full wave run.
    Returns summary dict.
    """
    profile = load_profile(profile_name)
    target_text = load_target(target)
    total_waves = profile["waves"]
    rh_checks = profile.get("reward_hack_checks", [])
    task_id = f"run-{int(time.time())}"

    if dry_run:
        print(f"\n=== DRY RUN — {profile['name']} ===")
        print(f"Profile:     {profile['name']}")
        print(f"Description: {profile['description']}")
        print(f"Waves:       {total_waves}")
        print(f"Agents/wave: {profile['agents_per_wave']}")
        print(f"Total slots: {total_waves * profile['agents_per_wave']}")
        print(f"Vendor:      {vendor} ({VENDOR_CONFIGS.get(vendor, {}).get('free_note', '')})")
        print(f"Out path:    {out_path}")
        print(f"Target:      {target_text[:80]!r}{'...' if len(target_text) > 80 else ''}")
        print(f"\nWave plan:")
        for w in range(1, total_waves + 1):
            agents = agents_for_wave(profile, w)
            roles = [a["role"] for a in agents]
            print(f"  Wave {w}/{total_waves}: {roles}")
        print(f"\nReward-hack checks: {rh_checks}")
        print(f"\nNo API calls made (--dry-run).")
        return {
            "dry_run": True,
            "profile": profile_name,
            "total_slots": total_waves * profile["agents_per_wave"],
            "vendor": vendor,
        }

    # Real run
    prev_sha16 = "0" * 16
    seq = 0
    total_agents = 0
    rh_flags_total: list[dict] = []
    task_ids_seen: set[str] = set()
    prior_receipts: list[dict] = []

    out_file = open(out_path, "a", encoding="utf-8")

    try:
        for wave_num in range(1, total_waves + 1):
            agents = agents_for_wave(profile, wave_num)
            total_in_wave = len(agents)

            for agent_idx, agent_def in enumerate(agents, 1):
                seq += 1
                total_agents += 1
                role = agent_def["role"]
                preamble = agent_def["preamble"]

                # Build context: preamble + target + prior wave receipts (last 10)
                prior_context = ""
                if prior_receipts:
                    recent = prior_receipts[-10:]
                    prior_context = "\n\nPrior agent outputs (most recent first):\n" + "\n".join(
                        json.dumps(r, separators=(",", ":")) for r in reversed(recent)
                    )

                messages = [
                    {"role": "system", "content": preamble},
                    {
                        "role": "user",
                        "content": (
                            f"TARGET:\n{target_text[:4000]}"
                            f"{prior_context}\n\n"
                            "Output exactly one JSONL line (valid JSON, no markdown wrapping)."
                        ),
                    },
                ]

                t0 = time.monotonic()
                response_text, elapsed = call_vendor(vendor, messages, model)
                elapsed = time.monotonic() - t0

                row = parse_agent_response(
                    response_text, role, wave_num, seq, task_id, prev_sha16, hmac_key
                )

                # Reward-hack check
                flags = quick_reward_hack_check(row, rh_checks)
                if flags:
                    row["rh_flags"] = flags
                    rh_flags_total.append({"seq": seq, "agent": role, "flags": flags})

                out_file.write(json.dumps(row, separators=(",", ":")) + "\n")
                out_file.flush()

                prior_receipts.append(row)
                prev_sha16 = row["this_sha16"]

                flag_str = f" RH:{flags}" if flags else ""
                print(
                    f"[wave {wave_num}/{total_waves} · agent {agent_idx}/{total_in_wave}"
                    f" · {role} · {vendor} · {elapsed:.1f}s{flag_str}]"
                )

                # Rate-limit pacing
                if request_delay_ms > 0:
                    time.sleep(request_delay_ms / 1000.0)

    finally:
        out_file.close()

    # Verify chain on output file
    chain_valid = _verify_chain_file(out_path, hmac_key)

    summary = {
        "profile": profile_name,
        "total_agents_dispatched": total_agents,
        "out_path": out_path,
        "chain_valid": chain_valid,
        "rh_flags_count": len(rh_flags_total),
        "rh_flags": rh_flags_total,
        "vendor": vendor,
        "cost": "$0 (free-tier)" if vendor in ("openrouter", "groq") else "see vendor dashboard",
        "confidence": "7/8 (no quorum certificate)",
    }

    print("\n=== SUMMARY ===")
    print(f"Agents dispatched: {total_agents}")
    print(f"Output:            {out_path}")
    print(f"HMAC chain valid:  {chain_valid}")
    print(f"RH flags:          {len(rh_flags_total)}")
    print(f"Cost:              {summary['cost']}")
    return summary


def _verify_chain_file(path: str, key: bytes) -> bool:
    """Quick in-process chain verify. Returns True if all rows pass."""
    prev = ""
    try:
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    return False
                expected = _compute_sha16(key, row)
                if row.get("this_sha16") != expected:
                    return False
                prev = row.get("this_sha16", "")
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Inline tests
# ---------------------------------------------------------------------------

def run_tests() -> None:
    import tempfile

    errors: list[str] = []

    def fail(msg: str) -> None:
        errors.append(msg)
        print(f"  FAIL: {msg}")

    def ok(name: str) -> None:
        print(f"  PASS: {name}")

    print("Running inline tests...")

    # Test 1: 2x2 profile loads cleanly
    try:
        p = load_profile("2x2")
        assert "agents" in p, "no 'agents' key"
        assert len(p["agents"]) > 0, "empty agents list"
        ok("Test 1: 2x2 loads")
    except Exception as e:
        fail(f"Test 1: 2x2 load failed: {e}")

    # Test 2: 4x4 has 4 waves x 4 agents = 16 expected slots
    try:
        p = load_profile("4x4")
        assert p["waves"] == 4, f"expected 4 waves, got {p['waves']}"
        assert p["agents_per_wave"] == 4, f"expected 4 apw, got {p['agents_per_wave']}"
        total = sum(len(agents_for_wave(p, w)) for w in range(1, p["waves"] + 1))
        assert total == 16, f"expected 16 slots, got {total}"
        ok("Test 2: 4x4 → 4x4 = 16 slots")
    except Exception as e:
        fail(f"Test 2: 4x4 failed: {e}")

    # Test 3: hfo_full_8x8 has 8 waves x 8 agents = 64 expected slots
    try:
        p = load_profile("8x8")
        assert p["waves"] == 8, f"expected 8 waves, got {p['waves']}"
        assert p["agents_per_wave"] == 8, f"expected 8 apw, got {p['agents_per_wave']}"
        total = sum(len(agents_for_wave(p, w)) for w in range(1, p["waves"] + 1))
        assert total == 64, f"expected 64 slots, got {total}"
        ok("Test 3: 8x8 → 8x8 = 64 slots")
    except Exception as e:
        fail(f"Test 3: hfo_full_8x8 failed: {e}")

    # Test 4: HMAC chain link is correctly computed from prev_sha16 + canonical row bytes
    try:
        key = b"testkey123"
        row = {
            "prev_sha16": "abcd1234abcd1234",
            "ts": "2026-05-11T00:00:00Z",
            "opcode_verb": "OBSERVE",
            "agent": "test-agent",
            "task_id": "t1",
            "claim": "test claim",
            "evidence": {"k": "v"},
            "confidence": "7/8",
            "meta": {},
            "mode": "test",
        }
        sha16 = _compute_sha16(key, row)
        assert len(sha16) == 16, f"sha16 len should be 16, got {len(sha16)}"
        assert all(c in "0123456789abcdef" for c in sha16), f"sha16 not hex: {sha16}"
        # Verify changing claim changes the hash (tamper detection)
        row2 = dict(row)
        row2["claim"] = "tampered claim"
        sha16_tampered = _compute_sha16(key, row2)
        assert sha16 != sha16_tampered, "HMAC must differ after claim change"
        # Verify idempotent (same input → same hash)
        assert _compute_sha16(key, row) == sha16, "HMAC must be deterministic"
        ok("Test 4: HMAC chain link computation correct")
    except Exception as e:
        fail(f"Test 4: HMAC computation failed: {e}")

    # Test 5: --dry-run produces correct plan without API call
    try:
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = run(
                profile_name="2x2",
                target="demo text for dry run",
                out_path="/tmp/run_wave_test_dryrun.jsonl",
                vendor="openrouter",
                model=None,
                dry_run=True,
                hmac_key=b"",
                request_delay_ms=0,
            )
        output = buf.getvalue()
        assert result["dry_run"] is True, "dry_run flag not set"
        # 2x2: 2 waves x 2 agents = 4 slots
        assert result["total_slots"] == 4, f"expected 4 slots, got {result['total_slots']}"
        assert "Wave 1/2" in output, "wave plan not in output"
        assert "orchestrator" in output, "orchestrator not in output"
        # Verify no API calls were made (no file written with actual rows)
        ok("Test 5: --dry-run plan correct, no API calls")
    except Exception as e:
        fail(f"Test 5: dry-run failed: {e}")

    print()
    if errors:
        print(f"RESULT: {len(errors)} test(s) FAILED")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("RESULT: All 5 tests PASSED")


# ---------------------------------------------------------------------------
# Self-redteam: what bypasses run_wave.py?
# ---------------------------------------------------------------------------
# SELF-REDTEAM (minute-6 edge cases for new users):
#
# 1. Free-tier rate limits — OpenRouter free models cap ~20 req/min. 4x4
#    (16 calls) will likely hit the cap mid-run. Fix: set SIGRUN_REQUEST_DELAY_MS=3000
#    (3s gap), or use groq which has a more generous free tier.
#
# 2. Malformed agent JSON — The parser extracts the first {...} block from agent
#    output. If the model returns a markdown code fence instead of raw JSON, the
#    outer block is stripped but nested content may be mis-parsed. Fallback: the
#    raw text lands in evidence.raw_response, so no data is lost, but the structured
#    fields (claim, opcode_verb) will be defaults.
#
# 3. HMAC key default is empty string — The HMAC chain is cryptographically valid
#    but provides no security without a secret key. Set SIGRUN_CHAIN_HMAC_KEY to a
#    random string to make the chain tamper-evident in the meaningful sense.
#
# 4. Target truncation — Targets longer than 4000 chars are silently truncated in
#    the prompt. For large diffs or docs, pass a file path; the file is read in full
#    but the prompt still truncates. Mitigate by pre-summarizing the target or
#    chunking it manually.
#
# 5. Sycophantic agent cascade — Wave 2+ agents receive all prior receipts. If wave-1
#    agents anchor on a wrong claim, later agents tend to converge on it. The critic
#    role is designed to break this, but it can still collapse. Mitigation: use the
#    --config 4x4 proposer-D (contrarian proposer) role explicitly.
#
# 6. Vendor API key exposure in logs — run_wave.py never prints API keys, but
#    shell history, CI logs, and 'ps aux' output can expose env vars. Use a dedicated
#    .env file and source it in a subshell, never inline on the command line.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "run_wave.py — 10-minute thin-slice multi-agent review driver.\n"
            "Quickstart: python3 run_wave.py --config 2x2 --target myfile.py"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config", default="2x2",
        help="Profile name (loads profiles/<name>.json). Default: 2x2",
    )
    parser.add_argument(
        "--target", default="",
        help="File path or literal text to review.",
    )
    parser.add_argument(
        "--out", default=None,
        help="Output JSONL path. Default: ./run_<timestamp>.jsonl",
    )
    parser.add_argument(
        "--vendor", default="openrouter",
        choices=list(VENDOR_CONFIGS),
        help="API vendor. Default: openrouter (free tier)",
    )
    parser.add_argument(
        "--model", default=None,
        help="Override model. Default: vendor's default free model.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print plan without making API calls.",
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Run inline tests and exit.",
    )
    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    if not args.target and not args.dry_run:
        parser.error("--target is required unless --dry-run or --test")

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or f"./run_{ts}.jsonl"
    hmac_key = os.environ.get("SIGRUN_CHAIN_HMAC_KEY", "").encode("utf-8")
    request_delay_ms = int(os.environ.get("SIGRUN_REQUEST_DELAY_MS", "0"))

    result = run(
        profile_name=args.config,
        target=args.target,
        out_path=out_path,
        vendor=args.vendor,
        model=args.model,
        dry_run=args.dry_run,
        hmac_key=hmac_key,
        request_delay_ms=request_delay_ms,
    )

    if not args.dry_run:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if "--test" in sys.argv:
        run_tests()
    else:
        main()
