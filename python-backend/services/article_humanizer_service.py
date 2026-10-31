from __future__ import annotations

import json
import re
from collections import Counter
from html.parser import HTMLParser
from typing import Any

from sqlalchemy.orm import Session

from models import KnowledgeArticle
from services.article_service import update_article


class _ArticleFactParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.media: list[str] = []
        self.code_blocks: list[str] = []
        self.visible_parts: list[str] = []
        self._code_tag: str | None = None
        self._code_parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attributes = {key.lower(): value or "" for key, value in attrs}
        href = attributes.get("href", "").strip()
        src = attributes.get("src", "").strip()
        if href:
            self.links.append(href)
        if src:
            self.media.append(src)
        if tag in {"script", "style"}:
            self._skip_depth += 1
        if tag in {"pre", "code"} and self._code_tag is None:
            self._code_tag = tag
            self._code_parts = []

    def handle_endtag(self, tag: str):
        if self._code_tag == tag:
            block = re.sub(r"\s+", " ", " ".join(self._code_parts)).strip()
            if block:
                self.code_blocks.append(block)
            self._code_tag = None
            self._code_parts = []
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str):
        if self._code_tag is not None:
            self._code_parts.append(data)
        elif self._skip_depth == 0:
            self.visible_parts.append(data)


def _counter_values(counter: Counter) -> list[str]:
    values = []
    for value, count in sorted(counter.items()):
        values.extend([value] * count)
    return values


def build_article_fact_profile(content: str) -> dict[str, Any]:
    parser = _ArticleFactParser()
    parser.feed(content or "")
    links = Counter(parser.links)
    media = Counter(parser.media)
    visible = re.sub(r"\s+", " ", " ".join(parser.visible_parts)).strip()
    numbers = Counter(re.findall(r"(?<![\w.])\d+(?:[.,:/-]\d+)*(?:%|％)?(?![\w.])", visible))
    quotes = Counter(
        quote.strip()
        for pair in re.findall(r"“([^”\n]{2,200})”|\"([^\"\n]{2,200})\"", visible)
        for quote in pair
        if quote.strip()
    )
    return {
        "links": _counter_values(links),
        "media": _counter_values(media),
        "code": parser.code_blocks,
        "numbers": _counter_values(numbers),
        "quotes": _counter_values(quotes),
    }


def compare_article_facts(original: str, rewritten: str) -> dict[str, Any]:
    before = build_article_fact_profile(original)
    after = build_article_fact_profile(rewritten)
    issues: dict[str, dict[str, list[str]]] = {}
    for field in ("links", "media", "code", "numbers", "quotes"):
        missing = list((Counter(before[field]) - Counter(after[field])).elements())
        added = list((Counter(after[field]) - Counter(before[field])).elements())
        if missing or added:
            issues[field] = {
                "missing": missing[:20],
                "added": added[:20],
            }
    return {
        "valid": not issues,
        "issues": issues,
        "before": {key: len(value) for key, value in before.items()},
        "after": {key: len(value) for key, value in after.items()},
    }


def apply_humanized_article(
    db: Session,
    article_id: str,
    rewritten_content: str,
    change_summary: str = "",
) -> str:
    if not article_id:
        return json.dumps({"error": "需要 article_id"}, ensure_ascii=False)
    if not (rewritten_content or "").strip():
        return json.dumps({"error": "改写后的文章内容不能为空"}, ensure_ascii=False)

    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        return json.dumps({"error": f"文章不存在: {article_id}"}, ensure_ascii=False)

    validation = compare_article_facts(article.content or "", rewritten_content)
    if not validation["valid"]:
        return json.dumps({
            "error": "事实校验未通过，文章未修改。请补回缺失事实或移除新增事实后重试。",
            "validation": validation,
        }, ensure_ascii=False)

    if not update_article(db, article_id, {"content": rewritten_content}):
        return json.dumps({"error": f"文章更新失败: {article_id}"}, ensure_ascii=False)
    return json.dumps({
        "id": article_id,
        "status": "updated",
        "change_summary": (change_summary or "").strip()[:500],
        "validation": validation,
    }, ensure_ascii=False)
