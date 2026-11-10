from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    Date,
    DateTime,
    CheckConstraint,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import relationship

from app.models import Base


class FacultySkill(Base):
    __tablename__ = "faculty_skills"

    skill_id = Column(
        String(13),
        primary_key=True
    )

    faculty_id = Column(
        String(13),
        ForeignKey("faculty.faculty_id"),
        nullable=False
    )

    skill_name = Column(
        String(100),
        nullable=False
    )

    proficiency_level = Column(
        Integer,
        nullable=False
    )

    effective_start_date = Column(Date, nullable=False)
    effective_end_date = Column(Date, nullable=True)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "faculty_id",
            "skill_name",
            "effective_start_date",
            name="uq_faculty_skill"
        ),
        CheckConstraint(
            "proficiency_level BETWEEN 1 AND 5",
            name="check_proficiency"
        ),
    )

    faculty = relationship(
        "Faculty",
        back_populates="skills"
    )