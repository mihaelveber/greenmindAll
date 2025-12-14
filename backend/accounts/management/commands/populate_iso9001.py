from django.core.management.base import BaseCommand
from accounts.models import ESRSCategory, ESRSStandard, ESRSDisclosure


class Command(BaseCommand):
    help = 'Populate ISO 9001:2015 Quality Management System standard in database'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting ISO 9001:2015 population...')
        
        # Clear existing ISO 9001 data (keep ESRS data)
        ESRSDisclosure.objects.filter(standard_type='ISO9001').delete()
        ESRSStandard.objects.filter(standard_type='ISO9001').delete()
        ESRSCategory.objects.filter(standard_type='ISO9001').delete()
        
        total_requirements = 0
        
        # ==================== ISO 9001:2015 Structure ====================
        
        # Clause 4: Context of the Organization
        context = ESRSCategory.objects.create(
            standard_type='ISO9001',
            name='Context of the Organization',
            code='4',
            description='Understanding the organization and its context, needs of interested parties, and QMS scope',
            order=1
        )
        
        clause_4 = ESRSStandard.objects.create(
            standard_type='ISO9001',
            category=context,
            code='4',
            name='Context of the Organization',
            description='Determine external and internal issues, interested parties, and QMS scope',
            order=1
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard_type='ISO9001', standard=clause_4, code='4.1', 
                          name='Understanding the organization and its context',
                          description='Determine external and internal issues relevant to purpose and strategic direction',
                          requirement_text='The organization shall determine external and internal issues that are relevant to its purpose and its strategic direction and that affect its ability to achieve the intended result(s) of its quality management system.',
                          order=1),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_4, code='4.2', 
                          name='Understanding the needs and expectations of interested parties',
                          description='Determine interested parties and their requirements relevant to QMS',
                          requirement_text='The organization shall determine: a) the interested parties that are relevant to the quality management system; b) the requirements of these interested parties that are relevant to the quality management system.',
                          order=2),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_4, code='4.3', 
                          name='Determining the scope of the QMS',
                          description='Establish boundaries and applicability of the QMS',
                          requirement_text='The organization shall determine the boundaries and applicability of the quality management system to establish its scope. When determining this scope, the organization shall consider: a) the external and internal issues; b) the requirements of relevant interested parties; c) the products and services of the organization.',
                          order=3),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_4, code='4.4', 
                          name='Quality management system and its processes',
                          description='Establish, implement, maintain and continually improve the QMS',
                          requirement_text='The organization shall establish, implement, maintain and continually improve a quality management system, including the processes needed and their interactions.',
                          order=4),
        ])
        total_requirements += 4
        
        # Clause 5: Leadership
        leadership = ESRSCategory.objects.create(
            standard_type='ISO9001',
            name='Leadership',
            code='5',
            description='Leadership commitment, customer focus, quality policy, and organizational roles',
            order=2
        )
        
        clause_5 = ESRSStandard.objects.create(
            standard_type='ISO9001',
            category=leadership,
            code='5',
            name='Leadership',
            description='Top management commitment, customer focus, and organizational responsibilities',
            order=1
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard_type='ISO9001', standard=clause_5, code='5.1', 
                          name='Leadership and commitment',
                          description='Top management demonstrates leadership and commitment to QMS',
                          requirement_text='Top management shall demonstrate leadership and commitment with respect to the quality management system by: a) taking accountability for the effectiveness of the QMS; b) ensuring quality policy and objectives are established; c) ensuring integration of QMS into business processes; d) promoting process approach and risk-based thinking.',
                          order=1),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_5, code='5.1.1', 
                          name='General leadership commitment',
                          description='Overall leadership and commitment requirements',
                          requirement_text='Top management shall take accountability for the effectiveness of the quality management system.',
                          order=2),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_5, code='5.1.2', 
                          name='Customer focus',
                          description='Top management ensures customer focus is maintained',
                          requirement_text='Top management shall demonstrate leadership and commitment with respect to customer focus by ensuring that: a) customer and applicable statutory and regulatory requirements are determined, understood and consistently met; b) risks and opportunities that can affect conformity of products and services are determined and addressed; c) the focus on enhancing customer satisfaction is maintained.',
                          order=3),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_5, code='5.2', 
                          name='Quality policy',
                          description='Establish, implement and communicate quality policy',
                          requirement_text='Top management shall establish, implement and maintain a quality policy that: a) is appropriate to the purpose and context; b) provides framework for quality objectives; c) includes commitment to satisfy applicable requirements; d) includes commitment to continual improvement.',
                          order=4),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_5, code='5.3', 
                          name='Organizational roles, responsibilities and authorities',
                          description='Assign and communicate responsibilities and authorities',
                          requirement_text='Top management shall ensure that the responsibilities and authorities for relevant roles are assigned, communicated and understood within the organization.',
                          order=5),
        ])
        total_requirements += 5
        
        # Clause 6: Planning
        planning = ESRSCategory.objects.create(
            standard_type='ISO9001',
            name='Planning',
            code='6',
            description='Risk management, quality objectives, and planning of changes',
            order=3
        )
        
        clause_6 = ESRSStandard.objects.create(
            standard_type='ISO9001',
            category=planning,
            code='6',
            name='Planning',
            description='Actions to address risks and opportunities, quality objectives, and change management',
            order=1
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard_type='ISO9001', standard=clause_6, code='6.1', 
                          name='Actions to address risks and opportunities',
                          description='Determine and address risks and opportunities',
                          requirement_text='When planning for the quality management system, the organization shall consider the issues and requirements and determine the risks and opportunities that need to be addressed to: a) give assurance that the QMS can achieve its intended result(s); b) enhance desirable effects; c) prevent, or reduce, undesired effects; d) achieve improvement.',
                          order=1),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_6, code='6.2', 
                          name='Quality objectives and planning to achieve them',
                          description='Establish quality objectives and plans to achieve them',
                          requirement_text='The organization shall establish quality objectives at relevant functions, levels and processes. Quality objectives shall: a) be consistent with the quality policy; b) be measurable; c) take into account applicable requirements; d) be relevant to conformity of products and services; e) be monitored; f) be communicated; g) be updated as appropriate.',
                          order=2),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_6, code='6.3', 
                          name='Planning of changes',
                          description='Plan and control changes to QMS',
                          requirement_text='When the organization determines the need for changes to the quality management system, the changes shall be carried out in a planned manner.',
                          order=3),
        ])
        total_requirements += 3
        
        # Clause 7: Support
        support = ESRSCategory.objects.create(
            standard_type='ISO9001',
            name='Support',
            code='7',
            description='Resources, competence, awareness, communication, and documented information',
            order=4
        )
        
        clause_7 = ESRSStandard.objects.create(
            standard_type='ISO9001',
            category=support,
            code='7',
            name='Support',
            description='Resources, personnel, infrastructure, environment, monitoring, competence, awareness, communication, and documentation',
            order=1
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard_type='ISO9001', standard=clause_7, code='7.1', 
                          name='Resources',
                          description='Determine and provide resources needed for QMS',
                          requirement_text='The organization shall determine and provide the resources needed for the establishment, implementation, maintenance and continual improvement of the quality management system.',
                          order=1),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_7, code='7.1.1', 
                          name='General resources',
                          description='Consider capabilities and constraints on existing resources',
                          requirement_text='The organization shall consider capabilities of, and constraints on, existing internal resources, and what needs to be obtained from external providers.',
                          order=2),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_7, code='7.1.2', 
                          name='People',
                          description='Determine and provide persons necessary for QMS',
                          requirement_text='The organization shall determine and provide the persons necessary for the effective implementation of its quality management system and for the operation and control of its processes.',
                          order=3),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_7, code='7.1.3', 
                          name='Infrastructure',
                          description='Determine, provide and maintain infrastructure',
                          requirement_text='The organization shall determine, provide and maintain the infrastructure necessary for the operation of its processes and to achieve conformity of products and services.',
                          order=4),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_7, code='7.1.4', 
                          name='Environment for the operation of processes',
                          description='Determine, provide and maintain suitable environment',
                          requirement_text='The organization shall determine, provide and maintain the environment necessary for the operation of its processes and to achieve conformity of products and services.',
                          order=5),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_7, code='7.1.5', 
                          name='Monitoring and measuring resources',
                          description='Determine and provide monitoring and measurement resources',
                          requirement_text='The organization shall determine and provide the resources needed to ensure valid and reliable results when monitoring or measuring is used to verify the conformity of products and services to requirements.',
                          order=6),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_7, code='7.2', 
                          name='Competence',
                          description='Determine, ensure and maintain competence',
                          requirement_text='The organization shall: a) determine the necessary competence of person(s); b) ensure that these persons are competent; c) where applicable, take actions to acquire the necessary competence; d) retain appropriate documented information as evidence of competence.',
                          order=7),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_7, code='7.3', 
                          name='Awareness',
                          description='Ensure awareness of quality policy, objectives, and contribution',
                          requirement_text='The organization shall ensure that persons doing work under the organization\'s control are aware of: a) the quality policy; b) relevant quality objectives; c) their contribution to the effectiveness of the QMS; d) the implications of not conforming with QMS requirements.',
                          order=8),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_7, code='7.4', 
                          name='Communication',
                          description='Determine internal and external communications',
                          requirement_text='The organization shall determine the internal and external communications relevant to the quality management system, including: a) on what it will communicate; b) when to communicate; c) with whom to communicate; d) how to communicate; e) who communicates.',
                          order=9),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_7, code='7.5', 
                          name='Documented information',
                          description='Create, update and control documented information',
                          requirement_text='The organization\'s quality management system shall include: a) documented information required by this International Standard; b) documented information determined by the organization as being necessary for the effectiveness of the QMS.',
                          order=10),
        ])
        total_requirements += 10
        
        # Clause 8: Operation
        operation = ESRSCategory.objects.create(
            standard_type='ISO9001',
            name='Operation',
            code='8',
            description='Operational planning, customer requirements, design, production, and release of products/services',
            order=5
        )
        
        clause_8 = ESRSStandard.objects.create(
            standard_type='ISO9001',
            category=operation,
            code='8',
            name='Operation',
            description='Planning and control of operations, product/service requirements, design, production, and delivery',
            order=1
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard_type='ISO9001', standard=clause_8, code='8.1', 
                          name='Operational planning and control',
                          description='Plan, implement and control processes to meet requirements',
                          requirement_text='The organization shall plan, implement and control the processes needed to meet the requirements for the provision of products and services, and to implement the actions determined in Clause 6.',
                          order=1),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_8, code='8.2', 
                          name='Requirements for products and services',
                          description='Determine, review and meet customer requirements',
                          requirement_text='The organization shall determine, review and meet requirements for products and services to be offered to customers.',
                          order=2),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_8, code='8.3', 
                          name='Design and development of products and services',
                          description='Establish, implement and maintain design and development process',
                          requirement_text='The organization shall establish, implement and maintain a design and development process that is appropriate to ensure the subsequent provision of products and services.',
                          order=3),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_8, code='8.4', 
                          name='Control of externally provided processes, products and services',
                          description='Ensure externally provided processes/products/services conform to requirements',
                          requirement_text='The organization shall ensure that externally provided processes, products and services conform to requirements.',
                          order=4),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_8, code='8.5', 
                          name='Production and service provision',
                          description='Carry out production and service provision under controlled conditions',
                          requirement_text='The organization shall implement production and service provision under controlled conditions.',
                          order=5),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_8, code='8.6', 
                          name='Release of products and services',
                          description='Verify that product/service requirements have been met',
                          requirement_text='The organization shall implement planned arrangements at appropriate stages to verify that the product and service requirements have been met.',
                          order=6),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_8, code='8.7', 
                          name='Control of nonconforming outputs',
                          description='Identify and control nonconforming outputs',
                          requirement_text='The organization shall ensure that outputs that do not conform to their requirements are identified and controlled to prevent their unintended use or delivery.',
                          order=7),
        ])
        total_requirements += 7
        
        # Clause 9: Performance Evaluation
        performance = ESRSCategory.objects.create(
            standard_type='ISO9001',
            name='Performance Evaluation',
            code='9',
            description='Monitoring, measurement, analysis, internal audit, and management review',
            order=6
        )
        
        clause_9 = ESRSStandard.objects.create(
            standard_type='ISO9001',
            category=performance,
            code='9',
            name='Performance Evaluation',
            description='Monitoring, measurement, analysis, evaluation, internal audit, and management review',
            order=1
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard_type='ISO9001', standard=clause_9, code='9.1', 
                          name='Monitoring, measurement, analysis and evaluation',
                          description='Determine what needs to be monitored and measured',
                          requirement_text='The organization shall determine: a) what needs to be monitored and measured; b) the methods for monitoring, measurement, analysis and evaluation; c) when monitoring and measuring shall be performed; d) when the results shall be analyzed and evaluated.',
                          order=1),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_9, code='9.1.1', 
                          name='General monitoring and measurement',
                          description='Evaluate QMS performance and effectiveness',
                          requirement_text='The organization shall evaluate the performance and the effectiveness of the quality management system.',
                          order=2),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_9, code='9.1.2', 
                          name='Customer satisfaction',
                          description='Monitor customer perceptions and satisfaction',
                          requirement_text='The organization shall monitor customers\' perceptions of the degree to which their needs and expectations have been fulfilled.',
                          order=3),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_9, code='9.1.3', 
                          name='Analysis and evaluation',
                          description='Analyze and evaluate monitoring and measurement data',
                          requirement_text='The organization shall analyze and evaluate appropriate data and information arising from monitoring and measurement.',
                          order=4),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_9, code='9.2', 
                          name='Internal audit',
                          description='Conduct internal audits at planned intervals',
                          requirement_text='The organization shall conduct internal audits at planned intervals to provide information on whether the quality management system: a) conforms to requirements; b) is effectively implemented and maintained.',
                          order=5),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_9, code='9.3', 
                          name='Management review',
                          description='Top management reviews QMS at planned intervals',
                          requirement_text='Top management shall review the organization\'s quality management system, at planned intervals, to ensure its continuing suitability, adequacy, effectiveness and alignment with the strategic direction.',
                          order=6),
        ])
        total_requirements += 6
        
        # Clause 10: Improvement
        improvement = ESRSCategory.objects.create(
            standard_type='ISO9001',
            name='Improvement',
            code='10',
            description='Nonconformity, corrective action, and continual improvement',
            order=7
        )
        
        clause_10 = ESRSStandard.objects.create(
            standard_type='ISO9001',
            category=improvement,
            code='10',
            name='Improvement',
            description='Nonconformity, corrective action, and continual improvement of QMS',
            order=1
        )
        
        ESRSDisclosure.objects.bulk_create([
            ESRSDisclosure(standard_type='ISO9001', standard=clause_10, code='10.1', 
                          name='General improvement',
                          description='Determine and select opportunities for improvement',
                          requirement_text='The organization shall determine and select opportunities for improvement and implement any necessary actions to meet customer requirements and enhance customer satisfaction.',
                          order=1),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_10, code='10.2', 
                          name='Nonconformity and corrective action',
                          description='React to nonconformity and take corrective action',
                          requirement_text='When a nonconformity occurs, the organization shall: a) react to the nonconformity; b) evaluate the need for action to eliminate the cause(s); c) implement any action needed; d) review the effectiveness of any corrective action taken; e) update risks and opportunities; f) make changes to the QMS, if necessary.',
                          order=2),
            ESRSDisclosure(standard_type='ISO9001', standard=clause_10, code='10.3', 
                          name='Continual improvement',
                          description='Continually improve suitability, adequacy and effectiveness of QMS',
                          requirement_text='The organization shall continually improve the suitability, adequacy and effectiveness of the quality management system.',
                          order=3),
        ])
        total_requirements += 3
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created 7 ISO 9001 categories'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created 7 ISO 9001 clauses'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {total_requirements} ISO 9001 requirements'))
        self.stdout.write(self.style.SUCCESS('ISO 9001:2015 QMS population complete!'))
