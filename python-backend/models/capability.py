from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from database import Base
from .user import now


class CapabilityAsset(Base):
    __tablename__ = "capability_asset"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    kind = Column(String(24), nullable=False, index=True)
    name = Column(String(160), nullable=False)
    category = Column(String(80), nullable=False, default="未分类", index=True)
    description = Column(String(600), default="")
    content = Column(Text, default="")
    config_json = Column(Text, default="")
    status = Column(Integer, default=1, index=True)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)


class UserCapabilityState(Base):
    __tablename__ = "user_capability_state"
    __table_args__ = (
        UniqueConstraint("user_id", "capability_id", name="uq_user_capability_state"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    capability_id = Column(String(180), nullable=False, index=True)
    enabled = Column(Integer, default=1, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now)
