import unittest
import json
from unittest.mock import patch

from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from database import Base
from models import CapabilityAsset, User
from routers.workbench import (
    CapabilityImportBody,
    CapabilityInspectBody,
    CapabilityToggleBody,
    import_asset,
    inspect_asset,
    toggle_asset,
)
from services.agent_service import _submit_capability_draft
from services.asset_service import (
    filter_enabled_mcp_tools,
    imported_prompt_context,
    imported_skill_body,
    list_assets,
)


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

    def test_inspect_detects_standard_skill_metadata_before_import(self):
        content = """---
name: humanizer
description: Rewrite AI-sounding prose without changing facts.
category: 写作规范
triggers: [去 AI 味]
tools: [get_article, update_article]
license: MIT
metadata:
  version: "3.1.0"
---
# Humanizer

Rewrite only the prose.
"""
        result = inspect_asset(
            CapabilityInspectBody(kind="auto", filename="SKILL.md", content=content),
            user_id=1,
            db=self.db,
        )
        data = result["data"]

        self.assertEqual(data["kind"], "skill")
        self.assertEqual(data["name"], "humanizer")
        self.assertEqual(data["triggers"], ["去 AI 味"])
        self.assertEqual(data["config"]["version"], "3.1.0")
        self.assertEqual(data["config"]["license"], "MIT")
        self.assertNotIn("---\nname:", data["body"])

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
        self.assertTrue(items["skill:content-writer"]["enabled"])

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
        toggle_asset(
            "capability:" + imported["id"].split(":", 1)[1],
            CapabilityToggleBody(enabled=False),
            user_id=1,
            db=self.db,
        )
        self.assertEqual(imported_prompt_context(self.db, 1, "please review this"), "")

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
    def test_standard_yaml_skill_import_preserves_metadata(self, *_mocks):
        content = """---
name: humanizer
description: Rewrite AI-sounding prose without changing facts.
category: 写作规范
triggers: [去 AI 味, 润色文章]
tools: [get_article, update_article]
license: MIT
metadata:
  version: "3.1.0"
---
# Humanizer

Rewrite only the prose.
"""
        import_asset(
            CapabilityImportBody(
                kind="skill",
                name="humanizer",
                content=content,
            ),
            user_id=1,
            db=self.db,
        )

        catalog = list_assets(self.db, user_id=1)
        imported = next(item for item in catalog["items"] if item["name"] == "humanizer")
        assert imported["description"] == "Rewrite AI-sounding prose without changing facts."
        assert imported["category"] == "写作规范"
        assert imported["triggers"] == ["去 AI 味", "润色文章"]
        assert imported["tools"] == ["get_article", "update_article"]
        assert imported["config"]["license"] == "MIT"
        assert imported["config"]["version"] == "3.1.0"
        assert imported["content"].startswith("# Humanizer")

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
        imported_id = item["id"]
        self.assertEqual(item["status"], "pending")
        self.assertEqual(item["config"]["endpoint"], "example.com")
        self.assertNotIn("url", item["config"])

        with patch("routers.workbench.activate_mcp_server", return_value=(True, "connected")) as activate:
            toggle_asset(
                item["id"],
                CapabilityToggleBody(enabled=True),
                user_id=1,
                db=self.db,
            )
            activate.assert_called_once()

        with patch("services.asset_service.get_mcp_catalog", return_value=[{
            "name": "demo",
            "transport": "http",
            "tools": [],
        }]):
            enabled_catalog = list_assets(self.db, user_id=1)
        imported_mcp = next(entry for entry in enabled_catalog["items"] if entry["id"] == imported_id)
        self.assertTrue(imported_mcp["enabled"])
        self.assertEqual(imported_mcp["status"], "connected")

    def test_mcp_tool_filter_respects_disabled_server(self):
        tools = [
            {"type": "function", "function": {"name": "mcp_search__lookup"}},
            {"type": "function", "function": {"name": "search_articles"}},
        ]
        filtered = filter_enabled_mcp_tools(tools, {"mcp:search"})

        self.assertEqual([tool["function"]["name"] for tool in filtered], ["search_articles"])

    @patch("services.asset_service.get_skill_catalog", return_value=[])
    @patch("services.asset_service.get_prompt_catalog", return_value=[])
    @patch("services.asset_service.get_mcp_catalog", return_value=[])
    def test_agent_submits_capability_as_review_draft_until_user_enables_it(self, *_mocks):
        content = """---
description: Review drafts
triggers: [review]
---
Review the draft carefully.
"""
        result = json.loads(_submit_capability_draft(self.db, {
            "kind": "prompt",
            "name": "agent-reviewer",
            "content": content,
        }, user_id=1))

        self.assertEqual(result["status"], "pending_review")
        self.assertFalse(result["enabled"])
        self.assertEqual(imported_prompt_context(self.db, 1, "please review"), "")

        toggle_asset(
            result["id"],
            CapabilityToggleBody(enabled=True),
            user_id=1,
            db=self.db,
        )
        self.assertIn("Review the draft", imported_prompt_context(self.db, 1, "please review"))


if __name__ == "__main__":
    unittest.main()
