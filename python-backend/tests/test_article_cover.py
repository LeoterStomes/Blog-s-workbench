import unittest

from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from database import Base
from models import KnowledgeArticle
from services.article_service import create_article, get_detail, update_article


@compiles(BigInteger, "sqlite")
def compile_big_integer_as_sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


class ArticleCoverTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        self.db = sessionmaker(bind=engine)()

    def tearDown(self):
        self.db.close()

    def test_create_and_update_persist_cover_image(self):
        article_id = create_article(self.db, {
            "title": "Cover test",
            "content": "<p>Body</p>",
            "coverImage": "/uploads/cover-one.jpg",
        }, author_id=1)

        self.assertEqual(get_detail(self.db, article_id)["coverImage"], "/uploads/cover-one.jpg")

        update_article(self.db, article_id, {"coverImage": "/uploads/cover-two.jpg"})
        row = self.db.query(KnowledgeArticle).filter_by(id=article_id).first()
        self.assertEqual(row.cover_image, "/uploads/cover-two.jpg")


if __name__ == "__main__":
    unittest.main()
