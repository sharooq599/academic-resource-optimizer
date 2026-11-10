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


class Program(Base):
    __tablename__ = "programs"

    program_id = Column(String(13), primary_key=True)
    program_name = Column(String(150), nullable=False)
    department = Column(String(100), nullable=False)
    degree_level = Column(String(30), nullable=False)
    duration_years = Column(Integer, nullable=False)

    effective_start_date = Column(Date, nullable=False)
    effective_end_date = Column(Date, nullable=True)

    status = Column(String(20), nullable=False, default="ACTIVE")

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "duration_years > 0",
            name="check_program_duration"
        ),
        CheckConstraint(
            "degree_level IN ('BACHELORS', 'MASTERS', 'DIPLOMA', 'DOCTORATE')",
            name="check_degree_level"
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'ARCHIVED')",
            name="check_program_status"
        ),
    )

    courses = relationship(
        "Course",
        back_populates="program"
    )

    student_plans = relationship(
        "StudentPlan",
        back_populates="program"
    )

    def __repr__(self):
        return f"<Program {self.program_id}: {self.program_name}>"