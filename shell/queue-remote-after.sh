#!/usr/bin/env bash
# Start a waiter on a remote host. The waiter polls ps and runs one command
# after every blocking process has exited. It does not kill existing jobs.
#
# Required:
#   QUEUE_SSH           user@host
#   QUEUE_REMOTE_CWD    remote working directory
#   QUEUE_BLOCK         cmdline substrings joined by |
#   QUEUE_RUN           remote command run when QUEUE_BLOCK is clear
# Optional:
#   QUEUE_SSH_PORT      default 22
#   QUEUE_SSH_PASS      password, env only; prefers sshpass
#   QUEUE_PYTHON        remote interpreter, default python3
#   QUEUE_WAIT_ID       token shown in ps, default next
#   QUEUE_POLL_SECONDS  default 60, clamped to 5..3600 by the waiter
#   QUEUE_LOG           remote log path, default <cwd>/queue-<wait-id>.log
#
# A second start with the same QUEUE_WAIT_ID exits without launching another waiter.
set -euo pipefail

: "${QUEUE_SSH:?set QUEUE_SSH}"
: "${QUEUE_REMOTE_CWD:?set QUEUE_REMOTE_CWD}"
: "${QUEUE_BLOCK:?set QUEUE_BLOCK}"
: "${QUEUE_RUN:?set QUEUE_RUN}"

QUEUE_SSH_PORT="${QUEUE_SSH_PORT:-22}"
QUEUE_PYTHON="${QUEUE_PYTHON:-python3}"
QUEUE_WAIT_ID="${QUEUE_WAIT_ID:-next}"
QUEUE_POLL_SECONDS="${QUEUE_POLL_SECONDS:-60}"
QUEUE_LOG="${QUEUE_LOG:-queue-${QUEUE_WAIT_ID}.log}"

if [[ ! "$QUEUE_WAIT_ID" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "QUEUE_WAIT_ID must match [A-Za-z0-9._-]+" >&2
  exit 2
fi
if [[ "$QUEUE_BLOCK" == *$'\n'* || "$QUEUE_RUN" == *$'\n'* || "$QUEUE_REMOTE_CWD" == *$'\n'* || "$QUEUE_LOG" == *$'\n'* ]]; then
  echo "QUEUE_BLOCK, QUEUE_RUN, QUEUE_REMOTE_CWD, and QUEUE_LOG must be single-line" >&2
  exit 2
fi
if [[ "$QUEUE_REMOTE_CWD" == *" "* || "$QUEUE_LOG" == *" "* ]]; then
  echo "QUEUE_REMOTE_CWD and QUEUE_LOG must not contain spaces" >&2
  exit 2
fi
if [[ -z "${QUEUE_BLOCK//|/}" || -z "${QUEUE_BLOCK// /}" ]]; then
  echo "QUEUE_BLOCK is empty" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WAIT_SRC="$ROOT/python/queue-remote-wait.py"
if [[ ! -f "$WAIT_SRC" ]]; then
  echo "missing waiter: $WAIT_SRC" >&2
  exit 1
fi

ENV_FILE="$(mktemp)"
trap 'rm -f "$ENV_FILE"' EXIT
{
  printf 'QUEUE_BLOCK=%s\n' "$QUEUE_BLOCK"
  printf 'QUEUE_RUN=%s\n' "$QUEUE_RUN"
  printf 'QUEUE_POLL_SECONDS=%s\n' "$QUEUE_POLL_SECONDS"
  printf 'QUEUE_CWD=%s\n' "$QUEUE_REMOTE_CWD"
} > "$ENV_FILE"

_ssh() {
  if [[ -n "${QUEUE_SSH_PASS:-}" ]]; then
    export SSHPASS="$QUEUE_SSH_PASS"
    sshpass -e ssh \
      -o StrictHostKeyChecking=no \
      -o PreferredAuthentications=password \
      -o PubkeyAuthentication=no \
      -p "$QUEUE_SSH_PORT" \
      "$QUEUE_SSH" "$@"
  else
    ssh -o StrictHostKeyChecking=no -p "$QUEUE_SSH_PORT" "$QUEUE_SSH" "$@"
  fi
}

_scp_to() {
  local src="$1"
  local dest="$2"
  if [[ -n "${QUEUE_SSH_PASS:-}" ]]; then
    export SSHPASS="$QUEUE_SSH_PASS"
    sshpass -e scp \
      -o StrictHostKeyChecking=no \
      -o PreferredAuthentications=password \
      -o PubkeyAuthentication=no \
      -P "$QUEUE_SSH_PORT" \
      "$src" "${QUEUE_SSH}:${dest}"
  else
    scp -o StrictHostKeyChecking=no -P "$QUEUE_SSH_PORT" "$src" "${QUEUE_SSH}:${dest}"
  fi
}

echo "queue ${QUEUE_WAIT_ID} on ${QUEUE_SSH} cwd=${QUEUE_REMOTE_CWD}"

_ssh "mkdir -p $(printf '%q' "$QUEUE_REMOTE_CWD/.queue-wait")"
_scp_to "$WAIT_SRC" "$QUEUE_REMOTE_CWD/.queue-wait/queue-remote-wait.py"
_scp_to "$ENV_FILE" "$QUEUE_REMOTE_CWD/.queue-wait/${QUEUE_WAIT_ID}.env"

_ssh bash -s -- "$QUEUE_REMOTE_CWD" "$QUEUE_PYTHON" "$QUEUE_WAIT_ID" "$QUEUE_LOG" << 'EOF'
set -euo pipefail
cwd="$1"
py="$2"
wid="$3"
log="$4"
marker="queue-remote-wait.py ${wid}"
if ps -eo args | grep -F "$marker" | grep -v grep >/dev/null; then
  echo "already running: ${wid}"
else
  case "$log" in
    /*) ;;
    *) log="${cwd}/${log}" ;;
  esac
  cd "$cwd"
  nohup "$py" -u "${cwd}/.queue-wait/queue-remote-wait.py" "$wid" > "$log" 2>&1 < /dev/null &
  echo "started pid=$! log=${log}"
  sleep 1
fi
echo "=== log ==="
case "$log" in
  /*) use_log="$log" ;;
  *) use_log="${cwd}/${log}" ;;
esac
tail -n 20 "$use_log" 2>/dev/null || true
echo "=== waiter ==="
ps -eo pid,etime,args | grep -F "$marker" | grep -v grep || true
EOF
