# txt2mp3
Convert large novel.txt file to mp3 files using [IndexTTS-2.5](https://github.com/index-tts/index-tts).

## Requirements
- Python 3.11 (required: `>=3.10,<3.12`, pinned in `.python-version`)
- [uv](https://docs.astral.sh/uv/)
- [ffmpeg](https://ffmpeg.org/) in `PATH` (for MP3 encoding)
- ~10 GB free disk space for model weights
- Internet access on first run (voice sample and auxiliary models are downloaded automatically)

## Setup
```bash
uv sync
uv run hf download IndexTeam/IndexTTS-2.5 --local-dir=checkpoints
```

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

Output files keep the chapter name, e.g. `novel/0001.txt` → `mp3/0001.mp3`. Existing
MP3 files are skipped unless `--overwrite` is given.

Options:

- `--voice PATH` reference voice wav (default: `examples/voice_01.wav`, auto-downloaded)
- `--lang ZH` language: `ZH`, `EN`, `JA`, `ES`, `AR`
- `--device cuda:0` torch device (default: auto-detect)
- `--bf16` use bfloat16 (recommended on Ampere or newer GPUs)
- `--bitrate 192k` MP3 bitrate
- `--max-tokens 120` max text tokens per synthesis segment
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
