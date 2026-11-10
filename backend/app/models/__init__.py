
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Enum,
    Text,
)

from sqlalchemy.orm import relationship

from app.database.connection import Base

# Import all models to register them with SQLAlchemy.

from app.models.program import Program
from app.models.course import Course
from app.models.prerequisite import Prerequisite
from app.models.student import StudentPlan, RegistrationInterest
from app.models.faculty import Faculty
from app.models.faculty_skill import FacultySkill
from app.models.availability import Availability
from app.models.room import Room
from app.models.section import Section
from app.models.allocation import WorkloadAssignment

# Historical demand model
from app.models.historical_demand import HistoricalCourseDemand
