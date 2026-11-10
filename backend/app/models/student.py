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


class StudentPlan(Base):
    __tablename__ = "student_plans"

    student_plan_id = Column(
        String(15),
        primary_key=True
    )

    student_id = Column(
        String(20),
        nullable=False,
        index=True
    )

    program_id = Column(
        String(13),
        ForeignKey("programs.program_id"),
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

    study_level = Column(
        Integer,
        nullable=False
    )

    planned_credits = Column(
        Integer,
        nullable=False
    )

    effective_date = Column(Date, nullable=False)

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
            "student_id",
            "academic_year",
            "semester",
            name="uq_student_term_plan"
        ),
        CheckConstraint(
            "semester IN (1, 2, 3)",
            name="check_student_semester"
        ),
        CheckConstraint(
            "planned_credits >= 0",
            name="check_planned_credits"
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')",
            name="check_student_plan_status"
        ),
    )

    program = relationship(
        "Program",
        back_populates="student_plans"
    )

    registration_interests = relationship(
        "RegistrationInterest",
        back_populates="student_plan"
    )


class RegistrationInterest(Base):
    __tablename__ = "registration_interests"

    interest_id = Column(
        String(15),
        primary_key=True
    )

    student_plan_id = Column(
        String(15),
        ForeignKey("student_plans.student_plan_id"),
        nullable=False
    )

    course_id = Column(
        String(13),
        ForeignKey("courses.course_id"),
        nullable=False
    )

    preference_rank = Column(
        Integer,
        nullable=False,
        default=1
    )

    interest_date = Column(
        Date,
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="REQUESTED"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "student_plan_id",
            "course_id",
            name="uq_student_course_interest"
        ),
        CheckConstraint(
            "preference_rank > 0",
            name="check_preference_rank"
        ),
        CheckConstraint(
            "status IN ('REQUESTED', 'APPROVED', 'REJECTED', 'WAITLISTED', 'WITHDRAWN')",
            name="check_interest_status"
        ),
    )

    student_plan = relationship(
        "StudentPlan",
        back_populates="registration_interests"
    )

    course = relationship("Course")