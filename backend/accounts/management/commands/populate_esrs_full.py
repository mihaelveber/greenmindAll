from django.core.management.base import BaseCommand
from accounts.models import ESRSCategory, ESRSStandard, ESRSDisclosure
from html.parser import HTMLParser
import re
import urllib.request


ESRS_SOURCE_URL = "https://xbrl.efrag.org/e-esrs/esrs-set1-2023.html"


class _ESRSTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks = []

    def handle_starttag(self, tag, attrs):
        if tag in {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4", "table"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in {"p", "li", "div", "tr", "table"}:
            self._chunks.append("\n")


    def handle_data(self, data):
        if data and data.strip():
            self._chunks.append(data)

    def get_text(self) -> str:
        return "".join(self._chunks)


def _fetch_esrs_html(url: str) -> str:
    print(f"Fetching {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _html_to_lines(html: str) -> list[str]:
    parser = _ESRSTextExtractor()
    parser.feed(html)
    raw_text = parser.get_text()
    
    lines = []
    # Replace non-breaking spaces and dashes
    raw_text = raw_text.replace("\u00a0", " ").replace("\u2013", "-").replace("\u2014", "-")
    
    for line in raw_text.splitlines():
        cleaned = re.sub(r"\s+", " ", line.strip())
        if cleaned:
            lines.append(cleaned)
    return lines


def _normalize_section_text(lines: list[str]) -> str:
    paragraphs = []
    current = ""
    # Matches: "1.", "53.", "(a)", "a)", "i.", "(i)", "AR 1."
    prefix_pattern = re.compile(r"^(\d+\.|AR \d+\.|\(?[a-z]\)|\(?[ivx]+\)\.?|[ivx]+\.)\s", re.IGNORECASE)

    for line in lines:
        if "Disclosure Requirement" in line:
            continue
            
        is_new_block = prefix_pattern.match(line)
        
        if is_new_block:
            if current:
                paragraphs.append(current.strip())
            current = line
        else:
            if current:
                current = f"{current} {line}".strip()
            else:
                current = line

    if current:
        paragraphs.append(current.strip())

    return "\n".join(paragraphs).strip()


def _extract_lettered_sections(section_text: str) -> dict[str, str]:
    """
    Extracts (a), (b) or a), b) items from text.
    """
    items = {}
    lines = section_text.splitlines()
    
    current_key = None
    buffer = []
    
    # Pattern for (a), (b), a), b)
    key_pattern = re.compile(r"^(\([a-z]\)|[a-z]\))\s+(.*)$", re.IGNORECASE)
    
    for line in lines:
        match = key_pattern.match(line.strip())
        if match:
            # Save previous
            if current_key:
                # Add text to previous key
                if buffer:
                     items[current_key] = "\n".join(buffer).strip()
            
            # Start new
            raw_key = match.group(1).replace("(", "").replace(")", "") # clean to "a"
            current_key = raw_key.lower()
            content = match.group(2)
            buffer = [content]
        else:
            if current_key:
                buffer.append(line.strip())
            # Note: Header text before first item is ignored in this dict return
            # but usually passed as main req text.
                
    if current_key and buffer:
        items[current_key] = "\n".join(buffer).strip()
        
    return items


def _extract_disclosure_sections(html: str) -> dict[str, str]:
    # Use the robust parsing from scrape_and_inspect.py
    lines = _html_to_lines(html)
    
    parsed_data = {}
    current_dr_code = None
    current_buffer = []
    
    # Matches "Disclosure Requirement E1-1" etc.
    dr_start_pattern = re.compile(r"^Disclosure Requirement\s+([A-Z0-9-]+)(\s+.*)?$", re.IGNORECASE)
    
    for i, line in enumerate(lines):
        match = dr_start_pattern.match(line)
        if match:
            # Save previous
            if current_dr_code and current_buffer:
                full_text = _normalize_section_text(current_buffer)
                parsed_data[current_dr_code] = full_text
            
            # Start new
            current_dr_code = match.group(1).upper()
            current_buffer = [] 
        else:
            if current_dr_code:
                current_buffer.append(line)
                
    # Save last
    if current_dr_code and current_buffer:
        parsed_data[current_dr_code] = _normalize_section_text(current_buffer)
        
    return parsed_data


def _get_standard_for_code(code: str) -> ESRSStandard | None:
    # Standard mapping logic
    # E.g. E1-1 -> E1. S1-1 -> S1.
    # BP-1 -> ESRS 2. GOV-1 -> ESRS 2.
    
    if '-' not in code:
        return None
    
    prefix = code.split('-')[0]
    
    if prefix in ['E1', 'E2', 'E3', 'E4', 'E5', 'S1', 'S2', 'S3', 'S4', 'G1']:
        return ESRSStandard.objects.filter(code=prefix).first()
    
    if prefix in ['BP', 'GOV', 'SBM', 'IRO', 'MDR']:
        return ESRSStandard.objects.filter(code='ESRS 2').first()
        
    return None

def _extract_esrs1_chapters(html: str) -> dict[str, str]:
    """
    ESRS 1 doesn't have 'Disclosure Requirement X-Y'. 
    It has numbered chapters like '1. Categories of standards...'.
    We will extract these as pseudo-requirements.
    """
    try:
        lines = _html_to_lines(html)
        
        # Locate ESRS 1 region
        start_idx = 0
        end_idx = len(lines)
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if "esrs 1" in line_lower and "general requirements" in line_lower:
                if start_idx == 0: start_idx = i
            if "esrs 2" in line_lower and "general disclosures" in line_lower:
                if i > start_idx + 10: # Ensure we don't catch TOC or early refs
                    end_idx = i
                    break
                
        esrs1_lines = lines[start_idx:end_idx]
        
        chapters = {
            "1": "Categories of standards",
            "2": "Qualitative characteristics of information",
            "3": "Double materiality as the basis for sustainability disclosures",
            "4": "Due diligence",
            "5": "Value chain",
            "6": "Time horizons",
            "7": "Preparation and presentation of sustainability information",
            "8": "Structure of sustainability statement",
            "9": "Linkages with other parts of corporate reporting",
            "10": "Transitional provisions"
        }
        
        sections = {}
        current_chapter = None
        buffer = []
        
        for line in esrs1_lines:
            found_chapter = None
            clean = line.strip()
            for num, title in chapters.items():
                # Check for "1. Title" or "1 Title" or just "Title" if it looks like a header
                if clean.startswith(f"{num}. {title}") or clean.startswith(f"{num} {title}"):
                    found_chapter = num
                    break
                # Strict check for just title if it's on its own line
                if clean == title:
                     found_chapter = num
                     break
            
            if found_chapter:
                if current_chapter and buffer:
                    sections[f"ESRS1-{current_chapter}"] = "\n".join(buffer).strip()
                current_chapter = found_chapter
                buffer = [line]
            else:
                if current_chapter:
                    buffer.append(line)
        
        if current_chapter and buffer:
            sections[f"ESRS1-{current_chapter}"] = "\n".join(buffer).strip()
            
        return sections
    except Exception as e:
        print(f"Error parsing ESRS 1: {e}")
        return {}


def _update_disclosures_from_source(url: str) -> int:
    html = _fetch_esrs_html(url)
    sections = _extract_disclosure_sections(html)
    
    # Add ESRS 1 Chapters
    esrs1_sections = _extract_esrs1_chapters(html)
    sections.update(esrs1_sections)
    
    updated = 0
    created = 0

    # First pass: Create/Update main disclosures
    for code, section_text in sections.items():
        standard = _get_standard_for_code(code)
        
        # Explicit mapping for ESRS 1 chapters
        if code.startswith("ESRS1-"):
             standard = ESRSStandard.objects.filter(code="ESRS 1").first()

        if not standard:
            continue

        disclosure, was_created = ESRSDisclosure.objects.update_or_create(
            code=code,
            defaults={
                'standard': standard,
                'name': f"Disclosure Requirement {code}", # Fallback name
                'description': section_text[:200] + "..." if len(section_text) > 200 else section_text,
                'requirement_text': section_text,
                'parent': None
            }
        )
        if was_created:
            created += 1
        else:
            updated += 1

    # Second pass: Sub-requirements (a), (b), etc.
    sub_code_pattern = re.compile(r"^\(([a-z])\)$") # Matches exactly (a), (b)
    
    for code, section_text in sections.items():
        parent_disclosure = ESRSDisclosure.objects.filter(code=code).first()
        if not parent_disclosure:
            continue
            
        lettered = _extract_lettered_sections(section_text)
        
        for suffix, text in lettered.items():
            sub_code = f"{code}-{suffix}" # E.g. E1-1-a
            # Or usually noted as E1-1(a) or just E1-1a. Let's use E1-1a for cleaner URLs/IDs if needed, or maintain hierarchy.
            # User request mentioned subrequirements.
            
            # Check if this sub-disclosure already exists or create it
            ESRSDisclosure.objects.update_or_create(
                code=sub_code,
                defaults={
                    'standard': parent_disclosure.standard,
                    'parent': parent_disclosure,
                    'name': f"Requirement {code} paragraph ({suffix})",
                    'description': text[:200] + "...",
                    'requirement_text': text,
                }
            )

    return updated + created


class Command(BaseCommand):
    help = 'Populate ESRS standards and disclosures in database with complete hierarchy from EFRAG source'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting complete ESRS population with live scraping...')
        
        # Clear existing data - WARNING: This deletes everything!
        self.stdout.write('Clearing existing ESRS data...')
        ESRSDisclosure.objects.all().delete()
        ESRSStandard.objects.all().delete()
        ESRSCategory.objects.all().delete()
        
        # 1. Create Categories
        cc_cat = ESRSCategory.objects.create(name='Cross-cutting', code='CC', description='General requirements', order=1)
        env_cat = ESRSCategory.objects.create(name='Environmental', code='E', description='Environmental matters', order=2)
        soc_cat = ESRSCategory.objects.create(name='Social', code='S', description='Social matters', order=3)
        gov_cat = ESRSCategory.objects.create(name='Governance', code='G', description='Governance matters', order=4)
        
        # 2. Create Standards Structure
        standards_map = [
            ('ESRS 1', 'General Requirements', cc_cat),
            ('ESRS 2', 'General Disclosures', cc_cat),
            ('E1', 'Climate Change', env_cat),
            ('E2', 'Pollution', env_cat),
            ('E3', 'Water and Marine Resources', env_cat),
            ('E4', 'Biodiversity and Ecosystems', env_cat),
            ('E5', 'Resource Use and Circular Economy', env_cat),
            ('S1', 'Own Workforce', soc_cat),
            ('S2', 'Workers in the Value Chain', soc_cat),
            ('S3', 'Affected Communities', soc_cat),
            ('S4', 'Consumers and End-users', soc_cat),
            ('G1', 'Business Conduct', gov_cat),
        ]
        
        for code, name, category in standards_map:
            ESRSStandard.objects.create(
                category=category,
                code=code,
                name=name,
                description=f'{name} Standard',
                order=0
            )
            self.stdout.write(f'Created standard: {code}')

        # 3. Scrape and Populate Disclosures
        self.stdout.write(f'Fetching and parsing data from {ESRS_SOURCE_URL}...')
        try:
            count = _update_disclosures_from_source(ESRS_SOURCE_URL)
            self.stdout.write(self.style.SUCCESS(f'Successfully populated/updated {count} disclosure elements from official source.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to scrape data: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

        self.stdout.write(self.style.SUCCESS('ESRS population complete.'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✓ Successfully populated ESRS database using official source!'))
        self.stdout.write(self.style.SUCCESS('='*60))
