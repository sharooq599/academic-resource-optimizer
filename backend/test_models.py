from app.database.connection import Base, engine

# Import all models
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

# Create tables
Base.metadata.create_all(bind=engine)

print("\nDatabase tables created successfully!")

print("\nAvailable tables:")

for table in Base.metadata.sorted_tables:
    print("-", table.name)

print("\nTotal tables:", len(Base.metadata.tables))