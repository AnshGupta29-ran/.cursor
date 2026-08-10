"""SQLite persistence via SQLAlchemy. Schema auto-created on startup."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class InputAsset(Base):
    __tablename__ = "input_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sha256: Mapped[str] = mapped_column(String(64), index=True)  # dedupe key
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str] = mapped_column(String(50))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    byte_size: Mapped[int] = mapped_column(Integer)
    stored_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    predictions: Mapped[list["Prediction"]] = relationship(back_populates="asset")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    asset_id: Mapped[int] = mapped_column(ForeignKey("input_assets.id"), index=True)
    request_id: Mapped[str] = mapped_column(String(36), index=True)
    intake_tag: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    profile_name: Mapped[str] = mapped_column(String(50))
    model_name: Mapped[str] = mapped_column(String(50))
    model_version: Mapped[str] = mapped_column(String(50))
    category_map_version: Mapped[str] = mapped_column(String(50))
    top1_label: Mapped[str] = mapped_column(String(100))
    top1_score: Mapped[float] = mapped_column(Float)
    top1_category: Mapped[str] = mapped_column(String(50), index=True)
    latency_ms: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), index=True)  # auto_routed | needs_review | failed
    routing_hint: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    asset: Mapped[InputAsset] = relationship(back_populates="predictions")
    labels: Mapped[list["PredictionLabel"]] = relationship(
        back_populates="prediction", cascade="all, delete-orphan",
        order_by="PredictionLabel.rank",
    )
    review_task: Mapped["ReviewTask | None"] = relationship(
        back_populates="prediction", cascade="all, delete-orphan", uselist=False,
    )


class PredictionLabel(Base):
    __tablename__ = "prediction_labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_id: Mapped[str] = mapped_column(ForeignKey("predictions.id"), index=True)
    rank: Mapped[int] = mapped_column(Integer)  # 1..5
    imagenet_label: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Float)
    mapped_category: Mapped[str] = mapped_column(String(50))

    prediction: Mapped[Prediction] = relationship(back_populates="labels")


class ReviewTask(Base):
    __tablename__ = "review_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_id: Mapped[str] = mapped_column(ForeignKey("predictions.id"), index=True)
    reason: Mapped[str] = mapped_column(String(50))  # below_threshold | ambiguous_margin | ...
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)  # open | confirmed | corrected
    corrected_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    prediction: Mapped[Prediction] = relationship(back_populates="review_task")


def make_session_factory(database_url: str) -> sessionmaker:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
