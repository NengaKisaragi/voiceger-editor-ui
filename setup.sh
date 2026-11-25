#!/usr/bin/env bash
# voiceger-editor-ui 初回セットアップ（macOS / Linux）
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

if [ -f "$VOICEGER_ROOT/env.sh" ]; then
  # shellcheck disable=SC1091
  source "$VOICEGER_ROOT/env.sh"
fi

PY="$VOICEGER_ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "Voiceger の Python が見つかりません: $PY" >&2
  echo "先に Voiceger (voiceger_v2) をインストールするか、VOICEGER_ROOT にそのフォルダを指定してください。" >&2
  exit 1
fi

cd "$UI_DIR"
exec "$PY" "$UI_DIR/setup.py"
