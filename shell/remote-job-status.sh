#!/usr/bin/env bash
# Query recent job status on a remote training host (running / queued / done).
# Does not kill processes. Password only via env.
#
# Required:
#   STATUS_SSH          user@host
#   STATUS_REMOTE_CWD   remote working directory (e.g. FgBgAug root)
# Optional:
#   STATUS_SSH_PORT     default 22
#   STATUS_SSH_PASS     password; prefers sshpass
#   STATUS_DAYS         only waiter/log items within N days (default 7; 0=all)
#   STATUS_LIMIT        max rows after keeping running/queued (default 20; 0=all)
#   STATUS_JSON         1 → JSON output
#   STATUS_PYTHON       remote interpreter, default python3
#
# Example:
#   STATUS_SSH=user@host STATUS_REMOTE_CWD=/path/to/FgBgAug STATUS_SSH_PORT=22 \
#   STATUS_SSH_PASS=<pass> STATUS_DAYS=3 STATUS_LIMIT=15 \
#   bash fawai_shovels/shell/remote-job-status.sh
set -euo pipefail

: "${STATUS_SSH:?set STATUS_SSH}"
: "${STATUS_REMOTE_CWD:?set STATUS_REMOTE_CWD}"

STATUS_SSH_PORT="${STATUS_SSH_PORT:-22}"
STATUS_PYTHON="${STATUS_PYTHON:-python3}"
STATUS_DAYS="${STATUS_DAYS:-7}"
STATUS_LIMIT="${STATUS_LIMIT:-20}"
STATUS_JSON="${STATUS_JSON:-0}"

if [[ "$STATUS_REMOTE_CWD" == *" "* ]]; then
  echo "STATUS_REMOTE_CWD must not contain spaces" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROBE="$ROOT/python/remote-job-status.py"
if [[ ! -f "$PROBE" ]]; then
  echo "missing probe: $PROBE" >&2
  exit 1
fi

_ssh() {
  if [[ -n "${STATUS_SSH_PASS:-}" ]]; then
    export SSHPASS="$STATUS_SSH_PASS"
    sshpass -e ssh \
      -o StrictHostKeyChecking=no \
      -o PreferredAuthentications=password \
      -o PubkeyAuthentication=no \
      -p "$STATUS_SSH_PORT" \
      "$STATUS_SSH" "$@"
  else
    ssh -o StrictHostKeyChecking=no -p "$STATUS_SSH_PORT" "$STATUS_SSH" "$@"
  fi
}

_scp_to() {
  local src="$1"
  local dst="$2"
  if [[ -n "${STATUS_SSH_PASS:-}" ]]; then
    export SSHPASS="$STATUS_SSH_PASS"
    sshpass -e scp \
      -o StrictHostKeyChecking=no \
      -o PreferredAuthentications=password \
      -o PubkeyAuthentication=no \
      -P "$STATUS_SSH_PORT" \
      "$src" "$STATUS_SSH:$dst"
  else
    scp -o StrictHostKeyChecking=no -P "$STATUS_SSH_PORT" "$src" "$STATUS_SSH:$dst"
  fi
}

REMOTE_PROBE="${STATUS_REMOTE_CWD}/.queue-wait/remote-job-status.py"
_ssh "mkdir -p '${STATUS_REMOTE_CWD}/.queue-wait'"
_scp_to "$PROBE" "$REMOTE_PROBE"

EXTRA_ARGS=(--cwd "${STATUS_REMOTE_CWD}" --days "${STATUS_DAYS}" --limit "${STATUS_LIMIT}")
if [[ "$STATUS_JSON" == "1" || "$STATUS_JSON" == "true" || "$STATUS_JSON" == "yes" ]]; then
  EXTRA_ARGS+=(--json)
fi

# Build a remote argv string without embedding secrets.
REMOTE_CMD=$(printf '%q ' "${STATUS_PYTHON}" "${REMOTE_PROBE}" "${EXTRA_ARGS[@]}")
echo "status ${STATUS_SSH} cwd=${STATUS_REMOTE_CWD} days=${STATUS_DAYS} limit=${STATUS_LIMIT}"
_ssh "cd $(printf '%q' "${STATUS_REMOTE_CWD}") && ${REMOTE_CMD}"
