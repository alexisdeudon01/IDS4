#!/usr/bin/env bash
set -euo pipefail

cd /home/tor/Downloads/oooo/oi

PI_IP="100.118.244.54"
PI_USER="pi"

# Demande la clé Tailscale sans l'afficher
read -rsp "TAILSCALE auth key: " TSKEYAUTH; echo

# Utilise GITAPI si présent pour GH_TOKEN (sinon demande)
if [[ -z "${GH_TOKEN:-}" && -n "${GITAPI:-}" ]]; then
  export GH_TOKEN="$GITAPI"
fi
if [[ -z "${GH_TOKEN:-}" ]]; then
  read -rsp "GitHub token (GH_TOKEN): " GH_TOKEN; echo
  export GH_TOKEN
fi

KEY_PATH="$HOME/.ssh/pi_github_actions"
if [[ ! -f "$KEY_PATH" ]]; then
  ssh-keygen -t rsa -b 4096 -m PEM -N "" -f "$KEY_PATH" -C "github-actions"
fi

# Ajoute la clé publique au Pi
if command -v ssh-copy-id >/dev/null 2>&1; then
  ssh-copy-id -i "${KEY_PATH}.pub" "${PI_USER}@${PI_IP}"
else
  cat "${KEY_PATH}.pub" | ssh "${PI_USER}@${PI_IP}" \
    'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
fi

# Variables lues par scripts/actions_secrets.map
export PI_IP PI_USER TSKEYAUTH
export PI="$(cat "$KEY_PATH")"

./scripts/gh_actions_sync_secrets.sh --repo OWNER/REPO

# Nettoyage
unset PI TSKEYAUTH