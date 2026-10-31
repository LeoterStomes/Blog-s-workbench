from services.capability_document import parse_capability_document


def test_parse_standard_yaml_skill_document():
    content = """---
name: humanizer
description: Rewrite AI-sounding prose without changing facts.
category: 写作规范
triggers: [去 AI 味, 润色文章]
tools:
  - get_article
  - update_article
license: MIT
metadata:
  version: "3.1.0"
---
# Humanizer

Rewrite only the prose.
"""

    parsed = parse_capability_document(content, "skill", "SKILL")

    assert parsed["name"] == "humanizer"
    assert parsed["description"] == "Rewrite AI-sounding prose without changing facts."
    assert parsed["category"] == "写作规范"
    assert parsed["triggers"] == ["去 AI 味", "润色文章"]
    assert parsed["tools"] == ["get_article", "update_article"]
    assert parsed["license"] == "MIT"
    assert parsed["version"] == "3.1.0"
    assert parsed["body"].startswith("# Humanizer")
    assert "---\nname:" not in parsed["body"]


def test_parse_legacy_skill_document_remains_supported():
    content = """# Proofreader
## description
Proofread drafts
## trigger
proofread、检查
## tools
- `get_article`
## category
内容创作
## workflow
Read and fix.
"""

    parsed = parse_capability_document(content, "skill", "proofreader")

    assert parsed["name"] == "Proofreader"
    assert parsed["triggers"] == ["proofread", "检查"]
    assert parsed["tools"] == ["get_article"]
    assert parsed["category"] == "内容创作"
    assert parsed["body"] == content.strip()
