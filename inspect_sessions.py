#!/usr/bin/env python
"""Inspect the existing sessions table."""
from dotenv import load_dotenv
load_dotenv()

from app.configuration.database_connection import DatabaseConnection
from sqlalchemy import text

engine = DatabaseConnection._create_engine()
with engine.connect() as conn:
    # Get column information
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'sessions'
        ORDER BY ordinal_position
    """))
    
    print("Existing 'sessions' table structure:")
    print("-" * 80)
    for row in result:
        print(f"  {row[0]:<30} {row[1]:<20} NULL: {row[2]:<5} DEFAULT: {row[3]}")
