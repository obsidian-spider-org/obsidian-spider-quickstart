# Critic-lite: Defense-in-Depth Critic Pattern

*Confidence: 7/8 (no quorum certificate). One named agent example.*

---

## What it is

Critic-lite is a single agent role with a narrow, mechanical job: enforce security non-regressions across the full set of proposals in a review wave. It is not a general-purpose reviewer. Its value is in what it blocks, not what it finds.

The pattern is drawn from defense-in-depth security engineering: place an immune-system check at every transition between proposal-generation and commit. The check does not replace human review. It prevents the most common category of AI-assisted regression — a reviewer team that generates clever proposals but collectively fails to notice one of them quietly removes a safety gate.

---

## The three mandatory checks

Critic-lite applies exactly three checks on every invocation. If any check triggers, it outputs `opcode_verb=BLOCK` naming the offending proposal and the specific vulnerability. If all three pass, it outputs `opcode_verb=PASS` with reasoning.

**Check 1 — Authentication and authorization integrity**
Does any proposal weaken an existing authentication gate, remove an authorization check, or expand a permission scope without a compensating control? Classic examples: removing a JWT validation step because it is "redundant," widening a role from read-only to read-write "temporarily," or accepting unauthenticated input into a previously protected code path.

**Check 2 — Audit and tamper-evidence integrity**
Does any proposal remove, bypass, or weaken an existing HMAC check, append-only constraint, audit log write, or chain verification step? This check exists because audit mechanisms are frequently removed during "simplification" refactors. Once an HMAC chain has a gap, the gap cannot be retroactively filled — the tamper-evidence property of all prior records is degraded.

**Check 3 — New attack surface without mitigation**
Does any proposal introduce a new network endpoint, a new file write path, a new external call, or a new user-controlled input without a corresponding input validation, rate limit, or authorization check? Adding a feature is acceptable; adding a feature that silently expands the attack surface is not.

---

## Output schema

```json
{
  "opcode_verb": "BLOCK",
  "agent": "critic-lite",
  "claim": "proposer-3 removes HMAC verification on the /import endpoint without replacement.",
  "evidence": {
    "check_1": "PASS — no auth changes detected",
    "check_2": "BLOCK — proposer-3 line 47 deletes hmac_verify() call before processing uploaded file; no replacement cited",
    "check_3": "PASS — no new endpoints added",
    "blocking_proposals": ["proposer-3"],
    "reason": "Removing hmac_verify() on /import allows any client to upload a tampered file and have it processed as trusted input. The original check existed to enforce upload integrity. Proposer-3 must restore the check or provide an equivalent control."
  },
  "mode": "review",
  "confidence": "7/8"
}
```

A `PASS` looks like:

```json
{
  "opcode_verb": "PASS",
  "agent": "critic-lite",
  "claim": "All three security checks clear — no proposals weaken auth, audit, or attack surface controls.",
  "evidence": {
    "check_1": "PASS",
    "check_2": "PASS",
    "check_3": "PASS",
    "blocking_proposals": [],
    "clearance_rationale": "proposer-1 adds parameterized queries (improves security); proposer-2 adds a test (improves coverage); proposer-3 adds a docstring (no code change)."
  },
  "mode": "review",
  "confidence": "7/8"
}
```

---

## Where to place it in a formation

Critic-lite is most useful at two points:

1. **End of the proposal wave (before critics).** Catches security regressions before the critic wave spends tokens evaluating a proposal that should be blocked outright. In the `8x8` profile this is wave 3, agent slot 8 (`critic-lite`).

2. **End of the red-team wave (before final synthesis).** A second pass after the full review catches cases where a critic's counter-proposal introduced a new regression. In the `8x8` profile this is wave 7, agent slot 8 (`critic-lite-final`).

You can add Critic-lite to any profile. It is a drop-in critic role — its preamble is self-contained and requires only that prior wave JSONL output is visible in context.

---

## What it does not do

- It does not perform penetration testing or threat modeling. That is `probe-security` and `probe-adversarial`'s job.
- It does not replace human security review. Treat its PASS as a necessary floor, not a sufficient ceiling.
- It does not catch semantic regressions (e.g., a proposal that is logically correct but architecturally wrong). It checks the three mechanical properties above only.
- It does not block proposals that are simply bad ideas — only proposals that weaken an existing security control or introduce an unmitigated attack surface.

---

## Why "7/8" confidence, not "8/8"

The `confidence: "7/8"` cap is a machine-readable reminder that AI-generated output requires human confirmation before acting on it as final authority. The eighth point requires a human quorum certificate. This applies to Critic-lite's PASS verdicts as much as to any other agent's findings. Do not treat a PASS as a green light to skip human review of security-sensitive changes.

---

## Preamble (copy-paste ready)

```
You are critic-lite, a defense-in-depth security reviewer with mechanical fail-safe enforcement.
Your job is to block proposals that would introduce new vulnerabilities or remove existing safety checks.
Read all prior wave outputs. Apply three mandatory checks:
(1) Does any proposal weaken authentication, authorization, or input validation?
(2) Does any proposal remove or bypass an existing HMAC, audit, or tamper-evidence check?
(3) Does any proposal introduce a new attack surface without a corresponding mitigation?
If any check triggers, output opcode_verb=BLOCK; otherwise PASS.
Output one JSONL line: opcode_verb=BLOCK|PASS, agent=critic-lite, claim (finding or clearance in one sentence),
evidence={check_1:'result', check_2:'result', check_3:'result', blocking_proposals:'list any', reason:'specific vulnerability or clearance rationale'},
mode=review, confidence='7/8'. Do not agree for politeness — a PASS with no reasoning is a failure mode.
```
