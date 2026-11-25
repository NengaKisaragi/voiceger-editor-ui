"""voiceger-editor-UI: browser front-end that drives voiceger-editor as its engine.

Run with the Python of the Voiceger virtual environment (start-ui.sh /
start-ui.bat do this). VOICEGER_ROOT points at the Voiceger installation.
"""

from __future__ import annotations

import argparse
import atexit
import os
import shutil
import tempfile
import threading
import time
import uuid
import webbrowser
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from voiceger_editor import api as engine_api
from voiceger_editor.mixed_language import (
    build_mixed_audio_query,
    detect_language_segments,
    is_pure_japanese,
    japanese_dictionary_pitch_options,
)
from voiceger_editor.openjtalk_converter import text_to_pronunciation
from voiceger_editor.output import save_output_audio
from voiceger_editor.pronunciation import (
    PronunciationSyntaxError,
    format_pronunciation,
    parse_pronunciation,
)
from voiceger_editor.settings import load_settings
from voiceger_editor.styles import available_styles, get_style
from voiceger_editor.terms_acceptance import VoicegerTermsAcceptanceError
from voiceger_editor.voiceger_environment import VoicegerEnvironmentError
from voiceger_editor.synthesis import synthesize_audio_query
from voiceger_editor.voicevox_query import build_audio_query

HERE = Path(__file__).resolve().parent
FRAMES_DIR = HERE / "frames"
STATIC_DIR = HERE / "static"
TAKES_DIR = Path(tempfile.mkdtemp(prefix="voiceger-ui-takes-"))
AUDIO_EXT = {".wav", ".flac", ".mp3"}

app = FastAPI(title="voiceger-editor-UI")
# The original VOICEVOX-style engine API stays reachable under /engine.
app.mount("/engine", engine_api.app)

# The GPU model is not safe to drive from several threads at once.
_synth_lock = threading.Lock()
_takes: dict[str, dict] = {}


def adapter():
    return engine_api.get_adapter()


def settings():
    return load_settings()


# 保存先は、このUIのフォルダ直下の output/（--output-dir か VOICEGER_UI_OUTPUT_DIR で変更可）。
# 形式（wav/flac/mp3）やファイル名テンプレートは Voiceger Editor の設定に従う。
OUTPUT_DIR = Path(
    os.environ.get("VOICEGER_UI_OUTPUT_DIR") or HERE / "output"
).expanduser().resolve()


def output_dir() -> Path:
    return OUTPUT_DIR


# ---------------------------------------------------------------- info

@app.get("/ui/info")
def info():
    s = settings()
    a = adapter()
    return {
        "character": a.character_name,
        "styles": [{"id": st.id, "name": st.name} for st in available_styles(a.voiceger_root)],
        "defaults": {
            "style_id": s.style_id,
            "speed": s.speed,
            "take_count": s.take_count,
            "temperature": s.temperature,
            "top_k": s.top_k,
            "top_p": s.top_p,
        },
        "output_dir": str(output_dir()),
        "output_format": s.output_format,
    }


@app.get("/ui/frames")
def frames():
    if not FRAMES_DIR.is_dir():
        return []
    return sorted(
        p.name for p in FRAMES_DIR.iterdir()
        if p.suffix.lower() in {".png", ".gif", ".webp", ".jpg", ".jpeg"}
    )


# ---------------------------------------------------------------- pronunciation

class TextIn(BaseModel):
    text: str


@app.post("/ui/pronunciation")
def pronunciation(body: TextIn):
    """Return the editable kana for pure-Japanese text (None for mixed text)."""
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "テキストが空です")
    segments = detect_language_segments(text)
    if not segments or not is_pure_japanese(segments):
        return {"editable": False, "kana": None}
    a = adapter()
    with _synth_lock:
        a.ensure_japanese_dictionary_active()
        opts = japanese_dictionary_pitch_options(a)
        pron = text_to_pronunciation(text, pitch_words=opts["japanese_pitch_words"]) \
            if opts else text_to_pronunciation(text)
    return {"editable": True, "kana": format_pronunciation(pron)}


# ---------------------------------------------------------------- synthesis

class SynthIn(BaseModel):
    text: str
    style_id: int
    kana: Optional[str] = None
    speed: float = Field(1.0, gt=0.2, le=4.0)
    temperature: float = Field(1.0, gt=0, le=2.0)
    top_k: int = Field(20, ge=1, le=100)
    top_p: float = Field(1.0, gt=0, le=1.0)


def _build_query(a, text: str, kana: Optional[str]):
    if kana and kana.strip():
        return build_audio_query(pronunciation=parse_pronunciation(kana.strip()))
    a.ensure_japanese_dictionary_active()
    return build_mixed_audio_query(
        text,
        english_g2p=a.english_phonemes,
        output_sampling_rate=32000,
        **japanese_dictionary_pitch_options(a),
    )


