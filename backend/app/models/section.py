from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import relationship

from app.models import Base


class Section(Base):
    __tablename__ = "sections"

    section_id = Column(
        String(15),
        primary_key=True
    )

    course_id = Column(
        String(13),
        ForeignKey("courses.course_id"),
        nullable=False
    )

    room_id = Column(
        String(13),
        ForeignKey("rooms.room_id"),
        nullable=True
    )

    section_number = Column(
        Integer,
        nullable=False
    )

    academic_year = Column(
        Integer,
        nullable=False
    )

    semester = Column(
        Integer,
        nullable=False
    )

    section_capacity = Column(
        Integer,
        nullable=False
    )

    scheduled_day = Column(
        String(10),
        nullable=True
    )

    start_time = Column(
        String(5),
        nullable=True
    )

    end_time = Column(
        String(5),
        nullable=True
    )

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="PROPOSED"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "academic_year",
            "semester",
            "section_number",
            name="uq_course_section"
        ),
        CheckConstraint(
            "section_capacity > 0",
            name="check_section_capacity"
        ),
        CheckConstraint(
            "semester IN (1, 2, 3)",
            name="check_section_semester"
        ),
        CheckConstraint(
            "status IN ('PROPOSED', 'OPEN', 'CLOSED', 'CANCELLED')",
            name="check_section_status"
        ),
    )

    course = relationship(
        "Course",
        back_populates="sections"
    )

    room = relationship(
        "Room",
        back_populates="sections"
    )

    workload_assignments = relationship(
        "WorkloadAssignment",
        back_populates="section"
    )