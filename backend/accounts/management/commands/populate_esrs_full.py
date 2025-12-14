from django.core.management.base import BaseCommand
from accounts.models import ESRSCategory, ESRSStandard, ESRSDisclosure


class Command(BaseCommand):
    help = 'Populate ESRS standards and disclosures in database with complete hierarchy'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting complete ESRS population with all sub-disclosures...')
        
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
        
        # ===================
        # E1: CLIMATE CHANGE
        # ===================
        e1 = ESRSStandard.objects.create(
            category=env_category,
            code='E1',
            name='Climate Change',
            description='Climate change mitigation and adaptation disclosures',
            order=1
        )
        
        # E1-1: Transition plan for climate change mitigation
        e1_1 = ESRSDisclosure.objects.create(
            standard=e1, code='E1-1', parent=None,
            name='Transition plan for climate change mitigation',
            description='The undertaking shall disclose its transition plan for climate change mitigation',
            requirement_text='Describe the transition plan that covers: targets, decarbonisation levers, investments, key actions',
            order=1
        )
        total_disclosures += 1
        
        # E1-2: Policies related to climate change mitigation and adaptation
        e1_2 = ESRSDisclosure.objects.create(
            standard=e1, code='E1-2', parent=None,
            name='Policies related to climate change mitigation and adaptation',
            description='The undertaking shall describe its policies adopted to manage its material impacts, risks and opportunities related to climate change mitigation and adaptation',
            requirement_text='Disclose policies implemented to mitigate climate change and adapt to climate risks',
            order=2
        )
        total_disclosures += 1
        
        # E1-3: Actions and resources related to climate change policies
        e1_3 = ESRSDisclosure.objects.create(
            standard=e1, code='E1-3', parent=None,
            name='Actions and resources related to climate change policies',
            description='The undertaking shall disclose its climate change mitigation and adaptation actions and the resources allocated to their implementation',
            requirement_text='Describe key actions taken and planned, and their expected outcomes. Disclose CAPEX and OPEX related to actions',
            order=3
        )
        total_disclosures += 1
        
        # E1-3 sub-disclosures
        e1_3_subs = [
            ('E1-3a', 'Climate change mitigation actions', 'The undertaking shall disclose its key actions taken and planned to achieve climate-related policy objectives and targets related to mitigation, including: decarbonisation levers (energy efficiency, renewable energy, fuel switching, electrification, carbon capture and storage), nature-based solutions, product and service design changes, and upstream and downstream value chain initiatives.'),
            ('E1-3b', 'Climate change adaptation actions', 'The undertaking shall disclose actions taken and planned to build resilience and adapt its strategy and business model to climate change, including: adaptation solutions implemented (infrastructure hardening, diversification, relocation, water management, cooling systems), nature-based adaptation solutions, and how adaptation actions address key climate-related physical risks identified.'),
            ('E1-3c', 'Resources allocated', 'The undertaking shall disclose financial and human resources allocated to climate change actions, including: capital expenditure (CapEx) and operational expenditure (OpEx) for climate mitigation and adaptation, investments in R&D for climate solutions, dedicated staff and organizational resources, and whether climate investments are aligned with EU Taxonomy criteria.'),
            ('E1-3d', 'Action plans', 'The undertaking shall describe detailed action plans with specific information on: key actions with timelines and milestones, responsible organizational units or individuals, expected outcomes and contribution to targets, scope of application (own operations, upstream or downstream value chain), and status of implementation (planned, ongoing, completed).'),
        ]
        for code, name, req_text in e1_3_subs:
            ESRSDisclosure.objects.create(
                standard=e1, code=code, parent=e1_3,
                name=name, description=req_text,
                requirement_text=req_text, order=total_disclosures
            )
            total_disclosures += 1
        
        # E1-4: Targets related to climate change mitigation and adaptation
        e1_4 = ESRSDisclosure.objects.create(
            standard=e1, code='E1-4', parent=None,
            name='Targets related to climate change mitigation and adaptation',
            description='The undertaking shall disclose the climate-related targets it has adopted',
            requirement_text='Disclose targets for GHG emission reductions and climate adaptation',
            order=total_disclosures
        )
        total_disclosures += 1
        
        # E1-5: Energy consumption and mix
        e1_5 = ESRSDisclosure.objects.create(
            standard=e1, code='E1-5', parent=None,
            name='Energy consumption and mix',
            description='The undertaking shall provide information on its energy consumption and mix',
            requirement_text='Disclose total energy consumption in MWh, breakdown by source (renewable vs non-renewable)',
            order=total_disclosures
        )
        total_disclosures += 1
        
        # E1-5 sub-disclosures
        e1_5_subs = [
            ('E1-5a', 'Total energy consumption', 'The undertaking shall disclose its total energy consumption in MWh related to own operations, broken down by: (a) total energy consumption from fossil sources; (b) total energy consumption from nuclear sources; (c) total energy consumption from renewable sources.'),
            ('E1-5b', 'Renewable energy consumption', 'The undertaking shall disclose the percentage of renewable energy in total energy consumption, calculated as renewable energy consumption divided by total energy consumption. Renewable energy includes: renewable sources (solar, wind, hydro, geothermal, ocean energy, biomass, biogas, and renewable hydrogen).'),
            ('E1-5c', 'Non-renewable energy consumption', 'The undertaking shall disclose total consumption from non-renewable sources broken down by: fossil fuel sources (coal, oil, gas) and nuclear sources. This includes purchased electricity, heat, steam and cooling from non-renewable sources.'),
            ('E1-5d', 'Energy intensity', 'The undertaking shall disclose its energy intensity based on total energy consumption per net revenue (MWh/million EUR). Alternatively, energy intensity may be calculated per another appropriate denominator such as: full-time equivalent employees (FTE), production units, or other business-specific metric.'),
        ]
        for code, name, req_text in e1_5_subs:
            ESRSDisclosure.objects.create(
                standard=e1, code=code, parent=e1_5,
                name=name, description=req_text,
                requirement_text=req_text, order=total_disclosures
            )
            total_disclosures += 1
        
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
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✓ Successfully populated ESRS database!'))
        self.stdout.write(self.style.SUCCESS(f'  - Categories: 4'))
        self.stdout.write(self.style.SUCCESS(f'  - Standards: 12'))
        self.stdout.write(self.style.SUCCESS(f'  - Total Disclosures (including sub-disclosures): {total_disclosures}'))
        self.stdout.write(self.style.SUCCESS('='*60))
