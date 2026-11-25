"""voiceger-editor-ui 初回セットアップ（Voicegerの仮想環境のPythonで実行する）

1. Voiceger Editor 0.1.1 を入れる（入っていなければ）
2. 環境チェック
3. Voicegerずんだもん音源利用規約への同意（本人が agree と入力した場合のみ記録）

setup.bat / setup.command / setup.sh から呼ばれます。
"""

from __future__ import annotations

import subprocess
import sys

VERSION = "0.1.1"
TERMS_URL = "https://zunko.jp/con_ongen_kiyaku.html"
RUN_EDITOR = "import sys; from voiceger_editor.entrypoint import main; sys.exit(main())"


def editor(*args: str) -> int:
    return subprocess.call([sys.executable, "-c", RUN_EDITOR, *args])


def say(msg: str = "") -> None:
    print(msg, flush=True)


def step1_install() -> bool:
    try:
        import importlib.metadata as md

        if md.version("voiceger-editor") == VERSION and md.version("fastapi"):
            say(f"[1/3] Voiceger Editor {VERSION} は導入済みです。")
            return True
    except Exception:
        pass
    say(f"[1/3] Voiceger Editor {VERSION} をインストールします（インターネット接続が必要）...")
    code = subprocess.call(
        [sys.executable, "-m", "pip", "install", f"voiceger-editor[api,tui]=={VERSION}"]
    )
    if code != 0:
        say("インストールに失敗しました。上のメッセージを確認してください。")
        return False
    return True


def step2_check() -> bool:
    say("\n[2/3] 環境チェック（voiceger-editor --check）")
    code = editor("--check")
    if code != 0:
        say("\nVoiceger本体の環境に問題があります。上の項目を確認してください。")
        say("（Voiceger自体のインストールが済んでいるか確認してください）")
        return False
    return True


def step3_terms() -> bool:
    say("\n[3/3] 利用規約の確認")
    if editor("--voiceger-terms-status") == 0:
        say("規約への同意は記録済みです。")
        return True
    say("Voiceger で生成した音声には、次の利用規約が適用されます。")
    say(f"  {TERMS_URL}")
    say("必ず全文を読んでください。生成音声の利用にはクレジット表記も必要です。")
    say("")
    say("規約を読んで同意する場合のみ、半角で  agree  と入力して Enter を押してください。")
    say("それ以外（空欄を含む）の場合は同意せずに終了します。")
    try:
        answer = input("> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = ""
    if answer != "agree":
        say("\n同意は記録していません。同意するまで、このUIでは音声を生成できません。")
        return False
    return editor("--accept-voiceger-terms") == 0


def main() -> int:
    ok = step1_install() and step2_check() and step3_terms()
    say("")
    if ok:
        say("セットアップ完了です。start-ui（.bat / .command / .sh）で起動できます。")
        return 0
    say("セットアップは完了していません。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
