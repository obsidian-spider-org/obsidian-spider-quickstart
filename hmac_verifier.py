#!/usr/bin/env python3
# MIT License
# Copyright (c) 2026 Obsidian_Spider — built by the cybernetic_unit Sigrún + 8 Valkyries
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
hmac_verifier.py — walk a JSONL chain in seq order and verify HMAC-SHA256 linkage.
Confidence: 7/8 (no quorum certificate).
Standalone, stdlib-only.

Canonical bytes per row (fields joined by 0x1F unit-separator):
  prev_sha16 | ts | opcode_verb | agent | task_id | claim |
  json.dumps(evidence) | confidence | json.dumps(meta) | mode

Environment:
  SIGRUN_CHAIN_HMAC_KEY — HMAC key string (default: empty string)
"""

import argparse
import hashlib
import hmac
import json
import os
import sys

SEP = "\x1f"
DEFAULT_KEY = ""


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


def _compute_sha16(key: bytes, canonical: bytes) -> str:
    return hmac.new(key, canonical, hashlib.sha256).hexdigest()[:16]


def verify_chain(path: str, key: bytes) -> dict:
    verified = 0
    failed = 0
    first_fail_seq = None
    prev_sha16 = ""
    total_rows = 0

    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            total_rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                failed += 1
                seq = lineno
                if first_fail_seq is None:
                    first_fail_seq = seq
                print(json.dumps({
                    "lineno": lineno, "error": "parse", "detail": str(exc)
                }), file=sys.stderr)
                prev_sha16 = ""
                continue

            seq = row.get("seq", row.get("chain_seq", lineno))

            # Check prev_sha16 linkage (skip for first row)
            row_prev = row.get("prev_sha16", "")
            if total_rows > 1 and row_prev != prev_sha16:
                failed += 1
                if first_fail_seq is None:
                    first_fail_seq = seq
                print(json.dumps({
                    "lineno": lineno, "seq": seq, "error": "prev_sha16_mismatch",
                    "expected": prev_sha16, "got": row_prev,
                }), file=sys.stderr)
                prev_sha16 = row.get("this_sha16", "")
                continue

            # Recompute HMAC
            canonical = _canonical_bytes(row)
            expected = _compute_sha16(key, canonical)
            actual = row.get("this_sha16", "")

            if expected != actual:
                failed += 1
                if first_fail_seq is None:
                    first_fail_seq = seq
                print(json.dumps({
                    "lineno": lineno, "seq": seq, "error": "hmac_mismatch",
                    "expected": expected, "got": actual,
                }), file=sys.stderr)
            else:
                verified += 1

            prev_sha16 = actual

    return {
        "verified": verified,
        "failed": failed,
        "first_fail_seq": first_fail_seq,
        "total_rows": total_rows,
        "confidence": "7/8 (no quorum certificate)",
    }


# ---------------------------------------------------------------------------
# Inline tests — 3 PASS + 3 FAIL fixtures
# ---------------------------------------------------------------------------

def _make_row(prev: str, key: bytes, **kwargs) -> dict:
    row = {
        "prev_sha16": prev,
        "ts": "2026-05-11T00:00:00Z",
        "opcode_verb": "VERIFY",
        "agent": "eir",
        "task_id": "t1",
        "claim": "test claim",
        "evidence": {},
        "confidence": "7/8",
        "meta": {},
        "mode": "test",
    }
    row.update(kwargs)
    canonical = _canonical_bytes(row)
    row["this_sha16"] = _compute_sha16(key, canonical)
    row["seq"] = kwargs.get("seq", 1)
    return row


def run_tests() -> None:
    import tempfile

    key = b"testkey"
    errors = []

    def write(path, rows):
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    with tempfile.TemporaryDirectory() as td:
        p = os.path.join

        # PASS 1: single row with correct HMAC
        r1 = _make_row("0" * 16, key, seq=1)
        write(p(td, "pass1.jsonl"), [r1])
        res = verify_chain(p(td, "pass1.jsonl"), key)
        assert res["verified"] == 1 and res["failed"] == 0, f"PASS1 failed: {res}"

        # PASS 2: two-row chain, both correct
        r2 = _make_row(r1["this_sha16"], key, seq=2, task_id="t2")
        write(p(td, "pass2.jsonl"), [r1, r2])
        res = verify_chain(p(td, "pass2.jsonl"), key)
        assert res["verified"] == 2 and res["failed"] == 0, f"PASS2 failed: {res}"

        # PASS 3: three-row chain
        r3 = _make_row(r2["this_sha16"], key, seq=3, task_id="t3")
        write(p(td, "pass3.jsonl"), [r1, r2, r3])
        res = verify_chain(p(td, "pass3.jsonl"), key)
        assert res["verified"] == 3 and res["failed"] == 0, f"PASS3 failed: {res}"

        # FAIL 1: wrong HMAC on single row
        bad1 = dict(r1)
        bad1["this_sha16"] = "deadbeefdeadbeef"
        write(p(td, "fail1.jsonl"), [bad1])
        res = verify_chain(p(td, "fail1.jsonl"), key)
        assert res["failed"] >= 1, f"FAIL1 should have failed: {res}"

        # FAIL 2: broken prev_sha16 linkage on row 2
        bad2 = dict(r2)
        bad2["prev_sha16"] = "0000000000000000"
        write(p(td, "fail2.jsonl"), [r1, bad2])
        res = verify_chain(p(td, "fail2.jsonl"), key)
        assert res["failed"] >= 1, f"FAIL2 should have failed: {res}"

        # FAIL 3: tampered payload (claim changed after HMAC computed)
        bad3 = dict(r1)
        bad3["claim"] = "tampered claim"
        write(p(td, "fail3.jsonl"), [bad3])
        res = verify_chain(p(td, "fail3.jsonl"), key)
        assert res["failed"] >= 1, f"FAIL3 should have failed: {res}"

    print("All tests passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify HMAC-SHA256 chain integrity of a JSONL receipt file."
    )
    parser.add_argument("file", nargs="?", help="Path to JSONL chain file")
    parser.add_argument("--key", default=None,
                        help="HMAC key string (overrides SIGRUN_CHAIN_HMAC_KEY env var)")
    parser.add_argument("--test", action="store_true", help="Run inline tests and exit")
    args = parser.parse_args()

    if args.test:
        run_tests()
        sys.exit(0)

    if not args.file:
        parser.print_help()
        sys.exit(2)

    raw_key = args.key if args.key is not None else os.environ.get("SIGRUN_CHAIN_HMAC_KEY", DEFAULT_KEY)
    key_bytes = raw_key.encode("utf-8")

    result = verify_chain(args.file, key_bytes)
    print(json.dumps(result))
    sys.exit(1 if result["failed"] > 0 else 0)

# ---------------------------------------------------------------------------
# Skǫgul self-redteam: what bypasses this verifier?
# ---------------------------------------------------------------------------
# 1. Key compromise: if SIGRUN_CHAIN_HMAC_KEY is leaked, an attacker can produce
#    a fully valid chain for any payload. Key secrecy is the entire security model.
# 2. Genesis forgery: the first row's prev_sha16 is unchecked (no predecessor).
#    An attacker can replace the entire chain with a fresh valid one starting at seq 1.
# 3. Truncation attack: dropping tail rows is undetected unless the reader knows
#    the expected final seq independently.
# 4. Field-omission: if a field (e.g., evidence) is legitimately absent in some
#    rows, the canonical bytes differ from rows that include it — callers must use
#    a consistent schema or verification breaks silently.
# 5. Encoding divergence: if the writer uses a different JSON serializer that
#    produces different key ordering or whitespace, HMAC recompute will always fail
#    even for honest chains — this is a configuration error, not an attack, but
#    produces false positives.
