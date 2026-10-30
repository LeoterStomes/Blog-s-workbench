import unittest
from unittest.mock import patch

from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from database import Base
from models import CapabilityAsset, User
from routers.workbench import CapabilityImportBody, import_asset
from services.asset_service import imported_prompt_context, imported_skill_body, list_assets


@compiles(BigInteger, "sqlite")
def compile_big_integer_as_sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


class CapabilityLibraryTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        self.db = sessionmaker(bind=engine)()
        self.db.add_all([
            User(id=1, username="admin", password="hashed", user_type=2),
            User(id=2, username="reader", password="hashed", user_type=1),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    @patch("services.asset_service.get_skill_catalog")
    @patch("services.asset_service.get_prompt_catalog")
    @patch("services.asset_service.get_mcp_catalog")
    def test_catalog_maps_skills_prompts_and_mcp(self, mcp, prompts, skills):
        skills.return_value = [{
            "name": "Writer",
            "stem": "content-writer",
            "description": "Write articles",
            "body": "# Writer",
            "triggers": ["write", "draft"],
            "tools": ["create_draft", "search_articles"],
            "links": ["export.skill"],
        }]
        prompts.return_value = [{
            "name": "core",
            "description": "Core rules",
            "body": "Rules",
            "triggers": [],
            "always": True,
            "tools": [],
            "links": [],
        }]
        mcp.return_value = [{
            "name": "search",
            "transport": "http",
            "tools": [{"name": "mcp_search__lookup", "description": "Lookup", "parameters": {}}],
        }]

        catalog = list_assets(self.db, user_id=1)
        items = {item["id"]: item for item in catalog["items"]}

        self.assertEqual(items["skill:content-writer"]["category"], "内容创作")
        self.assertEqual(items["skill:content-writer"]["tools"], ["create_draft", "search_articles"])
        self.assertEqual(items["prompt:core"]["status"], "always")
        self.assertEqual(items["mcp:search"]["category"], "外部连接")
        self.assertEqual(items["mcp:search"]["tools"], ["mcp_search__lookup"])
        self.assertFalse(any(item["kind"] in {"image", "audio"} for item in catalog["items"]))

    @patch("services.asset_service.get_skill_catalog", return_value=[])
    @patch("services.asset_service.get_prompt_catalog", return_value=[])
    @patch("services.asset_service.get_mcp_catalog", return_value=[])
    def test_imported_assets_are_private_and_prompt_metadata_is_mapped(self, *_mocks):
        content = """---
description: Review drafts
triggers: [review, proofread]
tools: [get_article]
---
# Reviewer
Review the article carefully.
"""
        import_asset(
            CapabilityImportBody(
                kind="prompt",
                name="reviewer",
                content=content,
            ),
            user_id=1,
            db=self.db,
        )

        admin_catalog = list_assets(self.db, user_id=1)
        reader_catalog = list_assets(self.db, user_id=2)
        imported = next(item for item in admin_catalog["items"] if item["source"] == "imported")

        self.assertEqual(imported["description"], "Review drafts")
        self.assertIn("review", imported["triggers"])
        self.assertIn("get_article", imported["tools"])
        self.assertEqual(reader_catalog["items"], [])
        self.assertIn("Review the article", imported_prompt_context(self.db, 1, "please review this"))

    @patch("services.asset_service.get_skill_catalog", return_value=[])
    @patch("services.asset_service.get_prompt_catalog", return_value=[])
    @patch("services.asset_service.get_mcp_catalog", return_value=[])
    def test_imported_skill_can_be_loaded_by_agent(self, *_mocks):
        import_asset(
            CapabilityImportBody(
                kind="skill",
                name="Proofreader",
                content="""# Proofreader
## description
Proofread drafts
## trigger
proofread
## workflow
Read and fix the draft.
""",
            ),
            user_id=1,
            db=self.db,
        )

        self.assertIn("Read and fix", imported_skill_body(self.db, 1, "proofreader"))
        self.assertIsNone(imported_skill_body(self.db, 2, "proofreader"))

    @patch("services.asset_service.get_skill_catalog", return_value=[])
    @patch("services.asset_service.get_prompt_catalog", return_value=[])
    @patch("services.asset_service.get_mcp_catalog", return_value=[])
    def test_mcp_import_is_stored_as_pending_without_external_execution(self, *_mocks):
        import_asset(
            CapabilityImportBody(
                kind="mcp",
                name="demo",
                config={"mcpServers": {"demo": {"url": "https://example.com/mcp"}}},
            ),
            user_id=1,
            db=self.db,
        )

        catalog = list_assets(self.db, user_id=1)
        item = next(item for item in catalog["items"] if item["kind"] == "mcp")
        self.assertEqual(item["status"], "pending")
        self.assertEqual(item["config"]["endpoint"], "example.com")
        self.assertNotIn("url", item["config"])


if __name__ == "__main__":
    unittest.main()
