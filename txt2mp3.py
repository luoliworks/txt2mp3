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
SEGMENT_PROGRESS = re.compile(r"speech synthesis (\d+)/(\d+)")


class ProgressReporter:
    def __init__(self, total_files, total_chars):
        self.total_files = total_files
        self.total_chars = max(total_chars, 1)
        self.done_chars = 0
        self.file_index = 0
        self.path = None
        self.file_chars = 0
        self.file_start = 0.0
        self.segments = []
        self.low_vram_plan = None
        self.low_vram_index = 0

    def begin_file(self, index, path, text, low_vram_plan=None):
        self.file_index = index
        self.path = path
        self.file_chars = len(text)
        self.file_start = time.perf_counter()
        self.segments = []
        self.low_vram_plan = low_vram_plan
        self.low_vram_index = 0
        print(f"[{index}/{self.total_files}] {path.name} ({len(text)} chars)", flush=True)

    def set_segments(self, segments):
        self.segments = segments

    def overall_percent(self, fraction):
        return 100.0 * (self.done_chars + self.file_chars * fraction) / self.total_chars

    def print_segment(self, seg_no, seg_total, fraction, preview):
        preview = WHITESPACE.sub(" ", preview).strip()
        if len(preview) > 30:
            preview = preview[:30] + "..."
        print(
            f"  {self.path.name} | file {fraction * 100:5.1f}% | "
            f"total {self.overall_percent(fraction):5.1f}% | "
            f"{seg_no}/{seg_total} {preview}",
            flush=True,
        )

    def on_progress(self, value, desc):
        match = SEGMENT_PROGRESS.search(desc)
        if match:
            seg_no = int(match.group(1))
            seg_total = int(match.group(2))
            if self.low_vram_plan is not None:
                seg_total = len(self.low_vram_plan)
                if self.low_vram_index < seg_total:
                    seg_no = self.low_vram_index + 1
                    preview = self.low_vram_plan[self.low_vram_index]
                    fraction = self.low_vram_index / seg_total
                    self.low_vram_index += 1
                else:
                    seg_no = seg_total
                    preview = self.low_vram_plan[-1]
                    fraction = 1.0
            else:
                fraction = (seg_no - 1) / seg_total
                preview = self.segments[seg_no - 1] if seg_no <= len(self.segments) else ""
            self.print_segment(seg_no, seg_total, fraction, preview)
            return

        if value >= 0.9 and (self.low_vram_plan is None or self.low_vram_index >= len(self.low_vram_plan)):
            print(
                f"  {self.path.name} | file 100.0% | "
                f"total {self.overall_percent(1.0):5.1f}% | saving audio...",
                flush=True,
            )

    def finish_file(self, mp3_path):
        self.done_chars += self.file_chars
        elapsed = time.perf_counter() - self.file_start
        print(
            f"  Saved {mp3_path} in {elapsed:.1f}s | "
            f"total {100.0 * self.done_chars / self.total_chars:5.1f}%",
            flush=True,
        )

    def fail_file(self):
        self.done_chars += self.file_chars
        elapsed = time.perf_counter() - self.file_start
        print(
            f"  Failed after {elapsed:.1f}s | "
            f"total {100.0 * self.done_chars / self.total_chars:5.1f}%",
            flush=True,
        )


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

    pending = []
    for txt_path in txt_files:
        mp3_path = output_dir / f"{txt_path.stem}.mp3"
        if mp3_path.is_file() and not args.overwrite:
            print(f"Skip existing {mp3_path}")
            continue

        text = clean_text(txt_path.read_text(encoding="utf-8-sig"))
        if not text:
            print(f"Skip empty {txt_path}")
            continue
        pending.append((txt_path, mp3_path, text))

    if not pending:
        print("Nothing to do.")
        return

    reporter = ProgressReporter(len(pending), sum(len(text) for _, _, text in pending))
    print(f"Total: {len(pending)} file(s), {reporter.total_chars} chars", flush=True)

    original_split = tts.split_text_by_tokens

    def split_with_progress(text, max_tokens, lang_prefix=""):
        segments = original_split(text, max_tokens, lang_prefix)
        reporter.set_segments(segments)
        return segments

    tts.split_text_by_tokens = split_with_progress
    tts.gr_progress = reporter.on_progress

    failures = 0
    try:
        for index, (txt_path, mp3_path, text) in enumerate(pending, start=1):
            low_vram_plan = None
            if tts.low_vram and len(text) > 40:
                low_vram_plan = tts.split_text_by_punctuation(text, max_chars=40)
            reporter.begin_file(index, txt_path, text, low_vram_plan)
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
                reporter.fail_file()
                continue

            reporter.finish_file(mp3_path)
    finally:
        tts.split_text_by_tokens = original_split
        tts.gr_progress = None

    if failures:
        sys.exit(f"Finished with {failures} failed file(s)")
    print("All done.")


if __name__ == "__main__":
    main()
