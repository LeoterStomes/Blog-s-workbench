from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String

from database import Base
from .user import now


class UserAsset(Base):
    __tablename__ = "user_asset"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    mime_type = Column(String(120), default="")
    size = Column(Integer, default=0)
    kind = Column(String(32), default="other", index=True)
    source = Column(String(32), default="upload", index=True)
    created_at = Column(DateTime, default=now)
