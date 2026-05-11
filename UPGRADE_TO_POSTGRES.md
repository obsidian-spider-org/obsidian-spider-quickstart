# If You Want Stronger: Upgrading to Postgres + XTDB

*Confidence: 7/8 (no quorum certificate). This describes what the reference implementation actually runs — not a design proposal.*

---

## 1. When to upgrade

You do not need this if your JSONL chain is small, single-writer, and you have no need for historical queries. Three signals that say you have outgrown it:

- **JSONL file past ~50 MB and integrity checks are getting slow.** The Python HMAC verifier reads the file sequentially. At 50 MB it is fast; at 500 MB it is a tax you pay on every audit run.
- **You want time-travel queries.** "Show me the chain state at 14:00 yesterday" is not expressible against a flat file. XTDB bitemporal storage answers this natively.
- **Multiple writers.** Two processes appending to the same JSONL file race. The last write wins and neither process knows. Postgres with a row-lock trigger serializes concurrent writers correctly.

If none of those apply, keep the JSONL chain.

---

## 2. Architecture overview

```
  ┌─────────────────────────────────────────────────────┐
  │  Agent / bridge daemon                              │
  │  INSERT INTO chain (prev_sha16, opcode_verb, ...)   │
  └─────────────────────┬───────────────────────────────┘
                        │
                        ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  Postgres 16                                                  │
  │                                                               │
  │  chain  ←─ BEFORE INSERT trigger: enforces HMAC,             │
  │              prev_sha16 linkage, mode field, tail-row lock    │
  │           ←─ BEFORE UPDATE/DELETE: raises APPEND_ONLY error  │
  │                                                               │
  │  chain_outbox ←─ AFTER INSERT trigger (same transaction)     │
  └─────────────────────┬────────────────────────────────────────┘
                        │  bridge daemon drains outbox
                        ▼
  ┌────────────────────────────────┐
  │  XTDB 2.1.0                    │
  │  bitemporal mirror             │
  │  SELECT ... FOR SYSTEM_TIME    │
  └────────────────────────────────┘
```

**Postgres with HMAC trigger.** The `BEFORE INSERT` trigger recomputes the expected HMAC-SHA256 server-side, using a key stored in `app.chain_hmac_key`. Fake or missing hashes are rejected with `CHAIN_HMAC_MISMATCH`. The trigger also locks the tail row with `FOR UPDATE` before reading it, serializing concurrent writers so the chain cannot fork.

**XTDB bitemporal mirror.** XTDB stores every row with two time axes (when the event occurred; when it was recorded), enabling `FOR SYSTEM_TIME AS OF` queries without building that logic yourself. Rows arrive via the outbox, not by polling chain directly.

**Outbox pattern.** The `chain_outbox` table is populated by an `AFTER INSERT` trigger in the same database transaction as the chain INSERT. The bridge daemon drains unprocessed outbox rows to XTDB and marks them processed. If the bridge crashes, it restarts and drains from where it left off — no rows are missed and none are double-written.

---

## 3. Quick install

```yaml
# docker-compose.yml excerpt
services:
  postgres:
    image: postgres:16
    container_name: fanout_postgres
    environment:
      POSTGRES_USER: ${PG_USER}
      POSTGRES_PASSWORD: ${PG_PASSWORD}
      POSTGRES_DB: fanout_chain
    ports: ["5432:5432"]

  xtdb:
    image: ghcr.io/xtdb/xtdb:2.1.0
    container_name: fanout_xtdb
    ports: ["5433:5432"]
    environment:
      XTDB_POSTGRES_HOST: postgres
      XTDB_POSTGRES_DB: xtdb_mirror
```

Put `PG_USER`, `PG_PASSWORD`, and `CHAIN_HMAC_KEY` in `.env`. Then create the schema — Section 4 below sketches the seven steps in order; a senior engineer with the architecture overview in Section 2 can author the SQL directly, and the polished migration package is part of the T5 Hardening Sprint engagement in `GIFT_AND_OFFER.md` (it includes Phase B role-demotion steps that need operator-attended review and are not safe to ship as paste-this-and-run).

