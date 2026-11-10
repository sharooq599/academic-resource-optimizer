
from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    DateTime,
    CheckConstraint,
    func
)
from sqlalchemy.orm import relationship

from app.models import Base


class Faculty(Base):
    __tablename__ = "faculty"

    # Primary Key
    faculty_id = Column(
        String(13),
        primary_key=True
    )

    # Faculty Information
    faculty_name = Column(
        String(120),
        nullable=False
    )

    department = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(150),
        nullable=False,
        unique=True
    )

    designation = Column(
        String(50),
        nullable=False
    )

    # Maximum weekly teaching workload in hours
    max_weekly_workload = Column(
        Integer,
        nullable=False
    )

    employment_type = Column(
        String(20),
        nullable=False,
        default="FULL_TIME"
    )

    joining_date = Column(
        Date,
        nullable=False
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
        CheckConstraint(
            "max_weekly_workload > 0",
            name="check_faculty_workload"
        ),

        CheckConstraint(
            "employment_type IN ('FULL_TIME', 'PART_TIME', 'CONTRACT')",
            name="check_employment_type"
        ),

        CheckConstraint(
            "status IN ('ACTIVE', 'ON_LEAVE', 'INACTIVE')",
            name="check_faculty_status"
        ),
    )

    # Relationship: Faculty -> FacultySkill (One-to-Many)
    skills = relationship(
        "FacultySkill",
        back_populates="faculty"
    )

    # Relationship: Faculty -> Availability (One-to-Many)
    availabilities = relationship(
        "Availability",
        back_populates="faculty"
    )

    # Relationship: Faculty -> WorkloadAssignment (One-to-Many)
    workload_assignments = relationship(
        "WorkloadAssignment",
        back_populates="faculty"
    )

    def __repr__(self):
        return (
            f"<Faculty {self.faculty_id}: "
            f"{self.faculty_name}>"
        )
