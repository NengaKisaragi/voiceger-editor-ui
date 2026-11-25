#!/usr/bin/env bash
# voiceger-editor-UI launcher for macOS / Linux
#   ./start-ui.sh [--port 8610] [--no-browser]
# Voiceger の場所は VOICEGER_ROOT で指定（未指定なら ../voiceger_v2 → ~/voiceger_v2 の順に探す）
set -e
UI_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"

if [ -z "${VOICEGER_ROOT:-}" ]; then
  if [ -d "$UI_DIR/../voiceger_v2" ]; then
    VOICEGER_ROOT="$(cd -- "$UI_DIR/../voiceger_v2" && pwd)"
  else
    VOICEGER_ROOT="$HOME/voiceger_v2"
  fi
fi
export VOICEGER_ROOT

# Optional per-machine environment (e.g. GPU / data-dir settings)
if [ -f "$VOICEGER_ROOT/env.sh" ]; then
  # shellcheck disable=SC1091
  source "$VOICEGER_ROOT/env.sh"
fi

PY="$VOICEGER_ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "Voiceger の Python が見つかりません: $PY" >&2
  echo "VOICEGER_ROOT に Voiceger (voiceger_v2) のフォルダを指定してください。" >&2
  exit 1
fi

cd "$UI_DIR"
exec "$PY" "$UI_DIR/server.py" "$@"
