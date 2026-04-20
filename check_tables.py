#!/usr/bin/env python
"""Check what tables exist in the database."""
from dotenv import load_dotenv
load_dotenv()

from app.configuration.database_connection import DatabaseConnection
from sqlalchemy import text

engine = DatabaseConnection._create_engine()
with engine.connect() as conn:
    # Check for new tables
    new_tables = ['branches', 'terminals', 'sessions', 'assignments', 'closings']
    print("Checking for new tables:")
    for table in new_tables:
        result = conn.execute(text(f"SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = '{table}')"))
        exists = result.scalar()
        status = "✓ EXISTS" if exists else "✗ MISSING"
        print(f"  {status}: {table}")
    
    # Check alembic version
    result = conn.execute(text("SELECT version_num FROM alembic_version"))
    version = result.scalar()
    print(f"\nCurrent Alembic version: {version}")
