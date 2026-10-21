import os
import re
import shutil

# 创建输出目录
output_dir = "./novel"

# 如果目录存在且不为空，清空目录
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)  # 删除整个目录及其内容

os.makedirs(output_dir, exist_ok=True)  # 重新创建目录

# 读取小说内容
with open("novel.txt", "r", encoding="utf-8") as f:
    content = f.read()

# 使用正则表达式匹配章节标题（例如：第1章、第12章）
chapters = re.split(r"(第\d+章[^\n]*)", content)

# chapters[0] 是分割后的前导内容（可能为空），后续是标题和正文交替
for i in range(1, len(chapters), 2):
    title = chapters[i].strip()  # 章节标题
    body = chapters[i + 1].strip()  # 章节内容

    # 提取章节号并填充为4位
    match = re.search(r"第(\d+)章", title)
    if match:
        chapter_number = int(match.group(1))
        filename = f"{chapter_number:04d}.txt"  # 填充为4位数字
    else:
        filename = re.sub(r"[^\w]", "_", title) + ".txt"

    filepath = os.path.join(output_dir, filename)

    # 保存章节到文件
    with open(filepath, "w", encoding="utf-8") as chapter_file:
        chapter_file.write(f"{title}\n\n{body}")

print(f"章节已拆分并保存到 {output_dir}")
