"""
AI Brand Analyzer - Uses Claude Vision API to analyze logos and generate brand style guides
"""

import base64
import logging
from pathlib import Path
from typing import Dict, Any
from anthropic import Anthropic
from decouple import config

logger = logging.getLogger(__name__)


class BrandAnalyzer:
    """
    Analyzes company logos using Claude Vision API and generates comprehensive brand style guides
    """

    def __init__(self):
        self.client = Anthropic(api_key=config('ANTHROPIC_API_KEY'))
        self.model = "claude-3-7-sonnet-20250219"  # Vision-capable model (latest)

    def analyze_logo(self, logo_path: str) -> Dict[str, Any]:
        """
        Analyze a company logo and generate a complete brand style guide

        Args:
            logo_path: Path to the logo image file

        Returns:
            Dict containing brand style guide with colors, fonts, layout preferences, etc.
        """
        try:
            # Read and encode the image
            with open(logo_path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')

            # Determine image type
            image_type = self._get_image_type(logo_path)

            # Analyze with Claude Vision
            prompt = self._build_analysis_prompt()

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                system="You are a JSON API that only returns valid JSON. Never add explanations or text outside the JSON object. Always start with { and end with }.",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )

            # Extract the analysis result
            result_text = response.content[0].text

            logger.info(f"🎨 Raw AI response length: {len(result_text)} chars")
            logger.info(f"🎨 First 200 chars: {result_text[:200]}")

            # Parse the JSON response
            import json

            # Extract JSON from markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
                logger.info("🎨 Extracted JSON from ```json code block")
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
                logger.info("🎨 Extracted JSON from ``` code block")
            else:
                # Sometimes Claude returns thinking text before JSON, find the actual JSON
                if not result_text.strip().startswith('{'):
                    json_start = result_text.find('{')
                    if json_start != -1:
                        result_text = result_text[json_start:]
                        logger.info(f"🎨 Extracted JSON starting at position {json_start}")
                    else:
                        logger.error(f"🎨 No JSON found in response. Full response: {result_text}")
                        raise ValueError("No JSON found in Claude's response")

            # Try to parse JSON
            try:
                style_guide = json.loads(result_text)
            except json.JSONDecodeError as e:
                logger.error(f"🎨 JSON parse error: {e}")
                logger.error(f"🎨 Attempted to parse: {result_text[:500]}")
                raise

            logger.info(f"✅ Successfully analyzed logo: {logo_path}")
            logger.info(f"🎨 Extracted colors: {style_guide.get('colors', {})}")
            return style_guide

        except Exception as e:
            logger.error(f"Failed to analyze logo: {e}", exc_info=True)
            logger.warning(f"Using default style guide due to error")
            # Return default style guide on error
            return self._get_default_style_guide()

    def _get_image_type(self, file_path: str) -> str:
        """Determine MIME type from file extension"""
        ext = Path(file_path).suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        return mime_types.get(ext, 'image/png')

    def _build_analysis_prompt(self) -> str:
        """Build the prompt for logo analysis"""
        return """Analyze this logo and generate COMPLETE custom CSS for a professional PDF report.

Extract colors, shapes, and patterns from the logo. Generate production-ready CSS with:

**REQUIRED PDF LAYOUT (CRITICAL):**
```css
@page {
    size: A4;
    margin: 20mm;
}
body {
    margin: 0;
    padding: 0;
    font-size: 11pt;
    line-height: 1.6;
}
```

**MUST INCLUDE:**
1. Color variables from logo colors
2. Typography: font-family, sizes (h1: 24pt, h2: 18pt, h3: 14pt, p: 11pt)
3. Proper spacing: margins 12-20px, padding 10-16px
4. Header: max-height 60px, logo max 50px, aligned top
5. Footer: position fixed bottom, small text 9pt
6. Title page: centered vertically, readable, logo prominent
7. Content: readable text with proper line-height 1.6-1.8
8. Tables: proper padding (10px cells), alternating rows
9. Sections: clear spacing between (24-36px)
10. Cards/boxes: subtle backgrounds, good padding (16-20px)

**READABILITY RULES:**
- Text must be readable (not too large, not overlapping)
- Proper contrast (dark text on light bg, light text on dark bg)
- Decorative elements MUST NOT obscure text
- Backgrounds subtle (opacity 0.05-0.15 for patterns)
- Adequate whitespace between sections

Return ONLY this JSON (no markdown, no explanations):

{
  "css": "FULL CSS CODE HERE - 600+ lines, includes @page, all selectors, proper margins/padding",
  "design_notes": {
    "colors_extracted": ["#HEX", "#HEX", "#HEX"],
    "logo_shapes": ["circles"],
    "design_inspiration": "Modern fintech with pink accents"
  }
}

Make it beautiful BUT professional and readable. Logo colors should dominate the design."""

    def _get_default_style_guide(self) -> Dict[str, Any]:
        """Return a default professional style guide as fallback"""
        return {
            "colors": {
                "primary": "#1a472a",
                "secondary": "#2d5016",
                "accent": "#4a7c59",
                "text_dark": "#1a1a1a",
                "text_light": "#ffffff",
                "background_light": "#f8f9fa",
                "background_dark": "#2d5016",
                "table_header": "#2d5016",
                "table_row_alt": "#f0f4f0"
            },
            "typography": {
                "font_personality": "professional",
                "heading_weight": "bold",
                "body_weight": "normal",
                "letter_spacing": "normal"
            },
            "layout": {
                "density": "balanced",
                "style": "corporate",
                "whitespace": "normal"
            },
            "visual_elements": {
                "use_gradients": False,
                "border_style": "subtle",
                "corner_radius": "slightly-rounded",
                "shadow_style": "subtle"
            },
            "report_structure": {
                "header_style": "logo-only",
                "footer_style": "page-numbers",
                "section_dividers": "lines",
                "chart_style": "clean"
            },
            "personality": ["professional", "sustainable", "trustworthy"]
        }

    def generate_css_from_style(self, style_guide: Dict[str, Any]) -> str:
        """
        Extract CSS from AI-generated style guide or generate fallback

        Args:
            style_guide: Brand style guide dict from analyze_logo() containing 'css' key

        Returns:
            Complete CSS string ready to be injected into HTML templates
        """
        # If AI generated complete CSS, use it directly
        if 'css' in style_guide and style_guide['css']:
            logger.info("✅ Using AI-generated custom CSS")
            return style_guide['css']

        # Fallback: generate basic CSS if AI didn't return CSS
        logger.warning("⚠️ AI didn't return CSS, using fallback generator")
        colors = style_guide.get('colors', {})
        typography = style_guide.get('typography', {})
        layout = style_guide.get('layout', {})
        visual = style_guide.get('visual_elements', {})
        structure = style_guide.get('report_structure', {})

        # Font stacks based on personality
        font_stacks = {
            'modern': "'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif",
            'traditional': "'Georgia', 'Times New Roman', serif",
            'technical': "'Roboto Mono', 'Courier New', monospace",
            'elegant': "'Playfair Display', 'Georgia', serif",
            'creative': "'Poppins', 'Montserrat', sans-serif",
            'minimal': "'Helvetica', 'Arial', sans-serif",
            'bold': "'Montserrat', 'Arial Black', sans-serif"
        }

        font_family = font_stacks.get(typography.get('font_personality', 'modern'), font_stacks['modern'])

        # Spacing based on whitespace preference
        spacing_map = {
            'tight': {'base': '8px', 'section': '16px', 'large': '24px'},
            'normal': {'base': '12px', 'section': '24px', 'large': '36px'},
            'airy': {'base': '16px', 'section': '32px', 'large': '48px'},
            'generous': {'base': '20px', 'section': '40px', 'large': '60px'}
        }

        spacing = spacing_map.get(layout.get('whitespace', 'normal'), spacing_map['normal'])

        # Border radius
        radius_map = {
            'sharp': '0',
            'slightly-rounded': '4px',
            'rounded': '8px',
            'very-rounded': '12px'
        }
        border_radius = radius_map.get(visual.get('corner_radius', 'slightly-rounded'), '4px')

        # Shadow styles
        shadow_map = {
            'none': 'none',
            'subtle': '0 1px 3px rgba(0,0,0,0.1)',
            'medium': '0 2px 8px rgba(0,0,0,0.15)',
            'strong': '0 4px 16px rgba(0,0,0,0.2)'
        }
        box_shadow = shadow_map.get(visual.get('shadow_style', 'subtle'), shadow_map['subtle'])

        css = f"""
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Montserrat:wght@400;600;700&family=Roboto+Mono&display=swap');

        /* === ROOT VARIABLES === */
        :root {{
            /* Brand Colors */
            --color-primary: {colors.get('primary', '#1a472a')};
            --color-secondary: {colors.get('secondary', '#2d5016')};
            --color-accent: {colors.get('accent', '#4a7c59')};
            --color-text-dark: {colors.get('text_dark', '#1a1a1a')};
            --color-text-light: {colors.get('text_light', '#ffffff')};
            --color-bg-light: {colors.get('background_light', '#f8f9fa')};
            --color-bg-dark: {colors.get('background_dark', '#2d5016')};
            --color-table-header: {colors.get('table_header', '#2d5016')};
            --color-table-alt: {colors.get('table_row_alt', '#f0f4f0')};

            /* Typography */
            --font-family: {font_family};
            --font-weight-heading: {'300' if typography.get('heading_weight') == 'light' else '600' if typography.get('heading_weight') == 'bold' else '800' if typography.get('heading_weight') == 'extra-bold' else '400'};
            --font-weight-body: {'300' if typography.get('body_weight') == 'light' else '500' if typography.get('body_weight') == 'medium' else '400'};
            --letter-spacing: {'-0.02em' if typography.get('letter_spacing') == 'tight' else '0.05em' if typography.get('letter_spacing') == 'wide' else 'normal'};

            /* Spacing */
            --space-base: {spacing['base']};
            --space-section: {spacing['section']};
            --space-large: {spacing['large']};

            /* Visual */
            --border-radius: {border_radius};
            --box-shadow: {box_shadow};
            --border-color: {colors.get('primary', '#1a472a')}33;
            --border-width: {'2px' if visual.get('border_style') == 'bold' else '1px' if visual.get('border_style') == 'subtle' else '0'};
        }}

        /* === BASE STYLES === */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: var(--font-family);
            font-weight: var(--font-weight-body);
            color: var(--color-text-dark);
            line-height: 1.6;
            background: white;
            letter-spacing: var(--letter-spacing);
            padding: 20mm 20mm 30mm 20mm;
        }}

        @page {{
            size: A4;
            margin: 20mm;
        }}

        /* === HEADER === */
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: var(--space-section);
            margin-bottom: var(--space-section);
            {'border-bottom: var(--border-width) solid var(--border-color);' if structure.get('header_style') != 'minimal' else ''}
        }}

        .logo {{
            max-height: 60px;
            max-width: 200px;
            object-fit: contain;
        }}

        .header-info {{
            text-align: right;
            font-size: 0.9em;
            color: var(--color-text-dark);
            opacity: 0.8;
        }}

        /* === FOOTER === */
        .footer {{
            position: fixed;
            bottom: 15mm;
            left: 20mm;
            right: 20mm;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: var(--space-base);
            {'border-top: var(--border-width) solid var(--border-color);' if structure.get('footer_style') != 'minimal' else ''}
            font-size: 0.85em;
            color: var(--color-text-dark);
            opacity: 0.7;
        }}

        /* === TYPOGRAPHY === */
        h1 {{
            font-size: 2.5em;
            font-weight: var(--font-weight-heading);
            color: var(--color-primary);
            margin-bottom: var(--space-section);
            letter-spacing: var(--letter-spacing);
            position: relative;
            padding-left: 20px;
        }}

        h1::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 6px;
            background: linear-gradient(180deg, var(--color-primary) 0%, var(--color-accent) 100%);
            border-radius: 3px;
        }}

        h2 {{
            font-size: 1.8em;
            font-weight: var(--font-weight-heading);
            color: var(--color-secondary);
            margin-top: var(--space-large);
            margin-bottom: var(--space-base);
            padding-bottom: var(--space-base);
            padding-left: 16px;
            position: relative;
            {'border-bottom: 2px solid var(--color-primary);' if structure.get('section_dividers') == 'colored-bars' else 'border-bottom: 1px solid var(--border-color);' if structure.get('section_dividers') == 'lines' else ''}
        }}

        h2::before {{
            content: '▸';
            position: absolute;
            left: 0;
            color: var(--color-accent);
            font-size: 0.8em;
        }}

        h3 {{
            font-size: 1.3em;
            font-weight: var(--font-weight-heading);
            color: var(--color-primary);
            margin-top: var(--space-section);
            margin-bottom: var(--space-base);
        }}

        p {{
            margin-bottom: var(--space-base);
            text-align: justify;
            line-height: 1.7;
        }}

        strong {{
            color: var(--color-primary);
            font-weight: 600;
        }}

        em {{
            color: var(--color-secondary);
            font-style: italic;
        }}

        /* === TABLES === */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: var(--space-section) 0;
            box-shadow: var(--box-shadow);
            border-radius: var(--border-radius);
            overflow: hidden;
        }}

        thead {{
            background: var(--color-table-header);
            color: var(--color-text-light);
        }}

        th {{
            padding: 12px 16px;
            text-align: left;
            font-weight: var(--font-weight-heading);
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        td {{
            padding: 10px 16px;
            border-bottom: 1px solid var(--border-color);
        }}

        tbody tr:nth-child(even) {{
            background: var(--color-table-alt);
        }}

        tbody tr:hover {{
            background: {colors.get('primary', '#1a472a')}08;
        }}

        /* === CHARTS & IMAGES === */
        .chart-container {{
            margin: var(--space-section) 0;
            text-align: center;
        }}

        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
        }}

        .chart-caption {{
            margin-top: var(--space-base);
            font-size: 0.9em;
            color: var(--color-secondary);
            font-style: italic;
        }}

        /* === CARDS & SECTIONS === */
        .section {{
            margin-bottom: var(--space-large);
            page-break-inside: avoid;
        }}

        .card {{
            background: linear-gradient(135deg, var(--color-bg-light) 0%, {colors.get('primary', '#1a472a')}05 100%);
            padding: var(--space-section);
            border-radius: var(--border-radius);
            border-left: 4px solid var(--color-primary);
            margin: var(--space-section) 0;
            box-shadow: var(--box-shadow);
            position: relative;
            overflow: hidden;
        }}

        .card::after {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, {colors.get('accent', '#4a7c59')}08 0%, transparent 70%);
            pointer-events: none;
        }}

        .requirement {{
            background: linear-gradient(90deg, {colors.get('accent', '#4a7c59')}15 0%, {colors.get('accent', '#4a7c59')}05 100%);
            padding: var(--space-base);
            border-left: 3px solid var(--color-accent);
            margin: var(--space-base) 0;
            border-radius: var(--border-radius);
            position: relative;
        }}

        .requirement::before {{
            content: '📋';
            position: absolute;
            right: 16px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 2em;
            opacity: 0.1;
        }}

        /* === UTILITIES === */
        .text-center {{
            text-align: center;
        }}

        .page-break {{
            page-break-after: always;
        }}

        .no-break {{
            page-break-inside: avoid;
        }}

        /* === TITLE PAGE === */
        .title-page {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 250mm;
            text-align: center;
            background: linear-gradient(135deg, white 0%, var(--color-bg-light) 50%, {colors.get('primary', '#1a472a')}08 100%);
            position: relative;
            overflow: hidden;
        }}

        .title-page::before {{
            content: '';
            position: absolute;
            top: -100px;
            right: -100px;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, {colors.get('accent', '#4a7c59')}15 0%, transparent 70%);
            border-radius: 50%;
        }}

        .title-page::after {{
            content: '';
            position: absolute;
            bottom: -100px;
            left: -100px;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, {colors.get('secondary', '#2d5016')}10 0%, transparent 70%);
            border-radius: 50%;
        }}

        .title-page h1 {{
            font-size: 3em;
            margin-bottom: var(--space-base);
            position: relative;
            z-index: 1;
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .title-page .subtitle {{
            font-size: 1.2em;
            color: var(--color-secondary);
            margin-bottom: var(--space-large);
            position: relative;
            z-index: 1;
            font-weight: 500;
        }}
        """

        return css
