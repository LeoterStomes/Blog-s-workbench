import json
import unittest
from unittest.mock import patch

from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from database import Base
from models import KnowledgeArticle, KnowledgeCategory, User
from services.agent_service import _get_article, _list_articles, _search_articles
from services.prompt_builder import get_prompt_catalog, get_skill_catalog


@compiles(BigInteger, "sqlite")
def compile_big_integer_as_sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


class AgentCatalogTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        self.db = sessionmaker(bind=engine)()
        self.db.add_all([
            User(id=1, username="admin", password="hashed", user_type=2),
            User(id=2, username="reader", password="hashed", user_type=1),
            KnowledgeCategory(id=1, category_name="技术"),
        ])
        self.db.add_all([
            KnowledgeArticle(
                id=f"published-{index}",
                title=f"Published {index}",
                summary=f"Summary {index}",
                content=f"Content {index}",
                category_id=1,
                status=1,
            )
            for index in range(12)
        ])
        self.db.add_all([
            KnowledgeArticle(
                id=f"draft-{index}",
                title=f"Draft {index}",
                content="Draft content",
                category_id=1,
                status=0,
            )
            for index in range(2)
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_admin_can_page_through_every_article(self):
        first = json.loads(_list_articles(self.db, {"status": "all", "limit": 5}, user_id=1))
        second = json.loads(_list_articles(self.db, {"status": "all", "offset": first["next_offset"], "limit": 5}, user_id=1))
        third = json.loads(_list_articles(self.db, {"status": "all", "offset": second["next_offset"], "limit": 5}, user_id=1))

        ids = {article["id"] for page in (first, second, third) for article in page["articles"]}
        self.assertEqual(first["total"], 14)
        self.assertEqual(len(ids), 14)
        self.assertTrue(first["has_more"])
        self.assertFalse(third["has_more"])

    def test_reader_cannot_page_into_drafts(self):
        result = json.loads(_list_articles(self.db, {"status": "all", "limit": 100}, user_id=2))

        self.assertEqual(result["total"], 12)
        self.assertTrue(all(article["status"] == "published" for article in result["articles"]))

    def test_get_article_returns_content_in_chunks(self):
        article = self.db.query(KnowledgeArticle).filter_by(id="published-0").first()
        article.content = "x" * 25000
        self.db.commit()

        first = json.loads(_get_article(self.db, article.id, offset=0, max_chars=10000))
        second = json.loads(_get_article(self.db, article.id, offset=first["next_offset"], max_chars=10000))
        last = json.loads(_get_article(self.db, article.id, offset=second["next_offset"], max_chars=10000))

        self.assertEqual(len(first["content"]), 10000)
        self.assertTrue(first["has_more"])
        self.assertEqual(first["next_offset"], 10000)
        self.assertFalse(last["has_more"])

    def test_keyword_fallback_matches_category_when_rag_is_unavailable(self):
        with patch("services.rag_service.search_all", side_effect=RuntimeError("embedding unavailable")):
            result = json.loads(_search_articles(self.db, "技术", limit=10))

        self.assertEqual(result["search_type"], "keyword_fallback")
        self.assertGreater(result["count"], 0)

    def test_humanizer_voice_prompt_and_article_skill_are_in_catalogs(self):
        skills = {skill["stem"]: skill for skill in get_skill_catalog()}
        prompts = {prompt["name"]: prompt for prompt in get_prompt_catalog()}

        article_humanizer = skills["article-humanizer"]
        self.assertEqual(article_humanizer["category"], "写作规范")
        self.assertIn("去 AI 味", article_humanizer["triggers"])
        self.assertIn("apply_humanized_article", article_humanizer["tools"])
        self.assertIn("natural-voice", prompts)
        self.assertTrue(prompts["natural-voice"]["always"])


if __name__ == "__main__":
    unittest.main()
