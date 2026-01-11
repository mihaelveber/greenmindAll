"""
OpenAI Responses API Integration Service
Handles file uploads, vector store management, and file_search tool integration
"""
import os
import logging
from typing import Optional, Tuple, List, Dict, Any
from django.conf import settings
import openai

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for managing OpenAI Files and Vector Stores for Responses API file_search tool"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def generate(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 4096, **kwargs) -> Dict[str, Any]:
        """
        Generate completion using OpenAI
        
        Args:
            model: Model identifier (gpt-4o, gpt-4o-mini, etc.)
            messages: List of message dicts with 'role' and 'content'
            temperature: Randomness (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Dict with 'message' and 'usage' keys
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            result = {
                'message': {
                    'role': response.choices[0].message.role,
                    'content': response.choices[0].message.content
                },
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'model': response.model,
                'provider': 'openai'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def upload_file_to_openai(self, file_path: str, filename: str) -> Optional[str]:
        """
        Upload a file to OpenAI Files API for use with vector stores
        
        Args:
            file_path: Full path to the file on disk
            filename: Original filename
            
        Returns:
            OpenAI file_id or None if upload failed
        """
        try:
            with open(file_path, 'rb') as file:
                response = self.client.files.create(
                    file=file,
                    purpose='assistants'  # Required for vector store usage
                )
            
            logger.info(f'Uploaded file to OpenAI: {filename} -> {response.id}')
            return response.id
            
        except Exception as e:
            logger.error(f'Failed to upload file to OpenAI: {filename}: {str(e)}')
            return None
    
    def get_or_create_vector_store(self, user_id: int, vector_store_id: Optional[str] = None) -> Tuple[str, bool]:
        """
        Get existing vector store or create new one for user
        
        Args:
            user_id: Django user ID
            vector_store_id: Existing vector store ID (if any)
            
        Returns:
            Tuple of (vector_store_id, created: bool)
        """
        # If user already has a vector store, return it
        if vector_store_id:
            try:
                # Verify it still exists
                self.client.vector_stores.retrieve(vector_store_id)
                logger.info(f'Using existing vector store for user {user_id}: {vector_store_id}')
                return vector_store_id, False
            except Exception as e:
                logger.warning(f'Vector store {vector_store_id} not found, creating new one: {str(e)}')
        
        # Create new vector store
        try:
            response = self.client.vector_stores.create(
                name=f'User {user_id} Documents',
                expires_after={
                    'anchor': 'last_active_at',
                    'days': 365  # Expire after 1 year of inactivity
                }
            )
            
            logger.info(f'Created vector store for user {user_id}: {response.id}')
            return response.id, True
            
        except Exception as e:
            logger.error(f'Failed to create vector store for user {user_id}: {str(e)}')
            raise
    
    def add_file_to_vector_store(self, vector_store_id: str, file_id: str, 
                                  is_global: bool = False, disclosure_id: Optional[int] = None) -> bool:
        """
        Add a file to a vector store with metadata for filtering
        
        Args:
            vector_store_id: Vector store ID
            file_id: OpenAI file ID
            is_global: Whether document is global (auto-linked to all disclosures)
            disclosure_id: Specific disclosure ID if not global
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare metadata attributes for filtering
            attributes = {
                "is_global": "true" if is_global else "false"
            }
            
            # Add disclosure_id for specific documents
            if not is_global and disclosure_id:
                attributes["disclosure_id"] = str(disclosure_id)
            
            # Use create_and_poll to wait for file processing
            # Note: attributes parameter may not be supported in older SDK versions
            # If it fails, fallback to basic creation without attributes
            try:
                self.client.vector_stores.files.create_and_poll(
                    vector_store_id=vector_store_id,
                    file_id=file_id,
                    attributes=attributes
                )
                logger.info(f'Added file {file_id} to vector store {vector_store_id} with metadata: {attributes}')
            except TypeError:
                # Fallback: SDK doesn't support attributes yet
                self.client.vector_stores.files.create_and_poll(
                    vector_store_id=vector_store_id,
                    file_id=file_id
                )
                logger.warning(f'Added file {file_id} without metadata (SDK limitation)')
            
            return True
            
        except Exception as e:
            logger.error(f'Failed to add file {file_id} to vector store {vector_store_id}: {str(e)}')
            return False
    
    def remove_file_from_vector_store(self, vector_store_id: str, file_id: str) -> bool:
        """
        Remove a file from a vector store
        
        Args:
            vector_store_id: Vector store ID
            file_id: OpenAI file ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.vector_stores.files.delete(
                vector_store_id=vector_store_id,
                file_id=file_id
            )
            
            logger.info(f'Removed file {file_id} from vector store {vector_store_id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to remove file {file_id} from vector store {vector_store_id}: {str(e)}')
            return False
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from OpenAI (removes from all vector stores)
        
        Args:
            file_id: OpenAI file ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.files.delete(file_id)
            logger.info(f'Deleted file from OpenAI: {file_id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to delete file from OpenAI: {file_id}: {str(e)}')
            return False
    
    def generate_answer_with_structured_charts(self, prompt: str, vector_store_id: str, 
                                                 disclosure_code: str) -> dict:
        """
        Generate AI answer with Structured Outputs for chart data
        
        Uses OpenAI's Structured Outputs API to ensure chart data is properly formatted
        This is more reliable than regex extraction!
        
        Args:
            prompt: The user's question/prompt
            vector_store_id: Vector store ID for file_search
            disclosure_code: ESRS disclosure code (e.g., "S1-9")
            
        Returns:
            {
                'answer': str,  # Main AI answer text
                'charts': [     # Structured chart data
                    {
                        'type': 'bar|pie|line',
                        'category': 'gender|employees|emissions|percentages|financial',
                        'title': 'Chart Title',
                        'data': [{'label': 'Women', 'value': 69, 'color': '#FF6B6B'}, ...],
                        'config': {'xlabel': '...', 'ylabel': '...', 'colors': [...]}
                    }
                ],
                'tables': [     # Structured table data
                    {
                        'title': 'Table Title',
                        'headers': ['Column1', 'Column2'],
                        'rows': [['Value1', 'Value2'], ...]
                    }
                ]
            }
        """
        try:
            # Define JSON schema for structured response
            chart_schema = {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "Comprehensive answer to the user's question in Markdown format"
                    },
                    "charts": {
                        "type": "array",
                        "description": "Chart data extracted from numeric information in the answer",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["bar", "pie", "line"],
                                    "description": "Type of chart visualization"
                                },
                                "category": {
                                    "type": "string",
                                    "enum": ["gender", "employees", "emissions", "percentages", "financial", "time_series", "age", "diversity"],
                                    "description": "Category of data"
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Descriptive title for the chart"
                                },
                                "data": {
                                    "type": "array",
                                    "description": "Data points for the chart",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "label": {
                                                "type": "string",
                                                "description": "Label for this data point (e.g., 'Women', 'Men')"
                                            },
                                            "value": {
                                                "type": "number",
                                                "description": "Numeric value"
                                            }
                                        },
                                        "required": ["label", "value"],
                                        "additionalProperties": False
                                    }
                                },
                                "config": {
                                    "type": "object",
                                    "properties": {
                                        "xlabel": {"type": "string"},
                                        "ylabel": {"type": "string"},
                                        "unit": {"type": "string"}
                                    },
                                    "additionalProperties": False
                                }
                            },
                            "required": ["type", "category", "title", "data"],
                            "additionalProperties": False
                        }
                    },
                    "tables": {
                        "type": "array",
                        "description": "Data tables for structured numeric information",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "headers": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "rows": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                }
                            },
                            "required": ["title", "headers", "rows"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["answer", "charts", "tables"],
                "additionalProperties": False
            }
            
            # Create chat completion with Structured Outputs
            response = self.client.chat.completions.create(
                model="gpt-4o-2024-08-06",  # Structured Outputs supported
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an ESRS (European Sustainability Reporting Standards) expert.
                        
Analyze the provided documents and answer questions about {disclosure_code}.

IMPORTANT: Extract ALL numeric data into charts and tables:
- Gender statistics (women %, men %) → bar chart (preferred), category='gender'
- Employee statistics (full-time, part-time) → bar chart, category='employees'
- Emissions data (Scope 1/2/3, CO2) → bar chart, category='emissions'  
- Percentages (renewable energy, recycling rate) → bar chart, category='percentages'
- Financial data (revenue, costs) → bar chart, category='financial'
- Age distribution → bar chart (preferred), category='age'
- Diversity metrics → bar chart (preferred), category='diversity'
- Time series data → line chart only for trends over time

DEFAULT: Use bar chart unless specifically showing time-based trends (line) or part-of-whole relationships (pie).

Provide comprehensive answers in Markdown format with proper headings, lists, and bold text."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "esrs_answer_with_charts",
                        "strict": True,
                        "schema": chart_schema
                    }
                },
                tools=[{
                    "type": "file_search",
                    "file_search": {
                        "vector_store_ids": [vector_store_id]
                    }
                }]
            )
            
            # Parse structured response
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Add colors to chart data points
            color_palettes = {
                'gender': ['#FF6B6B', '#4ECDC4', '#45B7D1'],
                'employees': ['#F7B731', '#5F27CD', '#00D2D3', '#FF9FF3'],
                'emissions': ['#EE5A24', '#F79F1F', '#FEA47F'],
                'percentages': ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'],
                'financial': ['#1abc9c', '#e67e22', '#34495e', '#16a085'],
                'age': ['#9b59b6', '#3498db', '#e74c3c', '#f39c12'],
                'diversity': ['#1abc9c', '#3498db', '#e74c3c', '#f39c12', '#9b59b6'],
                'time_series': ['#3498db', '#2ecc71']
            }
            
            # Add colors and IDs to charts
            import uuid
            for chart in result.get('charts', []):
                chart['id'] = f"chart_{uuid.uuid4().hex[:8]}"
                chart['selected_for_report'] = True
                
                # Add colors to data points
                palette = color_palettes.get(chart.get('category', 'percentages'), color_palettes['percentages'])
                for i, data_point in enumerate(chart.get('data', [])):
                    data_point['color'] = palette[i % len(palette)]
            
            logger.info(f'Generated structured answer with {len(result.get("charts", []))} charts and {len(result.get("tables", []))} tables')
            return result
            
        except Exception as e:
            logger.error(f'Failed to generate structured answer: {str(e)}')
            # Fallback to simple answer
            return {
                'answer': f'Error generating answer: {str(e)}',
                'charts': [],
                'tables': []
            }
    
    def extract_charts_from_answer(self, answer_text: str, disclosure_code: str) -> dict:
        """
        Extract chart and table data from an AI-generated answer
        
        This is a SEPARATE AI request that analyzes the answer text and returns
        structured chart data. This allows users to still edit charts via AI!
        
        Args:
            answer_text: The AI-generated answer text
            disclosure_code: ESRS disclosure code (e.g., "S1-9")
            
        Returns:
            {
                'charts': [
                    {
                        'type': 'bar|pie|line',
                        'category': 'gender|employees|emissions|...',
                        'title': 'Chart Title',
                        'data': [{'label': 'Women', 'value': 69, 'color': '#FF6B6B'}, ...],
                        'config': {'xlabel': '...', 'ylabel': '...'}
                    }
                ],
                'tables': [...]
            }
        """
        try:
            # Define JSON schema for chart extraction
            chart_extraction_schema = {
                "type": "object",
                "properties": {
                    "charts": {
                        "type": "array",
                        "description": "Extract ALL numeric data as charts. Look for: percentages, counts, financial data, statistics, measurements.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["bar", "pie", "line"],
                                    "description": "Best visualization type for this data"
                                },
                                "category": {
                                    "type": "string",
                                    "enum": ["gender", "employees", "emissions", "percentages", "financial", "time_series", "age", "diversity", "other"],
                                    "description": "Data category"
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Clear, descriptive title"
                                },
                                "data": {
                                    "type": "array",
                                    "description": "Data points extracted from the answer",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "label": {
                                                "type": "string",
                                                "description": "Clean label (e.g., 'Women', 'Men', 'Scope 1')"
                                            },
                                            "value": {
                                                "type": "number",
                                                "description": "Numeric value"
                                            }
                                        },
                                        "required": ["label", "value"],
                                        "additionalProperties": False
                                    },
                                    "minItems": 1
                                },
                                "config": {
                                    "type": "object",
                                    "properties": {
                                        "xlabel": {"type": "string"},
                                        "ylabel": {"type": "string"},
                                        "unit": {"type": "string"}
                                    },
                                    "additionalProperties": False
                                }
                            },
                            "required": ["type", "category", "title", "data"],
                            "additionalProperties": False
                        }
                    },
                    "tables": {
                        "type": "array",
                        "description": "Extract structured data tables",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "headers": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "rows": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                }
                            },
                            "required": ["title", "headers", "rows"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["charts", "tables"],
                "additionalProperties": False
            }
            
            # Define function schema for OpenAI Function Calling
            function_schema = {
                "name": "extract_charts_and_tables",
                "description": "Extract numeric data from text and structure it as charts and tables. Use this to identify all percentages, counts, measurements, and statistics.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "charts": {
                            "type": "array",
                            "description": "List of all charts extracted from the text",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["bar", "pie", "line"],
                                        "description": "Chart type"
                                    },
                                    "category": {
                                        "type": "string",
                                        "enum": ["gender", "employees", "emissions", "percentages", "financial", "time_series", "age", "diversity", "other"],
                                        "description": "Data category"
                                    },
                                    "title": {
                                        "type": "string",
                                        "description": "Chart title"
                                    },
                                    "data": {
                                        "type": "array",
                                        "description": "Array of data points with labels and values",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "label": {
                                                    "type": "string",
                                                    "description": "Category name (e.g., 'Women', 'Men', 'Under 30'). MUST be noun/name, NOT verb!"
                                                },
                                                "value": {
                                                    "type": "number",
                                                    "description": "Numeric value"
                                                }
                                            },
                                            "required": ["label", "value"]
                                        }
                                    }
                                },
                                "required": ["type", "category", "title", "data"]
                            }
                        },
                        "tables": {
                            "type": "array",
                            "description": "List of tables extracted",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "headers": {"type": "array", "items": {"type": "string"}},
                                    "rows": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}
                                },
                                "required": ["title", "headers", "rows"]
                            }
                        }
                    },
                    "required": ["charts", "tables"]
                }
            }
            
            # Create chart extraction request with Function Calling
            temperature = 0.0  # Use deterministic extraction
            response = self.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                temperature=temperature,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a data extraction specialist. Your task is to extract numeric data from text and call the extract_charts_and_tables function.

**CRITICAL LABEL RULES:**
- Labels MUST be CATEGORY NAMES: "Women", "Men", "Under 30", "Management Positions"
- Labels MUST NOT be VERBS: NOT "Hold", "Occupy", "Represent", "Comprise", "Of"
- Labels MUST NOT be generic words: NOT "Value", "Range", "Data"

**EXAMPLES:**
✅ CORRECT: "Women", "Men", "Under 30", "31-50", "Leadership Roles", "Management Positions"
❌ WRONG: "Hold", "Occupy", "Of", "Value", "Comprise", "Up", "Range"

**TEXT PARSING:**
- "Women represent 69%, Men 31%" → labels: ["Women", "Men"]
- "Women hold 31% of management" → label: "Women in Management" or "Management Positions (Women)"
- "Age Under 30: 10%" → label: "Under 30"
- "Leadership roles: 56%" → label: "Leadership Roles"

Extract ALL numeric data and call the function."""
                    },
                    {
                        "role": "user",
                        "content": f"Extract all charts and tables from this text:\n\n{answer_text}"
                    }
                ],
                functions=[function_schema],
                function_call={"name": "extract_charts_and_tables"}
            )
            
            # Parse function call response
            import json
            function_call = response.choices[0].message.function_call
            if not function_call or function_call.name != "extract_charts_and_tables":
                logger.error("AI did not call the extraction function!")
                return {'charts': [], 'tables': []}
            
            # Debug: Print raw arguments
            print(f'📋 RAW FUNCTION ARGUMENTS (first 1000 chars):')
            print(function_call.arguments[:1000])
            
            # Parse JSON response (OpenAI returns valid JSON)
            try:
                result = json.loads(function_call.arguments)
            except json.JSONDecodeError as e:
                logger.error(f'JSON parsing error: {e}')
                logger.error(f'Raw arguments: {function_call.arguments[:500]}')
                return {'charts': [], 'tables': []}
            
            print(f'✅ FUNCTION CALL SUCCESS: AI called extract_charts_and_tables')
            print(f'   Arguments (first 500 chars): {function_call.arguments[:500]}')
            
            # CRITICAL: Validate and fix chart data structure
            validated_charts = []
            total_charts = len(result.get('charts', []))
            print(f'========== VALIDATION START: {total_charts} charts to validate ==========')
            
            for i, chart in enumerate(result.get('charts', [])):
                data = chart.get('data')
                data_type = type(data).__name__
                print(f'Chart {i} "{chart.get("title")}": data_type={data_type}, len={len(data) if hasattr(data, "__len__") else "N/A"}')
                
                if data_type == 'dict':
                    print(f'  → DICT DETECTED! Keys: {list(data.keys())}')
                    logger.error(f'CRITICAL: Chart {i} ({chart.get("title")}) has DICT structure! Converting to array or skipping.')
                    # Try to convert dict to array
                    try:
                        converted_data = [{'label': str(k), 'value': float(v)} for k, v in data.items()]
                        chart['data'] = converted_data
                        print(f'  → Successfully converted dict to array: {len(converted_data)} items')
                        logger.info(f'Successfully converted dict to array for chart {i}')
                    except Exception as e:
                        print(f'  → Conversion FAILED: {e}')
                        logger.error(f'Failed to convert dict for chart {i}: {e}. SKIPPING this chart.')
                        continue  # Skip this chart entirely
                
                elif data_type == 'list':
                    print(f'  → List structure OK, validating items...')
                    # Validate array structure
                    if len(data) == 0:
                        print(f'  → SKIP: Empty array!')
                        logger.warning(f'Chart {i} ({chart.get("title")}) has empty data array. SKIPPING.')
                        continue
                    
                    # Check if all items are dicts with label and value
                    if not all(isinstance(item, dict) and 'label' in item and 'value' in item for item in data):
                        print(f'  → SKIP: Invalid array items!')
                        logger.error(f'Chart {i} ({chart.get("title")}) has invalid array items. SKIPPING.')
                        continue
                    
                    print(f'  → VALID! Adding to validated_charts')
                
                else:
                    print(f'  → SKIP: Unexpected data type!')
                    logger.error(f'Chart {i} ({chart.get("title")}) has unexpected data type {data_type}. SKIPPING.')
                    continue
                
                validated_charts.append(chart)
                print(f'  → Chart {i} added to validated list (total: {len(validated_charts)})')
            
            # Replace with validated charts
            result['charts'] = validated_charts
            print(f'========== VALIDATION END: {len(validated_charts)} valid charts ==========')
            logger.info(f'Validation complete: {len(validated_charts)} valid charts out of {total_charts} total')
            
            # Add colors and IDs to VALIDATED charts
            color_palettes = {
                'gender': ['#FF6B6B', '#4ECDC4', '#45B7D1'],
                'employees': ['#F7B731', '#5F27CD', '#00D2D3', '#FF9FF3'],
                'emissions': ['#EE5A24', '#F79F1F', '#FEA47F'],
                'percentages': ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'],
                'financial': ['#1abc9c', '#e67e22', '#34495e', '#16a085'],
                'age': ['#9b59b6', '#3498db', '#e74c3c', '#f39c12'],
                'diversity': ['#1abc9c', '#3498db', '#e74c3c', '#f39c12', '#9b59b6'],
                'time_series': ['#3498db', '#2ecc71'],
                'other': ['#95a5a6', '#7f8c8d', '#bdc3c7']
            }
            
            import uuid
            # CRITICAL: Process VALIDATED charts only
            for chart in validated_charts:
                chart['id'] = f"chart_{uuid.uuid4().hex[:8]}"
                chart['selected_for_report'] = True
                
                # Add colors
                category = chart.get('category', 'other')
                palette = color_palettes.get(category, color_palettes['other'])
                
                for i, data_point in enumerate(chart.get('data', [])):
                    data_point['color'] = palette[i % len(palette)]
            
            logger.info(f'Extracted {len(validated_charts)} charts and {len(result.get("tables", []))} tables from answer')
            return result
            
        except Exception as e:
            logger.error(f'Failed to extract charts from answer: {str(e)}')
            return {'charts': [], 'tables': []}
