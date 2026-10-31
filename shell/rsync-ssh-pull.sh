#!/usr/bin/env bash
# Rsync from remote over SSH into a local directory (pull).
#
# Required:
#   PULL_REMOTE   user@host:/remote/path  (file or directory)
#   PULL_LOCAL    local destination directory (created if missing)
# Optional:
#   PULL_SSH_PORT   default 22
#   PULL_SSH_PASS   password (uses expect; do not commit)
#   PULL_EXCLUDES   space-separated rsync exclude patterns (default empty)
#   PULL_DELETE=1   pass --delete (default 0)
set -euo pipefail

: "${PULL_REMOTE:?set PULL_REMOTE}"
: "${PULL_LOCAL:?set PULL_LOCAL}"
PULL_SSH_PORT="${PULL_SSH_PORT:-22}"
PULL_EXCLUDES="${PULL_EXCLUDES:-}"
PULL_DELETE="${PULL_DELETE:-0}"

mkdir -p "$PULL_LOCAL"

ARGS=(rsync -avz)
if [[ "$PULL_DELETE" == "1" ]]; then
  ARGS+=(--delete)
fi
# shellcheck disable=SC2086
for pat in $PULL_EXCLUDES; do
  ARGS+=(--exclude "$pat")
done
ARGS+=(-e "ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no -p ${PULL_SSH_PORT}")
ARGS+=("$PULL_REMOTE" "${PULL_LOCAL%/}/")

echo "rsync ${PULL_REMOTE} → ${PULL_LOCAL%/}/ (port ${PULL_SSH_PORT}, delete=${PULL_DELETE})"

if [[ -n "${PULL_SSH_PASS:-}" ]]; then
  # Prefer sshpass (no PTY); fall back to expect.
  if command -v sshpass >/dev/null 2>&1; then
    export SSHPASS="$PULL_SSH_PASS"
    sshpass -e "${ARGS[@]}"
  elif command -v expect >/dev/null 2>&1; then
    export PULL_SSH_PASS
    ARGS_FILE="/tmp/rsync-ssh-pull.args.$$"
    printf '%s\0' "${ARGS[@]}" > "$ARGS_FILE"
    expect <<EOF
set timeout 600
set pass \$env(PULL_SSH_PASS)
set f [open "$ARGS_FILE" rb]
set data [read \$f]
close \$f
file delete -force "$ARGS_FILE"
set cmd [split \$data "\0"]
if {[lindex \$cmd end] eq ""} { set cmd [lrange \$cmd 0 end-1] }
spawn {*}\$cmd
expect {
  -re "(?i)yes/no" { send -- "yes\r"; exp_continue }
  -re "(?i)password:" { send -- "\$pass\r"; exp_continue }
  eof
}
catch wait result
exit [lindex \$result 3]
EOF
  else
    echo "PULL_SSH_PASS set but neither sshpass nor expect found" >&2
    exit 1
  fi
else
  "${ARGS[@]}"
fi

echo "done"
