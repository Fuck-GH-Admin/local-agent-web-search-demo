#!/usr/bin/env bash
# Dry-run by default. To prune merged historical branches, use --apply.
# Safety: each branch must have 0 commits ahead of main and 0 open PRs.
# Before deletion, create/check a same-named lightweight tag at its exact SHA.
# This retains historical git-clone --branch and source references.
set -euo pipefail

REPO="Fuck-GH-Admin/local-agent-web-search-demo"
MODE="${1:---dry-run}"
case "$MODE" in
  --dry-run|--apply) ;;
  *) printf 'Usage: bash %s [--dry-run|--apply]\n' "$0" >&2; exit 64 ;;
esac

command -v gh >/dev/null || { printf 'ERROR: GitHub CLI (gh) is required.\n' >&2; exit 127; }
gh auth status >/dev/null 2>&1 || { printf 'ERROR: gh auth login is required.\n' >&2; exit 2; }

# Audited on 2026-10-14; revalidate every branch live before deletion.
MERGED=(
  'b00/environment-baseline'
  'feat/b01-searxng-search'
  'feat/b02-httpx-fetch'
  'feat/b03-parser-comparison'
  'feat/b04-core-cli'
  'feat/b05-fastapi-webui'
  'feat/b06-agent-tool-loop'
  'feat/b06-readiness-audit'
  'feat/b07-agent-interfaces'
  'feat/b07-real-model'
  'feat/b08-final-validation'
  'feat/live-quality-url-security'
)

main_sha="$(gh api "repos/${REPO}/git/ref/heads/main" --jq '.object.sha')"
printf 'Repository: %s\nmain SHA:   %s\nmode:       %s\n\n' "$REPO" "$main_sha" "$MODE"

for name in "${MERGED[@]}"; do
  if ! sha="$(gh api "repos/${REPO}/git/ref/heads/${name}" --jq '.object.sha' 2>/dev/null)"; then
    printf '[SKIP] %s: branch already absent\n' "$name"
    continue
  fi
  ahead="$(gh api "repos/${REPO}/compare/main...${name}" --jq '.ahead_by')" || {
    printf '[SKIP] %s: cannot compare to main\n' "$name" >&2
    continue
  }
  if [[ "$ahead" != 0 ]]; then
    printf '[KEEP] %s: %s commit(s) absent from main\n' "$name" "$ahead"
    continue
  fi
  open_prs="$(gh pr list --repo "$REPO" --state open --head "$name" --json number --jq 'length')" || {
    printf '[SKIP] %s: cannot check open PRs\n' "$name" >&2
    continue
  }
  if [[ "$open_prs" != 0 ]]; then
    printf '[KEEP] %s: has %s open PR(s)\n' "$name" "$open_prs"
    continue
  fi
  tag_sha=""
  if tag_sha="$(gh api "repos/${REPO}/git/ref/tags/${name}" --jq '.object.sha' 2>/dev/null)"; then
    if [[ "$tag_sha" != "$sha" ]]; then
      printf '[KEEP] %s: same-named tag points elsewhere (%s)\n' "$name" "$tag_sha" >&2
      continue
    fi
  fi
  if [[ "$MODE" == '--dry-run' ]]; then
    printf '[DRY-RUN] tag and delete: %-41s %s\n' "$name" "$sha"
    continue
  fi
  if [[ -z "$tag_sha" ]]; then
    gh api --method POST "repos/${REPO}/git/refs" \
      --field "ref=refs/tags/${name}" --field "sha=${sha}" >/dev/null
  fi
  tag_sha="$(gh api "repos/${REPO}/git/ref/tags/${name}" --jq '.object.sha')"
  if [[ "$tag_sha" != "$sha" ]]; then
    printf '[KEEP] %s: backup tag verification failed\n' "$name" >&2
    continue
  fi
  current="$(gh api "repos/${REPO}/git/ref/heads/${name}" --jq '.object.sha')" || continue
  if [[ "$current" != "$sha" ]]; then
    printf '[KEEP] %s: branch moved during cleanup\n' "$name" >&2
    continue
  fi
  gh api --method DELETE "repos/${REPO}/git/refs/heads/${name}" >/dev/null
  printf '[ARCHIVED] %-41s %s\n' "$name" "$sha"
done

printf '\nPRESERVED: main; research/e00-benchmark-availability-20261014; codex/miku-small-runner-20261014; feat/b00-foundation; feat/b07-real-model-prep; feat/b07-real-model-integration.\n'
