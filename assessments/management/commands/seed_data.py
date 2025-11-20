"""
Django management command to seed test data for the ASR platform.

Creates:
- Test teachers
- Test students
- Assessments with questions
- Optional: Test attempts and responses

Usage:
    python manage.py seed_data
    python manage.py seed_data --with-attempts  # Include test attempts
    python manage.py seed_data --clear  # Clear existing data first
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from assessments.models import Assessment, Question, Attempt, Response

User = get_user_model()


class Command(BaseCommand):
    help = "Seed test data for teachers, students, assessments, and questions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing test data before seeding",
        )
        parser.add_argument(
            "--with-attempts",
            action="store_true",
            help="Create test attempts and responses",
        )
        parser.add_argument(
            "--teachers",
            type=int,
            default=2,
            help="Number of teachers to create (default: 2)",
        )
        parser.add_argument(
            "--students",
            type=int,
            default=5,
            help="Number of students to create (default: 5)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        clear = options["clear"]
        with_attempts = options["with_attempts"]
        num_teachers = options["teachers"]
        num_students = options["students"]

        if clear:
            self.stdout.write(self.style.WARNING("Clearing existing test data..."))
            self._clear_test_data()

        self.stdout.write(self.style.SUCCESS("Starting data seeding..."))

        # Create teachers
        teachers = self._create_teachers(num_teachers)
        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {len(teachers)} teacher(s)")
        )

        # Create students
        students = self._create_students(num_students)
        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {len(students)} student(s)")
        )

        # Create assessments
        assessments = self._create_assessments(teachers)
        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {len(assessments)} assessment(s)")
        )

        # Create attempts if requested
        if with_attempts:
            attempts = self._create_attempts(assessments, students)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created {len(attempts)} attempt(s)")
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\n" + "=" * 60
                + "\nData seeding completed successfully!"
                + "\n" + "=" * 60
            )
        )
        self._print_credentials(teachers, students)

    def _clear_test_data(self):
        """Clear existing test data."""
        deleted_counts = {
            "responses": 0,
            "attempts": 0,
            "assessments": 0,
            "teachers": 0,
            "students": 0,
        }

        # Delete responses and attempts
        deleted_counts["responses"] = Response.objects.filter(
            attempt__student__username__startswith="student"
        ).count()
        Response.objects.filter(
            attempt__student__username__startswith="student"
        ).delete()

        deleted_counts["attempts"] = Attempt.objects.filter(
            student__username__startswith="student"
        ).count()
        Attempt.objects.filter(
            student__username__startswith="student"
        ).delete()

        # Delete assessments created by test teachers
        deleted_counts["assessments"] = Assessment.objects.filter(
            teacher__username__startswith="teacher"
        ).count()
        Assessment.objects.filter(
            teacher__username__startswith="teacher"
        ).delete()

        # Delete test users
        deleted_counts["teachers"] = User.objects.filter(
            username__startswith="teacher"
        ).count()
        User.objects.filter(username__startswith="teacher").delete()

        deleted_counts["students"] = User.objects.filter(
            username__startswith="student"
        ).count()
        User.objects.filter(username__startswith="student").delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Cleared: {deleted_counts['responses']} responses, "
                f"{deleted_counts['attempts']} attempts, "
                f"{deleted_counts['assessments']} assessments, "
                f"{deleted_counts['teachers']} teachers, "
                f"{deleted_counts['students']} students"
            )
        )

    def _create_teachers(self, count: int) -> list:
        """Create test teachers."""
        teachers = []
        for i in range(1, count + 1):
            username = f"teacher{i}"
            email = f"teacher{i}@example.com"

            teacher, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "role": User.Roles.TEACHER,
                    "first_name": f"Teacher{i}",
                    "last_name": "Test",
                    "is_staff": True,
                    "is_superuser": False,
                },
            )

            if created:
                teacher.set_password("testpass123")
                teacher.save()
                teachers.append(teacher)
                self.stdout.write(f"  Created teacher: {username} (password: testpass123)")
            else:
                teachers.append(teacher)
                self.stdout.write(f"  Teacher {username} already exists")

        return teachers

    def _create_students(self, count: int) -> list:
        """Create test students."""
        students = []
        for i in range(1, count + 1):
            username = f"student{i}"
            email = f"student{i}@example.com"

            student, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "role": User.Roles.STUDENT,
                    "first_name": f"Student{i}",
                    "last_name": "Test",
                    "audio_feedback_enabled": True,
                },
            )

            if created:
                student.set_password("testpass123")
                student.save()
                students.append(student)
                self.stdout.write(f"  Created student: {username} (password: testpass123)")
            else:
                students.append(student)
                self.stdout.write(f"  Student {username} already exists")

        return students

    def _create_assessments(self, teachers: list) -> list:
        """Create assessments with questions for each teacher."""
        assessments = []

        # Assessment templates
        assessment_templates = [
            {
                "title": "Introduction to Python Programming",
                "subject": "Computer Science",
                "instructions": "Answer each question clearly and concisely. Use voice responses to explain your understanding.",
                "rubric_prompt": "Evaluate based on: correctness (40%), completeness (30%), clarity (30%)",
                "language": "en",
                "questions": [
                    {
                        "text": "What is a variable in Python? Explain with an example.",
                        "expected_answer": "A variable is a named location in memory that stores a value. In Python, you can assign values to variables using the assignment operator (=). For example: x = 10 creates a variable named x that stores the integer 10.",
                        "rubric": "Correct answer should mention: named location, stores value, assignment operator, provide example. Score based on completeness.",
                    },
                    {
                        "text": "What is the difference between a list and a tuple in Python?",
                        "expected_answer": "A list is mutable (can be modified after creation) and uses square brackets []. A tuple is immutable (cannot be modified) and uses parentheses (). Lists are typically used for collections that may change, while tuples are used for fixed collections.",
                        "rubric": "Must mention: mutability difference, syntax difference (brackets vs parentheses), use cases. Score based on accuracy and completeness.",
                    },
                    {
                        "text": "Explain what a function is in Python and how to define one.",
                        "expected_answer": "A function is a reusable block of code that performs a specific task. In Python, functions are defined using the 'def' keyword followed by the function name, parameters in parentheses, and a colon. The function body is indented. Example: def greet(name): return f'Hello, {name}'",
                        "rubric": "Should cover: definition, 'def' keyword, parameters, return statement, provide example. Score based on clarity and correctness.",
                    },
                ],
            },
            {
                "title": "World History: Ancient Civilizations",
                "subject": "History",
                "instructions": "Provide detailed answers based on your knowledge of ancient civilizations. Speak clearly and organize your thoughts.",
                "rubric_prompt": "Evaluate based on: historical accuracy (50%), detail and depth (30%), organization (20%)",
                "language": "en",
                "questions": [
                    {
                        "text": "Describe the key achievements of ancient Egyptian civilization.",
                        "expected_answer": "Ancient Egypt achieved remarkable feats including: the construction of pyramids and monuments, development of hieroglyphic writing, advances in mathematics and engineering, creation of a calendar system, and establishment of a complex religious and social structure. The civilization lasted for thousands of years along the Nile River.",
                        "rubric": "Should mention: pyramids, writing system, mathematics/engineering, calendar, social structure, Nile River. Score based on number of achievements mentioned and accuracy.",
                    },
                    {
                        "text": "What were the main characteristics of the Roman Republic?",
                        "expected_answer": "The Roman Republic featured: a system of checks and balances with separate branches of government (consuls, senate, assemblies), rule of law, citizen participation, expansion through military conquest, and eventually transition to empire. It lasted from approximately 509 BCE to 27 BCE.",
                        "rubric": "Must cover: government structure, checks and balances, rule of law, expansion, timeline. Score based on completeness and historical accuracy.",
                    },
                ],
            },
            {
                "title": "Basic Mathematics: Algebra Fundamentals",
                "subject": "Mathematics",
                "instructions": "Solve each problem step by step. Explain your reasoning clearly in your voice response.",
                "rubric_prompt": "Evaluate based on: correct solution (60%), explanation clarity (40%)",
                "language": "en",
                "questions": [
                    {
                        "text": "Solve for x: 2x + 5 = 15. Explain each step.",
                        "expected_answer": "To solve 2x + 5 = 15: First, subtract 5 from both sides: 2x = 10. Then, divide both sides by 2: x = 5. The solution is x = 5.",
                        "rubric": "Must show: subtraction step (2x = 10), division step (x = 5), final answer. Score based on correctness and explanation quality.",
                    },
                    {
                        "text": "What is the slope of the line passing through points (2, 3) and (5, 9)?",
                        "expected_answer": "The slope formula is (y2 - y1) / (x2 - x1). Using points (2, 3) and (5, 9): slope = (9 - 3) / (5 - 2) = 6 / 3 = 2. The slope is 2.",
                        "rubric": "Must show: correct formula, substitution, calculation, final answer. Score based on accuracy and explanation.",
                    },
                ],
            },
            {
                "title": "English Literature: Shakespeare Analysis",
                "subject": "Literature",
                "instructions": "Analyze the themes and characters. Provide thoughtful, well-structured responses.",
                "rubric_prompt": "Evaluate based on: understanding of themes (40%), character analysis (30%), writing quality (30%)",
                "language": "en",
                "questions": [
                    {
                        "text": "Discuss the theme of ambition in Macbeth. How does it drive the plot?",
                        "expected_answer": "Ambition is a central theme in Macbeth. Macbeth's ambition, fueled by the witches' prophecies and Lady Macbeth's encouragement, leads him to murder King Duncan. This act sets off a chain of events including further murders, paranoia, and ultimately Macbeth's downfall. The play explores how unchecked ambition can corrupt and destroy.",
                        "rubric": "Should discuss: Macbeth's ambition, influence of witches/Lady Macbeth, consequences (murders, downfall), moral lesson. Score based on depth of analysis and understanding.",
                    },
                    {
                        "text": "Compare and contrast the characters of Romeo and Juliet.",
                        "expected_answer": "Romeo is impulsive and passionate, quick to fall in love and act on emotions. Juliet is more practical and thoughtful, though equally passionate. Both are young and idealistic, willing to defy their families for love. Romeo tends to be more melancholic, while Juliet shows greater maturity and determination in their relationship.",
                        "rubric": "Must compare: personality traits, decision-making, maturity levels, similarities and differences. Score based on insight and detail.",
                    },
                ],
            },
        ]

        # Create assessments for each teacher
        for teacher in teachers:
            for template in assessment_templates:
                assessment, created = Assessment.objects.get_or_create(
                    teacher=teacher,
                    title=template["title"],
                    defaults={
                        "subject": template["subject"],
                        "instructions": template["instructions"],
                        "rubric_prompt": template["rubric_prompt"],
                        "language": template["language"],
                        "is_active": True,
                    },
                )

                if created:
                    assessments.append(assessment)
                    self.stdout.write(
                        f"  Created assessment: {assessment.title} (by {teacher.username})"
                    )

                    # Create questions for this assessment
                    for order, question_data in enumerate(template["questions"], start=1):
                        Question.objects.get_or_create(
                            assessment=assessment,
                            order=order,
                            defaults={
                                "text": question_data["text"],
                                "expected_answer": question_data["expected_answer"],
                                "rubric": question_data["rubric"],
                            },
                        )
                    self.stdout.write(
                        f"    Added {len(template['questions'])} question(s)"
                    )
                else:
                    assessments.append(assessment)
                    self.stdout.write(
                        f"  Assessment {assessment.title} already exists"
                    )

        return assessments

    def _create_attempts(self, assessments: list, students: list) -> list:
        """Create test attempts and responses."""
        attempts = []
        from datetime import timedelta

        for assessment in assessments[:2]:  # Limit to first 2 assessments
            for student in students[:3]:  # Limit to first 3 students
                # Check if attempt already exists
                existing = Attempt.objects.filter(
                    assessment=assessment,
                    student=student,
                    started_at__gte=timezone.now() - timedelta(days=1),
                ).first()

                if existing:
                    attempt = existing
                    created = False
                else:
                    attempt = Attempt.objects.create(
                        assessment=assessment,
                        student=student,
                        status=Attempt.Status.IN_PROGRESS,
                        started_at=timezone.now() - timedelta(hours=2),
                    )
                    created = True

                if created:
                    attempts.append(attempt)
                    self.stdout.write(
                        f"  Created attempt: {student.username} -> {assessment.title}"
                    )

                    # Create responses for some questions
                    questions = assessment.questions.all()[:2]  # First 2 questions
                    for question in questions:
                        response, _ = Response.objects.get_or_create(
                            attempt=attempt,
                            question=question,
                            defaults={
                                "transcription": f"Sample response from {student.username} for question {question.order}. This is a test transcription.",
                                "transcription_confidence": Decimal("0.85"),
                                "score": Decimal("75.50"),
                                "feedback_text": f"Good attempt! You demonstrated understanding of the key concepts. Consider providing more detail in your explanation.",
                                "wer": Decimal("12.50"),
                                "ai_metadata": {
                                    "model": "test-model",
                                    "confidence": 0.85,
                                },
                            },
                        )
                        self.stdout.write(f"    Created response for Q{question.order}")

        return attempts

    def _print_credentials(self, teachers: list, students: list):
        """Print login credentials for created users."""
        self.stdout.write(
            self.style.SUCCESS("\n" + "=" * 60)
        )
        self.stdout.write(self.style.SUCCESS("LOGIN CREDENTIALS"))
        self.stdout.write(
            self.style.SUCCESS("=" * 60)
        )

        self.stdout.write(self.style.WARNING("\nTeachers:"))
        for teacher in teachers:
            self.stdout.write(
                f"  Username: {self.style.SUCCESS(teacher.username)}"
                f" | Password: {self.style.SUCCESS('testpass123')}"
            )

        self.stdout.write(self.style.WARNING("\nStudents:"))
        for student in students:
            self.stdout.write(
                f"  Username: {self.style.SUCCESS(student.username)}"
                f" | Password: {self.style.SUCCESS('testpass123')}"
            )

        self.stdout.write(
            self.style.SUCCESS("\n" + "=" * 60)
        )

