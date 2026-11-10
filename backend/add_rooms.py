
import random

from app.database.connection import SessionLocal
from app.models import Room
from app.services.data.config import (
    SEED,
    NUM_ROOMS,
    MIN_ROOM_CAPACITY,
    MAX_ROOM_CAPACITY,
)


def add_rooms():
    db = SessionLocal()

    room_types = [
        "CLASSROOM",
        "CLASSROOM",
        "CLASSROOM",
        "LAB",
        "LECTURE_HALL",
    ]

    buildings = [
        "Block A",
        "Block B",
        "Block C",
        "Technology Block",
        "Science Block",
    ]

    try:
        existing_rooms = db.query(Room).all()
        existing_ids = {room.room_id for room in existing_rooms}

        print("EXISTING ROOMS:", len(existing_rooms))
        print("TARGET ROOMS:", NUM_ROOMS)

        added = 0

        for i in range(1, NUM_ROOMS + 1):
            room_id = f"ROM-{i:06d}"

            if room_id in existing_ids:
                continue

            rng = random.Random(SEED + 100000 + i)

            room = Room(
                room_id=room_id,
                room_name=f"ROOM-{i:03d}",
                building=rng.choice(buildings),
                capacity=rng.randint(
                    MIN_ROOM_CAPACITY,
                    MAX_ROOM_CAPACITY,
                ),
                room_type=rng.choice(room_types),
                has_projector=rng.choice([True, True, False]),
                is_active=True,
            )

            db.add(room)
            added += 1

        db.commit()

        total = db.query(Room).filter(
            Room.is_active == True
        ).count()

        print("\nROOM EXPANSION COMPLETED")
        print("========================")
        print("New rooms added:", added)
        print("Total active rooms:", total)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    add_rooms()
