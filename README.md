# txt2mp3
Convert large novel.txt file to mp3 files using [IndexTTS-2.5](https://github.com/index-tts/index-tts).

## Quick start (Windows)

1. Install [uv](https://docs.astral.sh/uv/) in PowerShell:
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
2. Install ffmpeg (for MP3 encoding) with winget:
   ```powershell
   winget install --id Gyan.FFmpeg -e
   ```
   Reopen the terminal (or sign out/in) so the updated `PATH` takes effect.
3. Clone the project and enter it (install [Git](https://git-scm.com/downloads)
   first, or download the ZIP from GitHub and extract it):
   ```bash
   git clone https://github.com/luoliworks/txt2mp3.git
   cd txt2mp3
   ```
4. Install dependencies (uv also installs the pinned Python 3.11 automatically):
   ```bash
   uv sync
   ```
5. Download the IndexTTS-2.5 model weights (~10 GB):
   ```bash
   uv run hf download IndexTeam/IndexTTS-2.5 --local-dir=checkpoints
   ```
6. Put your `novel.txt` in the project root, next to `convert.bat`. UTF-8 is not
   required; GBK/GB18030 and UTF-16 are converted automatically.
7. On low-VRAM GPUs (6 GB, etc.), run `convert.bat --bf16` in a terminal. bf16
   reduces VRAM usage and is recommended for NVIDIA RTX 30 series and newer,
   such as the RTX 3050 6 GB (double-clicking `convert.bat` runs without it).

The script splits `novel.txt` into `novel/` and writes MP3 files to `mp3/`.
Every run of `convert.bat` first converts `novel.txt` to UTF-8 if needed, then
clears both folders, so all chapters are regenerated from scratch. The first run
also downloads the voice sample and auxiliary models, so it needs internet
access.

The default voice is `examples/voice_09.wav`. Override it with `--voice`:

```bat
convert.bat --voice examples\voice_06.wav
```

`voice_09.wav` is a female voice (default).
`voice_06.wav` is a male voice.
`voice_11.wav` is a female voice (high pitch).

All official voice samples are in `examples/`; open `examples/listen.html` in a
browser to preview them.

## Requirements
- Python 3.11 (required: `>=3.10,<3.12`, pinned in `.python-version`; uv installs it automatically)
- [uv](https://docs.astral.sh/uv/)
- [ffmpeg](https://ffmpeg.org/) in `PATH` (for MP3 encoding)
- ~10 GB free disk space for model weights
- Internet access on first run (voice sample and auxiliary models are downloaded automatically)

## One-click conversion (Windows)
Run `convert.bat --bf16` in a terminal (or double-click `convert.bat` to run
without bf16). On every run it first converts `novel.txt` to UTF-8, clears
`novel/` and `mp3/`, then splits `novel.txt` and converts every chapter in
`novel/` to MP3 in `mp3/`.

## Split novel into chapters
Place `novel.txt` in the project root, then run:

```bash
uv run python split_novel.py
```

Chapters are detected at the start of a line using any of these heading formats:

- Arabic numerals: `第1章`, `第12章`
- Chinese numerals: `第一章`, `第十二章`, `第一百零一章`
- English: `Chapter 1`, `CHAPTER 4`

Each chapter is written to `novel/NNNN.txt` (zero-padded chapter number).

> Note: `novel/` is recreated on every run, so previous output is removed.

## Text to speech
Convert every file in `novel/` to MP3 in `mp3/`:

```bash
uv run python txt2mp3.py
```

Output files keep the chapter name, e.g. `novel/0001.txt` → `mp3/0001.mp3`. When
running this script directly, existing MP3 files are skipped unless `--overwrite`
is given (`convert.bat` already clears `mp3/`).

Options:

- `--voice PATH` reference voice wav (default: `examples/voice_09.wav`, auto-downloaded)
- `--lang ZH` language: `ZH`, `EN`, `JA`, `ES`, `AR`
- `--device cuda:0` torch device (default: auto-detect)
- `--bf16` use bfloat16 (recommended on Ampere or newer GPUs)
- `--bitrate 192k` MP3 bitrate
- `--max-tokens 120` max text tokens per synthesis segment
- `--duration-factor 1.0` speech duration factor, `0.5`–`2.0` (`1.1`–`1.2` slows down a rushed voice)
- `--overwrite` regenerate existing MP3 files
- `--verbose` print detailed IndexTTS logs

> CPU note: without an NVIDIA GPU IndexTTS runs on CPU at roughly 18x real time
> (a 4-second clip takes ~70 seconds here). Converting a whole novel will take a
> long time; a CUDA GPU is strongly recommended.

## Running on a CUDA machine

No code or dependency changes are needed; `uv.lock` already pins the cu128
torch/torchaudio wheels for Linux and Windows. On the CUDA machine:

1. Install a recent NVIDIA driver that supports CUDA 12.8. PyTorch ships
   prebuilt cu128 wheels, so the CUDA Toolkit is not required. Install CUDA
   Toolkit 12.8 only if you want the optional BigVGAN fused CUDA kernel.
2. Make sure `ffmpeg` is in `PATH`.
3. Copy `checkpoints/` (~10 GB) from the old machine, or download it again:
   ```bash
   uv sync
   uv run hf download IndexTeam/IndexTTS-2.5 --local-dir=checkpoints
   ```
4. Recreate the environment instead of copying `.venv`:
   ```bash
   uv sync
   ```
5. Run with bf16 and the GPU device:
   ```bash
   uv run python txt2mp3.py --device cuda:0 --bf16
   ```

`--device` can be omitted because CUDA is detected automatically. bf16 is
recommended on Ampere or newer GPUs (RTX 30 series and up). 8 GB of VRAM or more
is comfortable; below 10 GB IndexTTS automatically splits long text into chunks.
The voice sample and auxiliary models are downloaded automatically if missing,
so the first run needs network access.
