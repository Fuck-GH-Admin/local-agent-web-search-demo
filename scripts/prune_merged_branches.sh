#!/usr/bin/env bash
# Repository branch cleanup: dry-run by default. Archives and deletes only specified branches
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

# Fetch the current remote branch list (including refs missing from a shallow
# or single-branch checkout). Deleted branches will not break repeat runs.
git fetch --no-tags --prune "$REMOTE" "+refs/heads/*:refs/remotes/$REMOTE/*"

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
  # Preserve the historic branch SHA under a same-named lightweight Git tag.
  # This keeps documented 'git clone --branch ...' and old source references usable.
  remote_tag="$(git ls-remote --refs --tags "$REMOTE" "refs/tags/$branch" | awk '{print $1}')"
  if [[ -n "$remote_tag" && "$remote_tag" != "$head" ]]; then
    echo "PRESERVE (conflicting remote historical tag): $branch @ $remote_tag" >&2
    continue
  fi
  if [[ "${CONFIRM_DELETE_MERGED_BRANCHES:-}" == "YES" ]]; then
    if [[ -z "$remote_tag" ]]; then
      if local_tag="$(git rev-parse -q --verify "refs/tags/$branch" 2>/dev/null)"; then
        if [[ "$local_tag" != "$head" ]]; then
          echo "PRESERVE (conflicting local tag): $branch @ $local_tag" >&2
          continue
        fi
      else
        git tag "$branch" "$head"
      fi
      git push "$REMOTE" "refs/tags/$branch:refs/tags/$branch"
    fi
    verified="$(git ls-remote --refs --tags "$REMOTE" "refs/tags/$branch" | awk '{print $1}')"
    if [[ "$verified" != "$head" ]]; then
      echo "PRESERVE (backup tag verification failed): $branch" >&2
      continue
    fi
    # Compare-and-delete lease refuses deletion if the branch moved.
    git push "--force-with-lease=refs/heads/$branch:$head" "$REMOTE" ":refs/heads/$branch"
    echo "ARCHIVED/DELETED: $branch (tag at $head)"
  else
    echo "SAFE TO ARCHIVE: $branch @ $head (tag backup first)"
  fi
done

echo "Preserved by design: main, research/e00-benchmark-availability-20261014,"
echo "  codex/miku-small-runner-20261014, feat/b00-foundation,"
echo "  feat/b07-real-model-prep, feat/b07-real-model-integration."