@app.post("/ui/synthesize")
def synthesize(body: SynthIn):
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "テキストが空です")
    a = adapter()
    try:
        style = get_style(a.voiceger_root, body.style_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    import soundfile as sf

    t0 = time.time()
    try:
        with _synth_lock:
            query = _build_query(a, text, body.kana)
            query.speedScale = body.speed
            result = synthesize_audio_query(
                adapter=a,
                query=query,
                style=style,
                top_k=body.top_k,
                top_p=body.top_p,
                temperature=body.temperature,
            )
    except PronunciationSyntaxError as exc:
        raise HTTPException(400, f"読みの書式エラー: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # engine/runtime errors
        raise HTTPException(500, f"{type(exc).__name__}: {exc}") from exc

    take_id = uuid.uuid4().hex
    path = TAKES_DIR / f"{take_id}.wav"
    sf.write(path, result["audio"], result["sampling_rate"], format="WAV")
    duration = len(result["audio"]) / float(result["sampling_rate"])
    _takes[take_id] = {"path": path, "text": text, "style": style.name}
    return {
        "id": take_id,
        "duration": round(duration, 2),
        "style": style.name,
        "elapsed": round(time.time() - t0, 2),
    }


@app.get("/ui/take/{take_id}.wav")
def take(take_id: str):
    t = _takes.get(take_id)
    if not t or not t["path"].is_file():
        raise HTTPException(404, "take not found")
    return FileResponse(t["path"], media_type="audio/wav")


class SaveIn(BaseModel):
    id: str
    caption: Optional[str] = None


@app.post("/ui/save")
def save(body: SaveIn):
    t = _takes.get(body.id)
    if not t:
        raise HTTPException(404, "take not found")
    s = settings()
    enc = {"wav": s.wav_encoding, "flac": s.flac_encoding, "mp3": s.mp3_bitrate}[s.output_format]
    saved = save_output_audio(
        wav_source=t["path"],
        source_text=(body.caption or t["text"]).strip(),
        style_name=t["style"],
        output_dir=output_dir(),
        output_format=s.output_format,
        output_encoding=enc,
        save_text=s.save_text,
        filename_template=s.filename_template,
    )
    path = saved.wav_path.resolve()
    return {"file": path.name, "path": str(path)}


# ---------------------------------------------------------------- outputs

@app.get("/ui/outputs")
def outputs():
    d = output_dir()
    if not d.is_dir():
        return []
    files = [p for p in d.iterdir() if p.suffix.lower() in AUDIO_EXT]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"name": p.name, "mtime": p.stat().st_mtime} for p in files[:200]]


def _output_path(name: str) -> Path:
    d = output_dir().resolve()
    p = (d / name).resolve()
    if p.parent != d or not p.is_file():
        raise HTTPException(404, "file not found")
    return p


@app.get("/ui/outputs/{name}")
def output_file(name: str):
    return FileResponse(_output_path(name))


TERMS_HINT = (
    "Voicegerずんだもん音源利用規約への同意が記録されていません。"
    "規約 https://zunko.jp/con_ongen_kiyaku.html を読み、同意する場合は "
    "Voicegerの仮想環境で `voiceger-editor --accept-voiceger-terms` を実行してから、"
    "このUIを再起動してください。"
)


@app.exception_handler(VoicegerTermsAcceptanceError)
async def _terms_error(_request, exc: Exception):
    return JSONResponse(status_code=403, content={"detail": TERMS_HINT})


@app.exception_handler(VoicegerEnvironmentError)
async def _env_error(_request, exc: Exception):
    return JSONResponse(
        status_code=503,
        content={"detail": f"Voicegerの環境が見つかりません（VOICEGER_ROOTを確認）: {exc}"},
    )


@app.exception_handler(Exception)
async def _any_error(_request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"})


app.mount("/frames", StaticFiles(directory=FRAMES_DIR), name="frames")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


atexit.register(shutil.rmtree, TAKES_DIR, ignore_errors=True)


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description="Browser UI for voiceger-editor")
    parser.add_argument("--host", default=os.environ.get("VOICEGER_UI_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("VOICEGER_UI_PORT", "8610")))
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="folder for saved audio (default: ./output next to server.py)",
    )
    args = parser.parse_args()

    if args.output_dir is not None:
        global OUTPUT_DIR
        OUTPUT_DIR = args.output_dir.expanduser().resolve()

    url = f"http://{'127.0.0.1' if args.host in ('0.0.0.0', '::') else args.host}:{args.port}"
    print(f"voiceger-editor-UI: {url}  (Ctrl+C で終了)", flush=True)
    print(f"保存先: {OUTPUT_DIR}", flush=True)
    if not args.no_browser:
        threading.Timer(1.5, webbrowser.open, args=(url,)).start()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
