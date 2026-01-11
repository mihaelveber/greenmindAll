"""
Management command to add 10 most important EU/Slovenia standards and regulations
Run: python manage.py add_eu_standards
"""
from django.core.management.base import BaseCommand
from accounts.models import ESRSCategory, ESRSStandard, ESRSDisclosure


class Command(BaseCommand):
    help = 'Add 10 most important EU/Slovenia standards and regulations for companies'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Adding EU/Slovenia standards...'))
        
        standards_data = [
            {
                'type': 'ISO14001',
                'category_name': 'Environmental Management',
                'category_desc': 'ISO 14001 - Environmental Management System standard for reducing environmental impact',
                'standards': [
                    {
                        'code': 'ISO14001',
                        'name': 'Environmental Management System',
                        'description': 'ISO 14001 helps organizations improve their environmental performance through more efficient use of resources and reduction of waste',
                        'disclosures': [
                            {'code': '4.1', 'name': 'Understanding the organization and its context', 'requirement': 'Determine external and internal issues relevant to environmental management'},
                            {'code': '4.2', 'name': 'Understanding needs and expectations of interested parties', 'requirement': 'Identify interested parties and their environmental requirements'},
                            {'code': '6.1', 'name': 'Actions to address risks and opportunities', 'requirement': 'Plan actions to address environmental risks and opportunities'},
                            {'code': '7.1', 'name': 'Resources', 'requirement': 'Provide resources needed for environmental management system'},
                            {'code': '8.1', 'name': 'Operational planning and control', 'requirement': 'Establish controls for processes affecting environmental performance'},
                        ]
                    }
                ]
            },
            {
                'type': 'ISO27001',
                'category_name': 'Information Security',
                'category_desc': 'ISO 27001 - Information Security Management System for protecting sensitive company information',
                'standards': [
                    {
                        'code': 'ISO27001',
                        'name': 'Information Security Management',
                        'description': 'ISO 27001 provides requirements for establishing, implementing, maintaining and continually improving information security management',
                        'disclosures': [
                            {'code': 'A.5', 'name': 'Information security policies', 'requirement': 'Define and communicate information security policies'},
                            {'code': 'A.6', 'name': 'Organization of information security', 'requirement': 'Establish management framework for information security'},
                            {'code': 'A.8', 'name': 'Asset management', 'requirement': 'Identify and protect organizational assets'},
                            {'code': 'A.9', 'name': 'Access control', 'requirement': 'Limit access to information and systems'},
                            {'code': 'A.12', 'name': 'Operations security', 'requirement': 'Ensure correct and secure operations of information processing'},
                        ]
                    }
                ]
            },
            {
                'type': 'ISO45001',
                'category_name': 'Occupational Health & Safety',
                'category_desc': 'ISO 45001 - Occupational Health and Safety Management System for safe workplaces',
                'standards': [
                    {
                        'code': 'ISO45001',
                        'name': 'OH&S Management System',
                        'description': 'ISO 45001 helps organizations improve employee safety, reduce workplace risks and create better working conditions',
                        'disclosures': [
                            {'code': '4.1', 'name': 'Understanding the organization', 'requirement': 'Determine internal and external issues affecting OH&S management'},
                            {'code': '5.1', 'name': 'Leadership and commitment', 'requirement': 'Demonstrate leadership commitment to OH&S management'},
                            {'code': '6.1', 'name': 'Actions to address risks', 'requirement': 'Identify and assess OH&S risks and opportunities'},
                            {'code': '8.1', 'name': 'Operational planning', 'requirement': 'Plan, implement and control processes for OH&S requirements'},
                            {'code': '9.1', 'name': 'Monitoring and measurement', 'requirement': 'Monitor, measure and evaluate OH&S performance'},
                        ]
                    }
                ]
            },
            {
                'type': 'ISO50001',
                'category_name': 'Energy Management',
                'category_desc': 'ISO 50001 - Energy Management System for reducing energy consumption and costs',
                'standards': [
                    {
                        'code': 'ISO50001',
                        'name': 'Energy Management System',
                        'description': 'ISO 50001 helps organizations develop systems and processes to improve energy performance including energy efficiency and consumption',
                        'disclosures': [
                            {'code': '4.1', 'name': 'Understanding the organization', 'requirement': 'Determine issues affecting energy management system'},
                            {'code': '6.3', 'name': 'Energy review', 'requirement': 'Conduct energy review to establish baseline and identify opportunities'},
                            {'code': '6.4', 'name': 'Energy performance indicators', 'requirement': 'Determine and monitor energy performance indicators'},
                            {'code': '8.1', 'name': 'Operational control', 'requirement': 'Plan and control operations affecting energy performance'},
                            {'code': '9.1', 'name': 'Monitoring and analysis', 'requirement': 'Monitor and analyze energy performance'},
                        ]
                    }
                ]
            },
            {
                'type': 'GDPR',
                'category_name': 'Data Protection',
                'category_desc': 'GDPR - General Data Protection Regulation for personal data protection (EU mandatory)',
                'standards': [
                    {
                        'code': 'Ch-I',
                        'name': 'Chapter I - General Provisions',
                        'description': 'Defines scope, material and territorial application, and key definitions for GDPR compliance',
                        'disclosures': [
                            {'code': 'Art.4', 'name': 'Definitions', 'requirement': '''Key definitions for GDPR compliance:
• Personal data: any information relating to an identified or identifiable natural person
• Processing: any operation performed on personal data (collection, storage, use, disclosure, deletion)
• Controller: determines purposes and means of processing
• Processor: processes data on behalf of controller
• Consent: freely given, specific, informed and unambiguous indication of wishes
• Data breach: breach of security leading to accidental or unlawful destruction, loss, alteration, unauthorized disclosure
• Filing system: any structured set of personal data accessible according to specific criteria'''},
                        ]
                    },
                    {
                        'code': 'Ch-II',
                        'name': 'Chapter II - Principles',
                        'description': 'Core principles for lawful, fair and transparent data processing',
                        'disclosures': [
                            {'code': 'Art.5', 'name': 'Principles relating to processing of personal data', 'requirement': '''Personal data must be:
(a) Processed lawfully, fairly and in a transparent manner (lawfulness, fairness and transparency)
(b) Collected for specified, explicit and legitimate purposes (purpose limitation)
(c) Adequate, relevant and limited to what is necessary (data minimisation)
(d) Accurate and kept up to date (accuracy)
(e) Kept in a form which permits identification only as long as necessary (storage limitation)
(f) Processed in a manner that ensures appropriate security (integrity and confidentiality)

Controller is responsible for and must be able to demonstrate compliance (accountability).'''},
                            
                            {'code': 'Art.6', 'name': 'Lawfulness of processing', 'requirement': '''Processing is lawful only if at least one of the following applies:
(a) Data subject has given consent for specific purposes
(b) Processing is necessary for performance of a contract
(c) Processing is necessary for compliance with legal obligation
(d) Processing is necessary to protect vital interests of data subject
(e) Processing is necessary for public interest or official authority
(f) Processing is necessary for legitimate interests pursued by controller (except where overridden by data subject interests)

Additional conditions apply for public authorities and children's data.'''},
                            
                            {'code': 'Art.7', 'name': 'Conditions for consent', 'requirement': '''When processing is based on consent:
(1) Controller must be able to demonstrate that data subject has consented
(2) Request for consent must be clearly distinguishable, intelligible, easily accessible, and in clear and plain language
(3) Data subject has right to withdraw consent at any time (as easy to withdraw as to give)
(4) When assessing if consent is freely given, account whether performance of contract is conditional on consent

For children: consent requires parental authorization (under age 16, or lower as set by Member States).'''},
                            
                            {'code': 'Art.9', 'name': 'Processing of special categories of personal data', 'requirement': '''PROHIBITED to process data revealing:
• Racial or ethnic origin
• Political opinions
• Religious or philosophical beliefs
• Trade union membership
• Genetic data, biometric data for uniquely identifying a person
• Health data
• Data concerning sex life or sexual orientation

EXCEPTIONS when:
(a) Explicit consent given
(b) Necessary for employment/social security obligations
(c) Vital interests and data subject incapable of giving consent
(d) Processing by foundation/association for legitimate activities with appropriate safeguards
(e) Data manifestly made public by data subject
(f) Legal claims or judicial acts
(g) Substantial public interest with EU or Member State law
(h) Preventive/occupational medicine, medical diagnosis, health/social care
(i) Public health interests (communicable diseases, quality/safety of healthcare)
(j) Archiving, research, statistics with appropriate safeguards'''},
                        ]
                    },
                    {
                        'code': 'Ch-III',
                        'name': 'Chapter III - Rights of the Data Subject',
                        'description': 'Individual rights to control their personal data (transparency, access, rectification, erasure, portability)',
                        'disclosures': [
                            {'code': 'Art.12', 'name': 'Transparent information, communication and modalities', 'requirement': '''Controller shall provide information and communications in:
• Concise, transparent, intelligible and easily accessible form
• Clear and plain language (especially for children)
• Free of charge (unless requests are manifestly unfounded or excessive)
• Within one month of request (extendable by 2 months if complex)

Controller shall facilitate exercise of data subject rights and may not refuse to act unless able to demonstrate manifestly unfounded or excessive request.'''},
                            
                            {'code': 'Art.13', 'name': 'Information to be provided when data collected from data subject', 'requirement': '''At the time data is obtained, controller shall provide data subject with:

IDENTITY & CONTACT:
• Identity and contact details of controller
• Contact details of data protection officer (if applicable)
• Purposes of processing and legal basis
• Legitimate interests (if Art.6(1)(f) applies)

RECIPIENTS & TRANSFERS:
• Categories of recipients of personal data
• Intention to transfer to third country (safeguards)

RETENTION & RIGHTS:
• Period for which data will be stored
• Right to request access, rectification, erasure, restriction
• Right to withdraw consent at any time
• Right to lodge complaint with supervisory authority

ADDITIONAL:
• Whether providing data is statutory/contractual requirement or necessary to enter contract
• Whether data subject obliged to provide data and consequences of failure
• Existence of automated decision-making including profiling (logic involved, significance and envisaged consequences)'''},
                            
                            {'code': 'Art.15', 'name': 'Right of access by the data subject', 'requirement': '''Data subject has right to obtain from controller:

CONFIRMATION of whether personal data is being processed

IF YES, ACCESS TO:
• Purposes of processing
• Categories of personal data concerned
• Recipients or categories of recipients
• Envisaged period of storage (or criteria for determining period)
• Rights (rectification, erasure, restriction, objection)
• Right to lodge complaint with supervisory authority
• Source of data (if not collected from data subject)
• Existence of automated decision-making including profiling
• Safeguards for transfers to third countries

COPY: Data subject entitled to free copy of personal data undergoing processing. For additional copies, controller may charge reasonable fee based on administrative costs.'''},
                            
                            {'code': 'Art.16', 'name': 'Right to rectification', 'requirement': '''Data subject has right to obtain from controller without undue delay:
• Rectification of inaccurate personal data
• Completion of incomplete personal data (by providing supplementary statement)

Taking into account purposes of processing, data subject has right to have incomplete personal data completed.'''},
                            
                            {'code': 'Art.17', 'name': 'Right to erasure ("right to be forgotten")', 'requirement': '''Data subject has right to obtain erasure of personal data without undue delay where:

(a) Data no longer necessary for purposes for which collected
(b) Data subject withdraws consent and no other legal ground exists
(c) Data subject objects under Art.21(1) and no overriding legitimate grounds
(d) Personal data unlawfully processed
(e) Erasure required for compliance with legal obligation in EU or Member State law
(f) Data collected for information society services offered directly to children

WHERE CONTROLLER HAS MADE DATA PUBLIC:
Controller must take reasonable steps (including technical measures) to inform other controllers processing the data that data subject has requested erasure of links to, copies or replications of that data.

EXCEPTIONS (right does not apply where processing necessary for):
(a) Freedom of expression and information
(b) Compliance with legal obligation or public interest/official authority
(c) Public health interests
(d) Archiving, research or statistical purposes (with safeguards)
(e) Establishment, exercise or defence of legal claims'''},
                            
                            {'code': 'Art.18', 'name': 'Right to restriction of processing', 'requirement': '''Data subject has right to obtain restriction of processing where:
(a) Accuracy of data is contested (for period enabling controller to verify accuracy)
(b) Processing is unlawful and data subject opposes erasure and requests restriction instead
(c) Controller no longer needs data but data subject requires it for legal claims
(d) Data subject has objected to processing under Art.21(1) pending verification of whether legitimate grounds override

WHERE RESTRICTION: Personal data shall only be processed (with data subject consent or) for:
• Establishment, exercise or defence of legal claims
• Protection of rights of another person
• Reasons of important public interest

Before lifting restriction, data subject must be informed.'''},
                            
                            {'code': 'Art.20', 'name': 'Right to data portability', 'requirement': '''Data subject has right to receive personal data in structured, commonly used and machine-readable format and right to transmit to another controller where:
(a) Processing is based on consent (Art.6(1)(a) or Art.9(2)(a)) or contract (Art.6(1)(b))
(b) Processing is carried out by automated means

Data subject has right to have data transmitted directly from one controller to another where technically feasible.

RIGHT SHALL NOT ADVERSELY AFFECT:
• Rights and freedoms of others

RIGHT DOES NOT APPLY TO:
• Processing necessary for public interest or official authority vested in controller'''},
                            
                            {'code': 'Art.21', 'name': 'Right to object', 'requirement': '''Data subject has right to object, on grounds relating to particular situation, to processing based on:
• Art.6(1)(e) (public interest/official authority)
• Art.6(1)(f) (legitimate interests)

Controller must no longer process unless demonstrates compelling legitimate grounds which override interests/rights/freedoms of data subject OR for establishment/exercise/defence of legal claims.

DIRECT MARKETING:
Where processing for direct marketing, data subject has RIGHT TO OBJECT AT ANY TIME. If objected, personal data shall NO LONGER be processed for such purposes.

At latest at first communication, right shall be explicitly brought to attention and presented clearly and separately from other information.

INFORMATION SOCIETY SERVICES:
Right may be exercised by automated means using technical specifications.

SCIENTIFIC/HISTORICAL RESEARCH OR STATISTICS:
Data subject has right to object on grounds relating to particular situation unless processing necessary for public interest task.'''},
                            
                            {'code': 'Art.22', 'name': 'Automated individual decision-making, including profiling', 'requirement': '''Data subject has right not to be subject to decision based solely on automated processing (including profiling) which produces legal effects or similarly significantly affects them.

EXCEPTIONS - does not apply if decision:
(a) Necessary for entering into or performing contract between data subject and controller
(b) Authorized by EU or Member State law (with suitable safeguards)
(c) Based on data subject's explicit consent

IN CASES (a) AND (c): controller must implement suitable measures to safeguard data subject's rights and freedoms:
• Right to obtain human intervention on part of controller
• Right to express point of view
• Right to contest the decision

SPECIAL CATEGORIES:
Automated decisions based on special category data (Art.9(1)) shall not be based solely on automated processing UNLESS:
• Explicit consent given OR
• Processing necessary for substantial public interest with appropriate safeguards'''},
                        ]
                    },
                    {
                        'code': 'Ch-IV',
                        'name': 'Chapter IV - Controller and Processor',
                        'description': 'Obligations and responsibilities for data controllers and processors',
                        'disclosures': [
                            {'code': 'Art.24', 'name': 'Responsibility of the controller', 'requirement': '''Controller shall implement appropriate technical and organisational measures to ensure and demonstrate processing in accordance with GDPR (accountability).

Measures shall take into account:
• Nature, scope, context and purposes of processing
• Risks of varying likelihood and severity for rights and freedoms

Measures shall be reviewed and updated where necessary.

CODES OF CONDUCT (Art.40) and CERTIFICATION (Art.42) may be used to demonstrate compliance.'''},
                            
                            {'code': 'Art.25', 'name': 'Data protection by design and by default', 'requirement': '''BY DESIGN: Taking into account state of the art, cost, nature/scope/context/purposes, and risks, controller shall implement appropriate technical and organisational measures designed to:
• Implement data protection principles effectively (e.g. data minimisation)
• Integrate necessary safeguards into processing
Both at time of determining means of processing AND at time of processing itself

BY DEFAULT: Controller shall implement measures to ensure that by default:
• Only personal data necessary for each specific purpose is processed
• Applies to amount of data collected, extent of processing, period of storage, accessibility
• Personal data is not made accessible to indefinite number of persons without individual's intervention

CERTIFICATION mechanisms (Art.42) may demonstrate compliance.'''},
                            
                            {'code': 'Art.28', 'name': 'Processor', 'requirement': '''Controller shall use ONLY processors providing sufficient guarantees to implement appropriate technical and organisational measures meeting GDPR requirements and ensuring protection of data subject rights.

PROCESSOR SHALL NOT engage another processor without prior specific or general written authorisation of controller.

PROCESSING BY PROCESSOR governed by CONTRACT or other legal act binding processor to controller:
• Subject-matter and duration of processing
• Nature and purpose of processing
• Type of personal data and categories of data subjects
• Obligations and rights of controller

CONTRACT MUST STIPULATE PROCESSOR SHALL:
(a) Process only on documented instructions from controller
(b) Ensure persons authorised to process have committed to confidentiality
(c) Take measures required under Art.32 (security of processing)
(d) Respect conditions for engaging another processor
(e) Taking into account nature of processing, assist controller in ensuring compliance with obligations (Art.32-36)
(f) Delete or return all personal data after end of services (unless required to store)
(g) Make available to controller all information necessary to demonstrate compliance
(h) Allow for and contribute to audits conducted by controller or auditor

Where processor determines purposes and means, processor shall be considered controller and subject to GDPR rules.'''},
                            
                            {'code': 'Art.30', 'name': 'Records of processing activities', 'requirement': '''CONTROLLER shall maintain record of processing activities containing:
(a) Name and contact details of controller (and joint controller, representative, DPO)
(b) Purposes of processing
(c) Description of categories of data subjects and personal data
(d) Categories of recipients (including in third countries/international organisations)
(e) Transfers to third country (documentation of safeguards)
(f) Envisaged time limits for erasure of categories of data
(g) General description of technical and organisational security measures (Art.32(1))

PROCESSOR shall maintain record containing:
(a) Name and contact details of processor(s), controllers, representatives, DPO
(b) Categories of processing carried out on behalf of each controller
(c) Transfers to third country (documentation of safeguards)
(d) General description of technical and organisational security measures

Records shall be IN WRITING (including electronic form).

EXCEPTION: Organisation with fewer than 250 employees (unless processing likely to result in risk, not occasional, or includes special categories/criminal data).

Records shall be MADE AVAILABLE to supervisory authority on request.'''},
                            
                            {'code': 'Art.32', 'name': 'Security of processing', 'requirement': '''Controller and processor shall implement appropriate technical and organisational measures to ensure security appropriate to risk, including:
(a) Pseudonymisation and encryption of personal data
(b) Ability to ensure ongoing confidentiality, integrity, availability and resilience of processing systems
(c) Ability to restore availability and access to data in timely manner after physical/technical incident
(d) Process for regularly testing, assessing and evaluating effectiveness of security measures

In assessing appropriate level of security, account shall be taken of:
• State of the art
• Costs of implementation
• Nature, scope, context and purposes of processing
• Risk of varying likelihood and severity for rights and freedoms (accidental/unlawful destruction, loss, alteration, unauthorised disclosure/access)

ADHERENCE to approved code of conduct (Art.40) or certification mechanism (Art.42) may demonstrate compliance.

PROCESSOR: Controller and processor shall ensure persons authorised to process have committed themselves to confidentiality or are under statutory obligation of confidentiality.'''},
                            
                            {'code': 'Art.33', 'name': 'Notification of a personal data breach to the supervisory authority', 'requirement': '''In case of personal data breach, controller shall WITHOUT UNDUE DELAY and WHERE FEASIBLE NOT LATER THAN 72 HOURS after becoming aware, notify supervisory authority UNLESS breach unlikely to result in risk to rights and freedoms.

If notification not made within 72 hours, shall be accompanied by REASONS FOR DELAY.

NOTIFICATION SHALL CONTAIN:
(a) Nature of breach (categories and approximate number of data subjects, records)
(b) Name and contact details of DPO or other contact point
(c) Likely consequences of breach
(d) Measures taken or proposed to address breach and mitigate possible adverse effects

If information cannot be provided at same time, may be provided in phases without undue further delay.

DOCUMENTATION: Controller shall document all breaches (facts, effects, remedial action) to enable supervisory authority to verify compliance.

PROCESSOR: Where processor becomes aware of breach, shall notify controller without undue delay.'''},
                            
                            {'code': 'Art.34', 'name': 'Communication of a personal data breach to the data subject', 'requirement': '''When breach likely to result in HIGH RISK to rights and freedoms, controller shall communicate breach to data subject WITHOUT UNDUE DELAY.

COMMUNICATION shall describe in CLEAR AND PLAIN LANGUAGE:
(a) Nature of breach
(b) Name and contact details of DPO or other contact point
(c) Likely consequences of breach
(d) Measures taken or proposed to address breach and mitigate adverse effects

COMMUNICATION NOT REQUIRED if:
(a) Controller implemented appropriate technical/organisational protection measures (encryption) rendering data unintelligible to unauthorised persons
(b) Controller taken subsequent measures ensuring high risk no longer likely to materialise
(c) Would involve disproportionate effort → public communication or similar measure

If controller has not already communicated breach to data subject, supervisory authority may require it if considers breach likely to result in high risk.'''},
                            
                            {'code': 'Art.35', 'name': 'Data protection impact assessment', 'requirement': '''Where processing likely to result in HIGH RISK, controller shall carry out ASSESSMENT of impact of envisaged processing operations (DPIA) BEFORE processing.

REQUIRED in particular for:
(a) Systematic and extensive evaluation based on automated processing (including profiling) producing legal effects or similarly significantly affecting individuals
(b) Processing on large scale of special categories (Art.9(1)) or personal data relating to criminal convictions (Art.10)
(c) Systematic monitoring of publicly accessible area on large scale

DPIA shall contain at least:
(a) Systematic description of envisaged processing operations and purposes (including legitimate interests)
(b) Assessment of necessity and proportionality of operations in relation to purposes
(c) Assessment of risks to rights and freedoms of data subjects
(d) Measures envisaged to address risks (safeguards, security measures, mechanisms to ensure protection, demonstrating compliance)

PRIOR CONSULTATION (Art.36) required if DPIA indicates high risk in absence of measures to mitigate risk.

Controller shall seek views of DATA SUBJECTS or their representatives where appropriate.

DPIA may address multiple similar processing operations with similar high risks.'''},
                            
                            {'code': 'Art.37', 'name': 'Designation of the data protection officer', 'requirement': '''Controller and processor shall designate DATA PROTECTION OFFICER (DPO) where:

(a) Processing carried out by PUBLIC AUTHORITY or body (except courts acting in judicial capacity)

(b) Core activities consist of processing operations requiring REGULAR AND SYSTEMATIC MONITORING of data subjects on LARGE SCALE

(c) Core activities consist of processing on LARGE SCALE of SPECIAL CATEGORIES (Art.9) or personal data relating to criminal convictions (Art.10)

GROUP: Single DPO may be designated for group of undertakings (accessible from each establishment).

PUBLIC AUTHORITIES: May designate single DPO for several authorities taking into account organisational structure and size.

WHERE NOT REQUIRED: Controller/processor or associations may or shall designate DPO on voluntary basis or by law.

DPO shall be designated on basis of PROFESSIONAL QUALITIES and EXPERT KNOWLEDGE of data protection law and practices.

DPO may be STAFF MEMBER or EXTERNAL service provider.

Controller/processor shall PUBLISH CONTACT DETAILS and communicate to supervisory authority.'''},
                        ]
                    },
                    {
                        'code': 'Ch-V',
                        'name': 'Chapter V - Transfers of Personal Data',
                        'description': 'Rules for transferring personal data outside the EU/EEA',
                        'disclosures': [
                            {'code': 'Art.44', 'name': 'General principle for transfers', 'requirement': '''Transfers of personal data to THIRD COUNTRY or INTERNATIONAL ORGANISATION may take place where:

• Controller/processor complies with conditions in Chapter V
• Other provisions of GDPR respected (including onward transfers to another third country/organisation)

ENSURE: Level of protection of natural persons guaranteed by GDPR is not undermined.

All provisions in Chapter V shall be applied to ensure level of protection guaranteed by GDPR is not undermined (including onward transfers).'''},
                            
                            {'code': 'Art.46', 'name': 'Transfers subject to appropriate safeguards', 'requirement': '''In absence of adequacy decision (Art.45), transfer may take place where appropriate safeguards provided and enforceable data subject rights and effective legal remedies available:

(a) LEGALLY BINDING instrument between public authorities or bodies

(b) BINDING CORPORATE RULES (Art.47)

(c) STANDARD DATA PROTECTION CLAUSES adopted by Commission

(d) Standard data protection clauses adopted by supervisory authority and approved by Commission

(e) APPROVED CODE OF CONDUCT (Art.40) with binding enforceable commitments in third country

(f) APPROVED CERTIFICATION MECHANISM (Art.42) with binding enforceable commitments in third country

(g) CONTRACTUAL CLAUSES between controller/processor and recipient in third country (authorised by supervisory authority)

(h) Provisions in administrative arrangements between public authorities (authorised by supervisory authority)

Subject to authorisation by competent supervisory authority, safeguards may also be provided by:
• Ad hoc contractual clauses between controller/processor and third country recipient
• Administrative arrangements between public authorities

ENFORCEMENT: Transfer may not take place if supervisory authority considers safeguards insufficient.'''},
                        ]
                    },
                    {
                        'code': 'Ch-VIII',
                        'name': 'Chapter VIII - Remedies, Liability and Penalties',
                        'description': 'Legal remedies, compensation rights and administrative fines for violations',
                        'disclosures': [
                            {'code': 'Art.82', 'name': 'Right to compensation and liability', 'requirement': '''Any person who suffered MATERIAL OR NON-MATERIAL DAMAGE from infringement of GDPR has right to receive COMPENSATION from controller or processor.

CONTROLLER involved in processing liable for damage caused by processing which infringes GDPR.

PROCESSOR liable for damage where:
• Has not complied with obligations specifically directed to processors OR
• Has acted outside or contrary to lawful instructions of controller

EXEMPTION: Controller/processor exempt from liability if proves NOT IN ANY WAY responsible for event giving rise to damage.

WHERE MORE THAN ONE CONTROLLER/PROCESSOR involved in same processing:
• Each controller/processor held liable for ENTIRE damage (joint and several liability)
• Effective compensation assured to data subject

Where paid full compensation, controller/processor entitled to claim back from other controllers/processors involved proportion corresponding to their responsibility for damage.

JUDICIAL PROCEEDINGS for exercising right to compensation shall be brought before courts of Member State where controller/processor has establishment OR where data subject has habitual residence (unless controller/processor is public authority).'''},
                            
                            {'code': 'Art.83', 'name': 'General conditions for imposing administrative fines', 'requirement': '''Supervisory authorities shall ensure administrative fines are EFFECTIVE, PROPORTIONATE and DISSUASIVE in each case.

FACTORS considered:
(a) Nature, gravity and duration of infringement (number of data subjects, level of damage)
(b) Intentional or negligent character
(c) Action taken to mitigate damage
(d) Degree of responsibility (technical/organisational measures under Art.25 and 32)
(e) Relevant previous infringements
(f) Cooperation with supervisory authority
(g) Categories of data affected
(h) How infringement became known to authority
(i) Compliance with measures ordered (Art.58(2))
(j) Adherence to codes of conduct or certification
(k) Aggravating or mitigating factors (financial benefits or losses avoided)

MAXIMUM FINES - UP TO HIGHER OF:

€10 MILLION or 2% of TOTAL WORLDWIDE ANNUAL TURNOVER for:
• Infringements of Art.8, 11, 25-39, 42, 43 (controller/processor obligations, certification)
• Non-compliance with order by supervisory authority

€20 MILLION or 4% of TOTAL WORLDWIDE ANNUAL TURNOVER for:
• Infringements of basic principles (Art.5, 6, 7, 9)
• Data subjects' rights (Art.12-22)
• Transfers to recipient in third country (Art.44-49)
• Non-compliance with national law pursuant to Chapter IX
• Non-compliance with order by supervisory authority (Art.58(2))

EACH MEMBER STATE may lay down rules on:
• Whether and to what extent fines imposed on public authorities
• Whether fines applied to specific cases

Warning may be issued instead of or in addition to fines.

When deciding whether to impose fine and amount:
• Due regard given to whether paid by undertaking or by natural person
• For infringements by processor: account taken whether controller/processor failed to comply with obligations
• Imposition of fine under paragraph 2 shall not prejudice other corrective powers (Art.58(2))'''},
                        ]
                    }
                ]
            },
            {
                'type': 'NIS2',
                'category_name': 'Cybersecurity',
                'category_desc': 'NIS2 Directive - Network and Information Security (EU mandatory for critical sectors)',
                'standards': [
                    {
                        'code': 'NIS2',
                        'name': 'Network and Information Security',
                        'description': 'NIS2 Directive strengthens cybersecurity requirements for essential and important entities across EU',
                        'disclosures': [
                            {'code': 'Art.21', 'name': 'Cybersecurity risk management', 'requirement': 'Implement cybersecurity risk management measures'},
                            {'code': 'Art.23', 'name': 'Incident reporting', 'requirement': 'Report significant cybersecurity incidents within 24 hours'},
                            {'code': 'Risk-1', 'name': 'Risk analysis and security policies', 'requirement': 'Conduct risk analysis and implement information security policies'},
                            {'code': 'Risk-2', 'name': 'Incident handling', 'requirement': 'Establish incident handling procedures and business continuity'},
                            {'code': 'Risk-3', 'name': 'Supply chain security', 'requirement': 'Manage cybersecurity risks from supplier relationships'},
                        ]
                    }
                ]
            },
            {
                'type': 'CSRD',
                'category_name': 'Sustainability Reporting',
                'category_desc': 'CSRD - Corporate Sustainability Reporting Directive (replaces NFRD, mandatory from 2024)',
                'standards': [
                    {
                        'code': 'CSRD',
                        'name': 'Corporate Sustainability Reporting',
                        'description': 'CSRD requires large companies to report on sustainability matters (ESG) using ESRS standards',
                        'disclosures': [
                            {'code': 'Art.19a', 'name': 'Sustainability reporting', 'requirement': 'Include sustainability statement in management report'},
                            {'code': 'Art.29b', 'name': 'Sustainability audit', 'requirement': 'Ensure assurance of sustainability reporting'},
                            {'code': 'ESRS-1', 'name': 'General requirements', 'requirement': 'Apply ESRS standards for sustainability reporting'},
                            {'code': 'ESRS-2', 'name': 'General disclosures', 'requirement': 'Disclose general information on governance, strategy, impact'},
                            {'code': 'Double-Mat', 'name': 'Double materiality assessment', 'requirement': 'Assess impact materiality and financial materiality'},
                        ]
                    }
                ]
            },
            {
                'type': 'EUTaxonomy',
                'category_name': 'Sustainable Finance',
                'category_desc': 'EU Taxonomy - Classification system for environmentally sustainable economic activities',
                'standards': [
                    {
                        'code': 'EUTax',
                        'name': 'EU Taxonomy Alignment',
                        'description': 'EU Taxonomy defines criteria for determining whether an economic activity is environmentally sustainable',
                        'disclosures': [
                            {'code': 'Art.8', 'name': 'Taxonomy-aligned activities', 'requirement': 'Disclose proportion of taxonomy-aligned activities'},
                            {'code': 'Obj-1', 'name': 'Climate change mitigation', 'requirement': 'Report activities contributing to climate change mitigation'},
                            {'code': 'Obj-2', 'name': 'Climate change adaptation', 'requirement': 'Report activities contributing to climate change adaptation'},
                            {'code': 'DNSH', 'name': 'Do No Significant Harm', 'requirement': 'Ensure activities do not significantly harm environmental objectives'},
                            {'code': 'MinSafe', 'name': 'Minimum safeguards', 'requirement': 'Comply with minimum social safeguards'},
                        ]
                    }
                ]
            },
            {
                'type': 'DORA',
                'category_name': 'Digital Operational Resilience',
                'category_desc': 'DORA - Digital Operational Resilience Act (EU mandatory for financial sector from 2025)',
                'standards': [
                    {
                        'code': 'DORA',
                        'name': 'Digital Operational Resilience',
                        'description': 'DORA establishes requirements for ICT risk management in financial services',
                        'disclosures': [
                            {'code': 'Art.6', 'name': 'ICT risk management framework', 'requirement': 'Establish comprehensive ICT risk management framework'},
                            {'code': 'Art.11', 'name': 'ICT-related incident management', 'requirement': 'Implement processes for monitoring, logging and classifying ICT incidents'},
                            {'code': 'Art.17', 'name': 'Digital operational resilience testing', 'requirement': 'Conduct regular testing of ICT systems and applications'},
                            {'code': 'Art.28', 'name': 'Third-party ICT risk', 'requirement': 'Manage risks from third-party ICT service providers'},
                            {'code': 'Art.37', 'name': 'Threat intelligence', 'requirement': 'Exchange cyber threat information'},
                        ]
                    }
                ]
            },
            {
                'type': 'CSDDD',
                'category_name': 'Due Diligence',
                'category_desc': 'CSDDD - Corporate Sustainability Due Diligence Directive (human rights and environment)',
                'standards': [
                    {
                        'code': 'CSDDD',
                        'name': 'Sustainability Due Diligence',
                        'description': 'CSDDD requires companies to identify, prevent, mitigate and account for negative human rights and environmental impacts',
                        'disclosures': [
                            {'code': 'Art.6', 'name': 'Due diligence policy', 'requirement': 'Integrate due diligence into policies and risk management'},
                            {'code': 'Art.7', 'name': 'Identify and assess impacts', 'requirement': 'Identify actual and potential adverse impacts'},
                            {'code': 'Art.8', 'name': 'Prevent and mitigate', 'requirement': 'Take appropriate measures to prevent or mitigate adverse impacts'},
                            {'code': 'Art.9', 'name': 'Bring to an end', 'requirement': 'Take measures to bring actual adverse impacts to an end'},
                            {'code': 'Art.10', 'name': 'Stakeholder engagement', 'requirement': 'Conduct meaningful engagement with stakeholders'},
                            {'code': 'Art.11', 'name': 'Communication', 'requirement': 'Communicate on due diligence processes and outcomes'},
                        ]
                    }
                ]
            }
        ]
        
        created_count = 0
        
        for std_data in standards_data:
            # Create category
            category, cat_created = ESRSCategory.objects.get_or_create(
                code=std_data['type'],
                standard_type=std_data['type'],
                defaults={
                    'name': std_data['category_name'],
                    'description': std_data['category_desc'],
                    'order': 100 + created_count
                }
            )
            
            if cat_created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Category: {std_data["type"]} - {std_data["category_name"]}'))
            
            # Create standards
            for std in std_data['standards']:
                standard, std_created = ESRSStandard.objects.get_or_create(
                    code=std['code'],
                    standard_type=std_data['type'],
                    defaults={
                        'category': category,
                        'name': std['name'],
                        'description': std['description'],
                        'order': 0
                    }
                )
                
                if std_created:
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Standard: {std["code"]} - {std["name"]}'))
                    created_count += 1
                
                # Create disclosures
                for idx, disc in enumerate(std['disclosures']):
                    disclosure, disc_created = ESRSDisclosure.objects.get_or_create(
                        standard=standard,
                        code=disc['code'],
                        defaults={
                            'standard_type': std_data['type'],
                            'name': disc['name'],
                            'description': disc['name'],
                            'requirement_text': disc['requirement'],
                            'order': idx,
                            'is_mandatory': True
                        }
                    )
                    
                    if disc_created:
                        self.stdout.write(f'      ✓ {disc["code"]}: {disc["name"]}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully added {created_count} EU/Slovenia standards!'))
        self.stdout.write(self.style.SUCCESS(f'Total standards available: {ESRSStandard.objects.count()}'))
