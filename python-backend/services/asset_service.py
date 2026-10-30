from sqlalchemy.orm import Session

from models import KnowledgeArticle, Music, User, UserAsset


def list_assets(db: Session, user_id: int) -> list[dict]:
    assets = []
    user = db.query(User).filter(User.id == user_id).first()

    if user and user.avatar:
        assets.append({
            "id": f"avatar:{user.id}",
            "name": "当前头像",
            "url": user.avatar,
            "kind": "image",
            "source": "profile",
            "mime_type": "",
            "size": 0,
            "created_at": user.updated_at.isoformat() if user.updated_at else "",
        })

    for music in (
        db.query(Music)
        .filter(Music.user_id == user_id)
        .order_by(Music.sort_order.asc(), Music.id.desc())
        .all()
    ):
        assets.append({
            "id": f"music:{music.id}",
            "name": music.title,
            "url": music.url,
            "kind": "audio",
            "source": "music",
            "mime_type": "",
            "size": 0,
            "created_at": music.created_at.isoformat() if music.created_at else "",
        })

    for asset in (
        db.query(UserAsset)
        .filter(UserAsset.user_id == user_id)
        .order_by(UserAsset.created_at.desc())
        .all()
    ):
        assets.append({
            "id": f"asset:{asset.id}",
            "name": asset.name,
            "url": asset.url,
            "kind": asset.kind,
            "source": asset.source,
            "mime_type": asset.mime_type,
            "size": asset.size,
            "created_at": asset.created_at.isoformat() if asset.created_at else "",
        })

    covers = (
        db.query(KnowledgeArticle)
        .filter(
            KnowledgeArticle.status == 1,
            KnowledgeArticle.cover_image.isnot(None),
            KnowledgeArticle.cover_image != "",
        )
        .order_by(KnowledgeArticle.published_at.desc())
        .limit(50)
        .all()
    )
    for article in covers:
        assets.append({
            "id": f"article:{article.id}",
            "name": article.title,
            "url": article.cover_image,
            "kind": "image",
            "source": "article",
            "mime_type": "",
            "size": 0,
            "created_at": article.published_at.isoformat() if article.published_at else "",
        })

    return sorted(assets, key=lambda item: item["created_at"], reverse=True)
