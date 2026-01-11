"""
Management command to add ALL standards: ISO 14001, GDPR, ISO 27001, ISO 45001, ISO 50001, NIS2, CSRD, DORA, CSDDD, EU Taxonomy
Run: python manage.py add_all_standards
"""
from django.core.management.base import BaseCommand
from accounts.models import ESRSCategory, ESRSStandard, ESRSDisclosure


class Command(BaseCommand):
    help = 'Add ALL standards: ISO 14001, GDPR, ISO 27001, ISO 45001, ISO 50001, NIS2, CSRD, DORA, CSDDD, EU Taxonomy'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Adding ALL standards to database...'))
        
        # ISO 14001: Environmental Management System
        self.add_iso14001()
        
        # GDPR: General Data Protection Regulation
        self.add_gdpr()
        
        # ISO 27001: Information Security Management
        self.add_iso27001()
        
        # ISO 45001: Occupational Health and Safety
        self.add_iso45001()
        
        # ISO 50001: Energy Management System
        self.add_iso50001()
        
        # NIS2: Network and Information Security Directive
        self.add_nis2()
        
        # CSRD: Corporate Sustainability Reporting Directive
        self.add_csrd()
        
        # DORA: Digital Operational Resilience Act
        self.add_dora()
        
        # CSDDD: Corporate Sustainability Due Diligence Directive
        self.add_csddd()
        
        # EU Taxonomy: Sustainable Finance Regulation
        self.add_eu_taxonomy()
        
        self.stdout.write(self.style.SUCCESS('✅ ALL STANDARDS ADDED SUCCESSFULLY!'))
        self.print_summary()

    def add_iso14001(self):
        """ISO 14001: Environmental Management System"""
        self.stdout.write('📋 Adding ISO 14001...')
        
        # Category
        cat, _ = ESRSCategory.objects.get_or_create(
            code='ENV',
            standard_type='ISO14001',
            defaults={
                'name': 'Environmental Management',
                'description': 'ISO 14001 Environmental Management System requirements',
                'order': 1
            }
        )
        
        # Standard
        std, _ = ESRSStandard.objects.get_or_create(
            code='ISO14001',
            standard_type='ISO14001',
            defaults={
                'category': cat,
                'name': 'Environmental Management System',
                'description': 'Requirements for an environmental management system',
                'order': 1
            }
        )
        
        # Disclosures
        disclosures = [
            {
                'code': '4.1',
                'name': 'Understanding the organization and its context',
                'description': 'Organization context analysis',
                'requirement_text': 'The organization shall determine external and internal issues that are relevant to its purpose and that affect its ability to achieve the intended outcome(s) of its environmental management system.',
                'order': 1
            },
            {
                'code': '4.2',
                'name': 'Understanding the needs and expectations of interested parties',
                'description': 'Stakeholder requirements',
                'requirement_text': 'The organization shall determine: a) interested parties that are relevant to the environmental management system; b) the relevant needs and expectations of these interested parties; c) which of these needs and expectations become compliance obligations.',
                'order': 2
            },
            {
                'code': '5.1',
                'name': 'Leadership and commitment',
                'description': 'Top management commitment',
                'requirement_text': 'Top management shall demonstrate leadership and commitment with respect to the environmental management system by: taking accountability for the effectiveness of the EMS, ensuring environmental policy and objectives are established, integrating EMS requirements into business processes.',
                'order': 3
            },
            {
                'code': '6.1',
                'name': 'Actions to address risks and opportunities',
                'description': 'Risk assessment and planning',
                'requirement_text': 'When planning for the EMS, the organization shall consider the issues (4.1), requirements (4.2) and determine the risks and opportunities that need to be addressed to: give assurance EMS achieves intended outcomes, prevent or reduce undesired effects, achieve continual improvement.',
                'order': 4
            },
            {
                'code': '9.1',
                'name': 'Monitoring, measurement, analysis and evaluation',
                'description': 'Performance evaluation',
                'requirement_text': 'The organization shall establish the processes needed to monitor, measure, analyze and evaluate environmental performance. This includes: what needs monitoring and measurement, methods needed, criteria for evaluation, when monitoring and measurement shall be performed, when results shall be analyzed and evaluated.',
                'order': 5
            },
        ]
        
        for disc_data in disclosures:
            ESRSDisclosure.objects.get_or_create(
                standard=std,
                code=disc_data['code'],
                standard_type='ISO14001',
                defaults={
                    'name': disc_data['name'],
                    'description': disc_data['description'],
                    'requirement_text': disc_data['requirement_text'],
                    'order': disc_data['order'],
                    'is_mandatory': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ ISO 14001: 1 category, 1 standard, {len(disclosures)} disclosures'))

    def add_gdpr(self):
        """GDPR: 6 Chapters, 27 Key Articles"""
        self.stdout.write('📋 Adding GDPR...')
        
        # Category
        cat, _ = ESRSCategory.objects.get_or_create(
            code='GDPR',
            standard_type='GDPR',
            defaults={
                'name': 'Data Protection',
                'description': 'General Data Protection Regulation',
                'order': 1
            }
        )
        
        # Chapters (Standards)
        chapters = [
            ('Ch-I', 'General Provisions', 'Articles 1-4: Scope, definitions, territorial scope, processing'),
            ('Ch-II', 'Principles', 'Articles 5-11: Lawfulness, fairness, transparency, purpose limitation'),
            ('Ch-III', 'Rights of Data Subject', 'Articles 12-23: Information, access, rectification, erasure, restriction'),
            ('Ch-IV', 'Controller and Processor', 'Articles 24-43: Responsibility, security, data protection officer'),
            ('Ch-V', 'Transfers of Personal Data', 'Articles 44-50: International transfers, adequacy decisions, safeguards'),
            ('Ch-VI', 'Independent Supervisory Authorities', 'Articles 51-59: Establishment, independence, competence'),
        ]
        
        for order, (code, name, desc) in enumerate(chapters, 1):
            std, _ = ESRSStandard.objects.get_or_create(
                code=code,
                standard_type='GDPR',
                defaults={
                    'category': cat,
                    'name': name,
                    'description': desc,
                    'order': order
                }
            )
        
        # Key Articles (Disclosures) - 27 most important ones
        articles = [
            # Chapter I
            ('Ch-I', 'Art-1', 'Subject matter and objectives', 'This Regulation lays down rules relating to the protection of natural persons with regard to the processing of personal data and rules relating to the free movement of personal data.', 1200),
            ('Ch-I', 'Art-2', 'Material scope', 'This Regulation applies to the processing of personal data wholly or partly by automated means and to the processing other than by automated means of personal data which form part of a filing system.', 1400),
            ('Ch-I', 'Art-3', 'Territorial scope', 'This Regulation applies to the processing of personal data in the context of the activities of an establishment of a controller or a processor in the Union, regardless of whether the processing takes place in the Union or not.', 1500),
            ('Ch-I', 'Art-4', 'Definitions', "For the purposes of this Regulation: 'personal data' means any information relating to an identified or identifiable natural person; 'processing' means any operation performed on personal data; 'controller' determines the purposes and means of processing; 'processor' processes personal data on behalf of the controller.", 1800),
            
            # Chapter II
            ('Ch-II', 'Art-5', 'Principles relating to processing', 'Personal data shall be: (a) processed lawfully, fairly and transparently; (b) collected for specified, explicit and legitimate purposes; (c) adequate, relevant and limited; (d) accurate and kept up to date; (e) kept for no longer than necessary; (f) processed securely.', 1600),
            ('Ch-II', 'Art-6', 'Lawfulness of processing', 'Processing shall be lawful only if at least one applies: (a) data subject consent; (b) necessary for contract performance; (c) legal obligation; (d) vital interests; (e) public interest; (f) legitimate interests.', 1400),
            ('Ch-II', 'Art-7', 'Conditions for consent', 'Where processing is based on consent, the controller shall be able to demonstrate that the data subject has consented. Consent must be freely given, specific, informed and unambiguous.', 1100),
            ('Ch-II', 'Art-9', 'Processing of special categories', 'Processing of personal data revealing racial or ethnic origin, political opinions, religious beliefs, trade union membership, genetic data, biometric data, health data or data concerning sex life is prohibited (with specific exceptions).', 1300),
            
            # Chapter III
            ('Ch-III', 'Art-12', 'Transparent information', 'The controller shall take appropriate measures to provide information in a concise, transparent, intelligible and easily accessible form, using clear and plain language.', 900),
            ('Ch-III', 'Art-13', 'Information when data collected from subject', 'Where personal data are collected from the data subject, the controller shall provide: identity of controller, purposes of processing, legal basis, recipients, retention period, rights.', 1200),
            ('Ch-III', 'Art-15', 'Right of access', 'The data subject shall have the right to obtain from the controller confirmation as to whether personal data are being processed, and access to the personal data and information about the processing.', 1100),
            ('Ch-III', 'Art-16', 'Right to rectification', 'The data subject shall have the right to obtain without undue delay the rectification of inaccurate personal data and to have incomplete personal data completed.', 800),
            ('Ch-III', 'Art-17', 'Right to erasure (right to be forgotten)', "The data subject shall have the right to obtain erasure of personal data without undue delay where: data no longer necessary; consent withdrawn; objection to processing; data unlawfully processed; legal obligation to erase.", 1300),
            ('Ch-III', 'Art-20', 'Right to data portability', 'The data subject shall have the right to receive personal data in a structured, commonly used and machine-readable format and to transmit those data to another controller.', 950),
            
            # Chapter IV
            ('Ch-IV', 'Art-24', 'Responsibility of the controller', 'The controller shall implement appropriate technical and organisational measures to ensure and demonstrate that processing is performed in accordance with this Regulation (accountability principle).', 1100),
            ('Ch-IV', 'Art-25', 'Data protection by design and by default', 'The controller shall implement appropriate technical and organisational measures designed to implement data-protection principles effectively and integrate necessary safeguards into processing.', 1200),
            ('Ch-IV', 'Art-30', 'Records of processing activities', 'Each controller shall maintain a record of processing activities under its responsibility containing: name and contact details of controller, purposes of processing, categories of data subjects and personal data, categories of recipients, transfers, retention periods, security measures.', 1400),
            ('Ch-IV', 'Art-32', 'Security of processing', 'The controller and processor shall implement appropriate technical and organisational measures to ensure a level of security appropriate to the risk, including: pseudonymisation and encryption, confidentiality, integrity, availability and resilience, testing and evaluation.', 1350),
            ('Ch-IV', 'Art-33', 'Notification of personal data breach', 'In the case of a personal data breach, the controller shall without undue delay and, where feasible, not later than 72 hours after having become aware of it, notify the breach to the supervisory authority.', 1200),
            ('Ch-IV', 'Art-35', 'Data protection impact assessment', 'Where processing is likely to result in a high risk to rights and freedoms, the controller shall carry out an assessment of the impact of the envisaged processing operations on the protection of personal data (DPIA).', 1250),
            ('Ch-IV', 'Art-37', 'Designation of data protection officer', 'The controller and processor shall designate a DPO where: (a) carried out by public authority; (b) core activities require regular and systematic monitoring; (c) core activities consist of processing special categories of data.', 1150),
            
            # Chapter V
            ('Ch-V', 'Art-44', 'General principle for transfers', 'Any transfer of personal data to a third country or international organisation shall take place only if the controller and processor comply with the conditions laid down in this Chapter.', 950),
            ('Ch-V', 'Art-45', 'Transfers on basis of adequacy decision', 'A transfer of personal data to a third country may take place where the Commission has decided that the third country ensures an adequate level of protection.', 1000),
            ('Ch-V', 'Art-46', 'Transfers subject to appropriate safeguards', 'In the absence of an adequacy decision, a transfer may take place where appropriate safeguards have been provided: binding corporate rules, standard data protection clauses, approved code of conduct, approved certification mechanism.', 1300),
            
            # Chapter VI
            ('Ch-VI', 'Art-51', 'Supervisory authority', 'Each Member State shall provide for one or more independent public authorities to be responsible for monitoring the application of this Regulation (supervisory authority).', 850),
            ('Ch-VI', 'Art-57', 'Tasks of supervisory authority', 'The supervisory authority shall: monitor and enforce application of Regulation, promote public awareness, advise national parliament and government, handle complaints, conduct investigations, authorise contractual clauses, issue opinions to national parliament.', 1400),
            ('Ch-VI', 'Art-58', 'Powers of supervisory authority', 'Each supervisory authority shall have: investigative powers (obtain access to data, carry out audits), corrective powers (issue warnings, order rectification, impose limitations, order erasure, impose fines), authorisation and advisory powers.', 1500),
        ]
        
        disc_count = 0
        for std_code, disc_code, name, requirement, length in articles:
            std = ESRSStandard.objects.get(code=std_code, standard_type='GDPR')
            ESRSDisclosure.objects.get_or_create(
                standard=std,
                code=disc_code,
                standard_type='GDPR',
                defaults={
                    'name': name,
                    'description': f'GDPR {disc_code}: {name[:100]}',
                    'requirement_text': requirement,
                    'order': disc_count + 1,
                    'is_mandatory': True
                }
            )
            disc_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ GDPR: 1 category, {len(chapters)} chapters, {len(articles)} articles'))

    def add_iso27001(self):
        """ISO 27001: Information Security Management"""
        self.stdout.write('📋 Adding ISO 27001...')
        
        cat, _ = ESRSCategory.objects.get_or_create(
            code='SEC',
            standard_type='ISO27001',
            defaults={
                'name': 'Information Security',
                'description': 'ISO 27001 Information Security Management System',
                'order': 1
            }
        )
        
        std, _ = ESRSStandard.objects.get_or_create(
            code='ISO27001',
            standard_type='ISO27001',
            defaults={
                'category': cat,
                'name': 'Information Security Management System',
                'description': 'Requirements for establishing, implementing, maintaining and improving an ISMS',
                'order': 1
            }
        )
        
        disclosures = [
            ('4.1', 'Understanding organization and context', 'Determine external and internal issues relevant to ISMS purpose and ability to achieve intended outcomes for information security management.', 1100),
            ('5.1', 'Leadership and commitment', 'Top management demonstrates leadership and commitment to ISMS by ensuring information security policy and objectives are established and compatible with strategic direction.', 1000),
            ('6.1.2', 'Information security risk assessment', 'Define and apply an information security risk assessment process that: establishes risk criteria, ensures repeated assessments produce consistent results, identifies information security risks, analyzes and evaluates risks.', 1300),
            ('8.1', 'Operational planning and control', 'Plan, implement and control processes needed to meet information security requirements and implement actions determined in risk assessment and treatment.', 950),
            ('9.1', 'Monitoring, measurement, analysis and evaluation', 'Determine what needs to be monitored and measured, methods for monitoring and measurement, when monitoring and measuring shall be performed, when results shall be analyzed and evaluated.', 1150),
            ('10.1', 'Nonconformity and corrective action', 'When nonconformity occurs, react to the nonconformity, evaluate the need for action, implement any action needed, review the effectiveness of corrective action taken, make changes to the ISMS if necessary.', 1200),
            ('A.5.1', 'Information security policies', 'A set of policies for information security shall be defined, approved by management, published and communicated to employees and relevant external parties (Annex A Control).', 900),
        ]
        
        for code, name, req, length in disclosures:
            ESRSDisclosure.objects.get_or_create(
                standard=std,
                code=code,
                standard_type='ISO27001',
                defaults={
                    'name': name,
                    'description': f'ISO 27001 {code}: {name}',
                    'requirement_text': req,
                    'order': len(disclosures),
                    'is_mandatory': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ ISO 27001: 1 category, 1 standard, {len(disclosures)} disclosures'))

    def add_iso45001(self):
        """ISO 45001: Occupational Health and Safety"""
        self.stdout.write('📋 Adding ISO 45001...')
        
        cat, _ = ESRSCategory.objects.get_or_create(
            code='OHS',
            standard_type='ISO45001',
            defaults={
                'name': 'Occupational Health & Safety',
                'description': 'ISO 45001 OH&S Management System',
                'order': 1
            }
        )
        
        std, _ = ESRSStandard.objects.get_or_create(
            code='ISO45001',
            standard_type='ISO45001',
            defaults={
                'category': cat,
                'name': 'Occupational Health and Safety Management System',
                'description': 'Requirements for an OH&S management system',
                'order': 1
            }
        )
        
        disclosures = [
            ('4.1', 'Understanding organization and context', 'Determine external and internal issues relevant to its purpose and that affect ability to achieve intended outcomes of OH&S management system.', 1050),
            ('5.1', 'Leadership and commitment', 'Top management shall demonstrate leadership and commitment by: taking accountability for prevention of work-related injury and ill health, ensuring OH&S policy and objectives are established, ensuring integration of OH&S requirements into business processes.', 1250),
            ('6.1.1', 'Actions to address risks and opportunities', 'Determine risks and opportunities that need to be addressed to: give assurance OH&S management system achieves intended outcomes, prevent or reduce undesired effects, achieve continual improvement.', 1150),
            ('8.1.2', 'Eliminating hazards and reducing OH&S risks', 'Establish processes for hazard elimination and OH&S risk reduction using hierarchy of controls: elimination, substitution, engineering controls, administrative controls, PPE.', 1100),
            ('9.1.1', 'Monitoring, measurement, analysis, performance', 'Establish processes to monitor, measure, analyze and evaluate OH&S performance. Determine what needs monitoring (compliance, activities, health surveillance, effectiveness), methods, criteria, when performed.', 1300),
            ('10.2', 'Incident, nonconformity and corrective action', 'Establish processes to report, investigate and take action on incidents and nonconformities. React to incident, evaluate need for corrective action, implement action, review effectiveness, make changes to OH&S management system.', 1250),
        ]
        
        for code, name, req, length in disclosures:
            ESRSDisclosure.objects.get_or_create(
                standard=std,
                code=code,
                standard_type='ISO45001',
                defaults={
                    'name': name,
                    'description': f'ISO 45001 {code}: {name}',
                    'requirement_text': req,
                    'order': len(disclosures),
                    'is_mandatory': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ ISO 45001: 1 category, 1 standard, {len(disclosures)} disclosures'))

    def add_iso50001(self):
        """ISO 50001: Energy Management System"""
        self.stdout.write('📋 Adding ISO 50001...')
        
        cat, _ = ESRSCategory.objects.get_or_create(
            code='ENE',
            standard_type='ISO50001',
            defaults={
                'name': 'Energy Management',
                'description': 'ISO 50001 Energy Management System',
                'order': 1
            }
        )
        
        std, _ = ESRSStandard.objects.get_or_create(
            code='ISO50001',
            standard_type='ISO50001',
            defaults={
                'category': cat,
                'name': 'Energy Management System',
                'description': 'Requirements for establishing, implementing, maintaining and improving an EnMS',
                'order': 1
            }
        )
        
        disclosures = [
            ('4.1', 'Understanding organization and context', 'Determine external and internal issues relevant to its purpose and that affect ability to achieve intended outcomes of energy management system.', 1000),
            ('6.2', 'Energy review', 'Develop, record and maintain an energy review based on measurement and other data: analyze energy use and consumption, identify areas of significant energy use, identify opportunities for improving energy performance.', 1200),
            ('6.3', 'Energy baseline', 'Establish energy baselines using information from energy review. Energy baseline shall be adjusted when: EnPIs no longer reflect organizational use, major changes to process or systems, according to predetermined method.', 1100),
            ('6.4', 'Energy performance indicators', 'Determine energy performance indicators (EnPIs) appropriate for monitoring and measuring energy performance. EnPIs shall be reviewed and compared to energy baseline.', 950),
            ('8.1', 'Operational planning and control', 'Plan, implement and control processes needed to meet energy objectives and take actions by: establishing criteria for processes, implementing control of processes, ensuring controlled conditions.', 1050),
            ('9.1', 'Monitoring, measurement, analysis, evaluation', 'Monitor, measure, analyze and evaluate energy performance and EnMS. Determine what needs monitoring (significant energy uses, EnPIs, effectiveness of action plans), methods, when performed, when analyzed.', 1200),
        ]
        
        for code, name, req, length in disclosures:
            ESRSDisclosure.objects.get_or_create(
                standard=std,
                code=code,
                standard_type='ISO50001',
                defaults={
                    'name': name,
                    'description': f'ISO 50001 {code}: {name}',
                    'requirement_text': req,
                    'order': len(disclosures),
                    'is_mandatory': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ ISO 50001: 1 category, 1 standard, {len(disclosures)} disclosures'))

    def add_nis2(self):
        """NIS2: Network and Information Security Directive"""
        self.stdout.write('📋 Adding NIS2...')
        
        cat, _ = ESRSCategory.objects.get_or_create(
            code='NIS',
            standard_type='NIS2',
            defaults={
                'name': 'Network Security',
                'description': 'NIS2 Directive - Cybersecurity requirements',
                'order': 1
            }
        )
        
        std, _ = ESRSStandard.objects.get_or_create(
            code='NIS2',
            standard_type='NIS2',
            defaults={
                'category': cat,
                'name': 'Network and Information Security Directive',
                'description': 'EU Directive on security of network and information systems',
                'order': 1
            }
        )
        
        disclosures = [
            ('Art-21', 'Cybersecurity risk management', 'Essential and important entities shall take appropriate technical, operational and organizational measures to manage cybersecurity risks to network and information systems. Measures must be proportionate to risks.', 1150),
            ('Art-23', 'Reporting obligations', 'Essential and important entities shall notify CSIRT or competent authority of any incident having significant impact on provision of services. Early warning within 24h, incident notification within 72h, final report within 1 month.', 1300),
            ('Art-20', 'Governance and accountability', 'Management bodies of essential and important entities shall be responsible for overseeing cybersecurity risk management, approve cybersecurity risk measures, undergo training, ensure resources allocated.', 1100),
            ('Art-21(2)', 'Security measures', 'Cybersecurity risk measures shall include: policies on risk analysis and security, incident handling, business continuity, supply chain security, security in acquisition, development, use of network and information systems, encryption.', 1400),
            ('Art-32', 'Supervision and enforcement', 'Competent authorities shall supervise compliance of essential and important entities. Powers include: conducting on-site inspections, requiring information, issuing binding instructions, imposing administrative fines.', 1200),
        ]
        
        for code, name, req, length in disclosures:
            ESRSDisclosure.objects.get_or_create(
                standard=std,
                code=code,
                standard_type='NIS2',
                defaults={
                    'name': name,
                    'description': f'NIS2 {code}: {name}',
                    'requirement_text': req,
                    'order': len(disclosures),
                    'is_mandatory': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ NIS2: 1 category, 1 standard, {len(disclosures)} disclosures'))

    def add_csrd(self):
        """CSRD: Corporate Sustainability Reporting Directive"""
        self.stdout.write('📋 Adding CSRD...')
        
        cat, _ = ESRSCategory.objects.get_or_create(
            code='CSRD',
            standard_type='CSRD',
            defaults={
                'name': 'Sustainability Reporting',
                'description': 'CSRD - Corporate sustainability disclosure requirements',
                'order': 1
            }
        )
        
        std, _ = ESRSStandard.objects.get_or_create(
            code='CSRD',
            standard_type='CSRD',
            defaults={
                'category': cat,
                'name': 'Corporate Sustainability Reporting Directive',
                'description': 'EU Directive on corporate sustainability reporting',
                'order': 1
            }
        )
        
        disclosures = [
            ('Art-19a', 'Sustainability reporting', 'Large undertakings shall include in management report information necessary to understand undertaking impact on sustainability matters, and how sustainability matters affect development, performance and position.', 1400),
            ('Art-19b', 'Content of sustainability reporting', 'Report shall contain: brief description of business model and strategy, targets related to sustainability matters, role of administrative bodies, main impacts (adverse and positive), principal risks and how managed, key performance indicators.', 1500),
            ('Art-29b', 'Double materiality assessment', 'Undertaking shall report information necessary to understand: a) impacts of undertaking on people and environment (impact materiality), b) how sustainability matters affect development and position (financial materiality).', 1350),
            ('Art-29c', 'Value chain information', 'Sustainability reporting shall include information about own operations and where relevant information about upstream and downstream value chain including products, services and business relationships.', 1200),
            ('Art-34', 'Assurance of sustainability reporting', 'Statutory auditor shall check whether sustainability reporting has been provided and express opinion on compliance with reporting requirements (limited assurance initially, reasonable assurance from 2028).', 1300),
        ]
        
        for code, name, req, length in disclosures:
            ESRSDisclosure.objects.get_or_create(
                standard=std,
                code=code,
                standard_type='CSRD',
                defaults={
                    'name': name,
                    'description': f'CSRD {code}: {name}',
                    'requirement_text': req,
                    'order': len(disclosures),
                    'is_mandatory': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ CSRD: 1 category, 1 standard, {len(disclosures)} disclosures'))

    def add_dora(self):
        """DORA: Digital Operational Resilience Act"""
        self.stdout.write('📋 Adding DORA...')
        
        cat, _ = ESRSCategory.objects.get_or_create(
            code='DOR',
            standard_type='DORA',
            defaults={
                'name': 'Digital Resilience',
                'description': 'DORA - Financial sector digital operational resilience',
                'order': 1
            }
        )
        
        std, _ = ESRSStandard.objects.get_or_create(
            code='DORA',
            standard_type='DORA',
            defaults={
                'category': cat,
                'name': 'Digital Operational Resilience Act',
                'description': 'EU Regulation on digital operational resilience for financial sector',
                'order': 1
            }
        )
        
        disclosures = [
            ('Art-6', 'ICT risk management framework', 'Financial entities shall have internal governance and control framework ensuring effective and prudent management of ICT risk. Framework shall cover: strategy, policies, procedures, ICT protocols, tools covering security, availability, continuity, redundancy.', 1450),
            ('Art-17', 'ICT-related incident reporting', 'Financial entities shall report major ICT-related incidents to competent authority. Initial notification within 4h, intermediate report within 72h, final report within 1 month. Report shall include: affected users, geographic spread, impact, estimated costs.', 1400),
            ('Art-11', 'Testing of ICT tools and systems', 'Financial entities shall establish, maintain and review sound and comprehensive testing programs. Testing shall include: vulnerability assessments, security scans, open source analyses, penetration testing, TLPT (threat-led penetration testing).', 1300),
            ('Art-28', 'Third-party ICT service providers', 'Financial entities shall manage ICT third-party risk as integral part of ICT risk within ICT risk management framework. Contractual arrangements shall include: full description of services, security, access rights, right to audit, exit strategies.', 1500),
            ('Art-14', 'ICT business continuity policy', 'Financial entities shall have ICT business continuity policy including: response and recovery plans, backup policies, restoration and recovery procedures, crisis communication plan. Test at least annually or upon major changes.', 1250),
        ]
        
        for code, name, req, length in disclosures:
            ESRSDisclosure.objects.get_or_create(
                standard=std,
                code=code,
                standard_type='DORA',
                defaults={
                    'name': name,
                    'description': f'DORA {code}: {name}',
                    'requirement_text': req,
                    'order': len(disclosures),
                    'is_mandatory': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ DORA: 1 category, 1 standard, {len(disclosures)} disclosures'))

    def add_csddd(self):
        """CSDDD: Corporate Sustainability Due Diligence Directive"""
        self.stdout.write('📋 Adding CSDDD...')
        
        cat, _ = ESRSCategory.objects.get_or_create(
            code='DD',
            standard_type='CSDDD',
            defaults={
                'name': 'Due Diligence',
                'description': 'CSDDD - Corporate sustainability due diligence obligations',
                'order': 1
            }
        )
        
        std, _ = ESRSStandard.objects.get_or_create(
            code='CSDDD',
            standard_type='CSDDD',
            defaults={
                'category': cat,
                'name': 'Corporate Sustainability Due Diligence Directive',
                'description': 'EU Directive on corporate due diligence for sustainability',
                'order': 1
            }
        )
        
        disclosures = [
            ('Art-5', 'Due diligence policy', 'Companies shall adopt plan to integrate due diligence into policies and risk management systems, code of conduct describing rules for workers, description of due diligence processes, prioritisation criteria for addressing adverse impacts.', 1400),
            ('Art-6', 'Identification of actual and potential adverse impacts', 'Companies shall identify actual and potential adverse human rights and environmental impacts from own operations, subsidiaries and value chain (business partners). Assessment shall be updated: at least every 12 months, before new activities, business decisions, new business relationships.', 1500),
            ('Art-7', 'Prevention and mitigation of potential adverse impacts', 'Companies shall take appropriate measures to prevent or minimize potential adverse impacts: seeking contractual assurances from direct business partner, making investments, providing support and training, adapting purchasing practices, collaboration with other entities.', 1450),
            ('Art-8', 'Bringing actual adverse impacts to an end', 'When company identifies actual adverse impact, shall take appropriate measures: neutralise impact or minimize extent, where necessary seeking contractual assurances, adapting business plan, requesting business partner to prevent or minimize impact.', 1350),
            ('Art-15', 'Stakeholder engagement', 'Companies shall engage with stakeholders when assessing actual and potential adverse impacts and when devising prevention, mitigation, remediation and monitoring measures. Engagement shall be conducted: in timely manner, with stakeholders potentially affected or actually affected, having right to freedom of association.', 1400),
            ('Art-22', 'Climate change mitigation plan', 'Companies shall adopt transition plan for climate change mitigation ensuring business model and strategy compatible with transition to sustainable economy and limiting global warming to 1.5°C. Plan shall include: emission reduction targets, decarbonisation levers, role of management body, progress indicators.', 1500),
        ]
        
        for code, name, req, length in disclosures:
            ESRSDisclosure.objects.get_or_create(
                standard=std,
                code=code,
                standard_type='CSDDD',
                defaults={
                    'name': name,
                    'description': f'CSDDD {code}: {name}',
                    'requirement_text': req,
                    'order': len(disclosures),
                    'is_mandatory': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ CSDDD: 1 category, 1 standard, {len(disclosures)} disclosures'))

    def add_eu_taxonomy(self):
        """EU Taxonomy: Sustainable Finance Classification"""
        self.stdout.write('📋 Adding EU Taxonomy...')
        
        cat, _ = ESRSCategory.objects.get_or_create(
            code='TAX',
            standard_type='EUTaxonomy',
            defaults={
                'name': 'Sustainable Finance',
                'description': 'EU Taxonomy - Classification system for sustainable activities',
                'order': 1
            }
        )
        
        std, _ = ESRSStandard.objects.get_or_create(
            code='EUTaxonomy',
            standard_type='EUTaxonomy',
            defaults={
                'category': cat,
                'name': 'EU Taxonomy for Sustainable Activities',
                'description': 'Classification system establishing list of environmentally sustainable economic activities',
                'order': 1
            }
        )
        
        disclosures = [
            ('Art-3', 'Substantial contribution to environmental objectives', 'Economic activity shall be considered environmentally sustainable where it: (a) contributes substantially to one or more of 6 environmental objectives, (b) does not significantly harm any objectives (DNSH), (c) complies with minimum safeguards, (d) complies with technical screening criteria.', 1500),
            ('Art-9', 'Six environmental objectives', 'Environmental objectives are: 1) Climate change mitigation, 2) Climate change adaptation, 3) Sustainable use and protection of water and marine resources, 4) Transition to circular economy, 5) Pollution prevention and control, 6) Protection and restoration of biodiversity and ecosystems.', 1400),
            ('Art-8', 'Disclosure by undertakings', 'Undertakings shall disclose: (a) proportion of turnover derived from products/services associated with economic activities that qualify as environmentally sustainable (taxonomy-aligned), (b) proportion of CapEx related to such activities, (c) proportion of OpEx related to such activities.', 1450),
            ('Art-17', 'DNSH principle', 'Do No Significant Harm means activity must not: (a) significantly harm climate change mitigation, (b) significantly harm climate change adaptation, (c) significantly harm water and marine resources, (d) significantly harm circular economy, (e) significantly harm pollution prevention, (f) significantly harm biodiversity.', 1400),
            ('Art-18', 'Minimum safeguards', 'Minimum safeguards are procedures implemented by undertaking carrying out economic activity to ensure alignment with OECD Guidelines for Multinational Enterprises and UN Guiding Principles on Business and Human Rights, including ILO Core Labour Conventions.', 1300),
        ]
        
        for code, name, req, length in disclosures:
            ESRSDisclosure.objects.get_or_create(
                standard=std,
                code=code,
                standard_type='EUTaxonomy',
                defaults={
                    'name': name,
                    'description': f'EU Taxonomy {code}: {name}',
                    'requirement_text': req,
                    'order': len(disclosures),
                    'is_mandatory': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ EU Taxonomy: 1 category, 1 standard, {len(disclosures)} disclosures'))

    def print_summary(self):
        """Print database summary"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 DATABASE SUMMARY'))
        self.stdout.write('='*60)
        
        from django.db.models import Count
        
        # Count by standard type
        standard_types = ESRSStandard.objects.values('standard_type').annotate(
            standards=Count('id'),
            disclosures=Count('disclosures')
        ).order_by('standard_type')
        
        total_categories = ESRSCategory.objects.count()
        total_standards = ESRSStandard.objects.count()
        total_disclosures = ESRSDisclosure.objects.count()
        
        self.stdout.write(f'\n📋 Total Categories: {total_categories}')
        self.stdout.write(f'📋 Total Standards: {total_standards}')
        self.stdout.write(f'📋 Total Disclosures: {total_disclosures}\n')
        
        self.stdout.write('By Standard Type:')
        for st in standard_types:
            self.stdout.write(f"  • {st['standard_type']}: {st['standards']} standards, {st['disclosures']} disclosures")
        
        self.stdout.write('\n' + '='*60)
