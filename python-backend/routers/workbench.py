from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import get_current_user_id
from database import get_db
from services.asset_service import list_assets


router = APIRouter(prefix="/api/workbench", tags=["内容工作台"])


@router.get("/assets")
def assets(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return {"code": "200", "msg": "ok", "data": list_assets(db, user_id)}
