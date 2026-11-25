#!/usr/bin/env bash
# macOS: Finder でダブルクリックするとターミナルが開いてセットアップが始まります
cd "$(dirname "$0")" || exit 1
./setup.sh
status=$?
echo
read -r -p "Enter キーで閉じます" _
exit $status
