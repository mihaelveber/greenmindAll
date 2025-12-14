"""
Chart and Analytics service for ESRS responses
Detects numeric data, generates charts, and creates visual reports
"""

import logging
import re
import json
from typing import Dict, List, Tuple, Optional, Any
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

# Set seaborn style
sns.set_style("whitegrid")
sns.set_palette("husl")


class NumericDataDetector:
    """Detect numeric data patterns in text"""
    
    @staticmethod
    def extract_numeric_data(text: str) -> List[Dict[str, Any]]:
        """
        Extract numeric data from text
        Returns list of dicts with label and value
        """
        numeric_patterns = []
        
        # Pattern 1: "X employees" or "X workers" or "X people" with units
        # Example: "150 male employees and 120 female employees"
        pattern1 = r'(\d+(?:,\d+)?(?:\.\d+)?)\s*(male|female|men|women|employees|workers|people|tons|kg|hours|days|years|percent|%)'
        matches1 = re.finditer(pattern1, text, re.IGNORECASE)
        for match in matches1:
            value = float(match.group(1).replace(',', ''))
            unit = match.group(2)
            numeric_patterns.append({
                'value': value,
                'unit': unit,
                'context': match.group(0)
            })
        
        # Pattern 2: "Category: X" or "Category - X"
        # Example: "Male: 150, Female: 120"
        pattern2 = r'([A-Za-z\s]+):\s*(\d+(?:,\d+)?(?:\.\d+)?)'
        matches2 = re.finditer(pattern2, text)
        for match in matches2:
            label = match.group(1).strip()
            value = float(match.group(2).replace(',', ''))
            numeric_patterns.append({
                'value': value,
                'label': label,
                'context': match.group(0)
            })
        
        # Pattern 3: Percentages with labels
        # Example: "women representing 69%" or "women constitute 69%" or "31% men"
        pattern3a = r'([A-Za-z]+)\s+(?:representing|represent|constitute|account\s+for|are|is)?\s*(\d+(?:\.\d+)?)\s*%'
        matches3a = re.finditer(pattern3a, text, re.IGNORECASE)
        for match in matches3a:
            label = match.group(1).strip().title()
            value = float(match.group(2))
            numeric_patterns.append({
                'value': value,
                'unit': '%',
                'label': label,
                'context': match.group(0)
            })
        
        # Pattern 3b: "X% label"
        pattern3b = r'(\d+(?:\.\d+)?)\s*%\s*([A-Za-z]+)'
        matches3b = re.finditer(pattern3b, text, re.IGNORECASE)
        for match in matches3b:
            value = float(match.group(1))
            label = match.group(2).strip().title()
            numeric_patterns.append({
                'value': value,
                'unit': '%',
                'label': label,
                'context': match.group(0)
            })
        
        # Pattern 4: Currency (€, $, £) with amounts
        # Example: "€1,500 revenue" or "$2,000,000 profit"
        pattern4 = r'([€$£])\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*([A-Za-z\s]*)'
        matches4 = re.finditer(pattern4, text)
        for match in matches4:
            currency = match.group(1)
            value = float(match.group(2).replace(',', ''))
            label = match.group(3).strip() or 'Amount'
            numeric_patterns.append({
                'value': value,
                'unit': currency,
                'label': label,
                'context': match.group(0)
            })
        
        # Pattern 5: Time series (Year: Value)
        # Example: "2022: 100, 2023: 150, 2024: 200"
        pattern5 = r'(\d{4}):\s*(\d+(?:,\d+)?(?:\.\d+)?)'
        matches5 = re.finditer(pattern5, text)
        for match in matches5:
            year = match.group(1)
            value = float(match.group(2).replace(',', ''))
            numeric_patterns.append({
                'value': value,
                'label': f'Year {year}',
                'year': int(year),
                'context': match.group(0)
            })
        
        # Pattern 6: Ratios (X:Y format)
        # Example: "3:1 ratio" or "Male to Female ratio is 2:1"
        pattern6 = r'(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)\s*(ratio)?'
        matches6 = re.finditer(pattern6, text, re.IGNORECASE)
        for match in matches6:
            value1 = float(match.group(1))
            value2 = float(match.group(2))
            numeric_patterns.append({
                'value': value1,
                'label': 'First Part',
                'unit': 'ratio',
                'context': match.group(0)
            })
            numeric_patterns.append({
                'value': value2,
                'label': 'Second Part',
                'unit': 'ratio',
                'context': match.group(0)
            })
        
        # Pattern 7: Ranges (X-Y or X to Y)
        # Example: "10-20 tons" or "15 to 25 kg"
        # EXCLUDE: Disclosure codes like "S1-9", "E1-6", etc.
        # Use negative lookbehind to exclude patterns preceded by capital letter
        pattern7 = r'(?<![A-Z])(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s+([A-Za-z]+)'
        matches7 = re.finditer(pattern7, text, re.IGNORECASE)
        for match in matches7:
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            unit = match.group(3)
            
            # Additional check: skip if unit is too short (likely part of code)
            if len(unit) < 2:
                continue
            
            # Store average for charting
            avg_val = (min_val + max_val) / 2
            numeric_patterns.append({
                'value': avg_val,
                'min': min_val,
                'max': max_val,
                'unit': unit,
                'label': f'Range ({min_val}-{max_val}) {unit}',
                'context': match.group(0)
            })
        
        return numeric_patterns
    
    @staticmethod
    def categorize_data(numeric_data: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        Categorize numeric data into groups
        Returns dict with categories
        """
        categories = {
            'employee_stats': [],
            'gender_stats': [],
            'emissions': [],
            'energy': [],
            'waste': [],
            'percentages': [],
            'financial': [],
            'time_series': [],
            'ratios': [],
            'other': []
        }
        
        for item in numeric_data:
            unit = item.get('unit', '').lower()
            item_label = item.get('label', '').lower()
            context = item.get('context', '').lower()
            
            # Skip generic ranges without meaningful context
            if 'range' in item_label and not any(word in context for word in ['male', 'female', 'men', 'women', 'employee', 'emission', 'energy']):
                continue
            
            # Gender statistics
            if any(word in context for word in ['male', 'female', 'men', 'women', 'gender']):
                categories['gender_stats'].append(item)
            # Employee statistics
            elif any(word in context for word in ['employee', 'worker', 'people', 'staff']):
                categories['employee_stats'].append(item)
            # Emissions
            elif any(word in context for word in ['co2', 'emission', 'carbon', 'ghg', 'greenhouse']):
                categories['emissions'].append(item)
            # Energy
            elif any(word in context for word in ['energy', 'kwh', 'renewable', 'power']):
                categories['energy'].append(item)
            # Waste
            elif any(word in context for word in ['waste', 'recycl', 'disposal']):
                categories['waste'].append(item)
            # Financial (currency)
            elif unit in ['€', '$', '£']:
                categories['financial'].append(item)
            # Time series (has year)
            elif 'year' in item:
                categories['time_series'].append(item)
            # Ratios
            elif unit == 'ratio':
                categories['ratios'].append(item)
            # Percentages
            elif unit == '%':
                categories['percentages'].append(item)
            else:
                categories['other'].append(item)
        
        return categories


class ChartGenerator:
    """Generate charts from numeric data"""
    
    @staticmethod
    def generate_bar_chart(
        data: Dict[str, float],
        title: str,
        xlabel: str = "",
        ylabel: str = "Count",
        figsize: Tuple[int, int] = (10, 6)
    ) -> str:
        """
        Generate bar chart and return as base64 string
        """
        try:
            fig, ax = plt.subplots(figsize=figsize)
            
            labels = list(data.keys())
            values = list(data.values())
            
            bars = ax.bar(labels, values, color=sns.color_palette("husl", len(labels)))
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'{height:.0f}',
                    ha='center',
                    va='bottom',
                    fontweight='bold'
                )
            
            plt.tight_layout()
            
            # Save to bytes
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            
            return image_base64
        
        except Exception as e:
            logger.error(f"Error generating bar chart: {e}")
            return ""
    
    @staticmethod
    def generate_pie_chart(
        data: Dict[str, float],
        title: str,
        figsize: Tuple[int, int] = (8, 8)
    ) -> str:
        """
        Generate pie chart and return as base64 string
        """
        try:
            fig, ax = plt.subplots(figsize=figsize)
            
            labels = list(data.keys())
            values = list(data.values())
            colors = sns.color_palette("husl", len(labels))
            
            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                textprops={'fontsize': 11}
            )
            
            # Make percentage text bold
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(12)
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            # Save to bytes
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            
            return image_base64
        
        except Exception as e:
            logger.error(f"Error generating pie chart: {e}")
            return ""
    
    @staticmethod
    def generate_line_chart(
        data: Dict[str, List[float]],
        title: str,
        xlabel: str = "",
        ylabel: str = "",
        figsize: Tuple[int, int] = (10, 6)
    ) -> str:
        """
        Generate line chart for time series data
        data format: {'Series1': [val1, val2, ...], 'Series2': [...]}
        """
        try:
            fig, ax = plt.subplots(figsize=figsize)
            
            for label, values in data.items():
                ax.plot(range(len(values)), values, marker='o', label=label, linewidth=2)
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save to bytes
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            
            return image_base64
        
        except Exception as e:
            logger.error(f"Error generating line chart: {e}")
            return ""


class ChartAnalyticsService:
    """Main service for detecting numeric data and generating charts"""
    
    def __init__(self):
        self.detector = NumericDataDetector()
        self.chart_gen = ChartGenerator()
    
    def _add_chart_with_metadata(self, charts_list: List[Dict], chart_data: Dict):
        """Helper to add chart with ID and selection flag"""
        import uuid
        chart_data['id'] = f"chart_{uuid.uuid4().hex[:8]}"
        chart_data['selected_for_report'] = True  # Default to selected
        charts_list.append(chart_data)
    
    def _create_json_chart_data(
        self,
        chart_type: str,
        category: str,
        title: str,
        data_dict: Dict[str, float],
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create structured JSON chart data for frontend rendering
        
        Args:
            chart_type: 'bar', 'pie', 'line'
            category: 'gender', 'employees', 'emissions', etc.
            title: Chart title
            data_dict: {label: value} dictionary
            config: Optional config (xlabel, ylabel, colors, etc.)
        
        Returns:
            Structured chart data with colors and configuration
        """
        import uuid
        
        # Default color palettes by category
        color_palettes = {
            'gender': ['#FF6B6B', '#4ECDC4', '#45B7D1'],
            'employees': ['#F7B731', '#5F27CD', '#00D2D3', '#FF9FF3'],
            'emissions': ['#EE5A24', '#F79F1F', '#FEA47F'],
            'energy': ['#10AC84', '#1DD1A1', '#48DBFB'],
            'waste': ['#8395A7', '#576574', '#222F3E'],
            'percentages': ['#5F27CD', '#00D2D3', '#FF9FF3', '#54A0FF'],
            'financial': ['#1E90FF', '#00CED1', '#4682B4'],
            'default': ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE']
        }
        
        colors = color_palettes.get(category, color_palettes['default'])
        
        # Convert data_dict to array format with colors
        data_array = []
        for idx, (label, value) in enumerate(data_dict.items()):
            data_array.append({
                'label': label,
                'value': value,
                'color': colors[idx % len(colors)]
            })
        
        # Default config
        default_config = {
            'xlabel': '',
            'ylabel': 'Value',
            'show_legend': True,
            'show_values': True,
            'colors': colors
        }
        
        if config:
            default_config.update(config)
        
        return {
            'id': f"chart_{uuid.uuid4().hex[:8]}",
            'type': chart_type,
            'category': category,
            'title': title,
            'data': data_array,
            'config': default_config,
            'selected_for_report': True
        }
    
    def analyze_and_generate_charts(
        self,
        text: str,
        disclosure_code: str = "",
        output_format: str = "json"  # "json" for structured data, "png" for matplotlib images
    ) -> Dict[str, Any]:
        """
        Analyze text for numeric data and generate appropriate charts
        
        Args:
            text: AI answer text to analyze
            disclosure_code: ESRS code (e.g., S1-9)
            output_format: "json" (structured data for frontend) or "png" (matplotlib images)
        
        Returns:
            {
                'has_numeric_data': bool,
                'numeric_data': List[Dict],
                'categories': Dict,
                'charts': List[Dict],  # format depends on output_format
                'tables': List[Dict]    # Structured data tables
            }
            
        Chart format when output_format="json":
            {
                'id': 'chart_abc123',
                'type': 'bar|pie|line',
                'category': 'gender|employees|emissions|...',
                'title': 'Chart Title',
                'data': [{'label': 'Women', 'value': 69, 'color': '#FF6B6B'}, ...],
                'config': {'xlabel': 'Gender', 'ylabel': 'Percentage (%)', 'colors': [...]}
                'selected_for_report': True
            }
            
        Chart format when output_format="png":
            {
                'id': 'chart_abc123',
                'type': 'bar|pie|line',
                'category': 'gender|employees|emissions|...',
                'title': 'Chart Title',
                'data': {...},  # Original data dict
                'image_base64': '...',  # Base64 PNG image
                'selected_for_report': True
            }
        """
        result = {
            'has_numeric_data': False,
            'numeric_data': [],
            'categories': {},
            'charts': [],
            'tables': [],
            'output_format': output_format
        }
        
        # Extract numeric data
        numeric_data = self.detector.extract_numeric_data(text)
        if not numeric_data:
            return result
        
        result['has_numeric_data'] = True
        result['numeric_data'] = numeric_data
        
        # Categorize data
        categories = self.detector.categorize_data(numeric_data)
        result['categories'] = categories
        
        # Generate charts for each category
        
        # 1. Gender statistics - Pie & Bar chart
        if categories['gender_stats']:
            gender_data = {}
            for item in categories['gender_stats']:
                # Cleanup labels - extract key gender terms
                raw_label = item.get('label', item.get('unit', 'Unknown'))
                label = raw_label
                
                # Clean up common patterns
                if 'women' in raw_label.lower() or 'female' in raw_label.lower():
                    label = 'Women'
                elif 'men' in raw_label.lower() or 'male' in raw_label.lower():
                    label = 'Men'
                elif '%' in raw_label:
                    # Extract just the key term before %
                    label = raw_label.split('%')[0].strip().title()
                
                gender_data[label] = item['value']
            
            if gender_data:
                if output_format == "json":
                    # JSON format for frontend interactive rendering
                    pie_chart = self._create_json_chart_data(
                        chart_type='pie',
                        category='gender',
                        title='Gender Distribution',
                        data_dict=gender_data,
                        config={'ylabel': 'Percentage (%)'}
                    )
                    result['charts'].append(pie_chart)
                    
                    bar_chart = self._create_json_chart_data(
                        chart_type='bar',
                        category='gender',
                        title='Gender Statistics',
                        data_dict=gender_data,
                        config={'xlabel': 'Gender', 'ylabel': 'Count'}
                    )
                    result['charts'].append(bar_chart)
                else:
                    # PNG format for backward compatibility
                    pie_image = self.chart_gen.generate_pie_chart(
                        gender_data,
                        title=f"{disclosure_code} - Gender Distribution"
                    )
                    if pie_image:
                        self._add_chart_with_metadata(result['charts'], {
                            'type': 'pie',
                            'category': 'gender',
                            'title': 'Gender Distribution',
                            'data': gender_data,
                            'image_base64': pie_image
                        })
                    
                    # Bar chart
                    bar_image = self.chart_gen.generate_bar_chart(
                        gender_data,
                        title=f"{disclosure_code} - Gender Statistics",
                        ylabel="Number of Employees"
                    )
                    if bar_image:
                        self._add_chart_with_metadata(result['charts'], {
                            'type': 'bar',
                            'category': 'gender',
                            'title': 'Gender Statistics',
                            'data': gender_data,
                            'image_base64': bar_image
                        })
                
                # Table
                result['tables'].append({
                    'title': 'Gender Statistics',
                    'headers': ['Category', 'Count'],
                    'rows': [[k, v] for k, v in gender_data.items()]
                })
        
        # 2. Employee statistics
        if categories['employee_stats']:
            emp_data = {}
            for item in categories['employee_stats']:
                raw_label = item.get('label', 'Employees').lower()
                
                # Clean up employee labels
                if 'full-time' in raw_label or 'full time' in raw_label:
                    label = 'Full-time'
                elif 'part-time' in raw_label or 'part time' in raw_label:
                    label = 'Part-time'
                elif 'permanent' in raw_label:
                    label = 'Permanent'
                elif 'temporary' in raw_label or 'contract' in raw_label:
                    label = 'Temporary'
                elif 'total' in raw_label or 'all' in raw_label:
                    label = 'Total Employees'
                else:
                    # Extract first meaningful word
                    label = raw_label.split()[0].strip().title() if raw_label.split() else 'Employees'
                
                emp_data[label] = item['value']
            
            if emp_data:
                if output_format == "json":
                    bar_chart = self._create_json_chart_data(
                        chart_type='bar',
                        category='employees',
                        title='Employee Statistics',
                        data_dict=emp_data,
                        config={'xlabel': 'Employee Type', 'ylabel': 'Count'}
                    )
                    result['charts'].append(bar_chart)
                else:
                    bar_image = self.chart_gen.generate_bar_chart(
                        emp_data,
                        title=f"{disclosure_code} - Employee Statistics",
                        ylabel="Count"
                    )
                    if bar_image:
                        self._add_chart_with_metadata(result['charts'], {
                            'type': 'bar',
                            'category': 'employees',
                            'title': 'Employee Statistics',
                            'data': emp_data,
                            'image_base64': bar_image
                        })
        
        # 3. Emissions data
        if categories['emissions']:
            emissions_data = {}
            for item in categories['emissions']:
                raw_label = item.get('label', 'Emissions').lower()
                
                # Clean up emissions labels
                if 'scope 1' in raw_label or 'scope1' in raw_label:
                    label = 'Scope 1'
                elif 'scope 2' in raw_label or 'scope2' in raw_label:
                    label = 'Scope 2'
                elif 'scope 3' in raw_label or 'scope3' in raw_label:
                    label = 'Scope 3'
                elif 'co2' in raw_label or 'carbon' in raw_label:
                    label = 'CO2 Emissions'
                elif 'total' in raw_label:
                    label = 'Total Emissions'
                else:
                    # Extract first meaningful word
                    label = raw_label.split()[0].strip().title() if raw_label.split() else 'Emissions'
                
                emissions_data[label] = item['value']
            
            if emissions_data:
                if output_format == "json":
                    bar_chart = self._create_json_chart_data(
                        chart_type='bar',
                        category='emissions',
                        title='Emissions Data',
                        data_dict=emissions_data,
                        config={'xlabel': 'Scope', 'ylabel': 'CO2 (tons)'}
                    )
                    result['charts'].append(bar_chart)
                else:
                    bar_image = self.chart_gen.generate_bar_chart(
                        emissions_data,
                        title=f"{disclosure_code} - Emissions",
                        ylabel="CO2 (tons)"
                    )
                    if bar_image:
                        self._add_chart_with_metadata(result['charts'], {
                            'type': 'bar',
                            'category': 'emissions',
                            'title': 'Emissions Data',
                            'data': emissions_data,
                            'image_base64': bar_image
                        })
        
        # 4. Percentages
        if categories['percentages']:
            pct_data = {}
            for item in categories['percentages']:
                raw_label = item.get('label', 'Value').lower()
                
                # Clean up percentage labels
                if 'renewable' in raw_label:
                    label = 'Renewable Energy'
                elif 'recycl' in raw_label:
                    label = 'Recycling Rate'
                elif 'turnover' in raw_label or 'attrition' in raw_label:
                    label = 'Turnover Rate'
                elif 'training' in raw_label:
                    label = 'Training Coverage'
                else:
                    # Title case first 2-3 meaningful words
                    words = raw_label.split()[:3]
                    label = ' '.join(w.title() for w in words) if words else 'Value'
                
                pct_data[label] = item['value']
            
            if pct_data:
                bar_image = self.chart_gen.generate_bar_chart(
                    pct_data,
                    title=f"{disclosure_code} - Percentages",
                    ylabel="Percentage (%)"
                )
                if bar_image:
                    self._add_chart_with_metadata(result['charts'], {
                        'type': 'bar',
                        'category': 'percentages',
                        'title': 'Percentage Data',
                        'data': pct_data,
                        'image_base64': bar_image
                    })
        
        # 5. Financial data (currency)
        if categories['financial']:
            fin_data = {}
            for item in categories['financial']:
                raw_label = item.get('label', 'Amount').lower()
                
                # Clean up financial labels
                if 'revenue' in raw_label or 'turnover' in raw_label:
                    label = 'Revenue'
                elif 'profit' in raw_label or 'income' in raw_label:
                    label = 'Profit'
                elif 'cost' in raw_label or 'expense' in raw_label:
                    label = 'Costs'
                elif 'investment' in raw_label:
                    label = 'Investment'
                elif 'salary' in raw_label or 'wage' in raw_label:
                    label = 'Salaries'
                else:
                    # Title case first 2 words
                    words = raw_label.split()[:2]
                    label = ' '.join(w.title() for w in words) if words else 'Amount'
                
                fin_data[label] = item['value']
            
            if fin_data:
                bar_image = self.chart_gen.generate_bar_chart(
                    fin_data,
                    title=f"{disclosure_code} - Financial Data",
                    ylabel=f"Amount ({categories['financial'][0].get('unit', '€')})"
                )
                if bar_image:
                    self._add_chart_with_metadata(result['charts'], {
                        'type': 'bar',
                        'category': 'financial',
                        'title': 'Financial Data',
                        'data': fin_data,
                        'image_base64': bar_image
                    })
        
        # 6. Time series data (line chart)
        if categories['time_series']:
            # Sort by year
            sorted_data = sorted(categories['time_series'], key=lambda x: x.get('year', 0))
            years = [str(item.get('year', '')) for item in sorted_data]
            values = [item['value'] for item in sorted_data]
            
            if len(years) > 1:
                # Create dict for line chart
                time_data = {years[i]: values[i] for i in range(len(years))}
                
                bar_image = self.chart_gen.generate_bar_chart(
                    time_data,
                    title=f"{disclosure_code} - Time Series",
                    xlabel="Year",
                    ylabel="Value"
                )
                if bar_image:
                    self._add_chart_with_metadata(result['charts'], {
                        'type': 'bar',
                        'category': 'time_series',
                        'title': 'Time Series Data',
                        'data': time_data,
                        'image_base64': bar_image
                    })
                
                # Table
                result['tables'].append({
                    'title': 'Time Series Data',
                    'headers': ['Year', 'Value'],
                    'rows': [[y, v] for y, v in zip(years, values)]
                })
        
        return result
