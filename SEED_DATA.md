# Seed Data Script

This document describes how to use the seed data management command to populate the database with test data.

## Usage

### Basic Usage

Seed the database with default test data (2 teachers, 5 students, assessments with questions):

```bash
python manage.py seed_data
```

### Options

- `--clear`: Clear existing test data before seeding
- `--with-attempts`: Create test attempts and responses for students
- `--teachers N`: Number of teachers to create (default: 2)
- `--students N`: Number of students to create (default: 5)

### Examples

**Clear existing data and seed fresh:**
```bash
python manage.py seed_data --clear
```

**Seed with test attempts and responses:**
```bash
python manage.py seed_data --with-attempts
```

**Create custom number of users:**
```bash
python manage.py seed_data --teachers 3 --students 10
```

**Full example with all options:**
```bash
python manage.py seed_data --clear --with-attempts --teachers 2 --students 5
```

## What Gets Created

### Teachers
- Username format: `teacher1`, `teacher2`, etc.
- Password: `testpass123`
- Role: Teacher
- Staff access: Yes

### Students
- Username format: `student1`, `student2`, etc.
- Password: `testpass123`
- Role: Student
- Audio feedback: Enabled

### Assessments

Each teacher gets 4 assessments across different subjects:

1. **Introduction to Python Programming** (Computer Science)
   - 3 questions about Python basics

2. **World History: Ancient Civilizations** (History)
   - 2 questions about ancient civilizations

3. **Basic Mathematics: Algebra Fundamentals** (Mathematics)
   - 2 algebra problems

4. **English Literature: Shakespeare Analysis** (Literature)
   - 2 questions about Shakespeare

### Attempts (with `--with-attempts` flag)

- Creates attempts for first 3 students on first 2 assessments
- Includes sample responses with:
  - Transcriptions
  - Scores (75.50%)
  - Feedback text
  - WER values (12.50%)
  - AI metadata

## Login Credentials

After running the seed command, you'll see a summary of all created users with their credentials:

```
Teachers:
  Username: teacher1 | Password: testpass123
  Username: teacher2 | Password: testpass123

Students:
  Username: student1 | Password: testpass123
  Username: student2 | Password: testpass123
  ...
```

## Notes

- The script uses `get_or_create`, so running it multiple times won't create duplicates
- Use `--clear` to remove all test data (users starting with "teacher" or "student")
- All test data is clearly identifiable by username prefixes
- Assessments include realistic questions with expected answers and rubrics

## Development

To modify the seed data:

1. Edit `assessments/management/commands/seed_data.py`
2. Update the `assessment_templates` list to add/modify assessments
3. Adjust the `_create_attempts` method to change attempt/response data

