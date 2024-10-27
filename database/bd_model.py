from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date

from sqlalchemy.orm import declarative_base

from connection import engine

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


######## Disciplinary
class Discipline(Base):
    __tablename__ = 'disciplines'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message = Column(String(200))


Base.metadata.create_all(engine)
