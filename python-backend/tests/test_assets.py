import unittest

from sqlalchemy import create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy import BigInteger
from sqlalchemy.orm import sessionmaker

from database import Base
from models import KnowledgeArticle, Music, User, UserAsset
from services.asset_service import list_assets


@compiles(BigInteger, "sqlite")
def compile_big_integer_as_sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


class AssetLibraryTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        self.db = sessionmaker(bind=engine)()
        self.db.add_all([
            User(id=1, username="alice", password="hashed", avatar="/uploads/avatars/a.png"),
            User(id=2, username="bob", password="hashed"),
            Music(id=11, user_id=1, title="Alice audio", artist="A", url="/uploads/a.mp3"),
            UserAsset(id=21, user_id=1, name="notes.pdf", url="/uploads/agent/n.pdf", kind="document", source="agent_upload"),
            UserAsset(id=22, user_id=2, name="private.png", url="/uploads/agent/b.png", kind="image", source="agent_upload"),
            KnowledgeArticle(id="article-1", title="Published", status=1, cover_image="/uploads/cover.jpg"),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_library_aggregates_owned_and_public_blog_assets(self):
        assets = list_assets(self.db, user_id=1)
        ids = {asset["id"] for asset in assets}

        self.assertIn("avatar:1", ids)
        self.assertIn("music:11", ids)
        self.assertIn("asset:21", ids)
        self.assertIn("article:article-1", ids)
        self.assertNotIn("asset:22", ids)

    def test_library_contains_expected_categories(self):
        assets = list_assets(self.db, user_id=1)
        kinds = {asset["kind"] for asset in assets}

        self.assertIn("image", kinds)
        self.assertIn("audio", kinds)
        self.assertIn("document", kinds)


if __name__ == "__main__":
    unittest.main()
