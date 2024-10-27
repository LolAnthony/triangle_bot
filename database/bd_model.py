from SQLAlchemy import Connection, Column, Integer, String, Boolean, ForeignKey, Date, Text

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from database.connection import engine

Base = declarative_base


######## User 
class Role(base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    description = Column(String(100))

class User(base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    surname = Column(String(35))
    tgid = Column(Integer)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)


######## Rooms
class Room(base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    floor = Column(Integer)

class RoomUser(base):
    __tablename__ = 'rooms_users'
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

class RoomInit(base):
    __tablename__ = 'rooms_inits'
    id = Column(Integer, primary_key=True)
    key = Column(String(256))


######## Duty
class Duty(base):
    __tablename__ = 'duties'
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    date = Column(Date)

class DutyRoom(base):
    __tablename__ = 'duties_rooms'
    id = Column(Integer, primary_key=True)
    duty_id = Column(Integer, ForeignKey('duty.id'), nullable=False)
    is_approved = Column(Boolean)
    is_sent = Column(Boolean)


######## Disciplinary
class Discipline(base):
    __tablename__ = 'disciplines'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message = Column(String(200))


Base.metadata.create_all(engine)
