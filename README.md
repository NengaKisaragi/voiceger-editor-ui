# voiceger-editor-ui

[Voiceger Editor](https://github.com/sayosomi/voiceger-editor) をエンジンにして動く、**ブラウザ用の非公式UI** です。
セリフを入力して複数テイクを生成し、聴き比べて気に入ったものを保存できます。

> [!CAUTION]
> ## ⚠ ご利用の前に必ずお読みください（必読）
>
> このリポジトリは **UI部分のみ** です。Voiceger本体・モデル・参照音声・生成音声は含まれていません。
> 音声の生成には [Voiceger](https://github.com/zunzun999/voiceger_v2) と [Voiceger Editor](https://github.com/sayosomi/voiceger-editor) が必要で、**それぞれのライセンス・利用規約がそのまま適用されます。**
>
> - **Voicegerで生成した音声には [Voicegerずんだもん音源利用規約](https://zunko.jp/con_ongen_kiyaku.html) が適用されます。**
>   利用前に必ず全文を読み、内容に同意できる場合のみ使用してください。
> - 生成音声を公開・利用する際は、規約に従い **所定のクレジット表記** を行ってください。
>   表記例（Voiceger Editor の README より）：`Voicegerずんだもん` / `Voiceger:Zundamon`
> - Voiceger本体が利用しているOSS（GPT-SoVITS など）やモデルのライセンスは、[Voicegerの README](https://github.com/zunzun999/voiceger_v2#license-information) を参照してください。
> - Voiceger Editor の注意事項は [Voiceger Editor の README](https://github.com/sayosomi/voiceger-editor) と THIRD_PARTY_NOTICES.md を参照してください。
> - **このUIのライセンス（MIT）は、このリポジトリのコードにのみ適用されます。** 生成音声、Voiceger、モデル、参照音声、キャラクター・名称・商標など、第三者の権利について何の許諾も与えるものではありません。
> - このUIは非公式のものです。Voiceger・Voiceger Editor・東北ずん子・ずんだもんプロジェクトの公式とは関係ありません。
> - 規約への同意はこのUIからは行いません。初回は公式の手順（下記）で規約を確認し、同意してください。

---

## 必要なもの

| もの | 備考 |
| --- | --- |
| [Voiceger (voiceger_v2)](https://github.com/zunzun999/voiceger_v2) | 公式の手順でインストール。Python 3.9 の仮想環境（`.venv`）を作っておく |
| [Voiceger Editor](https://github.com/sayosomi/voiceger-editor) **0.1.1** | Voicegerの仮想環境に `api` 付きでインストール |

> [!NOTE]
> **Voiceger と Voiceger Editor はこのリポジトリに含まれていません。** それぞれ公式の手順で各自インストールしてください。
> このUIは起動時に、Voicegerの仮想環境にインストール済みの Voiceger Editor を読み込んで使います。

動作確認は **Linux（Ubuntu / CUDA）+ Voiceger Editor 0.1.1** でのみ行っています。
Windows / macOS 用の起動ファイルも用意していますが、実機での確認はしていません。
macOS では CUDA が使えないため、合成は遅くなります（Voiceger側の制約です）。

> このUIは Voiceger Editor の内部モジュールを直接呼び出しています。Voiceger Editor のバージョンが変わると動かなくなることがあります。

## セットアップ

### 1. Voiceger をインストール

[Voiceger の README](https://github.com/zunzun999/voiceger_v2) に従ってインストールします。

### 2. Voiceger Editor を入れる

macOS / Linux：

```bash
export VOICEGER_ROOT="$HOME/voiceger_v2"
source "$VOICEGER_ROOT/.venv/bin/activate"
python -m pip install "voiceger-editor[api,tui]==0.1.1"
voiceger-editor --check
```

Windows PowerShell：

```powershell
$env:VOICEGER_ROOT = "$HOME\voiceger_v2"
& "$env:VOICEGER_ROOT\.venv\Scripts\Activate.ps1"
python -m pip install "voiceger-editor[api,tui]==0.1.1"
voiceger-editor --check
```

### 3. 利用規約を確認して同意する（初回のみ）

[Voicegerずんだもん音源利用規約](https://zunko.jp/con_ongen_kiyaku.html) を読み、同意する場合は次を実行します（または `voiceger-editor` を一度起動して画面の案内に従う）。

```bash
voiceger-editor --accept-voiceger-terms
```

同意が記録されていないと、このUIは音声を生成しません。

### 4. このリポジトリを置く

どこに置いても構いません。Voicegerと同じ階層に置くと、自動でVoicegerを見つけます。

```
voiceger_v2/              ← Voiceger（各自インストール）
  └ .venv/                   └ ここに Voiceger Editor を pip でインストール（手順2）
voiceger-editor-ui/       ← このリポジトリ（UIのコードのみ）
```

別の場所にある場合は、環境変数 `VOICEGER_ROOT` でVoicegerのフォルダを指定してください（未指定の場合は `../voiceger_v2` → `~/voiceger_v2` の順に探します）。

設定・ユーザー辞書・規約同意の記録は、Voiceger Editor の標準の保存場所（Linux：`~/.config/voiceger-editor/`、macOS：`~/Library/Application Support/voiceger-editor/`、Windows：ユーザーの AppData 内）がそのまま使われます。TUI版と共通なので、このUI用に別のフォルダを用意する必要はありません。

## 起動

macOS / Linux：

```bash
./start-ui.sh
```

Windows：`start-ui.bat` をダブルクリック（またはコマンドプロンプトから実行）

ブラウザで http://127.0.0.1:8610 が開きます。終了はターミナルで `Ctrl+C`。

| オプション | 内容 |
| --- | --- |
| `--port 8700` | ポート番号を変更 |
| `--no-browser` | ブラウザを自動で開かない |
| `--host 0.0.0.0` | LAN内の他の端末からも開けるようにする（信頼できるネットワークでのみ） |

`VOICEGER_ROOT/env.sh` があれば起動時に読み込みます（GPU指定など、マシンごとの設定用。任意）。

## 使い方

1. セリフを入力 → スタイル・速さ・テイク数（最大20）を選ぶ → **▶ 生成**（`Ctrl+Enter`）
2. 候補テイクを `↑` `↓` / 数字キー / クリックで聴き比べ。`Space` で再生・停止
3. `Enter` か「保存」で出力フォルダに保存
4. 読みがおかしいときは「読み・アクセント編集」→「読みを取得」で直してから生成（日本語の文のみ）

出力フォルダ・保存形式・ファイル名テンプレートなどの設定は Voiceger Editor（TUI）と共通です。TUIの設定画面で変更してください。
初回の生成はモデルの読み込みのため時間がかかります。

## パラパラ漫画（おまけ）

右上のキャラクターは `frames/` フォルダの画像をファイル名順に1コマずつ表示します（png / gif / webp / jpg）。

```
frames/01.png
frames/02.png
frames/03.png ...
```

画像を追加したらブラウザを再読み込みしてください。「コマ速度」で速さを変えられ、音声の再生中は倍速になります。

## 構成

```
server.py        FastAPI サーバー（Voiceger Editor を import して合成）
static/          画面（HTML / CSS / JS、ビルド不要）
frames/          パラパラ漫画のコマ画像
start-ui.sh      macOS / Linux 用起動スクリプト
start-ui.bat     Windows 用起動スクリプト
```

Voiceger Editor の VOICEVOX互換API も `http://127.0.0.1:8610/engine/` 以下でそのまま使えます。

## ライセンス

このリポジトリのコードは [MIT License](LICENSE) です。
上記「ご利用の前に必ずお読みください」のとおり、生成音声や Voiceger・モデル等には各権利者のライセンス・利用規約が適用されます。
