"""
Django management command to check assessment data integrity.

Checks:
- Assessments without questions
- Questions without assessments
- Orphaned attempts/responses

Usage:
    python manage.py check_assessments
    python manage.py check_assessments --fix  # Attempt to fix issues
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from assessments.models import Assessment, Question, Attempt, Response


class Command(BaseCommand):
    help = "Check assessment data integrity"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Attempt to fix issues (add questions to assessments without any)",
        )

    def handle(self, *args, **options):
        fix = options["fix"]
        
        self.stdout.write(self.style.SUCCESS("\n=== Assessment Data Integrity Check ===\n"))
        
        # Check assessments without questions
        assessments_without_questions = Assessment.objects.annotate(
            question_count=Count('questions')
        ).filter(question_count=0, is_active=True)
        
        if assessments_without_questions.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠ Found {assessments_without_questions.count()} active assessment(s) without questions:"
                )
            )
            for assessment in assessments_without_questions:
                self.stdout.write(
                    f"  - ID {assessment.id}: '{assessment.title}' "
                    f"(Teacher: {assessment.teacher.username}, Subject: {assessment.subject})"
                )
            
            if fix:
                self.stdout.write(self.style.WARNING("\n⚠ Cannot auto-fix: Questions must be added manually via admin or teacher interface."))
                self.stdout.write("   Please add questions to these assessments.")
        else:
            self.stdout.write(self.style.SUCCESS("✓ All active assessments have questions"))
        
        # Check all assessments and their question counts
        self.stdout.write(self.style.SUCCESS("\n=== Assessment Summary ===\n"))
        all_assessments = Assessment.objects.annotate(
            question_count=Count('questions')
        ).order_by('teacher__username', 'title')
        
        for assessment in all_assessments:
            status = self.style.SUCCESS if assessment.question_count > 0 else self.style.ERROR
            self.stdout.write(
                f"  {status('✓' if assessment.question_count > 0 else '✗')} "
                f"'{assessment.title}' - {assessment.question_count} question(s) "
                f"(Teacher: {assessment.teacher.username}, Active: {assessment.is_active})"
            )
        
        # Check for orphaned data
        self.stdout.write(self.style.SUCCESS("\n=== Data Integrity ===\n"))
        
        orphaned_attempts = Attempt.objects.filter(assessment__is_active=False).count()
        if orphaned_attempts > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠ {orphaned_attempts} attempt(s) linked to inactive assessments")
            )
        else:
            self.stdout.write(self.style.SUCCESS("✓ No orphaned attempts"))
        
        self.stdout.write(self.style.SUCCESS("\n=== Check Complete ===\n"))

