from sqlalchemy.orm import Session
from .. import models, schemas
from typing import Dict, Any

def validate_and_log_event(db: Session, event: schemas.EventLogIn) -> models.EventLog:
    """
    イベントを検証し、データベースに記録する。
    PoC段階では、バリデーションは単純なものとする。
    """
    if not event.event_type or not event.raw_event:
        # 実際にはもっと複雑なバリデーションが必要
        raise ValueError("Event type and raw event data are required.")

    db_event = models.EventLog(
        event_type=event.event_type,
        raw_event=event.raw_event,
        notes=event.notes
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_event(db: Session, event_id: int):
    """
    IDを指定してイベントログを取得する。
    """
    return db.query(models.EventLog).filter(models.EventLog.id == event_id).first()

def get_events(db: Session, skip: int = 0, limit: int = 100):
    """
    イベントログのリストを取得する。
    """
    return db.query(models.EventLog).offset(skip).limit(limit).all() 