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
clears `novel/`, so all chapters are regenerated from scratch. Existing MP3
files in `mp3/` are kept; a same-name file is renamed to `NNNN-Copy.mp3` before
the new file is written. The first run also downloads the voice sample and
auxiliary models, so it needs internet access.

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
`novel/`, then splits `novel.txt` and converts every chapter in `novel/` to MP3
in `mp3/`. Existing MP3 files are preserved and backed up with a `-Copy` suffix.

## Split novel into chapters
Place `novel.txt` in the project root, then run:

```bash
uv run python split_novel.py
```

Chapters are detected at the start of a line using any of these heading formats:

- Arabic numerals: `第1章`, `第12章`
- Chinese numerals: `第一章`, `第十二章`, `第一百零一章`
- English: `Chapter 1`, `CHAPTER 4`
- Other units: `第三回`, `第5话`, `第6节`
- Special chapters without a number: `序章`, `序言`, `楔子`, `引子`, `前言`, `开篇`,
  `尾声`, `后记`, `终章`, `后日谈`, `大结局`, `番外` / `外传` (optionally with a
  number, e.g. `番外一`). The keyword must be the whole line, or be followed by a
  separator or space and a short title (up to 30 characters).

Each chapter is written to `novel/NNNN.txt` (zero-padded chapter number).
Special chapters are attached to the previous numbered chapter, e.g. `0100_1.txt`
(a prologue before chapter 1 is `0000_1.txt`), so they sort and play in book
order. If a chapter number repeats, the later one also gets a `_1`, `_2`, ...
suffix instead of overwriting the earlier file. Text before the first heading is
not exported.

> Note: `novel/` is recreated on every run, so previous output is removed.

## Text to speech
Convert every file in `novel/` to MP3 in `mp3/`:

```bash
uv run python txt2mp3.py
```

Output files keep the chapter name, e.g. `novel/0001.txt` → `mp3/0001.mp3`. If
`mp3/0001.mp3` already exists, it is renamed to `mp3/0001-Copy.mp3` before the
new file is written (then `0001-Copy2.mp3`, and so on).

While converting, the console shows the current file, the current TTS segment
text, that file's progress, and the overall progress.

Options:

- `--voice PATH` reference voice wav (default: `examples/voice_09.wav`, auto-downloaded)
- `--lang ZH` language: `ZH`, `EN`, `JA`, `ES`, `AR`
- `--device cuda:0` torch device (default: auto-detect)
- `--bf16` use bfloat16 (recommended on Ampere or newer GPUs)
- `--bitrate 64k` MP3 bitrate
- `--max-tokens 100` max text tokens per synthesis segment
- `--duration-factor 1.0` speech duration factor, `0.5`–`2.0` (`1.1`–`1.2` slows down a rushed voice)
- `--overwrite` replace existing MP3 files without creating a backup
- `--verbose` print detailed IndexTTS logs

> CPU note: without an NVIDIA GPU IndexTTS runs on CPU at roughly 18x real time
> (a 4-second clip takes ~70 seconds here). Converting a whole novel will take a
> long time; a CUDA GPU is strongly recommended.

## Running on Google Colab

[colab.ipynb](colab.ipynb) runs the whole pipeline on Google Colab (target: L4 GPU). Open it in Colab via **File → Open notebook → GitHub** and
enter `luoliworks/txt2mp3`, then choose **Runtime → Change runtime type → L4 GPU**
and run the cells in order:

1. Check the GPU, CUDA version (must be 12.8 or newer) and ffmpeg.
2. Mount Google Drive. MP3 files are written to `MyDrive/txt2mp3/mp3`
   (edit `OUTPUT_DIR` to change it), so they survive a disconnect.
3. Clone the repo, install `uv` and run `uv sync` (uv installs Python 3.11 itself).
4. Download the IndexTTS-2.5 weights (~10 GB). They are downloaded in every new
   session; they are intentionally not cached on Drive.
5. Provide `novel.txt`: upload it from your computer, or copy it from Drive
   (commented option in the cell).
6. Check `novel.txt`.
7. Convert it to UTF-8 and split it into chapters.
8. Convert the chapters to MP3 with `--bf16`, written to Drive. An existing MP3
   with the same name is backed up as `-Copy`, as in the local workflow.
9. Finish: play a beep in your browser, wait 5 minutes, flush and unmount Drive,
   then disconnect the runtime so it stops billing. Press the stop button of the
   cell within the 5 minutes to cancel the auto-disconnect. Cells 8 and 9 are in
   the same cell, so one click runs both.

Notes:

- The beep is played by the page, so the browser may block it if the tab is in
  the background or muted. Keep the tab in the foreground or click the page once.
- The runtime is disconnected even if the conversion failed. Check the output for
  `Failed` and stop the cell within the 5 minutes if you want to investigate.
- To convert another batch in the same session, re-run cells 5 to 8. Keep chapter
  numbers continuous across batches (e.g. 1–100, then 101–200); otherwise the new
  MP3 files get the same names and the old ones are renamed to `-Copy`.

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
