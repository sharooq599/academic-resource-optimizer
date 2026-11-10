from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    func
)
from sqlalchemy.orm import relationship

from app.models import Base


class WorkloadAssignment(Base):
    __tablename__ = "workload_assignments"

    workload_assignment_id = Column(
        String(15),
        primary_key=True
    )

    faculty_id = Column(
        String(13),
        ForeignKey("faculty.faculty_id"),
        nullable=False
    )

    section_id = Column(
        String(15),
        ForeignKey("sections.section_id"),
        nullable=False
    )

    weekly_hours = Column(
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

    effective_start_date = Column(Date, nullable=False)
    effective_end_date = Column(Date, nullable=True)

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
        CheckConstraint(
            "weekly_hours > 0",
            name="check_assignment_hours"
        ),
        CheckConstraint(
            "semester IN (1, 2, 3)",
            name="check_assignment_semester"
        ),
        CheckConstraint(
            "status IN ('PROPOSED', 'APPROVED', 'REJECTED', 'CANCELLED')",
            name="check_assignment_status"
        ),
    )

    faculty = relationship(
        "Faculty",
        back_populates="workload_assignments"
    )

    section = relationship(
        "Section",
        back_populates="workload_assignments"
    )