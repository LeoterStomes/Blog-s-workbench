import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import get_current_user_id
from database import get_db
from models import CapabilityAsset, User
from services.asset_service import list_assets, set_capability_enabled
from services.mcp_client import activate_mcp_server
from services.prompt_builder import _parse_frontmatter, _parse_skill


router = APIRouter(prefix="/api/workbench", tags=["内容工作台"])


class CapabilityImportBody(BaseModel):
    kind: Literal["skill", "mcp", "prompt"]
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(default="自定义", max_length=80)
    description: str = Field(default="", max_length=600)
    content: str = ""
    config: dict = Field(default_factory=dict)


class CapabilityToggleBody(BaseModel):
    enabled: bool


def _require_admin(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.user_type != 2:
        raise HTTPException(status_code=403, detail="仅管理员可以导入或删除能力资产")


@router.get("/assets")
def assets(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return {"code": "200", "msg": "ok", "data": list_assets(db, user_id)}


@router.post("/assets/import")
def import_asset(
    body: CapabilityImportBody,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _require_admin(db, user_id)
    name = body.name.strip()
    content = body.content.strip()
    config = body.config or {}

    if body.kind in {"skill", "prompt"} and not content:
        raise HTTPException(status_code=400, detail="Skill 或 Prompt 内容不能为空")
    parsed_description = body.description.strip()
    parsed_category = body.category.strip() or "自定义"
    if body.kind == "prompt":
        meta, _ = _parse_frontmatter(content)
        config.update({
            "triggers": meta.get("triggers", []),
            "tools": meta.get("tools", []),
            "links": meta.get("links", []),
            "always": bool(meta.get("always")),
        })
        parsed_description = parsed_description or str(meta.get("description", "")).strip()
        parsed_category = str(meta.get("category", "")).strip() or parsed_category
    elif body.kind == "skill":
        parsed = _parse_skill(content, name)
        config.update({
            "triggers": parsed.get("triggers", []),
            "tools": parsed.get("tools", []),
            "links": parsed.get("links", []),
        })
        parsed_description = parsed_description or parsed.get("description", "")
        parsed_category = parsed.get("category") or parsed_category
    if body.kind == "mcp":
        target = config.get("mcpServers", {}).get(name, config) if isinstance(config, dict) else {}
        if not target.get("url") and not target.get("command"):
            raise HTTPException(status_code=400, detail="MCP 配置必须包含 url 或 command")
        config = target

    row = (
        db.query(CapabilityAsset)
        .filter(
            CapabilityAsset.user_id == user_id,
            CapabilityAsset.kind == body.kind,
            CapabilityAsset.name == name,
        )
        .first()
    )
    if row is None:
        row = CapabilityAsset(
            user_id=user_id,
            kind=body.kind,
            name=name,
        )
        db.add(row)
    row.category = parsed_category
    row.description = parsed_description or content[:180]
    row.content = content
    row.config_json = json.dumps(config, ensure_ascii=False)
    row.status = 1
    db.commit()
    db.refresh(row)
    return {"code": "200", "msg": "能力资产已导入", "data": {"id": f"capability:{row.id}"}}


@router.put("/assets/{asset_id}/enabled")
def toggle_asset(
    asset_id: str,
    body: CapabilityToggleBody,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if asset_id.startswith("capability:"):
        try:
            row_id = int(asset_id.split(":", 1)[1])
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="能力资产 ID 无效")
        row = (
            db.query(CapabilityAsset)
            .filter(CapabilityAsset.id == row_id, CapabilityAsset.user_id == user_id)
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="能力资产不存在")
        if body.enabled:
            if row.kind == "mcp":
                try:
                    config = json.loads(row.config_json or "{}")
                except json.JSONDecodeError:
                    config = {}
                activated, reason = activate_mcp_server(row.name, config)
                if not activated:
                    raise HTTPException(status_code=502, detail=f"MCP 启用失败：{reason}")
            row.status = 1
            db.commit()
    elif not asset_id.startswith(("skill:", "prompt:", "mcp:")):
        raise HTTPException(status_code=400, detail="能力资产 ID 无效")

    set_capability_enabled(db, user_id, asset_id, body.enabled)
    return {"code": "200", "msg": "开关已更新", "data": {"id": asset_id, "enabled": body.enabled}}


@router.delete("/assets/{asset_id}")
def delete_imported_asset(
    asset_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _require_admin(db, user_id)
    if not asset_id.startswith("capability:"):
        raise HTTPException(status_code=400, detail="内置或运行时资产不能删除")
    try:
        row_id = int(asset_id.split(":", 1)[1])
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="能力资产 ID 无效")
    row = (
        db.query(CapabilityAsset)
        .filter(CapabilityAsset.id == row_id, CapabilityAsset.user_id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="能力资产不存在")
    row.status = 0
    db.commit()
    return {"code": "200", "msg": "已移除导入资产", "data": None}
