from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


def extract_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return YAML metadata and the Markdown body without the metadata header."""
    source = (text or "").lstrip("\ufeff")
    match = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", source, re.S)
    if not match:
        return {}, source.strip()
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, source[match.end():].strip()


def _string_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        values = [str(item).strip() for item in value]
    elif value is None:
        values = []
    else:
        values = [
            item.strip()
            for item in re.split(r"[、,，/\n]+", str(value))
        ]
    cleaned = [
        re.sub(r"^[-*]\s+", "", item.strip()).strip("`").strip()
        for item in values
    ]
    return [item for item in cleaned if item]


def _section(text: str, name: str) -> str:
    match = re.search(
        rf"^##\s*{re.escape(name)}\s*\r?\n(.*?)(?=^##\s|\Z)",
        text,
        re.M | re.S,
    )
    return match.group(1).strip() if match else ""


def _parse_legacy_skill(text: str, stem: str) -> dict[str, Any]:
    heading = re.search(r"^#\s+(.+)$", text, re.M)
    tools_section = _section(text, "tools")
    links_section = _section(text, "links")
    return {
        "name": heading.group(1).strip() if heading else stem,
        "description": _section(text, "description"),
        "triggers": _string_list(_section(text, "trigger")),
        "tools": _string_list(re.findall(r"`([^`]+)`", tools_section) or tools_section),
        "links": [
            line.lstrip("- ").strip()
            for line in links_section.splitlines()
            if line.strip().startswith("-")
        ],
        "category": _section(text, "category"),
    }


def parse_capability_document(content: str, kind: str, stem: str = "") -> dict[str, Any]:
    """Parse standard YAML Skill documents and the workbench's legacy section format."""
    raw = (content or "").strip()
    meta, body = extract_frontmatter(raw)
    metadata = meta.get("metadata") if isinstance(meta.get("metadata"), dict) else {}
    legacy = _parse_legacy_skill(body, stem or "capability")

    name = str(meta.get("name") or metadata.get("name") or legacy["name"] or stem).strip()
    description = re.sub(r"\s+", " ", str(
        meta.get("description")
        or metadata.get("description")
        or legacy["description"]
        or ""
    )).strip()
    category = str(
        meta.get("category")
        or metadata.get("category")
        or legacy["category"]
        or ""
    ).strip()
    triggers = _string_list(
        meta.get("triggers")
        if meta.get("triggers") is not None
        else metadata.get("triggers")
        if metadata.get("triggers") is not None
        else legacy["triggers"]
    )
    tools = _string_list(
        meta.get("tools")
        if meta.get("tools") is not None
        else metadata.get("tools")
        if metadata.get("tools") is not None
        else legacy["tools"]
    )
    links = _string_list(
        meta.get("links")
        if meta.get("links") is not None
        else metadata.get("links")
        if metadata.get("links") is not None
        else legacy["links"]
    )
    return {
        "kind": kind,
        "stem": stem,
        "name": name,
        "description": description,
        "category": category,
        "triggers": triggers,
        "tools": tools,
        "links": links,
        "always": bool(meta.get("always", metadata.get("always", False))),
        "version": str(meta.get("version") or metadata.get("version") or "1"),
        "license": str(meta.get("license") or metadata.get("license") or ""),
        "metadata": metadata,
        "body": body,
        "has_frontmatter": bool(meta),
    }


def detect_capability_kind(filename: str, content: str, requested: str = "auto") -> str:
    if requested in {"skill", "prompt", "mcp"}:
        return requested
    suffix = Path(filename or "").suffix.lower()
    if suffix == ".json":
        return "mcp"
    if suffix == ".skill" or Path(filename or "").name.lower() == "skill.md":
        return "skill"
    if content.lstrip().startswith("{") and '"mcpServers"' in content:
        return "mcp"
    return "prompt"
