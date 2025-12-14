from django.core.management.base import BaseCommand
from accounts.models import ESRSCategory, ESRSStandard, ESRSDisclosure


class Command(BaseCommand):
    help = 'Populate ESRS standards and disclosures in database with full hierarchy'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting ESRS population with sub-disclosures...')
        
        # Clear existing data
        ESRSDisclosure.objects.all().delete()
        ESRSStandard.objects.all().delete()
        ESRSCategory.objects.all().delete()
        
        # Create Categories
        cc_category = ESRSCategory.objects.create(
            name='Cross-cutting',
            code='CC',
            description='Cross-cutting standards applicable to all companies',
            order=1
        )
        
        env_category = ESRSCategory.objects.create(
            name='Environmental',
            code='E',
            description='Environmental sustainability matters',
            order=2
        )
        
        social_category = ESRSCategory.objects.create(
            name='Social',
            code='S',
            description='Social sustainability matters',
            order=3
        )
        
        gov_category = ESRSCategory.objects.create(
            name='Governance',
            code='G',
            description='Governance matters',
            order=4
        )
        
        self.stdout.write(self.style.SUCCESS('✓ Created categories'))
        
        total_disclosures = 0
        
        # ESRS 1: General Requirements
        esrs1 = ESRSStandard.objects.create(
            category=cc_category,
            code='ESRS 1',
            name='General Requirements',
            description='General requirements for disclosure of sustainability information',
            order=1
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard=esrs1, code='ESRS 1-1', name='Double materiality assessment', 
                          description='Process to identify material impacts, risks and opportunities',
                          requirement_text='Describe the process to identify and assess material impacts, risks and opportunities', order=1),
            ESRSDisclosure(standard=esrs1, code='ESRS 1-2', name='Due diligence', 
                          description='Due diligence process implemented',
                          requirement_text='Describe the due diligence process with respect to sustainability matters', order=2),
            ESRSDisclosure(standard=esrs1, code='ESRS 1-3', name='Value chain', 
                          description='Value chain disclosure',
                          requirement_text='Describe the undertaking\'s value chain and the approach to value chain disclosures', order=3),
        ])
        
        # ESRS 2: General Disclosures
        esrs2 = ESRSStandard.objects.create(
            category=cc_category,
            code='ESRS 2',
            name='General Disclosures',
            description='General disclosures about governance, strategy and business model',
            order=2
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard=esrs2, code='GOV-1', name='Role of governance bodies', 
                          description='Role of administrative, management and supervisory bodies',
                          requirement_text='Describe the role of the administrative, management and supervisory bodies', order=1),
            ESRSDisclosure(standard=esrs2, code='SBM-1', name='Strategy and business model', 
                          description='Strategy, business model and value chain',
                          requirement_text='Describe the undertaking\'s strategy and business model', order=2),
            ESRSDisclosure(standard=esrs2, code='SBM-2', name='Interests of stakeholders', 
                          description='Interests and views of stakeholders',
                          requirement_text='Describe how the interests and views of stakeholders are taken into account', order=3),
            ESRSDisclosure(standard=esrs2, code='IRO-1', name='Material impacts, risks and opportunities', 
                          description='Description of processes to identify material matters',
                          requirement_text='Describe the processes to identify and assess material impacts, risks and opportunities', order=4),
        ])
        
        # E1: Climate Change
        e1 = ESRSStandard.objects.create(
            category=env_category,
            code='E1',
            name='Climate Change',
            description='Climate change mitigation and adaptation',
            order=1
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard=e1, code='E1-1', name='Transition plan for climate change mitigation', 
                          description='Transition plan to reach net-zero emissions',
                          requirement_text='Describe the transition plan for climate change mitigation including GHG emissions reduction targets', order=1),
            ESRSDisclosure(standard=e1, code='E1-2', name='Policies related to climate change', 
                          description='Policies implemented to manage climate change',
                          requirement_text='Describe the policies implemented to manage climate change mitigation and adaptation', order=2),
            ESRSDisclosure(standard=e1, code='E1-3', name='Actions and resources', 
                          description='Actions taken and resources allocated',
                          requirement_text='Describe key actions taken and planned, and resources allocated to climate change', order=3),
            ESRSDisclosure(standard=e1, code='E1-4', name='Targets related to climate change', 
                          description='Targets set for climate change mitigation',
                          requirement_text='Disclose measurable, outcome-oriented and time-bound targets for climate change', order=4),
            ESRSDisclosure(standard=e1, code='E1-5', name='Energy consumption and mix', 
                          description='Total energy consumption by source',
                          requirement_text='Disclose total energy consumption, energy intensity and share of renewable energy', order=5),
            ESRSDisclosure(standard=e1, code='E1-6', name='Gross Scopes 1, 2, 3 and Total GHG emissions', 
                          description='Greenhouse gas emissions by scope',
                          requirement_text='Disclose Scope 1, Scope 2 and Scope 3 GHG emissions in tonnes of CO2 equivalent', order=6),
            ESRSDisclosure(standard=e1, code='E1-7', name='GHG removals and carbon credits', 
                          description='GHG removals and carbon credits in value chain',
                          requirement_text='Disclose GHG removals and carbon credits from own operations and value chain', order=7),
            ESRSDisclosure(standard=e1, code='E1-8', name='Internal carbon pricing', 
                          description='Internal price on GHG emissions',
                          requirement_text='Disclose whether and how internal carbon pricing schemes are applied', order=8),
            ESRSDisclosure(standard=e1, code='E1-9', name='Anticipated financial effects', 
                          description='Financial effects from climate-related risks and opportunities',
                          requirement_text='Disclose anticipated financial effects from material climate-related risks and opportunities', order=9),
        ])
        
        # E2: Pollution
        e2 = ESRSStandard.objects.create(
            category=env_category,
            code='E2',
            name='Pollution',
            description='Pollution of air, water and soil',
            order=2
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard=e2, code='E2-1', name='Policies related to pollution', 
                          description='Policies to prevent and control pollution',
                          requirement_text='Describe policies to prevent, control and reduce pollution', order=1),
            ESRSDisclosure(standard=e2, code='E2-2', name='Actions and resources', 
                          description='Actions taken and resources to prevent pollution',
                          requirement_text='Describe key actions and resources allocated to pollution prevention', order=2),
            ESRSDisclosure(standard=e2, code='E2-3', name='Targets related to pollution', 
                          description='Targets to prevent and reduce pollution',
                          requirement_text='Disclose targets related to pollution prevention and reduction', order=3),
            ESRSDisclosure(standard=e2, code='E2-4', name='Pollution of air, water and soil', 
                          description='Pollutants emitted to air, water and soil',
                          requirement_text='Disclose pollutants emitted and their impacts', order=4),
            ESRSDisclosure(standard=e2, code='E2-5', name='Substances of concern and substances of very high concern', 
                          description='Production, use, distribution of substances of concern',
                          requirement_text='Disclose substances of concern and very high concern produced, used or distributed', order=5),
            ESRSDisclosure(standard=e2, code='E2-6', name='Anticipated financial effects', 
                          description='Financial effects from pollution-related impacts',
                          requirement_text='Disclose anticipated financial effects from pollution-related risks and opportunities', order=6),
        ])
        
        # E3: Water and Marine Resources
        e3 = ESRSStandard.objects.create(
            category=env_category,
            code='E3',
            name='Water and Marine Resources',
            description='Water consumption and marine resource use',
            order=3
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard=e3, code='E3-1', name='Policies related to water and marine resources', 
                          description='Policies to manage water and marine resources',
                          requirement_text='Describe policies to manage water and marine resources sustainably', order=1),
            ESRSDisclosure(standard=e3, code='E3-2', name='Actions and resources', 
                          description='Actions taken for water and marine resources',
                          requirement_text='Describe key actions and resources for water and marine resources', order=2),
            ESRSDisclosure(standard=e3, code='E3-3', name='Targets related to water and marine resources', 
                          description='Targets for water consumption and marine resources',
                          requirement_text='Disclose targets related to water and marine resources', order=3),
            ESRSDisclosure(standard=e3, code='E3-4', name='Water consumption', 
                          description='Total water consumption by source',
                          requirement_text='Disclose total water consumption and water intensity', order=4),
            ESRSDisclosure(standard=e3, code='E3-5', name='Anticipated financial effects', 
                          description='Financial effects from water and marine-related risks',
                          requirement_text='Disclose anticipated financial effects from water and marine-related risks', order=5),
        ])
        
        # E4: Biodiversity and Ecosystems
        e4 = ESRSStandard.objects.create(
            category=env_category,
            code='E4',
            name='Biodiversity and Ecosystems',
            description='Impact on biodiversity and ecosystems',
            order=4
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard=e4, code='E4-1', name='Transition plan on biodiversity and ecosystems', 
                          description='Plan to address biodiversity impacts',
                          requirement_text='Describe transition plan related to biodiversity and ecosystems', order=1),
            ESRSDisclosure(standard=e4, code='E4-2', name='Policies related to biodiversity and ecosystems', 
                          description='Policies to protect biodiversity',
                          requirement_text='Describe policies to protect biodiversity and ecosystems', order=2),
            ESRSDisclosure(standard=e4, code='E4-3', name='Actions and resources', 
                          description='Actions for biodiversity protection',
                          requirement_text='Describe key actions and resources for biodiversity protection', order=3),
            ESRSDisclosure(standard=e4, code='E4-4', name='Targets related to biodiversity', 
                          description='Biodiversity targets and milestones',
                          requirement_text='Disclose targets related to biodiversity and ecosystems', order=4),
            ESRSDisclosure(standard=e4, code='E4-5', name='Impact metrics', 
                          description='Metrics on biodiversity impacts',
                          requirement_text='Disclose metrics related to material impacts on biodiversity', order=5),
            ESRSDisclosure(standard=e4, code='E4-6', name='Anticipated financial effects', 
                          description='Financial effects from biodiversity risks',
                          requirement_text='Disclose anticipated financial effects from biodiversity-related risks', order=6),
        ])
        
        # E5: Resource Use and Circular Economy
        e5 = ESRSStandard.objects.create(
            category=env_category,
            code='E5',
            name='Resource Use and Circular Economy',
            description='Resource efficiency and circular economy practices',
            order=5
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard=e5, code='E5-1', name='Policies related to resource use', 
                          description='Policies for resource efficiency and circular economy',
                          requirement_text='Describe policies related to resource use and circular economy', order=1),
            ESRSDisclosure(standard=e5, code='E5-2', name='Actions and resources', 
                          description='Actions for resource efficiency',
                          requirement_text='Describe key actions and resources for resource efficiency', order=2),
            ESRSDisclosure(standard=e5, code='E5-3', name='Targets related to resource use', 
                          description='Targets for circular economy',
                          requirement_text='Disclose targets related to resource use and circular economy', order=3),
            ESRSDisclosure(standard=e5, code='E5-4', name='Resource inflows', 
                          description='Material resource inputs',
                          requirement_text='Disclose total resource inflows including materials and products', order=4),
            ESRSDisclosure(standard=e5, code='E5-5', name='Resource outflows', 
                          description='Products, materials and waste outputs',
                          requirement_text='Disclose resource outflows including waste generated', order=5),
            ESRSDisclosure(standard=e5, code='E5-6', name='Anticipated financial effects', 
                          description='Financial effects from resource use',
                          requirement_text='Disclose anticipated financial effects from resource use risks', order=6),
        ])
        
        # S1: Own Workforce
        s1 = ESRSStandard.objects.create(
            category=social_category,
            code='S1',
            name='Own Workforce',
            description='Working conditions and treatment of employees',
            order=1
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard=s1, code='S1-1', name='Policies related to own workforce', 
                          description='Policies for employees and workers',
                          requirement_text='Describe policies related to own workforce', order=1),
            ESRSDisclosure(standard=s1, code='S1-2', name='Processes for engaging with own workforce', 
                          description='Engagement processes with workers',
                          requirement_text='Describe processes for engaging with own workforce and workers representatives', order=2),
            ESRSDisclosure(standard=s1, code='S1-3', name='Processes to remediate negative impacts', 
                          description='Channels for workforce to raise concerns',
                          requirement_text='Describe processes to provide for or cooperate in remediation', order=3),
            ESRSDisclosure(standard=s1, code='S1-4', name='Taking action on material impacts', 
                          description='Actions to address material impacts on workforce',
                          requirement_text='Describe actions taken and resources allocated to manage material impacts', order=4),
            ESRSDisclosure(standard=s1, code='S1-5', name='Targets related to own workforce', 
                          description='Targets for workforce matters',
                          requirement_text='Disclose time-bound targets related to own workforce', order=5),
            ESRSDisclosure(standard=s1, code='S1-6', name='Characteristics of employees', 
                          description='Number and demographics of employees',
                          requirement_text='Disclose characteristics of employees including diversity metrics', order=6),
            ESRSDisclosure(standard=s1, code='S1-7', name='Collective bargaining coverage', 
                          description='Percentage of employees covered by collective agreements',
                          requirement_text='Disclose percentage of employees covered by collective bargaining agreements', order=7),
            ESRSDisclosure(standard=s1, code='S1-8', name='Collective bargaining coverage by country', 
                          description='Coverage by country for major operations',
                          requirement_text='Disclose collective bargaining coverage rate for each country', order=8),
            ESRSDisclosure(standard=s1, code='S1-9', name='Diversity metrics', 
                          description='Gender and other diversity indicators',
                          requirement_text='Disclose diversity metrics including gender and age diversity', order=9),
            ESRSDisclosure(standard=s1, code='S1-10', name='Adequate wages', 
                          description='Living wage and fair remuneration',
                          requirement_text='Disclose percentage of employees earning below adequate wage', order=10),
            ESRSDisclosure(standard=s1, code='S1-11', name='Social protection', 
                          description='Social security coverage',
                          requirement_text='Disclose percentage of employees covered by social protection', order=11),
            ESRSDisclosure(standard=s1, code='S1-12', name='Persons with disabilities', 
                          description='Employment of persons with disabilities',
                          requirement_text='Disclose percentage of employees with disabilities', order=12),
            ESRSDisclosure(standard=s1, code='S1-13', name='Training and skills development', 
                          description='Investment in training programs',
                          requirement_text='Disclose training metrics and skills development indicators', order=13),
            ESRSDisclosure(standard=s1, code='S1-14', name='Health and safety metrics', 
                          description='Work-related incidents and fatalities',
                          requirement_text='Disclose work-related injuries, fatalities and ill health', order=14),
            ESRSDisclosure(standard=s1, code='S1-15', name='Work-life balance', 
                          description='Work-life balance arrangements',
                          requirement_text='Disclose work-life balance arrangements and parental leave uptake', order=15),
        ])
        
        # S2: Workers in Value Chain
        s2 = ESRSStandard.objects.create(
            category=social_category,
            code='S2',
            name='Workers in the Value Chain',
            description='Working conditions in supply chain',
            order=2
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard=s2, code='S2-1', name='Policies', 
                          description='Policies related to value chain workers',
                          requirement_text='Describe policies related to value chain workers', order=1),
            ESRSDisclosure(standard=s2, code='S2-2', name='Processes for engaging', 
                          description='Engagement with workers in value chain',
                          requirement_text='Describe processes for engaging with workers in the value chain', order=2),
            ESRSDisclosure(standard=s2, code='S2-3', name='Processes to remediate negative impacts', 
                          description='Channels for raising concerns in value chain',
                          requirement_text='Describe processes to remediate negative impacts in value chain', order=3),
            ESRSDisclosure(standard=s2, code='S2-4', name='Taking action on material impacts', 
                          description='Actions for value chain worker protection',
                          requirement_text='Describe actions to address material impacts on value chain workers', order=4),
            ESRSDisclosure(standard=s2, code='S2-5', name='Targets', 
                          description='Targets for value chain workers',
                          requirement_text='Disclose targets related to workers in the value chain', order=5),
        ])
        
        # S3: Affected Communities
        s3 = ESRSStandard.objects.create(
            category=social_category,
            code='S3',
            name='Affected Communities',
            description='Impact on local and affected communities',
            order=3
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard=s3, code='S3-1', name='Policies', 
                          description='Policies related to affected communities',
                          requirement_text='Describe policies related to affected communities', order=1),
            ESRSDisclosure(standard=s3, code='S3-2', name='Processes for engaging', 
                          description='Engagement with affected communities',
                          requirement_text='Describe processes for engaging with affected communities', order=2),
            ESRSDisclosure(standard=s3, code='S3-3', name='Processes to remediate negative impacts', 
                          description='Channels for communities to raise concerns',
                          requirement_text='Describe processes to remediate negative impacts on communities', order=3),
            ESRSDisclosure(standard=s3, code='S3-4', name='Taking action on material impacts', 
                          description='Actions to address community impacts',
                          requirement_text='Describe actions to address material impacts on affected communities', order=4),
            ESRSDisclosure(standard=s3, code='S3-5', name='Targets', 
                          description='Targets for affected communities',
                          requirement_text='Disclose targets related to affected communities', order=5),
        ])
        
        # S4: Consumers and End-users
        s4 = ESRSStandard.objects.create(
            category=social_category,
            code='S4',
            name='Consumers and End-users',
            description='Consumer protection and product safety',
            order=4
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard=s4, code='S4-1', name='Policies', 
                          description='Policies related to consumers',
                          requirement_text='Describe policies related to consumers and end-users', order=1),
            ESRSDisclosure(standard=s4, code='S4-2', name='Processes for engaging', 
                          description='Engagement with consumers',
                          requirement_text='Describe processes for engaging with consumers and end-users', order=2),
            ESRSDisclosure(standard=s4, code='S4-3', name='Processes to remediate negative impacts', 
                          description='Channels for consumer complaints',
                          requirement_text='Describe processes to remediate negative impacts on consumers', order=3),
            ESRSDisclosure(standard=s4, code='S4-4', name='Taking action on material impacts', 
                          description='Actions for consumer protection',
                          requirement_text='Describe actions to address material impacts on consumers', order=4),
            ESRSDisclosure(standard=s4, code='S4-5', name='Targets', 
                          description='Targets related to consumers',
                          requirement_text='Disclose targets related to consumers and end-users', order=5),
        ])
        
        # G1: Business Conduct
        g1 = ESRSStandard.objects.create(
            category=gov_category,
            code='G1',
            name='Business Conduct',
            description='Corporate culture, ethics and anti-corruption',
            order=1
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard=g1, code='G1-1', name='Business conduct policies and corporate culture', 
                          description='Policies and culture related to business conduct',
                          requirement_text='Describe business conduct policies and corporate culture', order=1),
            ESRSDisclosure(standard=g1, code='G1-2', name='Management of relationships with suppliers', 
                          description='Supplier relationship management',
                          requirement_text='Describe management of relationships with suppliers', order=2),
            ESRSDisclosure(standard=g1, code='G1-3', name='Prevention and detection of corruption and bribery', 
                          description='Anti-corruption procedures',
                          requirement_text='Describe procedures to prevent, detect and address corruption and bribery', order=3),
            ESRSDisclosure(standard=g1, code='G1-4', name='Incidents of corruption or bribery', 
                          description='Confirmed incidents and actions taken',
                          requirement_text='Disclose confirmed incidents of corruption or bribery and actions taken', order=4),
            ESRSDisclosure(standard=g1, code='G1-5', name='Political influence and lobbying activities', 
                          description='Political engagement and lobbying',
                          requirement_text='Disclose information about political influence and lobbying activities', order=5),
            ESRSDisclosure(standard=g1, code='G1-6', name='Payment practices', 
                          description='Terms of payment to suppliers',
                          requirement_text='Disclose information about payment practices including terms and average time', order=6),
        ])
        
        # Count statistics
        total_standards = ESRSStandard.objects.count()
        total_disclosures = ESRSDisclosure.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully populated ESRS database!'))
        self.stdout.write(self.style.SUCCESS(f'  - Categories: 4'))
        self.stdout.write(self.style.SUCCESS(f'  - Standards: {total_standards}'))
        self.stdout.write(self.style.SUCCESS(f'  - Disclosures: {total_disclosures}'))
