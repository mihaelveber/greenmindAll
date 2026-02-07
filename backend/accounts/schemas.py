from ninja import Schema
from typing import Optional
from datetime import datetime
class ErrorSchema(Schema):
    error: str
class UserSchema(Schema):
    id: int
    email: str
    username: str
    avatar: Optional[str] = None
    oauth_provider: Optional[str] = None
    is_active: bool
    date_joined: datetime
    wizard_completed: bool = False
    company_type: Optional[str] = None
    website_url: Optional[str] = None
    allowed_standards: list[str] = []
    is_staff: bool = False
    is_organization_owner: bool = True

class LoginSchema(Schema):
    email: str
    password: str

class RegisterSchema(Schema):
    email: str
    username: str
    password: str
    password_confirm: str

class TokenSchema(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserSchema

class OAuthCallbackSchema(Schema):
    code: str
    state: Optional[str] = None

class MessageSchema(Schema):
    message: str
    success: bool = True

class ErrorSchema(Schema):
    error: str

class CompanyTypeSchema(Schema):
    company_type: str
    website_url: Optional[str] = None

class DocumentSchema(Schema):
    id: int
    file_name: str
    file_size: int
    file_type: str
    uploaded_at: datetime
    is_global: bool = False
    rag_processing_status: Optional[str] = None
    rag_chunks_count: Optional[int] = None
    success: bool = True


class ESRSCategorySchema(Schema):
    id: int
    name: str
    code: str
    description: str
    order: int
    standard_type: str


class ESRSDisclosureSchema(Schema):
    id: int
    code: str
    name: str
    description: str
    requirement_text: str
    is_mandatory: bool
    order: int
    parent_id: Optional[int] = None
    sub_disclosures: list['ESRSDisclosureSchema'] = []


class ESRSStandardSchema(Schema):
    id: int
    code: str
    name: str
    description: str
    order: int
    category: ESRSCategorySchema
    ai_prompt: Optional[str] = None


class ESRSStandardDetailSchema(Schema):
    id: int
    code: str
    name: str
    description: str
    order: int
    category: ESRSCategorySchema
    disclosures: list[ESRSDisclosureSchema]


class SaveNotesSchema(Schema):
    disclosure_id: int
    notes: str

class SaveManualAnswerSchema(Schema):
    disclosure_id: int
    manual_answer: str


class SaveFinalAnswerSchema(Schema):
    disclosure_id: int
    final_answer: str


class LinkDocumentSchema(Schema):
    disclosure_id: int
    document_id: int
    notes: Optional[str] = None
    is_excluded: Optional[bool] = False


class GetAIAnswerSchema(Schema):
    disclosure_id: int
    ai_temperature: float = 0.2
    model_id: str = 'gpt-4o'  # Default model
    language: Optional[str] = None


class BulkAIAnswerSchema(Schema):
    ai_temperature: float = 0.2
    model_id: str = 'gpt-4o'
    language: Optional[str] = None


class ESRSUserResponseSchema(Schema):
    id: int
    disclosure_id: int
    notes: Optional[str] = None
    manual_answer: Optional[str] = None
    is_completed: bool
    ai_answer: Optional[str] = None
    final_answer: Optional[str] = None
    ai_sources: Optional[dict] = None
    # Chart & Analytics fields
    numeric_data: Optional[list] = None
    chart_data: Optional[list] = None  # List of {type, title, data, image_base64}
    table_data: Optional[list] = None  # List of {title, headers, rows}
    # AI Generation Settings
    ai_temperature: float = 0.2
    confidence_score: Optional[float] = None
    # Team Assignment
    assigned_to: Optional[int] = None  # User ID of assigned team member
    created_at: datetime
    updated_at: datetime


class DocumentEvidenceSchema(Schema):
    id: int
    document_id: int
    document: DocumentSchema  # Full document object
    linked_at: datetime
    notes: Optional[str] = None


class AITaskStatusSchema(Schema):
    id: int
    task_id: str
    task_type: str
    status: str
    progress: int
    total_items: int
    completed_items: int
    result: Optional[str] = None
    error_message: Optional[str] = None
    disclosure_code: Optional[str] = None
    standard_code: Optional[str] = None
    document_name: Optional[str] = None
    
    # Detailed progress tracking
    current_step: Optional[str] = None
    steps_completed: Optional[list] = None
    processing_steps: Optional[list] = None  # TIER RAG processing steps for ThinkingProcess UI
    documents_used: Optional[int] = None
    chunks_used: Optional[int] = None
    confidence_score: Optional[float] = None
    estimated_cost_usd: Optional[float] = None
    total_tokens: Optional[int] = None
    reasoning_summary: Optional[str] = None  # AI reasoning from OpenAI o1 models
    
    created_at: datetime
    updated_at: datetime


class StartAITaskResponse(Schema):
    task_id: str
    message: str


class UpdateNotesSchema(Schema):
    notes: Optional[str] = None
    manual_answer: Optional[str] = None
    ai_temperature: Optional[float] = None

class GenerateImageSchema(Schema):
    prompt: str


# Version System Schemas
class StartConversationSchema(Schema):
    item_type: str  # TEXT, CHART, IMAGE, TABLE
    item_id: int
    disclosure_id: int


class SendMessageSchema(Schema):
    message: str  # User's refinement instruction


class ConversationMessageSchema(Schema):
    role: str
    content: str
    timestamp: str


class ConversationSchema(Schema):
    id: str
    item_type: str
    item_id: int
    messages: list[ConversationMessageSchema]
    created_at: str


class VersionSchema(Schema):
    id: str
    version_number: int
    change_type: str
    change_description: str
    content: dict
    is_selected: bool
    created_at: str
    created_by_user: bool
    parent_version_id: Optional[str] = None
    conversation_id: Optional[str] = None


class VersionTreeNodeSchema(Schema):
    version: VersionSchema
    children: list['VersionTreeNodeSchema'] = []


class RefineTextSchema(Schema):
    disclosure_id: int
    current_version_id: Optional[str] = None  # If None, use selected version
    instruction: str  # "make it more formal", "add more details", etc


class RefineChartSchema(Schema):
    disclosure_id: int
    chart_id: str
    current_version_id: Optional[str] = None
    instruction: str


class ToggleChartSelectionSchema(Schema):
    disclosure_id: int
    chart_id: str


class ChartSelectionResponseSchema(Schema):
    """Response schema for chart selection toggle"""
    message: str
    success: bool = True
    selected_for_report: bool


class RefineImageSchema(Schema):
    disclosure_id: int  
    image_id: str
    current_version_id: Optional[str] = None
    instruction: str


class RefineTableSchema(Schema):
    disclosure_id: int
    table_id: str
    current_version_id: Optional[str] = None
    instruction: str


class SelectVersionSchema(Schema):
    version_id: str


class UpdateChartSchema(Schema):
    """Schema for updating chart data"""
    disclosure_id: int
    chart_id: str
    chart_data: dict


class UpdateTableSchema(Schema):
    """Schema for updating table data"""
    disclosure_id: int
    table_id: str
    table_data: dict


# ========== DYNAMIC STANDARDS SCHEMAS ==========

class StandardTypeSchema(Schema):
    """Schema for standard type metadata"""
    type: str  # ESRS, ISO9001, etc.
    name: str  # Full name
    description: str
    icon: str  # Emoji or icon class
    total_requirements: int
    answered_requirements: int
    completion_percentage: float


class CategoryWithProgressSchema(Schema):
    """Category schema with user progress"""
    id: int
    name: str
    code: str
    description: str
    order: int
    standard_type: str
    total_disclosures: int
    answered_disclosures: int
    completion_percentage: float


class WebsiteUrlSchema(Schema):
    """Schema for adding website as document"""
    website_url: str

class AssignDisclosureSchema(Schema):
    """Schema for assigning disclosure to a team member"""
    disclosure_id: int
    assigned_to_id: Optional[int] = None  # None to unassign

class UpdateRAGSettingsSchema(Schema):
    """Schema for updating RAG tier settings"""
    rag_tier1_enabled: bool
    rag_tier2_threshold: int
    rag_tier3_enabled: bool
    rag_tier3_threshold: int
