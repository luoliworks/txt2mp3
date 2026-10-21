import codecs
import sys
from pathlib import Path

NOVEL_PATH = Path("novel.txt")


def convert_to_utf8(path):
    raw = path.read_bytes()

    if raw.startswith(codecs.BOM_UTF8):
        print(f"{path} is already UTF-8 (with BOM)")
        return

    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    else:
        print(f"{path} is already UTF-8")
        return

    if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
        encoding = "utf-16"
    else:
        encoding = "gb18030"

    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError as exc:
        sys.exit(f"Could not decode {path} as UTF-8, UTF-16 or GB18030: {exc}")

    path.write_bytes(text.encode("utf-8"))
    print(f"Converted {path} from {encoding} to UTF-8")


def main():
    if not NOVEL_PATH.is_file():
        sys.exit(f"{NOVEL_PATH} was not found")
    convert_to_utf8(NOVEL_PATH)


if __name__ == "__main__":
    main()
