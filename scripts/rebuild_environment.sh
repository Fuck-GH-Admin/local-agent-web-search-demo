#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
REBUILD_ENVIRONMENT="${1:-.venv-rebuild}"
if [[ -e "$REBUILD_ENVIRONMENT" ]]; then
    echo "Choose a new environment directory: $REBUILD_ENVIRONMENT already exists." >&2
    exit 1
fi
uv venv --python "$(cat .python-version)" "$REBUILD_ENVIRONMENT"
uv pip sync --python "$REBUILD_ENVIRONMENT/bin/python" --require-hashes requirements.lock
uv pip install --python "$REBUILD_ENVIRONMENT/bin/python" --no-build-isolation --no-deps -e .
uv pip check --python "$REBUILD_ENVIRONMENT/bin/python"
"$REBUILD_ENVIRONMENT/bin/python" -m pytest -q
"$REBUILD_ENVIRONMENT/bin/python" -m local_search_demo --help
"$REBUILD_ENVIRONMENT/bin/python" -m local_search_demo environment --output reports/B00/rebuild-environment.json
