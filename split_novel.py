import os
import re
import shutil

CN_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
CN_UNITS = {"十": 10, "百": 100, "千": 1000, "万": 10000}

# 特殊章节关键字：序章、楔子、番外一、尾声 等（不带章节号）
# Special chapter keywords (no chapter number): prologue, extras, epilogue, etc.
SPECIAL_KEYWORDS = (
    r"(?:序章|序言|楔子|引子|前言|开篇|尾声|后记|终章|后日谈|大结局|完本感言|完结感言"
    r"|(?:番外|外传)篇?[0-9零〇一二两三四五六七八九十百]*)"
)
# 关键字之后必须直接结束，或跟分隔符/空白再接一段短标题，避免误匹配正文
# The keyword must end the line, or be followed by a separator/whitespace and a
# short title, to avoid matching ordinary body text.
SPECIAL_REST = r"(?:(?:[ \t\u3000]+|[：:｜|\-—、·.．]+)[^\n]{0,30})?"

# 匹配行首的章节标题：第1章、第十二章、第三回、Chapter 1，以及序章/番外等特殊章节
# Match chapter headings at line start: 第1章, 第十二章, 第三回, Chapter 1,
# plus special chapters such as 序章 / 番外.
CHAPTER_PATTERN = re.compile(
    r"^[ \t\u3000]*(?P<title>"
    r"第[ \t\u3000]*(?P<cn>[0-9]+|[零〇一二两三四五六七八九十百千万]+)[ \t\u3000]*[章回话節节][^\n]*"
    r"|Chapter[ \t]+(?P<en>[0-9]+)\b[^\n]*"
    rf"|(?P<special>{SPECIAL_KEYWORDS}{SPECIAL_REST})"
    r")[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)


def cn_to_int(text):
    total = 0
    section = 0
    number = 0
    for char in text:
        if char in CN_DIGITS:
            number = CN_DIGITS[char]
        elif char in CN_UNITS:
            unit = CN_UNITS[char]
            if unit == 10000:
                section = (section + number) * unit
                total += section
                section = 0
                number = 0
            else:
                if number == 0:
                    number = 1
                section += number * unit
                number = 0
        else:
            return None
    return total + section + number


TITLE_PAUSE_PATTERN = re.compile(
    r"^(?P<marker>"
    r"第[ \t\u3000]*(?:[0-9]+|[零〇一二两三四五六七八九十百千万]+)[ \t\u3000]*[章回话節节]"
    r"|Chapter[ \t]+[0-9]+\b"
    rf"|{SPECIAL_KEYWORDS}"
    r")(?P<rest>.*)$",
    re.IGNORECASE,
)
TITLE_REST_SEPARATORS = re.compile(r"^[ \t\u3000｜|:：、,，.。·\-—~～…]+")


def get_chapter_number(match):
    if match.group("special") is not None:
        return None
    cn = match.group("cn")
    en = match.group("en")
    if en is not None:
        return int(en)
    if cn.isdigit():
        return int(cn)
    return cn_to_int(cn)


def add_title_pause(title):
    match = TITLE_PAUSE_PATTERN.match(title)
    if match is None:
        return title
    rest = TITLE_REST_SEPARATORS.sub("", match.group("rest")).strip()
    if not rest:
        return title
    return f"{match.group('marker').strip()}…… {rest}"


def split_chapters(content):
    matches = list(CHAPTER_PATTERN.finditer(content))
    for index, match in enumerate(matches):
        title = match.group("title").strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        yield get_chapter_number(match), title, body, match.group("special") is not None


def unique_name(base, used, force_suffix):
    """序号相同或特殊章节追加 _1、_2…，保证文件名唯一且排序在对应章节之后。

    Append _1, _2, ... for duplicate numbers or special chapters, so filenames
    stay unique and sort right after the matching chapter.
    """
    if not force_suffix and base not in used:
        used.add(base)
        return base
    suffix = 1
    while f"{base}_{suffix}" in used:
        suffix += 1
    name = f"{base}_{suffix}"
    used.add(name)
    return name


def main():
    output_dir = "./novel"

    # 如果目录存在且不为空，清空目录
    # If the directory exists and is not empty, clear it
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    # 读取小说内容
    # Read the novel content
    with open("novel.txt", "r", encoding="utf-8-sig") as f:
        content = f.read()

    used = set()
    last_number = 0
    for chapter_number, title, body, is_special in split_chapters(content):
        if is_special:
            # 特殊章节挂在前一个编号章节之后，如 0100_1.txt；开头的序章为 0000_1.txt
            # Special chapters follow the previous numbered chapter, e.g. 0100_1.txt;
            # a leading prologue becomes 0000_1.txt
            filename = unique_name(f"{last_number:04d}", used, True) + ".txt"
        elif chapter_number is None:
            filename = re.sub(r"[^\w]", "_", title) + ".txt"
        else:
            last_number = chapter_number
            filename = unique_name(f"{chapter_number:04d}", used, False) + ".txt"

        filepath = os.path.join(output_dir, filename)

        # 保存章节到文件
        # Save the chapter to a file
        with open(filepath, "w", encoding="utf-8") as chapter_file:
            chapter_file.write(f"{add_title_pause(title)}\n……\n{body}")

    print(f"章节已拆分并保存到 {output_dir}")


if __name__ == "__main__":
    main()