The migrations should be written as idempotent (`IF NOT EXISTS`, `OR REPLACE`) so they are safe to re-run.

---

## 4. Schema sketch — the seven steps

The schema migrates in seven ordered steps. The polished SQL is operator-internal (see Section 9); this sketch is enough for a senior engineer to author the migrations directly.

**Step 1 — Initial schema**. Create `chain` with HMAC-link columns (`prev_sha16`, `this_sha16`), 8-value opcode-verb CHECK constraint, and JSONB evidence field. Also create `agents`, `vendor_telemetry`, `vendor_posterior`, and `passages_cache`; seed example agent rows and vendor priors.

**Step 2 — HMAC trigger**. Install `pgcrypto`. Define a `chain_compute_hmac()` function over a unit-separator (`0x1F`) canonical payload. Attach it as a `BEFORE INSERT FOR EACH ROW` trigger on `chain` that rejects any `this_sha16` not matching the server-computed HMAC. The trigger also takes a tail-row `FOR UPDATE` lock before reading prev-hash, serializing concurrent writers so the chain cannot fork.

**Step 3 — Mode column**. Add `mode` with a 10-value CHECK enum (`narrative-spec`, `task-completion`, `boring-engineering`, etc.). Update the HMAC function to include `mode` in the canonical payload. Lying about mode now breaks the chain — mode is cryptographically attested.

**Step 4 — Append-only enforcement**. Install `BEFORE UPDATE`, `BEFORE DELETE`, and `BEFORE TRUNCATE` triggers that raise `CHAIN_APPEND_ONLY_VIOLATION` for anyone not holding the `chain_maintenance` role with the maintenance session variable set. Revoke UPDATE, DELETE, TRUNCATE on `chain` from the default `app` role.

**Step 5 — Semantic dedup**. Add `content_digest` as a `GENERATED ALWAYS AS STORED` column (SHA-256 over semantic fields, 16-hex) with a UNIQUE index. Two processes generating identical content have the second INSERT rejected at the database layer.

**Step 6 — Chain outbox**. Create `chain_outbox` with a foreign key to `chain.seq`. Attach an `AFTER INSERT` trigger on `chain` that enqueues a row atomically in the same transaction. A partial index on `processed_at IS NULL` keeps the bridge drain query efficient. Backfill existing chain rows on first run.

**Step 7 — Role separation**. Create `chain_owner` (DDL principal; no login), `bridge_role` (drain outbox only; cannot INSERT into chain or disable triggers), and `audit_role` (read-only everywhere). Transfer `chain` and `chain_outbox` ownership to `chain_owner`. **Phase B** (operator-attended): create a `pg_admin` superuser, then demote `app` to `NOSUPERUSER`. After Phase B, `bridge_role` cannot disable the HMAC trigger because it does not own the table.

---

## 5. Operational discipline

- Chain INSERTs go through the trigger; the trigger computes HMAC server-side and serializes writers via tail-row lock.
- The bridge daemon drains the outbox to XTDB; target lag sub-1 second under normal load.
- A tamper-detection cron compares Postgres against XTDB; any mismatch emits a STRIFE signal.
- RFC 3161 timestamp authority entries can be stored in `meta` for external witness.

---

## 6. What this buys you

- **Tampering proves itself.** Any row where the stored `this_sha16` does not match a fresh HMAC recomputation flags on the next audit run. No trust required.
- **Time-travel.** `SELECT * FROM chain FOR SYSTEM_TIME AS OF TIMESTAMP '...'` returns the chain state at that moment. XTDB handles the bitemporality.
- **Multiple writers do not race.** The tail lock serializes them. No forked chains.
- **Four of nine bypass paths closed mechanically after migration 007 Phase B.** Agent cannot disable its own trigger, cannot UPDATE chain rows, cannot TRUNCATE.

