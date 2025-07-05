from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json

from . import models, schemas
from .database import SessionLocal, engine
from .services import event_logger, event_generator
from .services.inference_engine import inference_engine

# データベーステーブルを作成
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="動的知覚・推論システム PoC",
    description="戦術ループの動作を検証するためのAPI"
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/events/", response_model=schemas.EventLogOut, tags=["Events"])
def create_event_and_get_inference(event: schemas.EventLogIn, db: Session = Depends(get_db)):
    """
    新しいイベントを記録し、そのイベントに対する推論（アクション提案）を取得します。
    """
    # 1. バリデーターとロガーを使ってイベントをDBに記録
    db_event = event_logger.validate_and_log_event(db=db, event=event)
    
    # 2. 推論エンジンにイベント情報を渡してアクションを提案させる
    #    JSON形式のraw_eventを文字列に変換してクエリとして渡す
    query_str = json.dumps(db_event.raw_event, ensure_ascii=False, indent=2)
    inference_result = inference_engine.ask(query_str)
    
    # 3. 推論結果をnotesフィールドに追記して更新（オプション）
    notes_with_inference = (
        f"Inference Result: {inference_result['answer']}\\n"
        f"Source: {inference_result['source_documents']}"
    )
    db_event.notes = f"{db_event.notes or ''}\\n---\\n{notes_with_inference}"
    db.commit()
    db.refresh(db_event)
    
    return db_event

@app.post("/events/generate_and_process/", tags=["Events"])
def generate_and_process_event(db: Session = Depends(get_db)):
    """
    ダミーのイベントを自動生成し、記録と推論を一度に行います。
    """
    # 1. ダミーイベントを生成
    dummy_event_data = event_generator.generate_dummy_event()
    event = schemas.EventLogIn(**dummy_event_data)
    
    # 2. イベントの記録と推論の実行
    #    (create_event_and_get_inference と同じロジックを再利用)
    db_event = event_logger.validate_and_log_event(db=db, event=event)
    query_str = json.dumps(db_event.raw_event, ensure_ascii=False, indent=2)
    inference_result = inference_engine.ask(query_str)
    
    notes_with_inference = (
        f"Inference Result: {inference_result['answer']}\\n"
        f"Source: {inference_result['source_documents']}"
    )
    db_event.notes = f"{db_event.notes or ''}\\n---\\n{notes_with_inference}"
    db.commit()
    db.refresh(db_event)
    
    return {
        "processed_event": schemas.EventLogOut.from_orm(db_event),
        "inference": inference_result
    }


@app.get("/events/", response_model=List[schemas.EventLogOut], tags=["Events"])
def read_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    記録されたイベントのリストを取得します。
    """
    events = event_logger.get_events(db, skip=skip, limit=limit)
    return events

@app.get("/events/{event_id}", response_model=schemas.EventLogOut, tags=["Events"])
def read_event(event_id: int, db: Session = Depends(get_db)):
    """
    特定のIDのイベントを取得します。
    """
    db_event = event_logger.get_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event 