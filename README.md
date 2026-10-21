# txt2mp3
Convert large novel.txt file to mp3 files

## Requirements
- Python 3.11 (required: `>=3.10,<3.12`, pinned in `.python-version`)
- [uv](https://docs.astral.sh/uv/)

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
