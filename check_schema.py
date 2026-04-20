from app.configuration.database_connection import DatabaseConnection
from sqlalchemy import text

db = DatabaseConnection()
result = db.session.execute(text("""
    SELECT column_name, column_default, is_nullable 
    FROM information_schema.columns 
    WHERE table_name = 'branches' 
    AND column_name IN ('created_on', 'updated_on', 'deleted_on') 
    ORDER BY column_name
"""))

for row in result:
    print(f"{row[0]}: default={row[1]}, nullable={row[2]}")
