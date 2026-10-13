#!/usr/bin/env bash
# B00 reference clones; external upstream repositories are ignored by our Git repo.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="$ROOT/.references/upstream"
mkdir -p "$TARGET"
REPOS=(
  "searxng|https://github.com/searxng/searxng.git"
  "httpx|https://github.com/encode/httpx.git"
  "trafilatura|https://github.com/adbar/trafilatura.git"
  "selectolax|https://github.com/rushter/selectolax.git"
  "python-readability|https://github.com/buriy/python-readability.git"
  "openai-python|https://github.com/openai/openai-python.git"
)
for item in "${REPOS[@]}"; do
  name="${item%%|*}"
  url="${item#*|}"
  dest="$TARGET/$name"
  if [ -d "$dest/.git" ]; then
    echo "EXISTS: $name $(git -C "$dest" rev-parse HEAD)"
    continue
  fi
  if [ -e "$dest" ]; then
    echo "ERROR: $dest exists but is not a Git repo" >&2
    exit 1
  fi
  echo "CLONE: $name"
  git clone --depth 1 --recurse-submodules "$url" "$dest"
  echo "SHA: $name $(git -C "$dest" rev-parse HEAD)"
done
