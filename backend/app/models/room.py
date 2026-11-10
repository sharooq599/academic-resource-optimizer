from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    CheckConstraint,
    func
)
from sqlalchemy.orm import relationship

from app.models import Base


class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(
        String(13),
        primary_key=True
    )

    room_name = Column(
        String(100),
        nullable=False,
        unique=True
    )

    building = Column(
        String(100),
        nullable=False
    )

    capacity = Column(
        Integer,
        nullable=False
    )

    room_type = Column(
        String(30),
        nullable=False,
        default="CLASSROOM"
    )

    has_projector = Column(
        Boolean,
        nullable=False,
        default=False
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "capacity > 0",
            name="check_room_capacity"
        ),
        CheckConstraint(
            "room_type IN ('CLASSROOM', 'LAB', 'LECTURE_HALL')",
            name="check_room_type"
        ),
    )

    sections = relationship(
        "Section",
        back_populates="room"
    )