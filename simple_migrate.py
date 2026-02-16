from dotenv import load_dotenv
from sqlalchemy import create_engine
import os

load_dotenv()

from app.models import Base

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

print("Creating all tables...")
Base.metadata.create_all(engine)
print("Done!")
