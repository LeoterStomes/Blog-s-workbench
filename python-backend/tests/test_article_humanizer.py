import json

from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from database import Base
from models import KnowledgeArticle, User
from services.article_humanizer_service import (
    apply_humanized_article,
    build_article_fact_profile,
    compare_article_facts,
)


@compiles(BigInteger, "sqlite")
def compile_big_integer_as_sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


ORIGINAL_HTML = """
<p>Python 3.12 在 2023 年发布，性能提升约 5%。</p>
<p><a href="https://example.com/docs">官方文档</a> 仍是主要依据。</p>
<img src="/images/python.webp" alt="Python 示例">
<pre><code>python --version</code></pre>
<blockquote>“先测量，再优化。”</blockquote>
"""


def test_fact_profile_detects_links_media_code_numbers_and_quotes():
    profile = build_article_fact_profile(ORIGINAL_HTML)

    assert profile["links"] == ["https://example.com/docs"]
    assert profile["media"] == ["/images/python.webp"]
    assert profile["code"] == ["python --version"]
    assert "3.12" in profile["numbers"]
    assert "2023" in profile["numbers"]
    assert "5%" in profile["numbers"]
    assert profile["quotes"] == ["先测量，再优化。"]


def test_prose_only_rewrite_passes_fact_validation():
    rewritten = ORIGINAL_HTML.replace(
        "<p>Python 3.12 在 2023 年发布，性能提升约 5%。</p>",
        "<p>Python 3.12 于 2023 年发布，运行速度大约提升 5%。</p>",
    )

    assert compare_article_facts(ORIGINAL_HTML, rewritten)["valid"] is True


def test_apply_humanized_article_rejects_changed_facts_without_writing():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    try:
        db.add(User(id=1, username="admin", password="hashed", user_type=2))
        article = KnowledgeArticle(
            id="article-1",
            title="Python",
            content=ORIGINAL_HTML,
            author_id=1,
        )
        db.add(article)
        db.commit()

        broken = ORIGINAL_HTML.replace("5%", "15%")
        result = json.loads(apply_humanized_article(db, "article-1", broken, "润色正文"))

        assert "error" in result
        assert result["validation"]["valid"] is False
        assert result["validation"]["issues"]["numbers"]["added"] == ["15%"]
        assert result["validation"]["issues"]["numbers"]["missing"] == ["5%"]
        db.refresh(article)
        assert article.content == ORIGINAL_HTML
    finally:
        db.close()


def test_apply_humanized_article_updates_after_validation():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    try:
        db.add(User(id=1, username="admin", password="hashed", user_type=2))
        article = KnowledgeArticle(
            id="article-2",
            title="Python",
            content=ORIGINAL_HTML,
            author_id=1,
        )
        db.add(article)
        db.commit()
        rewritten = ORIGINAL_HTML.replace("仍是主要依据", "仍然是主要依据")

        result = json.loads(apply_humanized_article(db, "article-2", rewritten, "减少生硬表达"))

        assert result["status"] == "updated"
        assert result["validation"]["valid"] is True
        db.refresh(article)
        assert article.content == rewritten
    finally:
        db.close()
