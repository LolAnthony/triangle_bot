from datetime import datetime, timedelta
from io import BytesIO
from pprint import pprint

import qrcode
from dotenv import load_dotenv
from magic_filter import AttrDict
from sqlalchemy import create_engine, delete, Column, Integer, String, Boolean, ForeignKey, Date, inspect, select
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
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
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
        async for session in self.get_session():
            try:
                session.add(instance)
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"Error while adding instance: {e}")

    async def query(self, model, **kwargs):
        async for session in self.get_session():
            try:
                result = await session.execute(select(model).filter_by(**kwargs))
                return result.scalars().all()
            except SQLAlchemyError as e:
                print(f"Error querying data: {e}")
                return []

    async def query_one(self, model, **kwargs):
        async for session in self.get_session():
            try:
                result = await session.execute(select(model).filter_by(**kwargs))
                return result.scalars().first()
            except SQLAlchemyError as e:
                print(f"Error querying one data: {e}")
                return None

    async def get_user(self, user_id):
        return await self.query_one(User, id=user_id)

    async def get_user_role(self, telegram_id):
        user = await self.query_one(User, tgid=telegram_id)
        role = await self.query_one(Role, id=user.role_id)
        return role.name

    async def add_user(self, user):
        await self.add_instance(user)

    async def get_room_id_by_number(self, room_number: int):
        room = await self.query_one(Room, number=room_number)
        return room.id

    async def get_full_name(self, tgid: int):
        full_name = await self.query_one(User, tgid=tgid)
        return f"{full_name.name} {full_name.surname}"

    async def get_room_number_by_id(self, room_id: int):
        room = await self.query_one(Room, id=room_id)
        return room.number

    async def is_exist(self):
        async with self.engine.connect() as conn:
            return await conn.run_sync(self._check_tables_exist)

    def _check_tables_exist(self, conn):
        inspector = inspect(conn)
        table_names = inspector.get_table_names()
        expected_tables = [table.name for table in Base.metadata.sorted_tables]

        return all(table in table_names for table in expected_tables)

    async def get_users_in_room(self, room_id):
        async for session in self.get_session():
            try:
                room_users_result = await session.execute(select(RoomUser.user_id).filter_by(room_id=room_id))
                room_users = room_users_result.scalars().all()
                result = await session.execute(select(User).filter(User.tgid.in_(room_users)))
                return result.scalars().all()
            except SQLAlchemyError as e:
                print(f"Error querying data: {e}")
                return []

    async def set_user_role(self, user_id, role_id):
        async for session in self.get_session():
            user = await self.query_one(User, id=user_id)
            user.role_id = role_id
            await session.merge(user)
            await session.commit()
            return user

    async def get_schedule_for_date(self, date: datetime.date = None): # т.к. комната дежурит до 01:00
        if date is None:
            # Вычисляем текущую дату с учетом смещения на -1 час, если это необходимо
            date = (datetime.now() - timedelta(hours=1, seconds=5)).date()
        try:
            duties = await self.query(Duty, date=date)
            room_ids = [duty.room_id for duty in duties]

            users = []
            for room_id in room_ids:
                room_users = await self.query(RoomUser, room_id=room_id)
                for room_user in room_users:
                    users.append(room_user)
            return {
                "duties": [duty.id for duty in duties] if len(duties) > 0 else [],
                "users": [user.user_id for user in users] if len(users) > 0 else [],
                "date": date,
            }
        except AttributeError:
            print("Нет расписания")

    async def get_current_duty_room_id(self, floor: int = -1):
        now = (datetime.now() - timedelta(hours=1, seconds=5)).date()
        async for session in self.get_session():
            duty_room_request = await session.execute(
                select(DutyRoom)
                .join(Duty, DutyRoom.duty_id == Duty.id)
                .join(Room, Room.id == Duty.room_id)
                .filter(Room.floor == floor, Duty.date == now)
            )
            duty_room = duty_room_request.scalars().first()
            return duty_room.id

    async def change_report_sent_status(self, duty_room_id):
        async for session in self.get_session():
            duty_room = await self.query_one(DutyRoom, id=duty_room_id)
            duty_room.is_sent = not duty_room.is_sent
            await session.merge(duty_room)
            await session.commit()
            return duty_room

    async def change_report_approved_status(self, duty_room_id):
        async for session in self.get_session():
            duty_room = await self.query_one(DutyRoom, id=duty_room_id)
            duty_room.is_approved = not duty_room.is_approved
            await session.merge(duty_room)
            await session.commit()
            return duty_room

    async def get_supervisor_tgid_by_resident_tgid(self, resident_id):
        async for session in self.get_session():
            room_user = await self.query_one(RoomUser, user_id=resident_id)
            room_id = room_user.room_id
            room = await self.query_one(Room, id=room_id)
            floor = room.floor
            supervisors = await session.execute(
                select(User)
                .join(RoomUser, RoomUser.user_id == User.tgid)
                .join(Room, Room.id == RoomUser.room_id)
                .filter(User.role_id == 2, Room.floor == floor)
            )
            supervisors = supervisors.scalars().all()
            supervisors_id = [i.tgid for i in supervisors] if len(supervisors) > 1 else supervisors[0].tgid
            return supervisors_id

    async def get_qrcode_for_room(self, room_id):
        room_init = await self.query_one(RoomInit, room_id=room_id)
        room_key = room_init.key
        url_key = f"https://t.me/mospolytech_residence_bot?start={room_key}"
        qr = qrcode.make(url_key)
        img_buffer = BytesIO()
        qr.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return img_buffer

    async def get_floor_by_resident_tgid(self, resident_id):
        room_user = await self.query_one(RoomUser, user_id=resident_id)
        room_id = room_user.room_id
        room = await self.query_one(Room, id=room_id)
        return room.floor

    async def get_floor_duties(self, floor: int):
        async for session in self.get_session():
            try:
                result = await session.execute(
                    select(Duty)
                    .join(Room, Room.id == Duty.room_id)
                    .where(Room.floor == floor)
                )
                return result.scalars().all()
            except SQLAlchemyError as e:
                print(f"Error querying data: {e}")
                return []

    async def update_duties(self, schedule_data):
        async for session in my_db.get_session():
            for duty in schedule_data:
                room_id = await my_db.get_room_id_by_number(duty["room_number"])

                old_duty = await self.query_one(Duty, room_id=room_id)
                # Удаляем старое дежурство для той же комнаты и даты
                await session.execute(
                    delete(Duty).where(Duty.room_id == room_id)
                )

                if old_duty:
                    # Удаляем старое duty_id
                    await session.execute(
                        delete(DutyRoom).where(DutyRoom.duty_id == old_duty.id)
                    )


                # Добавляем новое дежурство
                new_duty = Duty(room_id=room_id, date=duty["duty_date"])
                session.add(new_duty)
                await session.flush()

                print(new_duty.id)
                # Добавляем новый duty_room
                new_duty_room = DutyRoom(duty_id=new_duty.id, is_approved=False, is_sent=False)
                session.add(new_duty_room)

            await session.commit()


def get_user_by_id(user_id):
    return User(id=user_id)


CONNECTION_STRING = getenv("CONNECTION_STRING")

my_db = Database(CONNECTION_STRING)
