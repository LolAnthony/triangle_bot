import random
import string

from database.database import User, Role, Room, RoomInit


async def triangle_init(db):
    roles = (
        ('admin', 'Полный доступ'),
        ('supervisor', 'Подтверждение дежурства, получение жалоб на этаже'),
        ('resident', 'Житель общежития')
    )
    for role in roles:
        add_role = Role (
            name = role[0],
            description = role[1],
        )
        await db.add_instance(add_role)

    users = (
        ('Егор', 'Голубев', 930555164, 1),
        ('Антон', 'Развадский', 123123123, 1)
    )
    for user in users:
        add_user = User (
            name = user[0],
            surname = user[1],
            tgid = user[2],
            role_id = user[3],
        )
        await db.add_instance(add_user)

    rooms = ((number, number//100) for number in range(100, 520) if 0 < number%100 < 20)
    for room in rooms:
        add_room = Room (
            number = room[0],
            floor = room[1],
        )
        await db.add_instance(add_room)

    key_room = [(room_id, ''.join(random.choices(string.ascii_letters, k=50))) for room_id in range(1, 97)]
    for key in key_room:
        add_key = RoomInit (
            room_id = key[0],
            key = key[1],
        )
        await db.add_instance(add_key)
