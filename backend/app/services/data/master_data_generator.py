
import random
from datetime import date

from app.database.connection import Base, engine, SessionLocal

# Import all models to register SQLAlchemy relationships
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

from app.services.data.config import (
    SEED,
    NUM_PROGRAMS,
    NUM_COURSES
)


# --------------------------------------------------
# 1. INITIAL CONFIGURATION
# --------------------------------------------------

rng = random.Random(SEED)

EFFECTIVE_DATE = date(2026, 1, 1)

DEPARTMENTS = [
    "Computer Science",
    "Information Technology",
    "Computer Applications",
    "Electronics",
    "Mechanical Engineering",
    "Civil Engineering",
    "Mathematics",
    "Physics",
    "Commerce",
    "Management",
    "Data Science",
    "Artificial Intelligence",
    "Statistics",
    "Business Administration"
]

DEGREE_LEVELS = [
    "BACHELORS",
    "MASTERS",
    "DIPLOMA",
    "DOCTORATE"
]

COURSE_CATALOG = [
    "Python Programming",
    "Java Programming",
    "Database Management Systems",
    "Data Structures",
    "Computer Networks",
    "Operating Systems",
    "Software Engineering",
    "Web Development",
    "Machine Learning",
    "Artificial Intelligence",
    "Data Science",
    "Cloud Computing",
    "Cyber Security",
    "Statistics",
    "Mathematics",
    "Digital Electronics",
    "Business Analytics",
    "Information Systems",
    "Deep Learning",
    "Computer Architecture"
]


# --------------------------------------------------
# 2. GENERATE PROGRAMS
# --------------------------------------------------

def generate_programs(db):

    programs = []

    for i in range(1, NUM_PROGRAMS + 1):

        department = rng.choice(DEPARTMENTS)
        degree_level = rng.choice(DEGREE_LEVELS)

        duration = {
            "BACHELORS": 3,
            "MASTERS": 2,
            "DIPLOMA": 2,
            "DOCTORATE": 4
        }[degree_level]

        program = Program(
            program_id=f"PRG-{i:06d}",
            program_name=(
                f"{department} {degree_level.title()} "
                f"Program {i:03d}"
            ),
            department=department,
            degree_level=degree_level,
            duration_years=duration,
            effective_start_date=EFFECTIVE_DATE,
            effective_end_date=None,
            status="ACTIVE"
        )

        programs.append(program)

    db.add_all(programs)
    db.flush()

    print(f"Generated {len(programs)} programs")

    return programs


# --------------------------------------------------
# 3. GENERATE COURSES
# --------------------------------------------------

def generate_courses(db, programs):

    courses = []
    course_counter = 1

    # Each program gets 10 courses
    courses_per_program = NUM_COURSES // NUM_PROGRAMS

    course_levels = [
        1, 1, 1,
        2, 2, 2,
        3, 3,
        4, 4
    ]

    section_sizes = [30, 40, 50, 60, 75]

    for program_index, program in enumerate(programs, start=1):

        for j in range(1, courses_per_program + 1):

            course_name = COURSE_CATALOG[
                (j - 1) % len(COURSE_CATALOG)
            ]

            course_level = course_levels[
                (j - 1) % len(course_levels)
            ]

            course_type = rng.choices(
                ["CORE", "ELECTIVE", "OPTIONAL"],
                weights=[60, 30, 10]
            )[0]

            course = Course(
                course_id=f"CRS-{course_counter:06d}",
                program_id=program.program_id,
                course_code=f"P{program_index:03d}-C{j:03d}",
                course_name=course_name,
                credits=rng.choice([2, 3, 4]),
                course_level=course_level,
                course_type=course_type,
                target_section_size=rng.choice(section_sizes),
                effective_start_date=EFFECTIVE_DATE,
                effective_end_date=None,
                status="ACTIVE"
            )

            courses.append(course)
            course_counter += 1

    db.add_all(courses)
    db.flush()

    print(f"Generated {len(courses)} courses")

    return courses


# --------------------------------------------------
# 4. GENERATE COURSE PREREQUISITES
# --------------------------------------------------

def generate_prerequisites(db, courses):

    prerequisites = []
    prerequisite_counter = 1

    # Group courses by program
    courses_by_program = {}

    for course in courses:

        courses_by_program.setdefault(
            course.program_id, []
        ).append(course)

    for program_courses in courses_by_program.values():

        for course in program_courses:

            # Only courses at level 2 or above
            # can have prerequisites
            if course.course_level <= 1:
                continue

            # Find lower-level courses
            eligible_courses = [
                previous_course
                for previous_course in program_courses
                if previous_course.course_level < course.course_level
            ]

            # Generate prerequisites for some courses
            if eligible_courses and rng.random() < 0.55:

                prerequisite_course = rng.choice(
                    eligible_courses
                )

                prerequisite = Prerequisite(
                    prerequisite_id=(
                        f"PRE-{prerequisite_counter:06d}"
                    ),
                    course_id=course.course_id,
                    prerequisite_course_id=(
                        prerequisite_course.course_id
                    ),
                    minimum_grade=rng.choice(
                        ["D", "C", "B"]
                    ),
                    effective_start_date=EFFECTIVE_DATE,
                    effective_end_date=None,
                    status="ACTIVE"
                )

                prerequisites.append(prerequisite)
                prerequisite_counter += 1

    db.add_all(prerequisites)
    db.flush()

    print(
        f"Generated {len(prerequisites)} prerequisites"
    )

    return prerequisites


# --------------------------------------------------
# 5. MAIN GENERATION WORKFLOW
# --------------------------------------------------

def generate_master_data():

    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:

        # Prevent accidental duplicate generation
        existing_programs = db.query(Program).count()
        existing_courses = db.query(Course).count()

        if existing_programs > 0 or existing_courses > 0:

            raise RuntimeError(
                "Master data already exists. "
                "Use a fresh database before regenerating."
            )

        print("\nStarting master data generation...")

        programs = generate_programs(db)

        courses = generate_courses(db, programs)

        prerequisites = generate_prerequisites(
            db,
            courses
        )

        # Save everything in one transaction
        db.commit()

        print("\nMASTER DATA GENERATION COMPLETED")

        print("--------------------------------")
        print("Programs:", len(programs))
        print("Courses:", len(courses))
        print("Prerequisites:", len(prerequisites))
        print("--------------------------------")

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":

    generate_master_data()
