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

# 匹配行首的章节标题：第1章、第十二章、Chapter 1
CHAPTER_PATTERN = re.compile(
    r"^[ \t\u3000]*(?P<title>"
    r"第[ \t\u3000]*(?P<cn>[0-9]+|[零〇一二两三四五六七八九十百千万]+)[ \t\u3000]*章[^\n]*"
    r"|Chapter[ \t]+(?P<en>[0-9]+)\b[^\n]*"
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
    r"第[ \t\u3000]*(?:[0-9]+|[零〇一二两三四五六七八九十百千万]+)[ \t\u3000]*章"
    r"|Chapter[ \t]+[0-9]+\b"
    r")(?P<rest>.*)$",
    re.IGNORECASE,
)
TITLE_REST_SEPARATORS = re.compile(r"^[ \t\u3000｜|:：、,，.。·\-—~～…]+")


def get_chapter_number(match):
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
        yield get_chapter_number(match), title, body


def main():
    output_dir = "./novel"

    # 如果目录存在且不为空，清空目录
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    # 读取小说内容
    with open("novel.txt", "r", encoding="utf-8-sig") as f:
        content = f.read()

    for chapter_number, title, body in split_chapters(content):
        if chapter_number is None:
            filename = re.sub(r"[^\w]", "_", title) + ".txt"
        else:
            filename = f"{chapter_number:04d}.txt"  # 填充为4位数字

        filepath = os.path.join(output_dir, filename)

        # 保存章节到文件
        with open(filepath, "w", encoding="utf-8") as chapter_file:
            chapter_file.write(f"{add_title_pause(title)}\n……\n{body}")

    print(f"章节已拆分并保存到 {output_dir}")


if __name__ == "__main__":
    main()
