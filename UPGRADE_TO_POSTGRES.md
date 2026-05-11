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

Put `PG_USER`, `PG_PASSWORD`, and `CHAIN_HMAC_KEY` in `.env`. Then apply migrations in order:

```bash
for m in 001 002 003 004 005 006 007; do
  docker exec -i fanout_postgres psql -U $PG_USER -d fanout_chain \
    < migrations/${m}_*.sql
done
```

All migrations are idempotent (`IF NOT EXISTS`, `OR REPLACE`). Safe to re-run.

---

## 4. Mandatory migrations

Files in the `migrations/` directory of this repo.

**001 — Initial schema** (`001_initial_schema.sql`). Creates `chain` with HMAC-link columns (`prev_sha16`, `this_sha16`), 8-value opcode verb CHECK constraint, and JSONB evidence field. Also creates `agents`, `vendor_telemetry`, `vendor_posterior`, and `passages_cache`; seeds example agent rows and vendor priors.

**002 — HMAC trigger** (`002_chain_hmac_trigger.sql`). Installs `pgcrypto`, defines `chain_compute_hmac()` over a unit-separator (`0x1F`) canonical payload, and attaches `chain_hmac_enforce` as a `BEFORE INSERT FOR EACH ROW` trigger. Rejects any `this_sha16` not matching the server-computed HMAC. Tail-row `FOR UPDATE` lock prevents concurrent writers from forking the chain.

**003 — Mode column** (`003_chain_mode_column.sql`). Adds `mode` with a 10-value CHECK enum (`narrative-spec`, `task-completion`, `boring-engineering`, etc.). Updates the HMAC function to include `mode` in the canonical payload. Lying about mode now breaks the chain — mode is cryptographically attested.

**004 — Append-only enforcement** (`004_chain_append_only.sql`). Installs `BEFORE UPDATE`, `BEFORE DELETE`, and `BEFORE TRUNCATE` triggers that raise `CHAIN_APPEND_ONLY_VIOLATION` for anyone not holding the `chain_maintenance` role with the maintenance session variable set. Revokes UPDATE, DELETE, TRUNCATE on `chain` from the default `app` role.

**005 — Semantic dedup** (`005_chain_semantic_dedup.sql`). Adds `content_digest` as a `GENERATED ALWAYS AS STORED` column (SHA-256 over semantic fields, 16-hex) with a UNIQUE index. Two processes generating identical content will have the second INSERT rejected at the database layer.

**006 — Chain outbox** (`006_chain_outbox.sql`). Creates `chain_outbox` with a foreign key to `chain.seq`. An `AFTER INSERT` trigger on `chain` enqueues a row atomically in the same transaction. A partial index on `processed_at IS NULL` makes the bridge drain query efficient. Backfills existing chain rows on first run.

**007 — Role separation** (`007_role_separation.sql`). Creates `chain_owner` (DDL principal; no login), `bridge_role` (drain outbox only; cannot INSERT into chain or disable triggers), and `audit_role` (read-only everywhere). Transfers `chain` and `chain_outbox` ownership to `chain_owner`. **Phase B** (manual operator step): create a `pg_admin` superuser, then demote `app` to `NOSUPERUSER`. After Phase B, `bridge_role` cannot disable the HMAC trigger because it does not own the table.

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

# Postgres ↔ XTDB consistent
python3 chain_tamper_detect.py --once

# UPDATE blocked — expect CHAIN_APPEND_ONLY_VIOLATION
psql -h localhost -U $PG_USER -d fanout_chain \
  -c "UPDATE chain SET claim = 'tampered' WHERE seq = 1;"
```

If the fourth command does not raise the error, migration 004 did not apply or the maintenance session variable is set. Check with `SHOW app.chain_append_only_maintenance;`.

---

## 9. The reference implementation

These are the actual files the operator runs:

```
migrations/
  001_initial_schema.sql
  002_chain_hmac_trigger.sql
  003_chain_mode_column.sql
  004_chain_append_only.sql
  005_chain_semantic_dedup.sql
  006_chain_outbox.sql
  007_role_separation.sql
```

Not a proposed architecture — what the reference implementation runs.

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
