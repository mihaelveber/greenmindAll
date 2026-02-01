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
        
        # E1-6: Gross Scopes 1, 2, 3 and Total GHG emissions
        e1_6 = ESRSDisclosure.objects.create(
            standard=e1, code='E1-6', parent=None,
            name='Gross Scopes 1, 2, 3 and Total GHG emissions',
            description='The undertaking shall disclose its gross GHG emissions in metric tonnes of CO2eq',
            requirement_text='Disclose Scope 1, Scope 2, and Scope 3 GHG emissions separately and in total',
            order=total_disclosures
        )
        total_disclosures += 1
        
        # E1-6 sub-disclosures
        e1_6_subs = [
            ('E1-6a', 'Scope 1 GHG emissions', 'The undertaking shall disclose its gross Scope 1 GHG emissions in metric tonnes of CO2 equivalent. Scope 1 emissions are direct GHG emissions that occur from sources that are owned or controlled by the undertaking, including: stationary combustion (boilers, furnaces, turbines), mobile combustion (vehicles, ships, aircraft), process emissions (chemical reactions, manufacturing), and fugitive emissions (leaks from refrigeration, air conditioning).'),
            ('E1-6b', 'Scope 2 GHG emissions', 'The undertaking shall disclose its gross Scope 2 GHG emissions in metric tonnes of CO2 equivalent. Scope 2 emissions are indirect emissions from the generation of purchased or acquired electricity, steam, heat, or cooling consumed by the undertaking. Disclose both location-based and market-based calculations where applicable.'),
            ('E1-6c', 'Scope 3 GHG emissions', 'The undertaking shall disclose its gross Scope 3 GHG emissions in metric tonnes of CO2 equivalent, broken down by the following categories where significant: purchased goods and services, capital goods, fuel and energy-related activities, upstream transportation and distribution, waste generated in operations, business travel, employee commuting, upstream leased assets, downstream transportation and distribution, processing of sold products, use of sold products, end-of-life treatment of sold products, downstream leased assets, franchises, and investments.'),
            ('E1-6d', 'Total GHG emissions', 'The undertaking shall disclose the total GHG emissions (Scope 1 + Scope 2 + Scope 3) in metric tonnes of CO2 equivalent. The undertaking shall separately disclose biogenic emissions of CO2 from the combustion or biodegradation of biomass.'),
            ('E1-6e', 'GHG emissions intensity', 'The undertaking shall disclose its GHG emissions intensity ratio: total GHG emissions (Scope 1, 2, and 3) per net revenue in metric tonnes of CO2 equivalent per million EUR. Alternative intensity ratios may be disclosed per: full-time equivalent employees, production volume, or other appropriate business-specific denominator.'),
        ]
        for code, name, req_text in e1_6_subs:
            ESRSDisclosure.objects.create(
                standard=e1, code=code, parent=e1_6,
                name=name, description=req_text,
                requirement_text=req_text, order=total_disclosures
            )
            total_disclosures += 1
        
        # E1-7: GHG removals and carbon credits
        e1_7 = ESRSDisclosure.objects.create(
            standard=e1, code='E1-7', parent=None,
            name='GHG removals and GHG mitigation projects financed through carbon credits',
            description='The undertaking shall disclose GHG removals and storage, and carbon credits',
            requirement_text='Disclose GHG removals, storage in own operations and carbon credits purchased',
            order=total_disclosures
        )
        total_disclosures += 1
        
        # E1-8: Internal carbon pricing
        e1_8 = ESRSDisclosure.objects.create(
            standard=e1, code='E1-8', parent=None,
            name='Internal carbon pricing',
            description='The undertaking shall disclose whether and how it applies internal carbon pricing schemes',
            requirement_text='Describe internal carbon pricing mechanisms and their application in decision-making',
            order=total_disclosures
        )
        total_disclosures += 1
        
        # E1-9: Anticipated financial effects from material physical and transition risks
        e1_9 = ESRSDisclosure.objects.create(
            standard=e1, code='E1-9', parent=None,
            name='Anticipated financial effects from material physical and transition risks',
            description='The undertaking shall disclose anticipated financial effects from material climate-related risks',
            requirement_text='Quantify financial effects of physical risks (extreme weather) and transition risks (policy changes, technology)',
            order=total_disclosures
        )
        total_disclosures += 1
        
        # E1-9 sub-disclosures
        e1_9_subs = [
            ('E1-9a', 'Physical risks - Anticipated financial effects', 'The undertaking shall disclose the anticipated financial effects from material physical climate risks, including: (a) acute physical risks from event-driven hazards (tropical cyclones, floods, droughts, wildfires, extreme precipitation, extreme heat); (b) chronic physical risks from longer-term shifts in climate patterns (temperature rise, sea level rise, water stress, biodiversity loss). Disclose potential financial impacts on: assets and operations (damage, impairment, write-offs), revenue (disruption, decreased demand), costs (increased operating costs, insurance premiums), and access to capital.'),
            ('E1-9b', 'Transition risks - Anticipated financial effects', 'The undertaking shall disclose the anticipated financial effects from material transition risks, including: (a) policy and legal risks (carbon pricing, emissions limits, litigation); (b) technology risks (substitution by lower-emission technology, unsuccessful investments in new technology); (c) market risks (changing customer behavior, uncertainty in market signals, increased cost of raw materials); (d) reputational risks (stakeholder concern, negative feedback). Disclose potential financial impacts on: assets (stranded assets, early retirement, impairment), revenue (decreased demand, obsolete products), costs (compliance costs, input cost increases), and access to capital.'),
        ]
        for code, name, req_text in e1_9_subs:
            ESRSDisclosure.objects.create(
                standard=e1, code=code, parent=e1_9,
                name=name, description=req_text,
                requirement_text=req_text, order=total_disclosures
            )
            total_disclosures += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created E1 Climate Change: {total_disclosures} disclosures'))
        
        # ===================
        # E2: POLLUTION
        # ===================
        e2 = ESRSStandard.objects.create(
            category=env_category,
            code='E2',
            name='Pollution',
            description='Pollution of air, water and soil',
            order=2
        )
        
        e2_disclosures = [
            ('E2-1', 'Policies related to pollution', 'Policies to prevent and control pollution of air, water and soil'),
            ('E2-2', 'Actions and resources related to pollution', 'Actions taken to prevent, control and eliminate pollution'),
            ('E2-3', 'Targets related to pollution', 'Targets for pollution prevention and reduction'),
            ('E2-4', 'Pollution of air, water and soil', 'Quantitative information on pollutants emitted'),
            ('E2-5', 'Substances of concern and substances of very high concern', 'Production, use and distribution of substances of concern'),
            ('E2-6', 'Anticipated financial effects from pollution-related impacts, risks and opportunities', 'Financial implications of pollution matters'),
        ]
        
        for idx, (code, name, description) in enumerate(e2_disclosures, start=1):
            ESRSDisclosure.objects.create(
                standard=e2, code=code, parent=None,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(e2_disclosures)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created E2 Pollution: {len(e2_disclosures)} disclosures'))
        
        # ===================
        # E3: WATER AND MARINE RESOURCES
        # ===================
        e3 = ESRSStandard.objects.create(
            category=env_category,
            code='E3',
            name='Water and Marine Resources',
            description='Water and marine resources',
            order=3
        )
        
        e3_disclosures = [
            ('E3-1', 'Policies related to water and marine resources', 'Policies for sustainable use and protection of water and marine resources'),
            ('E3-2', 'Actions and resources related to water and marine resources', 'Actions to protect water and marine resources'),
            ('E3-3', 'Targets related to water and marine resources', 'Targets for water consumption, marine protection'),
            ('E3-4', 'Water consumption', 'Total water consumption and water consumption in water-stressed areas'),
            ('E3-5', 'Anticipated financial effects from water and marine resources-related impacts, risks and opportunities', 'Financial implications of water matters'),
        ]
        
        for idx, (code, name, description) in enumerate(e3_disclosures, start=1):
            ESRSDisclosure.objects.create(
                standard=e3, code=code, parent=None,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(e3_disclosures)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created E3 Water: {len(e3_disclosures)} disclosures'))
        
        # ===================
        # E4: BIODIVERSITY AND ECOSYSTEMS
        # ===================
        e4 = ESRSStandard.objects.create(
            category=env_category,
            code='E4',
            name='Biodiversity and Ecosystems',
            description='Biodiversity and ecosystems',
            order=4
        )
        
        e4_disclosures = [
            ('E4-1', 'Policies related to biodiversity and ecosystems', 'Policies to protect biodiversity and ecosystems'),
            ('E4-2', 'Actions and resources related to biodiversity and ecosystems', 'Actions to avoid, reduce and remediate impacts on biodiversity'),
            ('E4-3', 'Targets related to biodiversity and ecosystems', 'Targets for biodiversity protection'),
            ('E4-4', 'Impact metrics related to biodiversity and ecosystems change', 'Metrics on changes in extent and condition of ecosystems'),
            ('E4-5', 'Impact metrics related to biodiversity and ecosystems', 'Metrics on species population impacts'),
            ('E4-6', 'Anticipated financial effects from biodiversity and ecosystems-related impacts, risks and opportunities', 'Financial implications of biodiversity matters'),
        ]
        
        for idx, (code, name, description) in enumerate(e4_disclosures, start=1):
            ESRSDisclosure.objects.create(
                standard=e4, code=code, parent=None,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(e4_disclosures)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created E4 Biodiversity: {len(e4_disclosures)} disclosures'))
        
        # ===================
        # E5: RESOURCE USE AND CIRCULAR ECONOMY
        # ===================
        e5 = ESRSStandard.objects.create(
            category=env_category,
            code='E5',
            name='Resource Use and Circular Economy',
            description='Resource use and circular economy',
            order=5
        )
        
        e5_disclosures = [
            ('E5-1', 'Policies related to resource use and circular economy', 'Policies to reduce resource consumption and implement circular economy'),
            ('E5-2', 'Actions and resources related to resource use and circular economy', 'Actions to implement circular economy principles'),
            ('E5-3', 'Targets related to resource use and circular economy', 'Targets for waste reduction and circular economy'),
            ('E5-4', 'Resource inflows', 'Resource use including materials, water and other resources'),
            ('E5-5', 'Resource outflows', 'Products, materials and waste flows'),
            ('E5-6', 'Anticipated financial effects from resource use and circular economy-related impacts, risks and opportunities', 'Financial implications of resource matters'),
        ]
        
        for idx, (code, name, description) in enumerate(e5_disclosures, start=1):
            ESRSDisclosure.objects.create(
                standard=e5, code=code, parent=None,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(e5_disclosures)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created E5 Resources: {len(e5_disclosures)} disclosures'))
        
        # ===================
        # S1: OWN WORKFORCE
        # ===================
        s1 = ESRSStandard.objects.create(
            category=social_category,
            code='S1',
            name='Own Workforce',
            description='Own workforce matters',
            order=1
        )
        
        s1_disclosures = [
            ('S1-1', 'Policies related to own workforce', 'Policies related to own workforce management'),
            ('S1-2', 'Processes for engaging with own workforce', 'Engagement processes with employees and their representatives'),
            ('S1-3', 'Processes to remediate negative impacts and channels for own workforce to raise concerns', 'Remediation processes and grievance mechanisms'),
            ('S1-4', 'Taking action on material impacts on own workforce', 'Actions and action plans to address workforce impacts'),
            ('S1-5', 'Targets related to managing material negative impacts, advancing positive impacts', 'Targets for workforce matters'),
            ('S1-6', 'Characteristics of the undertaking\'s employees', 'Workforce composition and characteristics'),
            ('S1-7', 'Characteristics of non-employee workers', 'Characteristics of non-employee workers in own workforce'),
            ('S1-8', 'Collective bargaining coverage and social dialogue', 'Collective bargaining and social dialogue'),
            ('S1-9', 'Diversity metrics', 'Gender and other diversity metrics'),
            ('S1-10', 'Adequate wages', 'Information on adequate wages'),
            ('S1-11', 'Social protection', 'Social protection coverage'),
            ('S1-12', 'Persons with disabilities', 'Inclusion of persons with disabilities'),
            ('S1-13', 'Training and skills development metrics', 'Training provided to employees'),
            ('S1-14', 'Health and safety metrics', 'Work-related incidents, injuries and ill health'),
            ('S1-15', 'Work-life balance metrics', 'Work-life balance arrangements'),
            ('S1-16', 'Remuneration metrics (pay gap and total remuneration)', 'Gender pay gap and remuneration'),
            ('S1-17', 'Incidents, complaints and severe human rights impacts', 'Human rights incidents and complaints'),
        ]
        
        for idx, (code, name, description) in enumerate(s1_disclosures, start=1):
            ESRSDisclosure.objects.create(
                standard=s1, code=code, parent=None,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(s1_disclosures)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created S1 Own Workforce: {len(s1_disclosures)} disclosures'))
        
        # ===================
        # S2: WORKERS IN THE VALUE CHAIN
        # ===================
        s2 = ESRSStandard.objects.create(
            category=social_category,
            code='S2',
            name='Workers in the Value Chain',
            description='Workers in the value chain',
            order=2
        )
        
        s2_disclosures = [
            ('S2-1', 'Policies related to value chain workers', 'Policies related to workers in the value chain'),
            ('S2-2', 'Processes for engaging with value chain workers', 'Engagement with value chain workers'),
            ('S2-3', 'Processes to remediate negative impacts', 'Remediation processes for value chain impacts'),
            ('S2-4', 'Taking action on material impacts on value chain workers', 'Actions to address value chain worker impacts'),
            ('S2-5', 'Targets related to managing material negative impacts', 'Targets for value chain worker matters'),
        ]
        
        for idx, (code, name, description) in enumerate(s2_disclosures, start=1):
            ESRSDisclosure.objects.create(
                standard=s2, code=code, parent=None,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(s2_disclosures)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created S2 Value Chain Workers: {len(s2_disclosures)} disclosures'))
        
        # ===================
        # S3: AFFECTED COMMUNITIES
        # ===================
        s3 = ESRSStandard.objects.create(
            category=social_category,
            code='S3',
            name='Affected Communities',
            description='Affected communities',
            order=3
        )
        
        s3_disclosures = [
            ('S3-1', 'Policies related to affected communities', 'Policies related to affected communities'),
            ('S3-2', 'Processes for engaging with affected communities', 'Engagement with affected communities'),
            ('S3-3', 'Processes to remediate negative impacts', 'Remediation for community impacts'),
            ('S3-4', 'Taking action on material impacts on affected communities', 'Actions to address community impacts'),
            ('S3-5', 'Targets related to managing material negative impacts', 'Targets for community matters'),
        ]
        
        for idx, (code, name, description) in enumerate(s3_disclosures, start=1):
            ESRSDisclosure.objects.create(
                standard=s3, code=code, parent=None,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(s3_disclosures)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created S3 Affected Communities: {len(s3_disclosures)} disclosures'))
        
        # ===================
        # S4: CONSUMERS AND END-USERS
        # ===================
        s4 = ESRSStandard.objects.create(
            category=social_category,
            code='S4',
            name='Consumers and End-Users',
            description='Consumers and end-users',
            order=4
        )
        
        s4_disclosures = [
            ('S4-1', 'Policies related to consumers and end-users', 'Policies related to consumers and end-users'),
            ('S4-2', 'Processes for engaging with consumers and end-users', 'Engagement with consumers and end-users'),
            ('S4-3', 'Processes to remediate negative impacts', 'Remediation for consumer impacts'),
            ('S4-4', 'Taking action on material impacts on consumers and end-users', 'Actions to address consumer impacts'),
            ('S4-5', 'Targets related to managing material negative impacts', 'Targets for consumer matters'),
        ]
        
        for idx, (code, name, description) in enumerate(s4_disclosures, start=1):
            ESRSDisclosure.objects.create(
                standard=s4, code=code, parent=None,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(s4_disclosures)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created S4 Consumers: {len(s4_disclosures)} disclosures'))
        
        # ===================
        # G1: BUSINESS CONDUCT
        # ===================
        g1 = ESRSStandard.objects.create(
            category=gov_category,
            code='G1',
            name='Business Conduct',
            description='Business conduct',
            order=1
        )
        
        g1_disclosures = [
            ('G1-1', 'Business conduct policies and corporate culture', 'Policies and culture regarding business conduct'),
            ('G1-2', 'Management of relationships with suppliers', 'Policies and practices for supplier relationships'),
            ('G1-3', 'Prevention and detection of corruption and bribery', 'Anti-corruption and anti-bribery measures'),
            ('G1-4', 'Confirmed incidents of corruption or bribery', 'Incidents of corruption or bribery'),
            ('G1-5', 'Political influence and lobbying activities', 'Political engagement and lobbying'),
            ('G1-6', 'Payment practices', 'Payment terms and practices'),
        ]
        
        for idx, (code, name, description) in enumerate(g1_disclosures, start=1):
            ESRSDisclosure.objects.create(
                standard=g1, code=code, parent=None,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(g1_disclosures)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created G1 Business Conduct: {len(g1_disclosures)} disclosures'))
        
        # ===================
        # ESRS 1 & 2 (Cross-cutting)
        # ===================
        esrs1 = ESRSStandard.objects.create(
            category=cc_category,
            code='ESRS 1',
            name='General Requirements',
            description='General requirements for disclosure of sustainability information',
            order=1
        )
        
        esrs1_disclosures = [
            ('ESRS1-1', 'Double materiality assessment process', 'Process to identify material impacts, risks and opportunities'),
            ('ESRS1-2', 'Disclosure requirements covered by the undertaking', 'List of material sustainability matters'),
            ('ESRS1-3', 'Material sustainability matters', 'Description of material matters'),
        ]
        
        for idx, (code, name, description) in enumerate(esrs1_disclosures, start=1):
            ESRSDisclosure.objects.create(
                standard=esrs1, code=code, parent=None,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(esrs1_disclosures)
        
        esrs2 = ESRSStandard.objects.create(
            category=cc_category,
            code='ESRS 2',
            name='General Disclosures',
            description='General disclosures about governance, strategy and business model',
            order=2
        )
        
        esrs2_disclosures = [
            ('GOV-1', 'The role of administrative, management and supervisory bodies', 'Governance bodies role in sustainability'),
            ('GOV-2', 'Information provided to administrative, management and supervisory bodies', 'Sustainability information to governance'),
            ('GOV-3', 'Integration of sustainability-related performance in incentive schemes', 'Sustainability in compensation'),
        ]
        
        for idx, (code, name, description) in enumerate(esrs2_disclosures, start=1):
            ESRSDisclosure.objects.create(
                standard=esrs2, code=code, parent=None,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(esrs2_disclosures)
        
        # GOV-4: Statement on due diligence (with sub-disclosures)
        gov4 = ESRSDisclosure.objects.create(
            standard=esrs2, code='GOV-4', parent=None,
            name='Statement on due diligence',
            description='Due diligence process statement',
            requirement_text='Statement describing the due diligence process',
            order=total_disclosures + 1
        )
        total_disclosures += 1
        
        gov4_subs = [
            ('GOV-4a', 'Due diligence policy', 'The undertaking shall describe its due diligence policy as embedded in the overall management system and governance structure, including: how the policy commits the undertaking to respect human rights, environmental protection and good governance; how the policy is approved at the highest level and applies to own operations, products, services and business relationships; and how it addresses the six due diligence steps (embed, identify and assess, prevent and mitigate, bring to an end, track and measure, communicate).'),
            ('GOV-4b', 'Due diligence process description', 'The undertaking shall describe how due diligence is conducted across own operations and value chain, including: methodologies and assumptions used to identify and prioritize material impacts, risks and opportunities; how the undertaking assesses severity and likelihood; how frequently assessments are performed; which operations and business relationships are covered; and how the undertaking engages with affected stakeholders and rights holders.'),
            ('GOV-4c', 'Principal adverse impacts identification', 'The undertaking shall disclose how it identifies its principal actual and potential adverse impacts on people and the environment, including: the most severe impacts identified through impact assessments; geographic areas or value chain segments where principal adverse impacts occur or may occur; affected stakeholder groups (workers, communities, consumers); and how impacts are prioritized based on severity (scale, scope, irremediable character) and likelihood.'),
            ('GOV-4d', 'Actions to prevent, mitigate and remediate adverse impacts', 'The undertaking shall describe measures taken to address principal adverse impacts, including: actions to prevent potential adverse impacts before they occur; actions to mitigate actual adverse impacts and reduce their severity; actions to bring to an end actual adverse impacts; grievance and remedy mechanisms available to affected stakeholders; and examples of remediation provided or contributed to in the reporting period.'),
        ]
        
        for idx, (code, name, description) in enumerate(gov4_subs, start=1):
            ESRSDisclosure.objects.create(
                standard=esrs2, code=code, parent=gov4,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(gov4_subs)
        
        # GOV-5: Risk management and internal controls (with sub-disclosures)
        gov5 = ESRSDisclosure.objects.create(
            standard=esrs2, code='GOV-5', parent=None,
            name='Risk management and internal controls over sustainability reporting',
            description='Controls over sustainability reporting',
            requirement_text='Description of risk management and internal controls',
            order=total_disclosures + 1
        )
        total_disclosures += 1
        
        gov5_subs = [
            ('GOV-5a', 'Risk assessment process for sustainability reporting', 'The undertaking shall describe its risk assessment process specific to sustainability reporting, including: how it identifies risks related to the quality of reported sustainability information (completeness, accuracy, balance, comparability); how it assesses risks of material misstatement (intentional or unintentional); procedures for identifying changes in the undertaking that may affect sustainability reporting; and frequency and scope of sustainability reporting risk assessments.'),
            ('GOV-5b', 'Internal control framework over sustainability reporting', 'The undertaking shall describe its internal control framework and key components for sustainability reporting, including: control environment (tone at top, ethical values, organizational structure, competence of personnel); information systems and processes for capturing sustainability data; control activities (preventive and detective controls, authorization procedures, data validation); and monitoring activities (ongoing evaluations, separate evaluations, internal audit involvement).'),
            ('GOV-5c', 'Integration with enterprise risk management', 'The undertaking shall describe how sustainability-related risks and opportunities are integrated into its overall enterprise risk management (ERM) system, including: governance structure for risk management and how sustainability risks are incorporated; risk identification, assessment and prioritization processes that include sustainability matters; how material sustainability risks inform strategic planning and business decisions; and alignment between financial risk management and sustainability risk management processes.'),
            ('GOV-5d', 'Key controls and procedures for sustainability data', 'The undertaking shall describe key internal controls and procedures over the collection, processing and reporting of sustainability information, including: data collection and measurement procedures (methodologies, tools, systems); data validation and reconciliation procedures; roles and responsibilities for data quality and controls; IT systems and controls for sustainability data management; and review and approval procedures before publication of sustainability information.'),
        ]
        
        for idx, (code, name, description) in enumerate(gov5_subs, start=1):
            ESRSDisclosure.objects.create(
                standard=esrs2, code=code, parent=gov5,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(gov5_subs)
        
        # Other ESRS 2 disclosures
        other_esrs2 = [
            ('SBM-1', 'Strategy, business model and value chain', 'Description of strategy and business model'),
            ('SBM-2', 'Interests and views of stakeholders', 'Stakeholder engagement'),
            ('SBM-3', 'Material impacts, risks and opportunities and their interaction with strategy', 'Material matters and strategy'),
            ('IRO-1', 'Description of the processes to identify and assess material impacts, risks and opportunities', 'Materiality assessment process'),
            ('IRO-2', 'Disclosure Requirements in ESRS covered by the undertaking sustainability statement', 'Coverage of ESRS requirements'),
        ]
        
        for idx, (code, name, description) in enumerate(other_esrs2, start=1):
            ESRSDisclosure.objects.create(
                standard=esrs2, code=code, parent=None,
                name=name, description=description,
                requirement_text=description, order=total_disclosures + idx
            )
        total_disclosures += len(other_esrs2)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created ESRS 1 & 2: {len(esrs1_disclosures) + len(esrs2_disclosures)} disclosures'))

        # Update requirement text from official ESRS source
        try:
            self.stdout.write('Updating requirement text from official ESRS source...')
            updated = _update_disclosures_from_source(ESRS_SOURCE_URL)
            self.stdout.write(self.style.SUCCESS(f'✓ Updated {updated} disclosures from source'))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f'⚠ ESRS source update failed: {exc}'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✓ Successfully populated ESRS database!'))
        self.stdout.write(self.style.SUCCESS(f'  - Categories: 4'))
        self.stdout.write(self.style.SUCCESS(f'  - Standards: 12'))
        self.stdout.write(self.style.SUCCESS(f'  - Total Disclosures (including sub-disclosures): {total_disclosures}'))
        self.stdout.write(self.style.SUCCESS('='*60))
