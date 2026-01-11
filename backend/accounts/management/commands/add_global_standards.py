"""
Management command to add top 5 global green/ISO standards to database
"""
from django.core.management.base import BaseCommand
from accounts.models import ESRSStandard, ESRSCategory


class Command(BaseCommand):
    help = 'Add top 5 global green/ISO standards (GRI, ISO 14001, CDP, ISO 50001, TCFD) to database'

    def handle(self, *args, **options):
        standards_data = [
            {
                'code': 'GRI',
                'name': 'GRI Standards',
                'description': 'Global Reporting Initiative - World\'s most widely used sustainability reporting framework. Used by 22,700+ companies for environmental, social, and economic impact reporting.',
                'type': 'sustainability_reporting',
                'website': 'https://www.globalreporting.org'
            },
            {
                'code': 'ISO-14001',
                'name': 'ISO 14001:2015',
                'description': 'Environmental Management Systems - Requirements with guidance for use. 500,000+ certifications worldwide. Helps organizations improve environmental performance.',
                'type': 'iso_environmental',
                'website': 'https://www.iso.org/iso-14001-environmental-management.html'
            },
            {
                'code': 'CDP',
                'name': 'CDP (Carbon Disclosure Project)',
                'description': 'Environmental disclosure system for climate, water, and forests. 25+ years of operation. Used by companies representing 2/3 of global market capitalization.',
                'type': 'disclosure_framework',
                'website': 'https://www.cdp.net'
            },
            {
                'code': 'ISO-50001',
                'name': 'ISO 50001:2018',
                'description': 'Energy Management Systems - Requirements with guidance for use. Helps organizations improve energy efficiency, reduce costs, and meet climate targets.',
                'type': 'iso_energy',
                'website': 'https://www.iso.org/standard/60857.html'
            },
            {
                'code': 'TCFD',
                'name': 'TCFD (Task Force on Climate-related Financial Disclosures)',
                'description': 'Climate-related financial risk disclosure framework. Endorsed by G20. Links climate impacts to financial performance. Becoming regulatory requirement worldwide.',
                'type': 'financial_disclosure',
                'website': 'https://www.fsb-tcfd.org'
            }
        ]

        # Create a category for global standards if it doesn't exist
        global_category, created = ESRSCategory.objects.get_or_create(
            code='GLOBAL',
            defaults={
                'name': 'Global Standards',
                'description': 'International sustainability, environmental, and quality standards (GRI, ISO, CDP, TCFD)'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: {global_category.name}'))

        created_count = 0
        updated_count = 0

        for std_data in standards_data:
            code = std_data['code']
            
            # Check if standard already exists
            standard, created = ESRSStandard.objects.get_or_create(
                code=code,
                defaults={
                    'name': std_data['name'],
                    'description': std_data['description'],
                    'category': global_category
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Created: {standard.code} - {standard.name}'))
            else:
                # Update existing standard
                standard.name = std_data['name']
                standard.description = std_data['description']
                standard.category = global_category
                standard.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'⚠️  Updated: {standard.code} - {standard.name}'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ Done! Created: {created_count}, Updated: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total global standards in database: {ESRSStandard.objects.filter(category__code="GLOBAL").count()}'))
