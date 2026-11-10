
from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    func,
    UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.models import Base


class Course(Base):
    __tablename__ = "courses"

    # Primary Key
    course_id = Column(
        String(13),
        primary_key=True
    )

    # Foreign Key: Program
    program_id = Column(
        String(13),
        ForeignKey("programs.program_id"),
        nullable=False,
        index=True
    )

    # Course Information
    course_code = Column(
        String(30),
        nullable=False
    )

    course_name = Column(
        String(150),
        nullable=False
    )

    credits = Column(
        Integer,
        nullable=False
    )

    course_level = Column(
        Integer,
        nullable=False
    )

    course_type = Column(
        String(20),
        nullable=False,
        default="CORE"
    )

    # Expected maximum students per section
    target_section_size = Column(
        Integer,
        nullable=False,
        default=50
    )

    # Effective Dates
    effective_start_date = Column(
        Date,
        nullable=False
    )

    effective_end_date = Column(
        Date,
        nullable=True
    )

    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    # Database Constraints
    __table_args__ = (
        UniqueConstraint(
            "program_id",
            "course_code",
            name="uq_program_course_code"
        ),

        CheckConstraint(
            "credits > 0",
            name="check_course_credits"
        ),

        CheckConstraint(
            "course_level > 0",
            name="check_course_level"
        ),

        CheckConstraint(
            "course_type IN ('CORE', 'ELECTIVE', 'OPTIONAL')",
            name="check_course_type"
        ),

        CheckConstraint(
            "target_section_size > 0",
            name="check_section_size"
        ),

        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'ARCHIVED')",
            name="check_course_status"
        ),
    )

    # Relationship: Course -> Program (Many-to-One)
    program = relationship(
        "Program",
        back_populates="courses"
    )

    # Relationship: Course -> Prerequisite
    prerequisites = relationship(
        "Prerequisite",
        foreign_keys="Prerequisite.course_id",
        back_populates="course"
    )

    # Relationship: Course -> Courses that require this course
    is_prerequisite_for = relationship(
        "Prerequisite",
        foreign_keys="Prerequisite.prerequisite_course_id",
        back_populates="prerequisite_course"
    )

    # Relationship: Course -> Section (One-to-Many)
    sections = relationship(
        "Section",
        back_populates="course"
    )

    def __repr__(self):
        return (
            f"<Course {self.course_id}: "
            f"{self.course_name}>"
        )
