from app.configuration.database_connection import DatabaseConnection
from sqlalchemy import text

with DatabaseConnection() as db:
    result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'orders' ORDER BY ordinal_position"))
    print("Columns in orders table:")
    for row in result:
        print(f"  - {row[0]}")
