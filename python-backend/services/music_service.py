import os
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Music

MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "music")
ALLOWED_AUDIO_EXTENSIONS = {
    ".aac", ".flac", ".m4a", ".mp3", ".oga", ".ogg", ".opus", ".wav", ".weba", ".webm",
}
os.makedirs(MUSIC_DIR, exist_ok=True)


def get_list(db: Session, user_id: int):
    items = (
        db.query(Music)
        .filter(Music.user_id == user_id)
        .order_by(Music.sort_order.asc(), Music.id.desc())
        .all()
    )
    return [{"id": m.id, "title": m.title, "artist": m.artist, "url": m.url, "lyrics": m.lyrics, "cover": m.cover, "sort_order": m.sort_order} for m in items]


def normalize_sort_orders(db: Session, user_id: int):
    items = (
        db.query(Music)
        .filter(Music.user_id == user_id)
        .order_by(Music.sort_order.asc(), Music.id.desc())
        .all()
    )
    changed = False
    for position, music in enumerate(items, start=1):
        if music.sort_order != position:
            music.sort_order = position
            changed = True
    if changed:
        db.commit()
    return changed


def upload_and_create(db: Session, file_content: bytes, filename: str, title: str, artist: str, user_id: int):
    ext = os.path.splitext(filename)[1].lower() or ".mp3"
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValueError("不支持的音频格式")
    fname = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(MUSIC_DIR, fname), "wb") as f:
        f.write(file_content)
    url = f"/uploads/music/{fname}"
    max_order = (
        db.query(func.coalesce(func.max(Music.sort_order), 0))
        .filter(Music.user_id == user_id)
        .scalar()
        or 0
    )
    m = Music(
        user_id=user_id,
        title=title or filename.rsplit(".", 1)[0],
        artist=artist or "未知",
        url=url,
        sort_order=max_order + 1,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    normalize_sort_orders(db, user_id)
    return {"id": m.id, "title": m.title, "url": url}


def update(db: Session, user_id: int, mid: int, data: dict):
    m = (
        db.query(Music)
        .filter(Music.id == mid, Music.user_id == user_id)
        .first()
    )
    if not m:
        return False
    for f in ["title", "artist", "lyrics", "sort_order"]:
        if f in data and data[f] is not None:
            setattr(m, f, data[f])
    db.commit()
    if "sort_order" in data:
        normalize_sort_orders(db, user_id)
    return True


def delete(db: Session, user_id: int, mid: int):
    m = (
        db.query(Music)
        .filter(Music.id == mid, Music.user_id == user_id)
        .first()
    )
    if m:
        try:
            os.remove(os.path.join(MUSIC_DIR, os.path.basename(m.url)))
        except OSError:
            pass
        db.delete(m)
        db.commit()
        normalize_sort_orders(db, user_id)
    return m is not None
