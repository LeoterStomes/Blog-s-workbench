import unittest

from services.agent_service import (
    TOOLS_SCHEMA,
    agent_mode_instruction,
    filter_tools_by_mode,
    normalize_agent_mode,
)
from services.prompt_builder import build_system_prompt


class AgentModeTest(unittest.TestCase):
    def test_readonly_mode_only_exposes_read_tools(self):
        tools = filter_tools_by_mode(TOOLS_SCHEMA, "readonly")
        names = {tool["function"]["name"] for tool in tools}

        self.assertIn("search_articles", names)
        self.assertIn("list_articles", names)
        self.assertIn("read_url", names)
        self.assertNotIn("create_draft", names)
        self.assertNotIn("update_article", names)
        self.assertNotIn("set_status", names)
        self.assertNotIn("delete_article", names)
        self.assertNotIn("export_file", names)
        self.assertNotIn("submit_capability_draft", names)

    def test_plan_mode_does_not_expose_write_tools(self):
        names = {
            tool["function"]["name"]
            for tool in filter_tools_by_mode(TOOLS_SCHEMA, "plan")
        }

        self.assertIn("search_articles", names)
        self.assertNotIn("create_draft", names)
        self.assertNotIn("make_mindmap", names)
        self.assertNotIn("submit_capability_draft", names)

    def test_execute_mode_keeps_full_tool_set(self):
        tools = filter_tools_by_mode(TOOLS_SCHEMA, "execute")
        self.assertEqual(len(tools), len(TOOLS_SCHEMA))

    def test_unknown_mode_fails_closed_to_readonly(self):
        self.assertEqual(normalize_agent_mode("unknown"), "readonly")
        self.assertIn("只读", agent_mode_instruction("unknown"))

    def test_missing_mode_keeps_legacy_execute_behavior(self):
        self.assertEqual(normalize_agent_mode(None), "execute")

    def test_disabled_builtin_prompt_and_skill_are_not_injected(self):
        prompt, _ = build_system_prompt(
            "write an article",
            disabled_ids={"prompt:core", "skill:content-writer"},
        )

        self.assertNotIn("Content Writer", prompt)


if __name__ == "__main__":
    unittest.main()
