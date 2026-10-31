#!/usr/bin/env bash
# Rsync a local directory to remote over SSH.
#
# Required:
#   DEPLOY_LOCAL   local source directory
#   DEPLOY_REMOTE  user@host:/remote/dir
# Optional:
#   DEPLOY_SSH_PORT   default 22
#   DEPLOY_SSH_PASS   password (uses expect; do not commit)
#   DEPLOY_EXCLUDES   space-separated rsync exclude patterns
#   DEPLOY_DELETE=1   pass --delete (default 0)
set -euo pipefail

: "${DEPLOY_LOCAL:?set DEPLOY_LOCAL}"
: "${DEPLOY_REMOTE:?set DEPLOY_REMOTE}"
DEPLOY_SSH_PORT="${DEPLOY_SSH_PORT:-22}"
DEPLOY_EXCLUDES="${DEPLOY_EXCLUDES:-.git .venv __pycache__ .DS_Store *.log runs models *.pt}"
DEPLOY_DELETE="${DEPLOY_DELETE:-0}"

if [[ ! -d "$DEPLOY_LOCAL" ]]; then
  echo "DEPLOY_LOCAL not a directory: $DEPLOY_LOCAL" >&2
  exit 1
fi

ARGS=(rsync -avz)
if [[ "$DEPLOY_DELETE" == "1" ]]; then
  ARGS+=(--delete)
fi
# shellcheck disable=SC2086
for pat in $DEPLOY_EXCLUDES; do
  ARGS+=(--exclude "$pat")
done
ARGS+=(-e "ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no -p ${DEPLOY_SSH_PORT}")
ARGS+=("${DEPLOY_LOCAL%/}/" "$DEPLOY_REMOTE")

echo "rsync ${DEPLOY_LOCAL%/}/ → ${DEPLOY_REMOTE} (port ${DEPLOY_SSH_PORT}, delete=${DEPLOY_DELETE})"

if [[ -n "${DEPLOY_SSH_PASS:-}" ]]; then
  # Prefer sshpass (no PTY); fall back to expect.
  if command -v sshpass >/dev/null 2>&1; then
    export SSHPASS="$DEPLOY_SSH_PASS"
    # Rewrite -e ssh … into sshpass -e ssh …
    NEW_ARGS=()
    i=0
    while [[ $i -lt ${#ARGS[@]} ]]; do
      if [[ "${ARGS[$i]}" == "-e" ]]; then
        NEW_ARGS+=(-e "sshpass -e ${ARGS[$((i + 1))]}")
        i=$((i + 2))
      else
        NEW_ARGS+=("${ARGS[$i]}")
        i=$((i + 1))
      fi
    done
    "${NEW_ARGS[@]}"
  elif command -v expect >/dev/null 2>&1; then
    export DEPLOY_SSH_PASS
    # Pass cmd to expect via temp file (NUL-safe). 变量名勿用 argv（bash set -u）。
    ARGS_FILE="/tmp/rsync-ssh-deploy.args.$$"
    printf '%s\0' "${ARGS[@]}" > "$ARGS_FILE"
    expect <<EOF
set timeout 600
set pass \$env(DEPLOY_SSH_PASS)
set f [open "$ARGS_FILE" rb]
set data [read \$f]
close \$f
file delete -force "$ARGS_FILE"
set cmd [split \$data "\0"]
if {[lindex \$cmd end] eq ""} { set cmd [lrange \$cmd 0 end-1] }
# TCL: {*}\$cmd 中间不能有空格，否则会变成 spawn *
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
    echo "DEPLOY_SSH_PASS set but neither sshpass nor expect found" >&2
    exit 1
  fi
else
  "${ARGS[@]}"
fi

echo "done"
