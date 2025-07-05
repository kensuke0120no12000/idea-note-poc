from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# .envファイルからデータベースURLを読み込むか、デフォルトでSQLiteのメモリ内DBを使用
# PoCでは、ファイルベースのSQLiteを使用します。
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./poc_database.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # SQLiteを使用する場合、複数のスレッドで同じ接続を共有できないため、
    # connect_args={"check_same_thread": False} が必要です。
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base() 