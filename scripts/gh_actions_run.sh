#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/gh_actions_run.sh [--repo OWNER/REPO] [--workflow NAME] [--ref REF]

Trigger a GitHub Actions workflow using gh CLI.

Options:
  --repo OWNER/REPO   Target repository (default: current repo)
  --workflow NAME     Workflow file or name (default: ci-cd.yml)
  --ref REF           Git ref (default: main)
  -h, --help          Show this help
USAGE
}

REPO=""
WORKFLOW="ci-cd.yml"
REF="main"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="$2"
      shift 2
      ;;
    --workflow)
      WORKFLOW="$2"
      shift 2
      ;;
    --ref)
      REF="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${GH_TOKEN:-}" && -n "${GITAPI:-}" ]]; then
  export GH_TOKEN="${GITAPI}"
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required. Install from https://cli.github.com/" >&2
  exit 1
fi

if [[ -z "$REPO" ]]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
fi

gh workflow run "$WORKFLOW" --repo "$REPO" --ref "$REF"
