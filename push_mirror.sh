#!/usr/bin/env bash
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

# push_mirror.sh — push public_mirror_staging to GitHub and/or Codeberg
# Usage: ./push_mirror.sh [--dry-run] [--github-only] [--codeberg-only] [--test]
# Reads credentials from .env in the same directory (or SIGRUN_SECRETS_ENV if set).

set -euo pipefail

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
DRY_RUN=0
GITHUB_ONLY=0
CODEBERG_ONLY=0
TEST_MODE=0

for arg in "$@"; do
  case "$arg" in
    --dry-run)      DRY_RUN=1 ;;
    --github-only)  GITHUB_ONLY=1 ;;
    --codeberg-only) CODEBERG_ONLY=1 ;;
    --test)         TEST_MODE=1 ;;
    *) echo "Unknown flag: $arg"; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SIGRUN_SECRETS_ENV:-$SCRIPT_DIR/.env}"

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------
if [[ -f "$ENV_FILE" ]]; then
  set -a; . "$ENV_FILE"; set +a
  echo "[push_mirror] loaded env from $ENV_FILE"
else
  echo "[push_mirror] WARN: $ENV_FILE not found — relying on environment variables"
fi

GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_USER="${GITHUB_USER:-}"
CODEBERG_TOKEN="${CODEBERG_TOKEN:-}"
CODEBERG_USER="${CODEBERG_USER:-}"
MIRROR_REPO_NAME="${MIRROR_REPO_NAME:-}"
COMMIT_MSG="${COMMIT_MSG:-mirror: automated push $(date -u +%Y-%m-%dT%H:%M:%SZ)}"

# ---------------------------------------------------------------------------
# Safety net — refuse to push if internal terms found in tracked files
# ---------------------------------------------------------------------------
safety_check() {
  local dir="$1"
  local found
  # git grep runs inside the repo — reliable across platforms
  # Check both accented (Sigrún) and plain (Sigrun) to catch any variant
  found=$(git -C "$dir" grep -lE 'Sigrún|Sigrun|valkyrie' 2>/dev/null || true)
  if [[ -n "$found" ]]; then
    echo ""
    echo "ERROR: internal terms found in tracked files. Push aborted."
    echo "Files containing matches:"
    echo "$found"
    echo ""
    echo "Scrub these files before pushing to a public remote."
    exit 2
  fi
}

# ---------------------------------------------------------------------------
# Git init (idempotent)
# ---------------------------------------------------------------------------
init_repo() {
  local dir="$1"
  if [[ ! -d "$dir/.git" ]]; then
    echo "[push_mirror] git init $dir"
    [[ $DRY_RUN -eq 0 ]] && git -C "$dir" init
    [[ $DRY_RUN -eq 1 ]] && echo "  DRY-RUN: would run: git init $dir"
  else
    echo "[push_mirror] existing git repo at $dir"
  fi
}

# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------
stage_and_commit() {
  local dir="$1"
  echo "[push_mirror] staging all files"
  if [[ $DRY_RUN -eq 0 ]]; then
    git -C "$dir" add -A
    git -C "$dir" commit --allow-empty -m "$COMMIT_MSG" && echo "[push_mirror] committed" || echo "[push_mirror] nothing new to commit"
  else
    echo "  DRY-RUN: would run: git add -A && git commit --allow-empty -m '$COMMIT_MSG'"
  fi
}

# ---------------------------------------------------------------------------
# Remote helpers
# ---------------------------------------------------------------------------
set_remote() {
  local dir="$1" name="$2" url="$3"
  if git -C "$dir" remote get-url "$name" &>/dev/null; then
    echo "[push_mirror] updating remote $name"
    [[ $DRY_RUN -eq 0 ]] && git -C "$dir" remote set-url "$name" "$url"
    [[ $DRY_RUN -eq 1 ]] && echo "  DRY-RUN: would run: git remote set-url $name <url-with-token>"
  else
    echo "[push_mirror] adding remote $name"
    [[ $DRY_RUN -eq 0 ]] && git -C "$dir" remote add "$name" "$url"
    [[ $DRY_RUN -eq 1 ]] && echo "  DRY-RUN: would run: git remote add $name <url-with-token>"
  fi
}

