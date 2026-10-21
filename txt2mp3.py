import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEFAULT_CHECKPOINTS = "checkpoints"
DEFAULT_VOICE = "examples/voice_09.wav"
VOICE_URL = (
    "https://huggingface.co/spaces/IndexTeam/IndexTTS-2-Demo"
    "/resolve/main/examples/voice_09.wav"
)

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x85\xa0]+")
WHITESPACE = re.compile(r"\s+")


def clean_text(text):
    """Remove control characters and collapse whitespace."""
    text = text.replace("\u3000", " ")
    text = CONTROL_CHARS.sub(" ", text)
    return WHITESPACE.sub(" ", text).strip()


def ensure_voice(path):
    if path.is_file():
        return
    print(f"Voice sample not found, downloading to {path} ...")
    path.parent.mkdir(parents=True, exist_ok=True)
    import requests

    response = requests.get(VOICE_URL, timeout=120)
    response.raise_for_status()
    path.write_bytes(response.content)


def convert_to_mp3(ffmpeg, wav_path, mp3_path, bitrate):
    tmp_path = mp3_path.with_suffix(".tmp.mp3")
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(wav_path),
        "-codec:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        str(tmp_path),
    ]
    subprocess.run(cmd, check=True)
    os.replace(tmp_path, mp3_path)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert chapter txt files in ./novel to mp3 files in ./mp3 "
        "using IndexTTS-2.5."
    )
    parser.add_argument("--input-dir", default="novel", help="Directory of input txt files")
    parser.add_argument("--output-dir", default="mp3", help="Directory for generated mp3 files")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="Reference voice wav file")
    parser.add_argument("--lang", default="ZH", help="Language code (ZH, EN, JA, ES, AR)")
    parser.add_argument(
        "--device",
        default=None,
        help="Torch device, e.g. cpu or cuda:0 (default: auto-detect)",
    )
    parser.add_argument("--bitrate", default="64k", help="MP3 bitrate")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=100,
        help="Max text tokens per synthesis segment",
    )
    parser.add_argument(
        "--duration-factor",
        type=float,
        default=1.0,
        help="Speech duration factor, 0.5-2.0 (>1 is slower, default: 1.0)",
    )
    parser.add_argument("--bf16", action="store_true", help="Use bfloat16 on GPU")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing mp3 files")
    parser.add_argument("--verbose", action="store_true", help="Verbose IndexTTS output")
    return parser.parse_args()


def main():
    args = parse_args()
    if not 0.5 <= args.duration_factor <= 2.0:
        sys.exit("--duration-factor must be between 0.5 and 2.0")

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    voice_path = Path(args.voice)
    checkpoints = Path(DEFAULT_CHECKPOINTS)

    if not input_dir.is_dir():
        sys.exit(f"Input directory not found: {input_dir}")
    if not (checkpoints / "config.yaml").is_file():
        sys.exit(
            f"IndexTTS-2.5 checkpoints not found in {checkpoints}. "
            "Download them with: uv run hf download IndexTeam/IndexTTS-2.5 --local-dir=checkpoints"
        )

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        sys.exit("ffmpeg was not found in PATH")

    txt_files = sorted(input_dir.glob("*.txt"))
    if not txt_files:
        sys.exit(f"No .txt files found in {input_dir}")

    ensure_voice(voice_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    from indextts.infer_v2_5 import IndexTTS2

    print("Loading IndexTTS-2.5 ...")
    load_start = time.perf_counter()
    tts = IndexTTS2(
        cfg_path=str(checkpoints / "config.yaml"),
        model_dir=str(checkpoints),
        use_bf16=args.bf16,
        device=args.device,
        use_qwen_emo=False,
    )
    print(f"Model ready on {tts.device} in {time.perf_counter() - load_start:.1f}s")

    failures = 0
    for index, txt_path in enumerate(txt_files, start=1):
        mp3_path = output_dir / f"{txt_path.stem}.mp3"
        if mp3_path.is_file() and not args.overwrite:
            print(f"[{index}/{len(txt_files)}] Skip existing {mp3_path}")
            continue

        text = clean_text(txt_path.read_text(encoding="utf-8-sig"))
        if not text:
            print(f"[{index}/{len(txt_files)}] Skip empty {txt_path}")
            continue

        print(f"[{index}/{len(txt_files)}] Converting {txt_path.name} ({len(text)} chars)")
        start = time.perf_counter()
        try:
            with tempfile.TemporaryDirectory(dir=output_dir) as tmp_dir:
                wav_path = Path(tmp_dir) / f"{txt_path.stem}.wav"
                tts.infer(
                    spk_audio_prompt=str(voice_path),
                    text=text,
                    lang=args.lang,
                    output_path=str(wav_path),
                    verbose=args.verbose,
                    max_text_tokens_per_segment=args.max_tokens,
                    duration_factor=args.duration_factor,
                )
                if not wav_path.is_file():
                    raise RuntimeError("IndexTTS did not produce a wav file")
                convert_to_mp3(ffmpeg, wav_path, mp3_path, args.bitrate)
        except Exception as exc:
            failures += 1
            print(f"  Failed: {exc}")
            continue

        print(f"  Saved {mp3_path} in {time.perf_counter() - start:.1f}s")

    if failures:
        sys.exit(f"Finished with {failures} failed file(s)")
    print("All done.")


if __name__ == "__main__":
    main()
