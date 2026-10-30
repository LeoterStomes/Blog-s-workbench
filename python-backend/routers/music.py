import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user_id
from services.music_service import (
    ALLOWED_AUDIO_EXTENSIONS,
    get_list,
    upload_and_create,
    update,
    delete,
)
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/music", tags=["音乐"])
MAX_MUSIC_BYTES = 100 * 1024 * 1024


class MusicUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    lyrics: Optional[str] = None
    sort_order: Optional[int] = None


@router.get("/list")
def list_music(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return {"code": "200", "msg": "ok", "data": get_list(db, user_id)}


@router.post("/upload")
async def upload(file: UploadFile = File(...), title: str = Form(""), artist: str = Form("未知"),
                 lyrics: str = Form(""), user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    raw_name = file.filename or "未知"
    ext = os.path.splitext(raw_name)[1].lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的音频格式")

    chunks = []
    size = 0
    while chunk := await file.read(1024 * 1024):
        size += len(chunk)
        if size > MAX_MUSIC_BYTES:
            raise HTTPException(status_code=413, detail="音频文件不能超过 100 MB")
        chunks.append(chunk)
    content = b"".join(chunks)

    detected_title = title or raw_name.rsplit(".", 1)[0]
    detected_artist = artist
    if not title and not artist and " - " in raw_name.rsplit(".", 1)[0]:
        parts = raw_name.rsplit(".", 1)[0].split(" - ", 1)
        detected_artist = parts[0].strip()
        detected_title = parts[1].strip()
    result = upload_and_create(db, content, raw_name, detected_title, detected_artist, user_id)
    return {"code": "200", "msg": "上传成功", "data": result}


@router.put("/{mid}")
def update_music(mid: int, body: MusicUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    changed = update(db, user_id, mid, {k: v for k, v in body.model_dump().items() if v is not None})
    if not changed:
        raise HTTPException(status_code=404, detail="歌曲不存在")
    return {"code": "200", "msg": "更新成功", "data": None}


@router.delete("/{mid}")
def delete_music(mid: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    deleted = delete(db, user_id, mid)
    if not deleted:
        raise HTTPException(status_code=404, detail="歌曲不存在")
    return {"code": "200", "msg": "删除成功", "data": None}