push_remote() {
  local dir="$1" name="$2"
  echo "[push_mirror] pushing to $name"
  if [[ $DRY_RUN -eq 0 ]]; then
    if git -C "$dir" push "$name" main --force-with-lease; then
      echo "[push_mirror] $name push OK"
    else
      echo ""
      echo "ERROR: push to $name failed."
      echo "  - Verify the token has 'repo' (GitHub) or 'repository' (Codeberg) scope."
      echo "  - Verify the repo exists on the remote host."
      echo "  - If the remote has diverged, resolve manually — force-with-lease protects you from overwriting unseen commits."
      exit 3
    fi
  else
    echo "  DRY-RUN: would run: git push $name main --force-with-lease"
  fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  local dir="$SCRIPT_DIR"

  echo "[push_mirror] target directory: $dir"
  [[ $DRY_RUN -eq 1 ]] && echo "[push_mirror] DRY-RUN mode — no writes or pushes"

  safety_check "$dir"

  init_repo "$dir"
  stage_and_commit "$dir"

  # GitHub
  if [[ $CODEBERG_ONLY -eq 0 ]]; then
    if [[ -z "$GITHUB_TOKEN" || -z "$GITHUB_USER" || -z "$MIRROR_REPO_NAME" ]]; then
      echo "[push_mirror] SKIP GitHub — GITHUB_TOKEN / GITHUB_USER / MIRROR_REPO_NAME not set"
    else
      local gh_url="https://${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${MIRROR_REPO_NAME}.git"
      set_remote "$dir" github "$gh_url"
      push_remote "$dir" github
    fi
  fi

  # Codeberg
  if [[ $GITHUB_ONLY -eq 0 ]]; then
    if [[ -z "$CODEBERG_TOKEN" || -z "$CODEBERG_USER" || -z "$MIRROR_REPO_NAME" ]]; then
      echo "[push_mirror] SKIP Codeberg — CODEBERG_TOKEN / CODEBERG_USER / MIRROR_REPO_NAME not set"
    else
      local cb_url="https://${CODEBERG_USER}:${CODEBERG_TOKEN}@codeberg.org/${CODEBERG_USER}/${MIRROR_REPO_NAME}.git"
      set_remote "$dir" codeberg "$cb_url"
      push_remote "$dir" codeberg
    fi
  fi

  echo ""
  echo "push complete; confidence 7/8"
}

# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
run_tests() {
  local fail=0

  echo "=== push_mirror.sh smoke tests ==="

  # T1: required env vars documented in .env.example
  echo -n "T1 env vars documented in .env.example ... "
  local example="$SCRIPT_DIR/.env.example"
  for var in GITHUB_TOKEN GITHUB_USER CODEBERG_TOKEN CODEBERG_USER MIRROR_REPO_NAME; do
    if ! grep -q "^${var}=" "$example" 2>/dev/null; then
      echo "FAIL — $var missing from .env.example"
      fail=1
    fi
  done
  [[ $fail -eq 0 ]] && echo "PASS"

  # T2: safety grep catches internal terms (positive case)
  echo -n "T2 safety grep catches 'Sigrun' in a temp file ... "
  local tmpdir
  tmpdir=$(mktemp -d)
  git -C "$tmpdir" init -q
  echo "Sigrun is here" > "$tmpdir/bad.txt"
  git -C "$tmpdir" add bad.txt
  git -C "$tmpdir" commit -q -m "test"
  local t2_found
  t2_found=$(git -C "$tmpdir" grep -lE 'Sigrún|Sigrun|valkyrie' 2>/dev/null || true)
  if [[ -n "$t2_found" ]]; then
    echo "PASS"
  else
    echo "FAIL — grep did not catch Sigrun"
    fail=1
  fi
  rm -rf "$tmpdir"

  # T3: safety grep passes on clean content
  echo -n "T3 safety grep passes on clean file ... "
  local tmpdir2
  tmpdir2=$(mktemp -d)
  git -C "$tmpdir2" init -q
  echo "hello world" > "$tmpdir2/clean.txt"
  git -C "$tmpdir2" add clean.txt
  git -C "$tmpdir2" commit -q -m "test"
  local t3_found
  t3_found=$(git -C "$tmpdir2" grep -lE 'Sigrún|Sigrun|valkyrie' 2>/dev/null || true)
  if [[ -n "$t3_found" ]]; then
    echo "FAIL — clean file falsely matched"
    fail=1
  else
    echo "PASS"
  fi
  rm -rf "$tmpdir2"

  # T4: --dry-run produces output without pushing
  echo -n "T4 --dry-run produces output ... "
  local dry_out
  dry_out=$(GITHUB_TOKEN=fake GITHUB_USER=fake CODEBERG_TOKEN=fake CODEBERG_USER=fake \
    MIRROR_REPO_NAME=fake bash "$SCRIPT_DIR/push_mirror.sh" --dry-run 2>&1 || true)
  if echo "$dry_out" | grep -q "DRY-RUN"; then
    echo "PASS"
  else
    echo "FAIL — no DRY-RUN marker in output"
    fail=1
  fi

  echo ""
  if [[ $fail -eq 0 ]]; then
    echo "All tests PASS; confidence 7/8"
  else
    echo "Some tests FAILED"
    exit 1
  fi
}

if [[ $TEST_MODE -eq 1 ]]; then
  run_tests
else
  main
fi
