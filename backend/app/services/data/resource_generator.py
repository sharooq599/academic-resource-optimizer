
import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models import (
    Program,
    Course,
    Faculty,
    FacultySkill,
    Availability,
    Room,
)

from app.services.data.config import (
    SEED,
    NUM_FACULTY,
    NUM_ROOMS,
    MIN_WEEKLY_WORKLOAD,
    MAX_WEEKLY_WORKLOAD,
    MIN_ROOM_CAPACITY,
    MAX_ROOM_CAPACITY,
    ACADEMIC_START_DATE,
    ACADEMIC_END_DATE,
)


def generate_resources():
    rng = random.Random(SEED + 2)

    start_date = date.fromisoformat(ACADEMIC_START_DATE)
    end_date = date.fromisoformat(ACADEMIC_END_DATE)

    db: Session = SessionLocal()

    try:
        # Prevent duplicate generation
        if db.query(Faculty).first() or db.query(Room).first():
            print("Faculty or room records already exist.")
            print("Skipping generation to prevent duplicates.")
            return

        programs = db.query(Program).all()
        courses = db.query(Course).all()

        if not programs or not courses:
            raise ValueError(
                "Generate programs and courses before generating resources."
            )

        # --------------------------------------------------
        # 1. Prepare department and course information
        # --------------------------------------------------

        departments = sorted({
            program.department for program in programs
        })

        courses_by_department = {}

        for department in departments:
            department_program_ids = {
                program.program_id
                for program in programs
                if program.department == department
            }

            department_courses = [
                course
                for course in courses
                if course.program_id in department_program_ids
            ]

            # IMPORTANT:
            # Remove duplicate course names within each department.
            # FacultySkill has a unique constraint on faculty,
            # skill name and effective start date.

            unique_courses = {}

            for course in department_courses:
                unique_courses.setdefault(
                    course.course_name,
                    course
                )

            courses_by_department[department] = list(
                unique_courses.values()
            )

        # --------------------------------------------------
        # 2. Generate faculty
        # --------------------------------------------------

        first_names = [
            "Aarav", "Aditya", "Arjun", "Kiran", "Rahul",
            "Ravi", "Sanjay", "Vikram", "Ananya", "Divya",
            "Kavya", "Meera", "Neha", "Priya", "Sneha",
            "Swathi", "Pooja", "Ishita", "Rohan", "Varun",
        ]

        last_names = [
            "Sharma", "Reddy", "Kumar", "Rao", "Patel",
            "Verma", "Singh", "Gupta", "Naidu", "Das",
            "Iyer", "Nair", "Mehta", "Joshi", "Pillai",
        ]

        designations = [
            "Assistant Professor",
            "Associate Professor",
            "Professor",
            "Lecturer",
        ]

        employment_types = [
            "FULL_TIME",
            "FULL_TIME",
            "FULL_TIME",
            "PART_TIME",
            "CONTRACT",
        ]

        faculty_records = []

        for i in range(1, NUM_FACULTY + 1):
            department = rng.choice(departments)

            faculty = Faculty(
                faculty_id=f"FAC-{i:06d}",
                faculty_name=(
                    f"{rng.choice(first_names)} "
                    f"{rng.choice(last_names)}"
                ),
                department=department,
                email=f"faculty{i:06d}@example.edu",
                designation=rng.choice(designations),
                max_weekly_workload=rng.randint(
                    MIN_WEEKLY_WORKLOAD,
                    MAX_WEEKLY_WORKLOAD,
                ),
                employment_type=rng.choice(employment_types),
                joining_date=start_date - timedelta(
                    days=rng.randint(30, 2500)
                ),
                status="ACTIVE",
            )

            db.add(faculty)
            faculty_records.append(faculty)

        db.flush()

        print(f"Generated {len(faculty_records)} faculty members.")

        # --------------------------------------------------
        # 3. Generate faculty skills
        # --------------------------------------------------

        skill_counter = 1
        total_skills = 0

        for faculty in faculty_records:
            available_courses = courses_by_department.get(
                faculty.department,
                [],
            )

            if not available_courses:
                available_courses = list({
                    course.course_name: course
                    for course in courses
                }.values())

            if not available_courses:
                continue

            number_of_skills = min(
                len(available_courses),
                rng.randint(2, 5),
            )

            selected_courses = rng.sample(
                available_courses,
                number_of_skills,
            )

            # Extra safety: guarantee unique skill names per faculty.
            assigned_skill_names = set()

            for course in selected_courses:
                skill_name = course.course_name

                if skill_name in assigned_skill_names:
                    continue

                assigned_skill_names.add(skill_name)

                skill = FacultySkill(
                    skill_id=f"FSK-{skill_counter:07d}",
                    faculty_id=faculty.faculty_id,
                    skill_name=skill_name,
                    proficiency_level=rng.randint(2, 5),
                    effective_start_date=start_date,
                    effective_end_date=end_date,
                )

                db.add(skill)
                skill_counter += 1
                total_skills += 1

        db.flush()

        print(f"Generated {total_skills} faculty skill records.")

        # --------------------------------------------------
        # 4. Generate weekly faculty availability
        # --------------------------------------------------

        days = [
            "MONDAY",
            "TUESDAY",
            "WEDNESDAY",
            "THURSDAY",
            "FRIDAY",
        ]

        time_slots = [
            ("09:00", "12:00"),
            ("13:00", "16:00"),
        ]

        availability_counter = 1

        for faculty in faculty_records:
            for day in days:
                for start_time, end_time in time_slots:
                    availability = Availability(
                        availability_id=(
                            f"AVL-{availability_counter:07d}"
                        ),
                        faculty_id=faculty.faculty_id,
                        day_of_week=day,
                        start_time=start_time,
                        end_time=end_time,
                        effective_start_date=start_date,
                        effective_end_date=end_date,
                        status="AVAILABLE",
                    )

                    db.add(availability)
                    availability_counter += 1

        print(
            "Generated "
            f"{availability_counter - 1} weekly availability records."
        )

        # --------------------------------------------------
        # 5. Generate faculty leave periods
        # --------------------------------------------------

        leave_faculty = rng.sample(
            faculty_records,
            min(25, len(faculty_records)),
        )

        leave_counter = 0

        for faculty in leave_faculty:
            leave_start = date(2026, 3, 2) + timedelta(
                days=rng.randint(0, 90)
            )

            leave_end = leave_start + timedelta(
                days=rng.randint(2, 5)
            )

            if leave_end > end_date:
                leave_end = end_date

            leave = Availability(
                availability_id=(
                    f"AVL-{availability_counter:07d}"
                ),
                faculty_id=faculty.faculty_id,
                day_of_week="MONDAY",
                start_time="00:00",
                end_time="23:59",
                effective_start_date=leave_start,
                effective_end_date=leave_end,
                status="ON_LEAVE",
            )

            db.add(leave)
            availability_counter += 1
            leave_counter += 1

        print(f"Generated {leave_counter} faculty leave records.")

        # --------------------------------------------------
        # 6. Generate rooms
        # --------------------------------------------------

        room_types = [
            "CLASSROOM",
            "CLASSROOM",
            "CLASSROOM",
            "LAB",
            "LECTURE_HALL",
        ]

        buildings = [
            "Block A",
            "Block B",
            "Block C",
            "Technology Block",
            "Science Block",
        ]

        for i in range(1, NUM_ROOMS + 1):
            room_type = rng.choice(room_types)

            room = Room(
                room_id=f"ROM-{i:06d}",
                room_name=f"ROOM-{i:03d}",
                building=rng.choice(buildings),
                capacity=rng.randint(
                    MIN_ROOM_CAPACITY,
                    MAX_ROOM_CAPACITY,
                ),
                room_type=room_type,
                has_projector=rng.choice([True, True, False]),
                is_active=True,
            )

            db.add(room)

        # --------------------------------------------------
        # 7. Commit transaction
        # --------------------------------------------------

        db.commit()

        print("\nRESOURCE GENERATION COMPLETED")
        print("================================")
        print(f"Faculty: {len(faculty_records)}")
        print(f"Faculty skills: {total_skills}")
        print(f"Availability records: {availability_counter - leave_counter - 1}")
        print(f"Faculty leave records: {leave_counter}")
        print(f"Rooms: {NUM_ROOMS}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    generate_resources()
