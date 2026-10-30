import json
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from models import CapabilityAsset
from services.mcp_client import get_mcp_catalog
from services.prompt_builder import get_prompt_catalog, get_skill_catalog


SKILL_CATEGORIES = {
    "content-writer": "内容创作",
    "feishu-article": "内容创作",
    "whitepaper": "内容创作",
    "researcher": "研究与检索",
    "multi-search": "研究与检索",
    "rag-kb": "研究与检索",
    "summarize": "研究与检索",
    "mindmap": "生成与交付",
    "weekly-report": "生成与交付",
    "export": "生成与交付",
    "proactive": "助手与运营",
    "reader-helper": "助手与运营",
}

PROMPT_CATEGORIES = {
    "core": "系统规则",
    "tools-reference": "系统规则",
    "privacy": "系统规则",
    "citation": "写作规范",
    "search-guide": "研究与检索",
    "mindmap-guide": "生成与交付",
    "ppt-guide": "生成与交付",
    "blog-features": "站点知识",
}

CATEGORY_ORDER = [
    "全部",
    "内容创作",
    "研究与检索",
    "生成与交付",
    "助手与运营",
    "系统规则",
    "写作规范",
    "站点知识",
    "外部连接",
    "自定义",
]


def _as_list(value) -> list:
    if isinstance(value, list):
        return value
    if not value:
        return []
    return [str(value)]


def _builtin_skills() -> list[dict]:
    assets = []
    for skill in get_skill_catalog():
        category = skill.get("category") or SKILL_CATEGORIES.get(skill["stem"], "自定义")
        assets.append({
            "id": f"skill:{skill['stem']}",
            "kind": "skill",
            "name": skill["name"],
            "category": category,
            "description": skill.get("description") or "未填写技能说明",
            "source": "builtin",
            "status": "active",
            "triggers": _as_list(skill.get("triggers")),
            "tools": _as_list(skill.get("tools")),
            "links": _as_list(skill.get("links")),
            "content": skill.get("body", ""),
            "config": {},
            "metadata": {"slug": skill["stem"]},
        })
    return assets


def _builtin_prompts() -> list[dict]:
    assets = []
    for prompt in get_prompt_catalog():
        stem = prompt["name"]
        always = bool(prompt.get("always"))
        assets.append({
            "id": f"prompt:{stem}",
            "kind": "prompt",
            "name": stem,
            "category": PROMPT_CATEGORIES.get(stem, "自定义"),
            "description": prompt.get("description") or ("常驻系统提示词" if always else "按触发词加载的提示词"),
            "source": "builtin",
            "status": "always" if always else "active",
            "triggers": _as_list(prompt.get("triggers")),
            "tools": _as_list(prompt.get("tools")),
            "links": _as_list(prompt.get("links")),
            "content": prompt.get("body", ""),
            "config": {},
            "metadata": {"slug": stem, "always": always, "version": prompt.get("version", 1)},
        })
    return assets


def _connected_mcp_assets() -> list[dict]:
    assets = []
    for server in get_mcp_catalog():
        tools = server.get("tools", [])
        assets.append({
            "id": f"mcp:{server['name']}",
            "kind": "mcp",
            "name": server["name"],
            "category": "外部连接",
            "description": f"已连接 · {len(tools)} 个工具 · {server.get('transport', 'unknown').upper()} 传输",
            "source": "runtime",
            "status": "connected",
            "triggers": [],
            "tools": [tool["name"] for tool in tools],
            "links": [],
            "content": "",
            "config": {
                "transport": server.get("transport"),
                "tools": tools,
            },
            "metadata": {"connected": True},
        })
    return assets


