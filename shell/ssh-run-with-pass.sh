#!/usr/bin/env bash
# Run a local command that may prompt for an SSH/rsync password via expect.
# Prefer ssh keys; password is optional and must stay in env (never commit).
#
# Usage:
#   SSH_PASS=<pass> bash fawai_shovels/shell/ssh-run-with-pass.sh -- ssh user@host 'cmd'
#   HIPP_DEPLOY_SSH_PASS=<pass> bash fawai_shovels/shell/ssh-run-with-pass.sh -- rsync -av …
# Optional:
#   SSH_PASS_TIMEOUT  expect timeout seconds (default 900)
#
# If neither SSH_PASS nor HIPP_DEPLOY_SSH_PASS is set, runs the command directly.

set -euo pipefail

if [[ "${1:-}" == "--" ]]; then
  shift
fi
if [[ $# -lt 1 ]]; then
  echo "usage: ssh-run-with-pass.sh -- <command> [args…]" >&2
  exit 2
fi

PASS="${SSH_PASS:-${HIPP_DEPLOY_SSH_PASS:-}}"
TIMEOUT="${SSH_PASS_TIMEOUT:-900}"

if [[ -z "$PASS" ]]; then
  exec "$@"
fi

if ! command -v expect >/dev/null 2>&1; then
  echo "SSH_PASS/HIPP_DEPLOY_SSH_PASS set but expect not found" >&2
  exit 1
fi

export SSH_PASS_TIMEOUT="$TIMEOUT"
# Pass argv to expect via NUL-safe temp file (same pattern as rsync-ssh-deploy).
ARGS_FILE="$(mktemp)"
trap 'rm -f "$ARGS_FILE"' EXIT
printf '%s\0' "$@" >"$ARGS_FILE"
export ARGS_FILE
export SSH_PASS="$PASS"

expect <<'EOF'
set timeout $::env(SSH_PASS_TIMEOUT)
set pass $::env(SSH_PASS)
set fh [open $::env(ARGS_FILE) rb]
set data [read $fh]
close $fh
set cmd [split $data "\0"]
# drop trailing empty from final NUL
if {[lindex $cmd end] eq ""} {
  set cmd [lrange $cmd 0 end-1]
}
spawn {*}$cmd
expect {
  -re "(?i)yes/no" { send -- "yes\r"; exp_continue }
  -re "(?i)password:" { send -- "$pass\r"; exp_continue }
  eof {}
  timeout { puts stderr "TIMEOUT"; exit 1 }
}
catch wait result
set code [lindex $result 3]
exit $code
EOF
