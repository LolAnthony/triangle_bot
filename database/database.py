from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Date, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from os import getenv

load_dotenv()
DEV = getenv('DEV')

Base = declarative_base()

######## User
class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    description = Column(String(100))

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    surname = Column(String(35))
    tgid = Column(Integer)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)

######## Rooms
class Room(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    floor = Column(Integer)

class RoomUser(Base):
    __tablename__ = 'rooms_users'
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

class RoomInit(Base):
    __tablename__ = 'rooms_inits'
    id = Column(Integer, primary_key=True)
    key = Column(String(256))

######## Duty
class Duty(Base):
    __tablename__ = 'duties'
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    date = Column(Date)

class DutyRoom(Base):
    __tablename__ = 'duties_rooms'
    id = Column(Integer, primary_key=True)
    duty_id = Column(Integer, ForeignKey('duties.id'), nullable=False)
    is_approved = Column(Boolean)
    is_sent = Column(Boolean)

######## Database
class Database:
    def __init__(self, db_url):
        self.engine = create_async_engine(db_url, echo=True)
        self.Session = async_sessionmaker(self.engine, expire_on_commit=False)

    async def initialize(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self):
        async with self.Session() as session:
            yield session

    async def add_instance(self, instance):
        async with self.get_session() as session:
            try:
                await session.add(instance)
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"Error while adding instance: {e}")

    async def query(self, model, **kwargs):
        async with self.get_session() as session:
            try:
                result = await session.execute(session.query(model).filter_by(**kwargs))
                return result.scalars().all()
            except SQLAlchemyError as e:
                print(f"Error querying data: {e}")
                return []

    async def query_one(self, model, **kwargs):
        async with self.get_session() as session:
            try:
                result = await session.execute(session.query(model).filter_by(**kwargs))
                return result.scalars().first()
            except SQLAlchemyError as e:
                print(f"Error querying one data: {e}")
                return None

    async def is_exist(self):
        async with self.engine.connect() as conn:
            return await conn.run_sync(self._check_tables_exist)

    def _check_tables_exist(self, conn):
        inspector = inspect(conn)
        table_names = inspector.get_table_names()
        expected_tables = [table.name for table in Base.metadata.sorted_tables]

        return all(table in table_names for table in expected_tables)
