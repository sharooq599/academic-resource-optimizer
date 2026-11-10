from sqlalchemy import (
    Column,
    String,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import relationship

from app.models import Base


class Prerequisite(Base):
    __tablename__ = "prerequisites"

    prerequisite_id = Column(
        String(13),
        primary_key=True
    )

    course_id = Column(
        String(13),
        ForeignKey("courses.course_id"),
        nullable=False
    )

    prerequisite_course_id = Column(
        String(13),
        ForeignKey("courses.course_id"),
        nullable=False
    )

    minimum_grade = Column(
        String(5),
        nullable=False,
        default="D"
    )

    effective_start_date = Column(Date, nullable=False)
    effective_end_date = Column(Date, nullable=True)

    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "prerequisite_course_id",
            name="uq_course_prerequisite"
        ),
        CheckConstraint(
            "course_id != prerequisite_course_id",
            name="check_no_self_prerequisite"
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'ARCHIVED')",
            name="check_prerequisite_status"
        ),
    )

    course = relationship(
        "Course",
        foreign_keys=[course_id],
        back_populates="prerequisites"
    )

    prerequisite_course = relationship(
        "Course",
        foreign_keys=[prerequisite_course_id],
        back_populates="is_prerequisite_for"
    )

    def __repr__(self):
        return (
            f"<Prerequisite {self.course_id} "
            f"requires {self.prerequisite_course_id}>"
        )