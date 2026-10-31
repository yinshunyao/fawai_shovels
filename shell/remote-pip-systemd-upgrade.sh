#!/usr/bin/env bash
# On a remote host: pip install -U a package (optional pin) and systemctl restart a unit.
#
# Required:
#   REMOTE_SSH          user@host
#   REMOTE_PIP_PACKAGE  e.g. hipp-https-agent
# Optional:
#   REMOTE_PIP_VERSION  pin version (omit for latest)
#   REMOTE_SYSTEMD_UNIT systemd unit name (default: same as package with _ → - heuristics unused; default hipp-agent)
#   REMOTE_PIP_INDEX    default https://pypi.org/simple
#   REMOTE_SSH_PASS / HIPP_DEPLOY_SSH_PASS / SSH_PASS
#   REMOTE_VERIFY_CMD   extra remote check after restart (default: try package CLI --version)

set -euo pipefail

: "${REMOTE_SSH:?set REMOTE_SSH}"
: "${REMOTE_PIP_PACKAGE:?set REMOTE_PIP_PACKAGE}"
UNIT="${REMOTE_SYSTEMD_UNIT:-hipp-agent}"
INDEX="${REMOTE_PIP_INDEX:-https://pypi.org/simple}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNNER="$SCRIPT_DIR/ssh-run-with-pass.sh"

if [[ -n "${REMOTE_PIP_VERSION:-}" ]]; then
  SPEC="${REMOTE_PIP_PACKAGE}==${REMOTE_PIP_VERSION}"
else
  SPEC="${REMOTE_PIP_PACKAGE}"
fi

VERIFY="${REMOTE_VERIFY_CMD:-command -v hipp-agent; (hipp-agent --version 2>/dev/null || true)}"
# One line only: expect spawn breaks on embedded newlines.
REMOTE_CMD="set -e; python3 -m pip install -U -i '${INDEX}' '${SPEC}'; systemctl restart '${UNIT}'; sleep 1; systemctl is-active '${UNIT}'; ${VERIFY}"

export SSH_PASS="${REMOTE_SSH_PASS:-${HIPP_DEPLOY_SSH_PASS:-${SSH_PASS:-}}}"
bash "$RUNNER" -- ssh -o StrictHostKeyChecking=no "$REMOTE_SSH" "$REMOTE_CMD"
echo "upgraded $REMOTE_SSH -> ${SPEC} ($UNIT)"
