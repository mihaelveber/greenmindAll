from django.core.management.base import BaseCommand
from accounts.models import ESRSDisclosure
import openai
import os
import time

class Command(BaseCommand):
    help = 'Generate detailed ESRS requirement texts using AI for all disclosures'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating detailed ESRS requirement texts with AI...')
        
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        
        # Get all disclosures that need better requirement_text
        disclosures = ESRSDisclosure.objects.filter(parent_id__isnull=True).order_by('standard__code', 'code')
        
        total = disclosures.count()
        self.stdout.write(f'Found {total} parent disclosures to enhance')
        
        for idx, disclosure in enumerate(disclosures, 1):
            # Skip if already has long text (> 200 chars)
            if len(disclosure.requirement_text) > 200:
                self.stdout.write(f'[{idx}/{total}] ✓ {disclosure.code} already has detailed text')
                continue
            
            self.stdout.write(f'[{idx}/{total}] Generating for {disclosure.code}: {disclosure.name}...')
            
            try:
                prompt = f"""You are an ESRS (European Sustainability Reporting Standards) expert. Generate a detailed, professional requirement text for this ESRS disclosure requirement.

Standard: {disclosure.standard.code} - {disclosure.standard.name}
Disclosure Code: {disclosure.code}
Disclosure Name: {disclosure.name}
Current Description: {disclosure.description}

Generate a comprehensive requirement text (250-400 words) that:
1. Clearly states what the undertaking SHALL disclose
2. Lists specific information that must be included
3. Uses professional ESRS language and terminology
4. Is actionable and specific
5. Follows ESRS reporting format

Requirement Text:"""

                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an ESRS compliance expert who writes detailed, professional disclosure requirements."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=600
                )
                
                generated_text = response.choices[0].message.content.strip()
                
                # Update disclosure
                disclosure.requirement_text = generated_text
                disclosure.save()
                
                self.stdout.write(self.style.SUCCESS(f'  ✓ Generated {len(generated_text)} chars'))
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
                continue
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Completed! Enhanced {total} disclosures'))
