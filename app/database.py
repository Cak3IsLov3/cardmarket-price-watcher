from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_engine() -> Engine:
    return engine


def get_session():
    with Session(engine) as session:
        yield session
