# persons/management/commands/import_others.py

import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from persons.models import Person


class Command(BaseCommand):
    """
    Import persons from others.csv file.
    
    Usage:
        python manage.py import_others
    
    The CSV file path is hardcoded in this command.
    Each row creates one Person record in the database.
    """
    
    # Django displays this text when running: python manage.py help import_others
    help = 'Import persons from others.csv'
    
    # Hardcoded path to your CSV file
    # Update this path to match where you saved others.csv
    CSV_PATH = os.path.join(settings.BASE_DIR, 'imports', 'others.csv')
    
    def handle(self, *args, **options):
        """
        Main entry point for the management command.
        
        This method is called when you run: python manage.py import_others
        
        Args:
            *args: Positional arguments (none for this command)
            **options: Named arguments (none for this command)
        """
        
        # Counter for feedback
        created_count = 0
        skipped_count = 0
        
        # Open the CSV file
        with open(self.CSV_PATH, 'r', encoding='utf-8') as csv_file:
            # Create a DictReader - reads each row as a dictionary
            # Keys are the CSV column headers
            reader = csv.DictReader(csv_file)
            
            # Process each row
            for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is headers
                try:
                    # ─── Map CSV columns to Person fields ─────────────────────
                    # Note: CSV column names must match exactly (case-sensitive)
                    
                    # Handle use_tu: CSV has "False" as string, convert to boolean
                    use_tu_value = row.get('use_tu', '').strip()
                    use_tu = use_tu_value.lower() == 'true'
                    
                    # Create the Person record
                    person = Person.objects.create(
                        title=row.get('titre', '').strip(),
                        first_name=row.get('prénom', '').strip(),
                        last_name=row.get('nom', '').strip(),
                        address=row.get('adresse', '').strip(),
                        postal_code=row.get('CP', '').strip(),
                        city=row.get('lieu', '').strip(),
                        phone=row.get('tél. portable', '').strip(),
                        phone_2=row.get('tél. fixe', '').strip(),
                        email=row.get('e-mail', '').strip(),
                        about_me=row.get('remarques', '').strip(),
                        greeting_formula=row.get('formule', '').strip(),
                        use_tu=use_tu,
                        airtable_id=row.get('Airtable Record ID', '').strip(),
                    )
                    
                    # Success feedback
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created: {person.last_name} {person.first_name}')
                    )
                    created_count += 1
                    
                except Exception as e:
                    # Error handling - skip this row, continue with next
                    self.stdout.write(
                        self.style.ERROR(f'✗ Skipped row {row_num}: {str(e)}')
                    )
                    skipped_count += 1
        
        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS(f'Import complete!'))
        self.stdout.write(f'  Created: {created_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')