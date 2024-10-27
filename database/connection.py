from SQLAlchemy import create_engine

from dotenv import load_dotenv
import os

engine = create_engine(os.getenv('DATABASE_ENGINE_STRING'))