---

## 7. What it costs

- Docker Compose runtime (free).
- ~5 minutes operator time: compose up, apply 7 migrations, set HMAC key, change default role passwords from migration 007.
- ~400–600 MB RAM combined for Postgres 16 and XTDB 2.1.0 under light load.
- One background Python process (bridge daemon); negligible CPU at low-to-medium write rates.

---

## 8. Falsifiable acceptance commands

```bash
# Chain rows visible
psql -h localhost -U $PG_USER -d fanout_chain -c "SELECT count(*) FROM chain;"

# All rows verify — exits 0 on clean chain
python3 hmac_verifier.py

# UPDATE blocked — expect CHAIN_APPEND_ONLY_VIOLATION
psql -h localhost -U $PG_USER -d fanout_chain \
  -c "UPDATE chain SET claim = 'tampered' WHERE seq = 1;"
```

If the third command does not raise the error, step 4 did not apply or the maintenance session variable is set. Check with `SHOW app.chain_append_only_maintenance;`. Postgres ↔ XTDB consistency-watch is a separate tamper-detection daemon; the operator-internal reference implementation runs it as a cron, and the polished script is part of the T5 Hardening Sprint engagement.

---

## 9. The reference implementation

The polished migrations + Phase B role-demotion runbook + tamper-detection daemon are part of the T5 Hardening Sprint engagement in `GIFT_AND_OFFER.md`. They aren't shipped here because:

- Phase B involves operator-attended role-demotion review (`app` to `NOSUPERUSER`); a paste-this-and-run script that ships these steps would be irresponsible without context-aware review of your existing Postgres roles.
- The tamper-detection daemon depends on operator-internal CI plumbing that doesn't generalize cleanly to "everyone's setup."

This isn't a proposed architecture — it's what the reference implementation runs internally. The sketch in Section 4 is enough for a senior engineer to author their own version. If you want the polished, operator-attended implementation applied to your stack: T5 Hardening Sprint is the engagement (scope-locked, fixed-bid).

---

## Self-redteam: what would worry a thoughtful reader

Three real concerns before committing to this upgrade:

**The HMAC key is a single point of failure.** If `app.chain_hmac_key` is wrong, the trigger rejects all inserts. If it is lost, the chain cannot be verified by a third party without it. The default fallback key is visible in migration 002 — operators who do not change it have weaker guarantees than they think.

**Migration 007 Phase B is manual and easy to skip.** Phase A (automated) creates roles and transfers ownership. The critical step — demoting `app` from SUPERUSER — requires a separate manual action with a different credential. Skip Phase B and the bypass the migration is meant to close stays open.

**Importing an existing JSONL chain is not covered here.** The Postgres HMAC canonical payload format must match the Python writer exactly (unit-separator delimiters, specific field order). If you import historical rows with mismatched format, the chain verifies internally but hashes differ from the JSONL originals. That deserves its own runbook before you start.

These are real costs. Measure them against your needs before committing.

---

## Glossary

**HMAC** — Hash-based Message Authentication Code. A cryptographic function combining a secret key with message content; changing any byte changes the output. Used here to prove each chain row was written by a process that knew the key and has not been modified since.

**Bitemporal** — A database property where every record carries two time axes: when the event occurred (valid time) and when it was stored (system time). Enables historical point-in-time queries without custom logic.

**Outbox pattern** — Writing to a primary store and an outbox table in one transaction, then draining the outbox asynchronously to a secondary store. The secondary receives every write even if the bridge restarts mid-batch.

**Append-only** — A constraint preventing UPDATE and DELETE; rows can only be added. Makes the table a tamper-evident audit log.

**Tail lock** — A `SELECT ... FOR UPDATE` on the latest chain row before inserting. Serializes concurrent writers so the chain cannot fork.
