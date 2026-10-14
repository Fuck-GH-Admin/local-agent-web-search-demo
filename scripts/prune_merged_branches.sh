#!/usr/bin/env bash
# Repository branch cleanup: dry-run by default. Deletes only specified branches
# whose latest remote commits are already ancestors of the actual remote main.
# Usage:
#   bash scripts/prune_merged_branches.sh
#   CONFIRM_DELETE_MERGED_BRANCHES=YES bash scripts/prune_merged_branches.sh
set -Eeuo pipefail

EXPECTED_REPO="Fuck-GH-Admin/local-agent-web-search-demo"
REMOTE="${REMOTE:-origin}"

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "ERROR: run inside a Git working tree" >&2
  exit 2
fi

remote_url="$(git remote get-url "$REMOTE")"
case "$remote_url" in
  "https://github.com/$EXPECTED_REPO"|"https://github.com/$EXPECTED_REPO.git"|"git@github.com:$EXPECTED_REPO.git"|"git@github.com:$EXPECTED_REPO")
    ;;
  *)
    echo "ERROR: '$REMOTE' points to unexpected repository: $remote_url" >&2
    exit 2
    ;;
esac

# Fetch exactly what this script validates. Do not trust stale local refs.
git fetch --no-tags "$REMOTE" \
  "+refs/heads/main:refs/remotes/$REMOTE/main" \
  "+refs/heads/b00/environment-baseline:refs/remotes/$REMOTE/b00/environment-baseline" \
  "+refs/heads/feat/b01-searxng-search:refs/remotes/$REMOTE/feat/b01-searxng-search" \
  "+refs/heads/feat/b02-httpx-fetch:refs/remotes/$REMOTE/feat/b02-httpx-fetch" \
  "+refs/heads/feat/b03-parser-comparison:refs/remotes/$REMOTE/feat/b03-parser-comparison" \
  "+refs/heads/feat/b04-core-cli:refs/remotes/$REMOTE/feat/b04-core-cli" \
  "+refs/heads/feat/b05-fastapi-webui:refs/remotes/$REMOTE/feat/b05-fastapi-webui" \
  "+refs/heads/feat/b06-agent-tool-loop:refs/remotes/$REMOTE/feat/b06-agent-tool-loop" \
  "+refs/heads/feat/b06-readiness-audit:refs/remotes/$REMOTE/feat/b06-readiness-audit" \
  "+refs/heads/feat/b07-agent-interfaces:refs/remotes/$REMOTE/feat/b07-agent-interfaces" \
  "+refs/heads/feat/b07-real-model:refs/remotes/$REMOTE/feat/b07-real-model" \
  "+refs/heads/feat/b08-final-validation:refs/remotes/$REMOTE/feat/b08-final-validation" \
  "+refs/heads/feat/live-quality-url-security:refs/remotes/$REMOTE/feat/live-quality-url-security"

SAFE_BRANCHES=(
  "b00/environment-baseline"
  "feat/b01-searxng-search"
  "feat/b02-httpx-fetch"
  "feat/b03-parser-comparison"
  "feat/b04-core-cli"
  "feat/b05-fastapi-webui"
  "feat/b06-agent-tool-loop"
  "feat/b06-readiness-audit"
  "feat/b07-agent-interfaces"
  "feat/b07-real-model"
  "feat/b08-final-validation"
  "feat/live-quality-url-security"
)

if [[ "${CONFIRM_DELETE_MERGED_BRANCHES:-}" == "YES" ]]; then
  echo "DESTRUCTIVE MODE: deleting only merged branches from $REMOTE."
else
  echo "DRY RUN: nothing will be deleted."
  echo "To delete after review: CONFIRM_DELETE_MERGED_BRANCHES=YES bash scripts/prune_merged_branches.sh"
fi

base="$(git rev-parse "refs/remotes/$REMOTE/main")"
echo "Verified remote main: $base"

for branch in "${SAFE_BRANCHES[@]}"; do
  if ! git ls-remote --exit-code --heads "$REMOTE" "refs/heads/$branch" >/dev/null; then
    echo "SKIP (already absent): $branch"
    continue
  fi
  head="$(git rev-parse "refs/remotes/$REMOTE/$branch")"
  if ! git merge-base --is-ancestor "$head" "$base"; then
    echo "PRESERVE (contains unmerged commits): $branch @ $head" >&2
    continue
  fi
  if [[ "${CONFIRM_DELETE_MERGED_BRANCHES:-}" == "YES" ]]; then
    # Git push is atomic per ref; a concurrent new commit could race between
    # verification and deletion, so protect the exact branch SHA with a lease.
    git push "--force-with-lease=refs/heads/$branch:$head" "$REMOTE" ":refs/heads/$branch"
    echo "DELETED: $branch"
  else
    echo "SAFE TO DELETE: $branch @ $head"
  fi
done

echo "Preserved by design: main, research/e00-benchmark-availability-20261014,"
echo "  codex/miku-small-runner-20261014, feat/b00-foundation,"
echo "  feat/b07-real-model-prep, feat/b07-real-model-integration."
