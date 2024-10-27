from sqlalchemy import create_engine

from dotenv import load_dotenv
from os import getenv

load_dotenv()

connection_string = getenv('DATABASE_ENGINE_STRING')

engine = create_engine(connection_string)
