#!/usr/bin/env bash
# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
#
# Make an archive for an independent review that carries what a push would carry, and nothing more (Amendment A4, R2).
#
#     tools/make_review_archive.sh [BRANCH] [OUT_DIR] [LABEL]
#
# BRANCH defaults to the current branch; OUT_DIR to build/review (ignored by git). It writes
# OUT_DIR/manacitra-<label>-<commit>.zip and, beside it, the zip's SHA-256 in OUT_DIR/manacitra-<label>-<commit>.zip.sha256.
#
# The label names what the pull request carries, not the branch, whose name is fixed when it is opened: it is the
# latest amendment cited ("Amendment A7") in the messages of the commits the branch adds to the base branch (BASE,
# default main), lower-cased ("a7"). LABEL overrides it; with no amendment cited and no LABEL, the branch name is used.
#
# A working .git holds more than a push does: reflogs, other branches, and objects no ref reaches. So the archive is
# made from a fresh clone, `git clone --no-local --single-branch --branch BRANCH`, which copies only the objects
# reachable from that branch. The clone's own traces are then removed, because they name whoever ran it: the remote
# (a local path), the remote-tracking refs and the reflogs (the cloner's identity and the path cloned from). The
# script stops if any reflog remains, and it runs the identifier scan on the clone's tree and its git metadata
# (tools/scan_secrets.py and --git) before zipping: a finding stops it, and nothing is written.
set -euo pipefail

ROOT="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
BRANCH="${1:-$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)}"
OUT="${2:-$ROOT/build/review}"
PY="${PYTHON:-python3}"
[ -x "$ROOT/.venv/bin/python" ] && PY="${PYTHON:-$ROOT/.venv/bin/python}"

git -C "$ROOT" rev-parse --verify --quiet "refs/heads/$BRANCH" >/dev/null || {
    echo "no local branch named $BRANCH" >&2
    exit 2
}
COMMIT="$(git -C "$ROOT" rev-parse --short=12 "refs/heads/$BRANCH")"
BASE="${BASE:-main}"
RANGE="refs/heads/$BRANCH"
git -C "$ROOT" rev-parse --verify --quiet "refs/heads/$BASE" >/dev/null && RANGE="refs/heads/$BASE..refs/heads/$BRANCH"
LATEST="$(git -C "$ROOT" log --format=%B "$RANGE" | grep -oE 'Amendment A[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1 || true)"
LABEL="${3:-${LATEST:+a$LATEST}}"
LABEL="${LABEL:-${BRANCH//\//-}}"
NAME="manacitra-$LABEL-$COMMIT"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
git clone --quiet --no-local --single-branch --branch "$BRANCH" "$ROOT" "$WORK/manacitra"
CLONE="$WORK/manacitra"

# The clone's traces: the remote and its tracking refs, and every reflog
git -C "$CLONE" remote remove origin
git -C "$CLONE" reflog expire --expire=now --all
rm -rf "$CLONE/.git/logs"
git -C "$CLONE" gc --quiet --prune=now
if [ -e "$CLONE/.git/logs" ] || git -C "$CLONE" remote | grep -q .; then
    echo "the clone still holds a reflog or a remote; nothing written" >&2
    exit 1
fi

# What the archive carries: one branch, every commit reachable from it, and the scans on both
echo "branch $BRANCH at $COMMIT; $(git -C "$CLONE" rev-list --count HEAD) reachable commits; refs:"
git -C "$CLONE" for-each-ref --format='  %(refname)'
"$PY" "$CLONE/tools/scan_secrets.py"
(cd "$CLONE" && "$PY" tools/scan_secrets.py --git)

mkdir -p "$OUT"
rm -f "$OUT/$NAME.zip" "$OUT/$NAME.zip.sha256"
(cd "$WORK" && zip -qrX "$OUT/$NAME.zip" manacitra)
if command -v sha256sum >/dev/null; then
    (cd "$OUT" && sha256sum "$NAME.zip" >"$NAME.zip.sha256")
else
    (cd "$OUT" && shasum -a 256 "$NAME.zip" >"$NAME.zip.sha256")
fi
echo "wrote $OUT/$NAME.zip"
cat "$OUT/$NAME.zip.sha256"
