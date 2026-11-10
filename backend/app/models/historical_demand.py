
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    DateTime,
    CheckConstraint,
    UniqueConstraint,
    func,
)

from app.models import Base


class HistoricalCourseDemand(Base):
    __tablename__ = "historical_course_demand"

    # Primary Key
    historical_demand_id = Column(
        String(15),
        primary_key=True,
    )

    # Foreign Key
    course_id = Column(
        String(13),
        ForeignKey("courses.course_id"),
        nullable=False,
        index=True,
    )

    # Academic Information
    academic_year = Column(
        Integer,
        nullable=False,
    )

    semester = Column(
        Integer,
        nullable=False,
    )

    # Demand Information
    demand_count = Column(
        Integer,
        nullable=False,
    )

    enrolled_count = Column(
        Integer,
        nullable=False,
    )

    waitlisted_count = Column(
        Integer,
        nullable=False,
    )

    sections_offered = Column(
        Integer,
        nullable=False,
    )

    # Data provenance
    source_type = Column(
        String(30),
        nullable=False,
        default="SYNTHETIC_HISTORICAL",
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )

    # Database Constraints
    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "academic_year",
            "semester",
            name="uq_course_historical_demand",
        ),

        CheckConstraint(
            "academic_year >= 2023",
            name="check_historical_academic_year",
        ),

        CheckConstraint(
            "semester IN (1, 2, 3)",
            name="check_historical_semester",
        ),

        CheckConstraint(
            "demand_count >= 0",
            name="check_demand_count",
        ),

        CheckConstraint(
            "enrolled_count >= 0",
            name="check_enrolled_count",
        ),

        CheckConstraint(
            "waitlisted_count >= 0",
            name="check_waitlisted_count",
        ),

        CheckConstraint(
            "sections_offered >= 0",
            name="check_sections_offered",
        ),

        CheckConstraint(
            "enrolled_count + waitlisted_count = demand_count",
            name="check_demand_distribution",
        ),

        CheckConstraint(
            "source_type IN ('SYNTHETIC_HISTORICAL')",
            name="check_historical_source_type",
        ),
    )

    def __repr__(self):
        return (
            f"<HistoricalCourseDemand "
            f"{self.course_id} - "
            f"{self.academic_year} - "
            f"Semester {self.semester}>"
        )
