"""第二遍清洗：把 pre 之外所有元素的 color / background / border 内联样式剥掉。

背景：正文里除了代码块，还有「笔记卡片(带图标)、深色表格行、块引用、行内代码 chip」等
带 background 的块，上一遍按「有背景就保留」把它们留下了，导致它们不跟随明暗主题。

本脚本：
  - <pre> 及其内部（代码块 + 语法高亮）→ 保留
  - 其余元素 → 剥掉 color / background / border*（保留 padding/margin/border-radius 等布局）
  - 带「background + border-left」的 <div>（笔记卡片）→ 打上 data-note 标记，供 CSS 主题化

附 <pre> 内容完整性校验（按 HTML 解码后比对）。

用法：
  python clean_theme_blocks.py            # 干跑
  python clean_theme_blocks.py --apply    # 实际写入
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

# 保留的 border-* 布局属性（不属于颜色）
KEEP_BORDER = ("border-radius", "border-collapse", "border-spacing")


def strip_theme_props(style: str) -> str:
    """移除 color / background / border（保留布局类属性）。"""
    parts = []
    for part in style.split(";"):
        part = part.strip()
        if not part:
            continue
        prop = part.split(":", 1)[0].strip().lower()
        if prop == "color" or prop.startswith("background"):
            continue
        if prop.startswith("border") and not any(prop.startswith(k) for k in KEEP_BORDER):
            continue
        parts.append(part)
    return ";".join(parts)


def pre_contents(content: str):
    return [html.unescape(x) for x in re.findall(r"<pre[^>]*>(.*?)</pre>", content or "", re.S)]


def clean(content: str):
    """返回 (新内容, 处理过的元素数)。"""
    if not content:
        return content, 0
    soup = BeautifulSoup(content, "html.parser")
    n = 0
    for el in soup.select("[style]"):
        if el.name == "pre" or el.find_parent("pre"):
            continue
        style = el.get("style") or ""
        # 笔记卡片：带 background + border-left 的 div
        if el.name == "div" and "background" in style and "border-left" in style:
            el["data-note"] = "true"
        new_style = strip_theme_props(style)
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
        changed, skipped = [], []
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
            print(f"  {n:>3} 个元素  {a.id}  《{a.title}》")
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
