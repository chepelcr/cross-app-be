import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import pool

from alembic import context
from app.configuration.database_connection import DatabaseConnection

load_dotenv()

config = context.config

# Use the same engine as the app
engine = DatabaseConnection._create_engine()
config.set_main_option("sqlalchemy.url", str(engine.url))

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models so Alembic can detect them
from app.models import Base  # noqa: E402

target_metadata = Base.metadata

# Only manage tables that belong to THIS app — ignore tables from other projects
# sharing the same database.
OUR_TABLES = set(target_metadata.tables.keys())


def include_name(name, type_, parent_names):
    if type_ == "table":
        return name in OUR_TABLES
    # Always include indexes/constraints that belong to our tables
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
