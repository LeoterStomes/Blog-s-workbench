"""一次性清洗：移除文章正文中「标注模块(callout)」与「分隔线(hr)」的内联 style。

背景：旧版编辑器会把这两个块的颜色/背景写成内联样式，导致它们不跟随明暗主题。
用精确正则只摘 style 属性，正文其余内容逐字节不动（不做 HTML 重新序列化）。

用法（在 python-backend 目录下，用项目 venv 运行）：
  python clean_inline_styles.py            # 干跑：只报告，不写库
  python clean_inline_styles.py --apply    # 实际写入
"""
import sys
import re

# 让输出以 UTF-8 编码，避免 Windows GBK 控制台在中文/emoji 上崩掉
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from database import SessionLocal
from models import KnowledgeArticle

# 标注模块：<p data-callout="true" style="..."> 或 <div data-callout="true" style="...">
CALLOUT_STYLE_RE = re.compile(r'(data-callout="[^"]*")\s+style="[^"]*"')
# 分隔线：<hr style="...">（可能自闭合）
HR_STYLE_RE = re.compile(r'<hr\s+style="[^"]*"\s*/?>')


def clean(content: str):
    """返回 (新内容, 移除的 style 属性个数)。"""
    if not content:
        return content, 0
    new_content, n1 = CALLOUT_STYLE_RE.subn(r"\1", content)
    new_content, n2 = HR_STYLE_RE.subn("<hr>", new_content)
    return new_content, n1 + n2


def main():
    apply = "--apply" in sys.argv
    db = SessionLocal()
    try:
        articles = db.query(KnowledgeArticle).all()
        changed = []  # (article, 移除个数)
        for a in articles:
            new_content, n = clean(a.content or "")
            if n > 0:
                changed.append((a, new_content, n))

        print(f"total={len(articles)} changed={len(changed)}")
        for a, _, n in changed:
            print(f"  {n:>2} 个 style  {a.id}  《{a.title}》")

        if apply and changed:
            for a, new_content, _ in changed:
                a.content = new_content
            db.commit()
            print(f"applied={len(changed)}")
        elif not apply:
            print("dry-run: 未写入。确认后加 --apply 实际写入。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