def _imported_assets(db: Session, user_id: int) -> list[dict]:
    assets = []
    rows = (
        db.query(CapabilityAsset)
        .filter(CapabilityAsset.user_id == user_id, CapabilityAsset.status > 0)
        .order_by(CapabilityAsset.updated_at.desc())
        .all()
    )
    for row in rows:
        try:
            config = json.loads(row.config_json or "{}")
        except json.JSONDecodeError:
            config = {}
        public_config = config
        if row.kind == "mcp":
            parsed = urlparse(str(config.get("url", ""))) if config.get("url") else None
            public_config = {
                "transport": "http" if config.get("url") else "stdio",
                "endpoint": parsed.hostname if parsed else "",
                "command": config.get("command", ""),
                "args_count": len(config.get("args", [])) if isinstance(config.get("args"), list) else 0,
            }
        assets.append({
            "id": f"capability:{row.id}",
            "kind": row.kind,
            "name": row.name,
            "category": row.category or "自定义",
            "description": row.description or "用户导入的能力资产",
            "source": "imported",
            "status": "pending" if row.kind == "mcp" else "active",
            "triggers": _as_list(public_config.get("triggers")),
            "tools": _as_list(public_config.get("tools")),
            "links": _as_list(public_config.get("links")),
            "content": row.content or "",
            "config": public_config,
            "metadata": {
                "created_at": row.created_at.isoformat() if row.created_at else "",
                "updated_at": row.updated_at.isoformat() if row.updated_at else "",
            },
        })
    return assets


def _imported_rows(db: Session, user_id: int, kind: str) -> list[CapabilityAsset]:
    return (
        db.query(CapabilityAsset)
        .filter(
            CapabilityAsset.user_id == user_id,
            CapabilityAsset.kind == kind,
            CapabilityAsset.status > 0,
        )
        .order_by(CapabilityAsset.updated_at.desc())
        .all()
    )


def imported_skill_index(db: Session, user_id: int) -> str:
    rows = _imported_rows(db, user_id, "skill")
    if not rows:
        return ""
    lines = [
        "## 用户导入的技能",
        "需要时像内置技能一样调用 `use_skill` 加载完整流程。",
    ]
    for row in rows:
        lines.append(f"- **{row.name}** — {row.description or row.category}")
    return "\n".join(lines)


def imported_prompt_context(db: Session, user_id: int, match_text: str) -> str:
    bodies = []
    for row in _imported_rows(db, user_id, "prompt"):
        try:
            config = json.loads(row.config_json or "{}")
        except json.JSONDecodeError:
            config = {}
        triggers = [str(trigger).lower() for trigger in _as_list(config.get("triggers"))]
        if config.get("always") or any(trigger and trigger in match_text for trigger in triggers):
            bodies.append(row.content or "")
    return "\n\n".join(body for body in bodies if body)


def imported_skill_body(db: Session, user_id: int, name: str) -> str | None:
    key = (name or "").strip().lower()
    if not key:
        return None
    for row in _imported_rows(db, user_id, "skill"):
        if row.name.lower() == key:
            return row.content
    return None


def list_assets(db: Session, user_id: int) -> dict:
    assets = (
        _builtin_skills()
        + _builtin_prompts()
        + _connected_mcp_assets()
        + _imported_assets(db, user_id)
    )
    kind_counts = {"skill": 0, "mcp": 0, "prompt": 0}
    category_counts = {category: 0 for category in CATEGORY_ORDER[1:]}
    for asset in assets:
        kind_counts[asset["kind"]] = kind_counts.get(asset["kind"], 0) + 1
        category = asset["category"]
        category_counts[category] = category_counts.get(category, 0) + 1
    return {
        "items": assets,
        "kinds": [
            {"key": "all", "label": "全部", "count": len(assets)},
            {"key": "skill", "label": "Skill", "count": kind_counts["skill"]},
            {"key": "mcp", "label": "MCP", "count": kind_counts["mcp"]},
            {"key": "prompt", "label": "Prompt", "count": kind_counts["prompt"]},
        ],
        "categories": [
            {"name": category, "count": category_counts.get(category, 0)}
            for category in CATEGORY_ORDER
            if category == "全部" or category_counts.get(category, 0)
        ],
    }
