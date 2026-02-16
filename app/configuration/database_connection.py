import logging
from typing import Optional

import psycopg
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.configuration.app_config import AppConfig

logger = logging.getLogger(__name__)


class DatabaseConnection:
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None
    session: Optional[Session] = None

    def __init__(self):
        if not DatabaseConnection._engine:
            DatabaseConnection._engine = self._create_engine()
            DatabaseConnection._session_factory = sessionmaker(
                bind=DatabaseConnection._engine,
                expire_on_commit=False,
            )

    def __enter__(self):
        if DatabaseConnection._session_factory is None:
            raise RuntimeError("Database not initialized")

        self.session = DatabaseConnection._session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type is not None:
                self.session.rollback()
                logger.error(f"Rolling back transaction due to: {exc_type}")
            else:
                self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error during session cleanup: {e}")
        finally:
            self.session.close()

    @staticmethod
    def _create_engine() -> Engine:
        try:
            host = AppConfig.get_key("database.host")
            port = AppConfig.get_key("database.port", 5432)
            username = AppConfig.get_key("database.username")
            password = AppConfig.get_key("database.password")
            dbname = AppConfig.get_key("database.dbname")

            if not all([host, username, password, dbname]):
                raise ValueError("Missing required database credentials")

            connection_string = f"postgresql+psycopg://{username}:{password}@{host}:{port}/{dbname}"
            logger.info(f"Using database connection: {host}:{port}")

            def _creator():
                conn = psycopg.connect(
                    host=host,
                    port=int(port),
                    user=username,
                    password=password,
                    dbname=dbname,
                    prepare_threshold=None,
                )
                return conn

            engine = create_engine(
                "postgresql+psycopg://",
                creator=_creator,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=5,
                pool_pre_ping=True,
                pool_timeout=30,
                echo=False,
            )

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")

            return engine

        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise

    @classmethod
    def close_all(cls):
        if cls._engine:
            cls._engine.dispose()
            logger.info("All database connections closed")
