"""
Django management command to fix attempts that are missing responses.

This fixes cases where:
- Attempts were created before questions were added to assessments
- Questions were added after attempts were created
- Responses are missing for some questions

Usage:
    python manage.py fix_attempt_responses
    python manage.py fix_attempt_responses --student student1  # Fix for specific student
    python manage.py fix_attempt_responses --assessment 1  # Fix for specific assessment
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from assessments.models import Assessment, Attempt, Response


class Command(BaseCommand):
    help = "Fix attempts that are missing responses for questions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--student",
            type=str,
            help="Fix attempts for a specific student (username)",
        )
        parser.add_argument(
            "--assessment",
            type=int,
            help="Fix attempts for a specific assessment (ID)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be fixed without making changes",
        )

    def handle(self, *args, **options):
        student_username = options.get("student")
        assessment_id = options.get("assessment")
        dry_run = options.get("dry_run", False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made\n"))
        
        # Get attempts to fix
        attempts_query = Attempt.objects.select_related('assessment', 'student')
        
        if student_username:
            attempts_query = attempts_query.filter(student__username=student_username)
        
        if assessment_id:
            attempts_query = attempts_query.filter(assessment_id=assessment_id)
        
        attempts = attempts_query.all()
        
        if not attempts.exists():
            self.stdout.write(self.style.WARNING("No attempts found matching criteria."))
            return
        
        self.stdout.write(
            self.style.SUCCESS(f"\n=== Fixing {attempts.count()} attempt(s) ===\n")
        )
        
        fixed_count = 0
        total_responses_created = 0
        
        with transaction.atomic():
            for attempt in attempts:
                assessment = attempt.assessment
                questions = assessment.questions.all()
                question_count = questions.count()
                
                if question_count == 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ Attempt {attempt.id} - Assessment '{assessment.title}' "
                            f"has no questions (skipping)"
                        )
                    )
                    continue
                
                existing_responses = attempt.responses.all()
                existing_question_ids = set(existing_responses.values_list('question_id', flat=True))
                
                missing_questions = [q for q in questions if q.id not in existing_question_ids]
                
                if not missing_questions:
                    self.stdout.write(
                        f"  ✓ Attempt {attempt.id} - All {question_count} question(s) have responses"
                    )
                    continue
                
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ Attempt {attempt.id} - Missing responses for "
                        f"{len(missing_questions)} question(s)"
                    )
                )
                
                if not dry_run:
                    for question in missing_questions:
                        Response.objects.get_or_create(
                            attempt=attempt,
                            question=question
                        )
                        total_responses_created += 1
                    
                    fixed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    ✓ Created {len(missing_questions)} response(s)"
                        )
                    )
                else:
                    self.stdout.write(
                        f"    Would create {len(missing_questions)} response(s)"
                    )
        
        self.stdout.write(self.style.SUCCESS(f"\n=== Summary ==="))
        if dry_run:
            self.stdout.write(f"Would fix: {fixed_count} attempt(s)")
            self.stdout.write(f"Would create: {total_responses_created} response(s)")
        else:
            self.stdout.write(f"Fixed: {fixed_count} attempt(s)")
            self.stdout.write(f"Created: {total_responses_created} response(s)")
        self.stdout.write("")

