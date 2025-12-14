"""
ESRS Report Generator - PDF and Word Export
Generates professional reports with charts and tables
"""

import logging
from typing import Optional, List
from io import BytesIO
import base64
from datetime import datetime

# PDF Generation
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
    Table, TableStyle, Image as RLImage
)
from reportlab.lib import colors

# Word Generation
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from PIL import Image as PILImage

logger = logging.getLogger(__name__)


class ESRSReportGenerator:
    """Generate PDF and Word reports for ESRS disclosures"""
    
    def __init__(self, user, standard_id: Optional[int] = None, disclosure_ids: Optional[List[int]] = None):
        self.user = user
        self.standard_id = standard_id
        self.disclosure_ids = disclosure_ids
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a472a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        self.styles.add(title_style)
        
        # Heading2 custom
        h2_style = ParagraphStyle(
            'CustomH2',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2d5016'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )
        self.styles.add(h2_style)
        
        # Body text custom
        body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        self.styles.add(body_style)
    
    def _get_responses_queryset(self):
        """Get filtered ESRSUserResponse queryset"""
        from accounts.models import ESRSUserResponse
        from django.db.models import Q
        
        queryset = ESRSUserResponse.objects.filter(user=self.user).select_related(
            'disclosure__standard__category'
        ).order_by('disclosure__standard__order', 'disclosure__order')
        
        # Filter by standard if provided
        if self.standard_id:
            queryset = queryset.filter(disclosure__standard_id=self.standard_id)
        
        # Filter by specific disclosures if provided
        if self.disclosure_ids:
            queryset = queryset.filter(disclosure_id__in=self.disclosure_ids)
        
        # Only include responses with content
        queryset = queryset.filter(
            Q(ai_answer__isnull=False) | 
            Q(manual_answer__isnull=False) | 
            Q(final_answer__isnull=False)
        )
        
        return queryset
    
    def generate_pdf(self) -> BytesIO:
        """
        Generate PDF report
        Returns BytesIO buffer
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Title page
        story.append(Spacer(1, 2*inch))
        title = Paragraph("ESRS Sustainability Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Company info
        company_info = f"""
        <para align=center>
        <b>Company:</b> {self.user.email}<br/>
        <b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %H:%M')}<br/>
        <b>Report Type:</b> European Sustainability Reporting Standards
        </para>
        """
        story.append(Paragraph(company_info, self.styles['CustomBody']))
        story.append(PageBreak())
        
        # Get responses
        responses = self._get_responses_queryset()
        
        if not responses.exists():
            no_data = Paragraph("No ESRS responses available for this report.", self.styles['CustomBody'])
            story.append(no_data)
        else:
            # Group by standard
            current_standard = None
            
            for response in responses:
                disclosure = response.disclosure
                standard = disclosure.standard
                
                # Add standard header if changed
                if current_standard != standard.code:
                    current_standard = standard.code
                    story.append(Spacer(1, 0.2*inch))
                    standard_title = Paragraph(
                        f"{standard.code}: {standard.name}",
                        self.styles['Heading1']
                    )
                    story.append(standard_title)
                    story.append(Spacer(1, 0.1*inch))
                
                # Disclosure header
                disclosure_title = Paragraph(
                    f"<b>{disclosure.code}</b>: {disclosure.name}",
                    self.styles['CustomH2']
                )
                story.append(disclosure_title)
                
                # Requirement
                req_text = f"<i>Requirement:</i> {disclosure.requirement_text[:300]}..."
                story.append(Paragraph(req_text, self.styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                
                # Answer (final > ai > manual)
                answer_text = response.final_answer or response.ai_answer or response.manual_answer
                if answer_text:
                    story.append(Paragraph("<b>Answer:</b>", self.styles['CustomH2']))
                    # Split long text into paragraphs
                    paragraphs = answer_text.split('\n\n')
                    for para in paragraphs[:5]:  # Limit to first 5 paragraphs
                        if para.strip():
                            story.append(Paragraph(para.strip(), self.styles['CustomBody']))
                
                # Add charts if available
                if response.chart_data:
                    story.append(Spacer(1, 0.2*inch))
                    story.append(Paragraph("<b>Visual Analytics:</b>", self.styles['CustomH2']))
                    
                    for chart in response.chart_data[:3]:  # Max 3 charts per disclosure
                        try:
                            # Decode base64 image
                            image_data = base64.b64decode(chart['image_base64'])
                            img_buffer = BytesIO(image_data)
                            
                            # Create ReportLab image
                            img = RLImage(img_buffer, width=5*inch, height=3*inch)
                            story.append(img)
                            
                            # Chart caption
                            caption = Paragraph(
                                f"<i>{chart['title']} ({chart['type'].upper()} chart)</i>",
                                self.styles['Normal']
                            )
                            story.append(caption)
                            story.append(Spacer(1, 0.1*inch))
                        except Exception as e:
                            logger.warning(f"Failed to add chart to PDF: {e}")
                
                # Add tables if available
                if response.table_data:
                    for table_info in response.table_data[:2]:  # Max 2 tables per disclosure
                        try:
                            story.append(Spacer(1, 0.2*inch))
                            table_title = Paragraph(
                                f"<b>{table_info['title']}</b>",
                                self.styles['Normal']
                            )
                            story.append(table_title)
                            
                            # Build table data
                            table_data = [table_info['headers']] + table_info['rows']
                            
                            # Create table
                            t = Table(table_data, hAlign='LEFT')
                            t.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5016')),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 12),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)
                            ]))
                            story.append(t)
                        except Exception as e:
                            logger.warning(f"Failed to add table to PDF: {e}")
                
                story.append(Spacer(1, 0.3*inch))
                story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_word(self) -> BytesIO:
        """
        Generate Word document report
        Returns BytesIO buffer
        """
        doc = Document()
        
        # Set document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
        
        # Title page
        title = doc.add_heading('ESRS Sustainability Report', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Company info
        company_para = doc.add_paragraph()
        company_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        company_para.add_run(f'Company: {self.user.email}\n').bold = True
        company_para.add_run(f'Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")}\n')
        company_para.add_run('Report Type: European Sustainability Reporting Standards')
        
        doc.add_page_break()
        
        # Get responses
        responses = self._get_responses_queryset()
        
        if not responses.exists():
            doc.add_paragraph('No ESRS responses available for this report.')
        else:
            current_standard = None
            
            for response in responses:
                disclosure = response.disclosure
                standard = disclosure.standard
                
                # Add standard header if changed
                if current_standard != standard.code:
                    current_standard = standard.code
                    doc.add_heading(f"{standard.code}: {standard.name}", level=1)
                
                # Disclosure header
                doc.add_heading(f"{disclosure.code}: {disclosure.name}", level=2)
                
                # Requirement
                req_para = doc.add_paragraph()
                req_para.add_run('Requirement: ').italic = True
                req_para.add_run(disclosure.requirement_text[:300] + '...')
                
                # Answer
                answer_text = response.final_answer or response.ai_answer or response.manual_answer
                if answer_text:
                    doc.add_heading('Answer:', level=3)
                    paragraphs = answer_text.split('\n\n')
                    for para in paragraphs[:5]:
                        if para.strip():
                            doc.add_paragraph(para.strip())
                
                # Add charts
                if response.chart_data:
                    doc.add_heading('Visual Analytics:', level=3)
                    
                    for chart in response.chart_data[:3]:
                        try:
                            # Decode base64 image
                            image_data = base64.b64decode(chart['image_base64'])
                            img_buffer = BytesIO(image_data)
                            
                            # Add image to Word
                            doc.add_picture(img_buffer, width=Inches(5))
                            
                            # Caption
                            caption = doc.add_paragraph()
                            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            caption_run = caption.add_run(f"{chart['title']} ({chart['type'].upper()} chart)")
                            caption_run.italic = True
                        except Exception as e:
                            logger.warning(f"Failed to add chart to Word: {e}")
                
                # Add tables
                if response.table_data:
                    for table_info in response.table_data[:2]:
                        try:
                            doc.add_paragraph(table_info['title'], style='Heading 3')
                            
                            # Create table
                            table = doc.add_table(
                                rows=1 + len(table_info['rows']),
                                cols=len(table_info['headers'])
                            )
                            table.style = 'Light Grid Accent 1'
                            
                            # Header row
                            header_cells = table.rows[0].cells
                            for i, header in enumerate(table_info['headers']):
                                header_cells[i].text = str(header)
                                header_cells[i].paragraphs[0].runs[0].bold = True
                            
                            # Data rows
                            for row_idx, row_data in enumerate(table_info['rows']):
                                row_cells = table.rows[row_idx + 1].cells
                                for col_idx, cell_value in enumerate(row_data):
                                    row_cells[col_idx].text = str(cell_value)
                        except Exception as e:
                            logger.warning(f"Failed to add table to Word: {e}")
                
                doc.add_page_break()
        
        # Save to buffer
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
