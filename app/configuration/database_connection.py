import json
import logging
import os
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
    def _resolve_credentials() -> tuple:
        """Resolve DB credentials from env vars (local) or Secrets Manager (Lambda)."""
        host = AppConfig.get_key("database.host")
        port = AppConfig.get_key("database.port", 5432)
        username = AppConfig.get_key("database.username")
        password = AppConfig.get_key("database.password")
        dbname = AppConfig.get_key("database.dbname")

        if all([host, username, password, dbname]):
            return host, port, username, password, dbname

        # Fall back to shared Secrets Manager secret: tsuru/{env}/database
        secret_name = AppConfig.get_key("aws.database")
        if not secret_name:
            raise RuntimeError("Database credentials not found: set DATABASE_* env vars or deploy SSM params stack")

        logger.info(f"Loading DB credentials from Secrets Manager: {secret_name}")
        import boto3
        region = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION", "us-east-1")
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        creds = json.loads(response["SecretString"])

        return (
            creds.get("host", host),
            int(creds.get("port", port or 5432)),
            creds.get("username", username),
            creds.get("password", password),
            creds.get("dbname", dbname),
        )

    @staticmethod
    def _create_engine() -> Engine:
        try:
            host, port, username, password, dbname = DatabaseConnection._resolve_credentials()

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
    def from_session(cls, session: Session):
        """Create an instance that shares an existing session.

        Used when multiple repositories need to participate in the same
        transaction (e.g., upserting related entities during order parsing).
        """
        instance = cls.__new__(cls)
        instance.session = session
        return instance

    @classmethod
    def close_all(cls):
        if cls._engine:
            cls._engine.dispose()
            logger.info("All database connections closed")
