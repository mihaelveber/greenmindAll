"""
Management command to cleanup duplicate document evidence links.
After migration to OneToOneField, this removes old duplicate links.
"""
from django.core.management.base import BaseCommand
from accounts.models import DocumentEvidence, Document
from django.db.models import Count


class Command(BaseCommand):
    help = 'Cleanup duplicate document evidence links (keep most recent)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🔍 Checking for duplicate document links...'))
        
        # Find documents that have multiple evidence links
        duplicates = Document.objects.annotate(
            evidence_count=Count('esrs_evidence')
        ).filter(evidence_count__gt=1)
        
        if not duplicates.exists():
            self.stdout.write(self.style.SUCCESS('✓ No duplicate document links found!'))
            return
        
        self.stdout.write(self.style.WARNING(f'Found {duplicates.count()} documents with multiple links'))
        
        removed_count = 0
        for document in duplicates:
            evidence_links = DocumentEvidence.objects.filter(document=document).order_by('-linked_at')
            
            # Keep the most recent one
            keep = evidence_links.first()
            to_remove = evidence_links.exclude(id=keep.id)
            
            if to_remove.exists():
                count = to_remove.count()
                removed_count += count
                
                self.stdout.write(
                    f'  📄 {document.file_name}: '
                    f'Keeping link to {keep.disclosure.code}, '
                    f'removing {count} old link(s)'
                )
                
                to_remove.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Cleanup complete! Removed {removed_count} duplicate links.'
            )
        )
