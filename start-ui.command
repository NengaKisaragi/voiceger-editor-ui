#!/usr/bin/env bash
# macOS: Finder でダブルクリックすると起動します（終了はこのウィンドウを閉じるか Ctrl+C）
cd "$(dirname "$0")" || exit 1
./start-ui.sh
status=$?
if [ $status -ne 0 ]; then
  echo
  read -r -p "エラーで終了しました。Enter キーで閉じます" _
fi
exit $status
