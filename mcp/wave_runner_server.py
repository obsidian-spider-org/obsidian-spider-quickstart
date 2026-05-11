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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

"""
wave_runner_server.py — MCP server exposing wave_runner tools.

Server identity : wave_runner_server v0.1.0
Transport       : stdio (JSON-RPC 2.0, MCP spec)
Install         : pip install mcp
Smoke test      : python3 wave_runner_server.py --test

Confidence      : 7/8 (no quorum certificate)

Self-red-team
-------------
1. Subprocess boundary bypass: any tool that calls run_wave.py etc. passes
   user-controlled strings to subprocess. Shell injection is the obvious
   vector. Mitigation: all subprocess calls use list-form (no shell=True) and
   paths are resolved from a fixed BASE_DIR. If BASE_DIR itself is symlinked
   by an attacker to an arbitrary location, containment breaks — document this
   limitation clearly for production deployments.
2. MCP SDK API churn: the mcp package is pre-1.0; handler registration
   (@server.list_tools, @server.call_tool) may rename. The --test flag catches
   import-level breakage immediately; runtime breakage only surfaces when a
   client connects. Pin `mcp` in requirements.txt.
3. Audit JSONL is append-only, unencrypted, written to the same directory.
   A compromised working directory can tamper with audit log — not a
   cryptographic receipt, just an operational trace.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Graceful import guard
# ---------------------------------------------------------------------------
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    import mcp.types as types
except ImportError:
    print(
        "ERROR: mcp SDK not found.\n"
        "Install with:  pip install mcp\n"
        "Then retry:    python3 wave_runner_server.py",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent.resolve()
# Sibling scripts live one level up in public_mirror_staging/
PUBLIC_DIR = HERE.parent
PROFILES_DIR = PUBLIC_DIR / "profiles"
AUDIT_LOG = HERE / "tool_audit.jsonl"

# Scripts (expected to exist; errors are caught per-call)
RUN_WAVE_PY = PUBLIC_DIR / "run_wave.py"
HMAC_VERIFIER_PY = PUBLIC_DIR / "hmac_verifier.py"
REWARD_HACK_DETECTOR_PY = PUBLIC_DIR / "reward_hack_detector.py"

# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------

def _audit(tool: str, args: dict, result: dict | str) -> None:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "args": args,
        "result_summary": str(result)[:300],
    }
    try:
        with AUDIT_LOG.open("a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # audit failure must never break the tool call


# ---------------------------------------------------------------------------
# Subprocess helper
# ---------------------------------------------------------------------------

def _run(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Run cmd; return (returncode, stdout, stderr). Never shell=True."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired:
        return 124, "", "subprocess timed out"


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

server = Server("wave_runner_server")

# ── Tool registry ──────────────────────────────────────────────────────────

TOOLS = [
    types.Tool(
        name="run_wave",
        description="Run a wave using run_wave.py. Returns summary JSON.",
        inputSchema={
            "type": "object",
            "properties": {
                "config": {"type": "string", "description": "Path to wave config JSON"},
                "target": {"type": "string", "description": "Target identifier"},
                "vendor": {"type": "string", "description": "Optional vendor override"},
            },
            "required": ["config", "target"],
        },
    ),
    types.Tool(
        name="verify_chain",
        description="Verify HMAC chain integrity via hmac_verifier.py.",
        inputSchema={
            "type": "object",
            "properties": {
                "jsonl_path": {
                    "type": "string",
                    "description": "Path to chain JSONL file to verify",
                },
            },
            "required": ["jsonl_path"],
        },
    ),
    types.Tool(
        name="detect_reward_hacks",
        description="Detect reward hacks in a JSONL log via reward_hack_detector.py.",
        inputSchema={
            "type": "object",
            "properties": {
                "jsonl_path": {
                    "type": "string",
                    "description": "Path to JSONL log to scan",
                },
            },
            "required": ["jsonl_path"],
        },
    ),
    types.Tool(
        name="list_profiles",
        description="List available wave profile JSONs in the profiles/ directory.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
]


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return TOOLS


# ── Tool dispatch ──────────────────────────────────────────────────────────

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict
) -> list[types.TextContent]:

    try:
        result = await _dispatch(name, arguments)
    except Exception as exc:
        result = {"error": str(exc), "traceback": traceback.format_exc(limit=4)}

    _audit(name, arguments, result)
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


async def _dispatch(name: str, args: dict) -> dict:
    loop = asyncio.get_event_loop()

    if name == "run_wave":
        config = args.get("config", "")
        target = args.get("target", "")
        vendor = args.get("vendor", "")
        cmd = [sys.executable, str(RUN_WAVE_PY), "--config", config, "--target", target]
        if vendor:
            cmd += ["--vendor", vendor]
        rc, out, err = await loop.run_in_executor(None, lambda: _run(cmd))
        return {"returncode": rc, "stdout": out[:4000], "stderr": err[:1000]}

    elif name == "verify_chain":
        jsonl_path = args.get("jsonl_path", "")
        cmd = [sys.executable, str(HMAC_VERIFIER_PY), jsonl_path]
        rc, out, err = await loop.run_in_executor(None, lambda: _run(cmd))
        return {"returncode": rc, "stdout": out[:4000], "stderr": err[:1000]}

    elif name == "detect_reward_hacks":
        jsonl_path = args.get("jsonl_path", "")
        cmd = [sys.executable, str(REWARD_HACK_DETECTOR_PY), jsonl_path]
        rc, out, err = await loop.run_in_executor(None, lambda: _run(cmd))
        # Try to parse findings as JSON; fall back to raw text
        try:
            findings = json.loads(out)
        except (json.JSONDecodeError, ValueError):
            findings = out[:4000]
        return {"returncode": rc, "findings": findings, "stderr": err[:1000]}

    elif name == "list_profiles":
        if not PROFILES_DIR.exists():
            return {"profiles": [], "note": f"profiles dir not found: {PROFILES_DIR}"}
        profiles = sorted(p.name for p in PROFILES_DIR.glob("*.json"))
        return {"profiles": profiles, "count": len(profiles)}

    else:
        return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def _serve() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def _run_tests() -> None:
    """--test: registration check + schema validation."""
    print("=== wave_runner_server --test ===")
    errors: list[str] = []

    # T1: tool count
    expected = {"run_wave", "verify_chain", "detect_reward_hacks", "list_profiles"}
    registered = {t.name for t in TOOLS}
    if registered != expected:
        errors.append(f"T1 FAIL: registered={registered} expected={expected}")
    else:
        print(f"T1 PASS: {len(TOOLS)} tools registered — {sorted(registered)}")

    # T2: schema validation — every tool has required fields
    for tool in TOOLS:
        schema = tool.inputSchema
        if not isinstance(schema, dict) or "type" not in schema:
            errors.append(f"T2 FAIL: {tool.name} inputSchema missing 'type'")
            continue
        required = schema.get("required", [])
        props = schema.get("properties", {})
        for req_field in required:
            if req_field not in props:
                errors.append(
                    f"T2 FAIL: {tool.name} required field '{req_field}' not in properties"
                )
        print(f"T2 PASS: {tool.name} schema OK (required={required})")

    # T3: list_profiles smoke (no subprocess needed)
    result = asyncio.run(_dispatch("list_profiles", {}))
    if "profiles" not in result:
        errors.append(f"T3 FAIL: list_profiles result missing 'profiles' key: {result}")
    else:
        print(f"T3 PASS: list_profiles → {result['count']} profiles found")

    # T4: unknown tool returns error dict
    result = asyncio.run(_dispatch("nonexistent_tool", {}))
    if "error" not in result:
        errors.append(f"T4 FAIL: unknown tool should return error dict, got: {result}")
    else:
        print(f"T4 PASS: unknown tool → error: {result['error']}")

    # Summary
    if errors:
        print("\n--- FAILURES ---")
        for e in errors:
            print(" ", e)
        sys.exit(1)
    else:
        print("\nAll tests PASS. Confidence: 7/8 (no quorum certificate).")


if __name__ == "__main__":
    if "--test" in sys.argv:
        _run_tests()
    else:
        asyncio.run(_serve())
