"""一次性清洗（方案 A）：移除正文中「普通文字/表格」的内联 color，保留自带背景的块。

规则（对每个带 style 的元素）：
  1. 位于 <pre> 内（代码块及其语法高亮 span）→ 保留
  2. style 里含 background / background-color（笔记卡片、深色表头、行内代码 chip 等自含块）→ 保留
  3. 其余 → 只摘掉 color 属性，其余（padding/border/...）不动

附 <pre> 内容完整性校验：若清洗导致 <pre> 内文本变化，跳过该篇并告警。

用法（在 python-backend 目录下，用项目 venv 运行）：
  python clean_inline_colors.py            # 干跑
  python clean_inline_colors.py --apply    # 实际写入
"""
import sys
import re
import html

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from bs4 import BeautifulSoup
from database import SessionLocal
from models import KnowledgeArticle

BACKGROUND_RE = re.compile(r"(^|;)\s*background(-color)?\s*:")


def strip_color(style: str) -> str:
    """移除 style 中的 color 属性（不碰 background、border 等）。"""
    parts = []
    for part in style.split(";"):
        part = part.strip()
        if not part:
            continue
        prop = part.split(":", 1)[0].strip().lower()
        if prop == "color":
            continue
        parts.append(part)
    return ";".join(parts)


def pre_contents(content: str):
    """提取所有 <pre>…</pre> 的内部文本（HTML 解码后），用于校验代码块未被破坏。

    按解码后的文本比对：`>` 与 `&gt;` 这类等价转义不算变化，只拦真实内容差异。
    """
    return [html.unescape(x) for x in re.findall(r"<pre[^>]*>(.*?)</pre>", content or "", re.S)]


def clean(content: str):
    """返回 (新内容, 剥掉的 color 个数)。"""
    if not content:
        return content, 0
    soup = BeautifulSoup(content, "html.parser")
    n = 0
    for el in soup.select("[style]"):
        # 代码块（<pre> 及其内部）→ 保留
        if el.name == "pre" or el.find_parent("pre"):
            continue
        style = el.get("style") or ""
        # 自带背景的块 → 保留
        if BACKGROUND_RE.search(style):
            continue
        new_style = strip_color(style)
        if new_style != style:
            if new_style:
                el["style"] = new_style
            else:
                del el["style"]
            n += 1
    if n == 0:
        return content, 0
    new_content = soup.body.decode_contents() if soup.body else str(soup)
    return new_content, n


def main():
    apply = "--apply" in sys.argv
    db = SessionLocal()
    try:
        articles = db.query(KnowledgeArticle).all()
        changed = []
        skipped = []
        for a in articles:
            before = a.content or ""
            after, n = clean(before)
            if n == 0:
                continue
            if pre_contents(before) != pre_contents(after):
                skipped.append(a)
                continue
            changed.append((a, after, n))

        print(f"total={len(articles)} changed={len(changed)} skipped={len(skipped)}")
        for a, _, n in changed:
            print(f"  {n:>3} 处 color  {a.id}  《{a.title}》")
        for a in skipped:
            print(f"  [跳过·pre 内容变化] {a.id}  《{a.title}》")

        if apply and changed:
            for a, after, _ in changed:
                a.content = after
            db.commit()
            print(f"applied={len(changed)}")
        elif not apply:
            print("dry-run: 未写入。加 --apply 实际写入。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
