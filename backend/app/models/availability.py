from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Date,
    DateTime,
    CheckConstraint,
    func
)
from sqlalchemy.orm import relationship

from app.models import Base


class Availability(Base):
    __tablename__ = "availabilities"

    availability_id = Column(
        String(13),
        primary_key=True
    )

    faculty_id = Column(
        String(13),
        ForeignKey("faculty.faculty_id"),
        nullable=False
    )

    day_of_week = Column(
        String(10),
        nullable=False
    )

    start_time = Column(
        String(5),
        nullable=False
    )

    end_time = Column(
        String(5),
        nullable=False
    )

    effective_start_date = Column(Date, nullable=False)
    effective_end_date = Column(Date, nullable=True)

    status = Column(
        String(20),
        nullable=False,
        default="AVAILABLE"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "day_of_week IN ('MONDAY', 'TUESDAY', 'WEDNESDAY', "
            "'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY')",
            name="check_day_of_week"
        ),
        CheckConstraint(
            "start_time < end_time",
            name="check_availability_time"
        ),
        CheckConstraint(
            "status IN ('AVAILABLE', 'UNAVAILABLE', 'ON_LEAVE')",
            name="check_availability_status"
        ),
    )

    faculty = relationship(
        "Faculty",
        back_populates="availabilities"
    )