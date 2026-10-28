# persons/management/commands/import_students.py

import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from persons.models import Person, Student, Teacher
from django.utils import timezone


# Teacher mapping
TEACHER_MAPPING = {
    'CESAR': 'César',
    'ESTELLE': 'Estelle',
    'MATTHIEU': 'Matthieu',
    'NICOLAS': 'Nicolas',
    'OPHELIE': 'Ophélie',
}


# Status mapping: Airtable (French) → Django (English)
STATUS_MAPPING = {
    'actif': 'active',
    'ancien': 'former',
    'en pause': 'paused',
    'prospect': 'prospect',
    'perdu': 'lost',
}


class Command(BaseCommand):
    """
    Import students from students.csv file.
    
    Usage:
        python manage.py import_students
    
    Creates Person records (if they don't exist) and Student records.
    Teachers are matched by first name (e.g., "JULIE" in CSV → Teacher with first_name="Julie").
    """
    
    help = 'Import students from students.csv'
    CSV_PATH = os.path.join(settings.BASE_DIR, 'imports', 'students.csv')
    
    def handle(self, *args, **options):
        """
        Main entry point for the management command.
        """
        
        created_person_count = 0
        updated_person_count = 0
        created_student_count = 0
        skipped_count = 0
        
        with open(self.CSV_PATH, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # ─── Step 1: Get or create Person ─────────────────────────
                    airtable_id = row.get('Airtable Record ID', '').strip()
                    
                    # Handle use_tu: convert string to boolean
                    use_tu_value = row.get('use_tu', '').strip()
                    use_tu = use_tu_value.lower() == 'true'
                    
                    # Handle birth_date: parse string to date object
                    birth_date_str = row.get('date naissance', '').strip()
                    birth_date = self.parse_date(birth_date_str)
                    
                    # Handle enrollment_date
                    enrollment_date_str = row.get('date inscription', '').strip()
                    enrollment_date = self.parse_date(enrollment_date_str)
                    
                    # Handle end_date
                    end_date_str = row.get('quitte Opiano le', '').strip()
                    end_date = self.parse_date(end_date_str)
                    
                    # Get or create Person
                    person, person_created = Person.objects.get_or_create(
                        airtable_id=airtable_id,
                        defaults={
                            'title': row.get('titre', '').strip(),
                            'first_name': row.get('prénom', '').strip(),
                            'last_name': row.get('nom', '').strip(),
                            'address': row.get('adresse', '').strip(),
                            'postal_code': row.get('CP', '').strip(),
                            'city': row.get('lieu', '').strip(),
                            'phone': row.get('tél. portable', '').strip(),
                            'phone_2': row.get('tél. fixe', '').strip(),
                            'email': row.get('e-mail', '').strip(),
                            'about_me': row.get('remarques', '').strip(),
                            'greeting_formula': row.get('formule', '').strip(),
                            'use_tu': use_tu,
                            'birth_date': birth_date,
                        }
                    )
                    
                    if person_created:
                        created_person_count += 1
                        self.stdout.write(f'✓ Created Person: {person.last_name} {person.first_name}')
                    else:
                        updated_person_count += 1
                        # Update existing person's info
                        Person.objects.filter(airtable_id=airtable_id).update(
                            title=row.get('titre', '').strip(),
                            first_name=row.get('prénom', '').strip(),
                            last_name=row.get('nom', '').strip(),
                            # ... update other fields ...
                        )
                        self.stdout.write(f'~ Updated Person: {person.last_name} {person.first_name}')
                    
                    # ─── Step 2: Check if Student already exists ──────────────
                    student_exists = Student.objects.filter(person=person).exists()
                    
                    if student_exists:
                        self.stdout.write(f'  ⚠ Student already exists, skipping')
                        skipped_count += 1
                        continue
                    
                    # ─── Step 3: Map status (French → English) ────────────────
                    status_french = row.get('statut élève', '').strip().lower()
                    status = STATUS_MAPPING.get(status_french, 'prospect')
                    
                    # ─── Step 4: Lookup teacher by mapping ────────────────────
                    teacher_name_csv = row.get('profs', '').strip()

                    if teacher_name_csv:
                        # Look up the proper name from mapping
                        teacher_first_name = TEACHER_MAPPING.get(teacher_name_csv)
                        
                        if teacher_first_name:
                            try:
                                teacher = Teacher.objects.get(person__first_name=teacher_first_name)
                                self.stdout.write(f'  → Linked to teacher: {teacher.person.first_name}')
                            except Teacher.DoesNotExist:
                                self.stdout.write(f'  ⚠ Teacher not found: "{teacher_first_name}"')
                                teacher = None
                        else:
                            self.stdout.write(f'  ⚠ Unknown teacher: "{teacher_name_csv}"')
                            teacher = None
                    
                    # ─── Step 5: Create Student record ────────────────────────
                    student = Student.objects.create(
                        person=person,
                        status=status,
                        level=row.get('niveau', '').strip(),
                        styles=row.get('style', '').strip(),
                        enrollment_date=enrollment_date,
                        end_date=end_date,
                        teacher=teacher,  # Can be None
                    )
                    
                    created_student_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created Student'))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ Skipped row {row_num}: {str(e)}'))
                    skipped_count += 1
        
        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS(f'Import complete!'))
        self.stdout.write(f'  Persons created: {created_person_count}')
        self.stdout.write(f'  Persons updated: {updated_person_count}')
        self.stdout.write(f'  Students created: {created_student_count}')
        self.stdout.write(f'  Students skipped: {skipped_count}')
    
    def parse_date(self, date_string):
        """
        Parse date string from CSV to Python date object.
        
        Airtable exports dates as strings like "2024-01-15" or "15/01/2024".
        Returns None if empty or invalid.
        
        Args:
            date_string: String from CSV (e.g., "2024-01-15")
        
        Returns:
            date object or None
        """
        if not date_string:
            return None
        
        from datetime import datetime
        
        # Try different date formats
        formats = [
            '%Y-%m-%d',      # 2024-01-15
            '%d/%m/%Y',      # 15/01/2024
            '%d-%m-%Y',      # 15-01-2024
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt).date()
            except ValueError:
                continue
        
        # If no format works, return None
        return None