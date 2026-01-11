"""
LLM Router - Unified interface for multiple LLM providers
Supports: OpenAI (GPT-4o), Anthropic (Claude 3.5 Sonnet), Google (Gemini 1.5 Pro)
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class LLMModel(Enum):
    """Supported LLM models"""
    # OpenAI
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    
    # Anthropic
    CLAUDE_35_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_35_HAIKU = "claude-3-5-haiku-20241022"
    
    # Google
    GEMINI_15_PRO = "gemini-1.5-pro"
    GEMINI_15_FLASH = "gemini-1.5-flash"


@dataclass
class LLMCapabilities:
    """Model capabilities"""
    context_window: int  # tokens
    max_output: int  # tokens
    supports_streaming: bool
    supports_json: bool
    cost_per_1m_input: float  # USD
    cost_per_1m_output: float  # USD
    

# Model capabilities registry
MODEL_CAPABILITIES = {
    LLMModel.GPT_4O: LLMCapabilities(
        context_window=128_000,
        max_output=16_384,
        supports_streaming=True,
        supports_json=True,
        cost_per_1m_input=2.50,
        cost_per_1m_output=10.00
    ),
    LLMModel.GPT_4O_MINI: LLMCapabilities(
        context_window=128_000,
        max_output=16_384,
        supports_streaming=True,
        supports_json=True,
        cost_per_1m_input=0.15,
        cost_per_1m_output=0.60
    ),
    LLMModel.CLAUDE_35_SONNET: LLMCapabilities(
        context_window=200_000,
        max_output=8_192,
        supports_streaming=True,
        supports_json=True,
        cost_per_1m_input=3.00,
        cost_per_1m_output=15.00
    ),
    LLMModel.CLAUDE_35_HAIKU: LLMCapabilities(
        context_window=200_000,
        max_output=8_192,
        supports_streaming=True,
        supports_json=True,
        cost_per_1m_input=0.80,
        cost_per_1m_output=4.00
    ),
    LLMModel.GEMINI_15_PRO: LLMCapabilities(
        context_window=2_000_000,  # 2M tokens! 🚀
        max_output=8_192,
        supports_streaming=True,
        supports_json=True,
        cost_per_1m_input=1.25,
        cost_per_1m_output=5.00
    ),
    LLMModel.GEMINI_15_FLASH: LLMCapabilities(
        context_window=1_000_000,
        max_output=8_192,
        supports_streaming=True,
        supports_json=True,
        cost_per_1m_input=0.075,
        cost_per_1m_output=0.30
    ),
}


def get_provider_for_model(model: LLMModel) -> LLMProvider:
    """Get provider for a given model"""
    if model in [LLMModel.GPT_4O, LLMModel.GPT_4O_MINI]:
        return LLMProvider.OPENAI
    elif model in [LLMModel.CLAUDE_35_SONNET, LLMModel.CLAUDE_35_HAIKU]:
        return LLMProvider.ANTHROPIC
    elif model in [LLMModel.GEMINI_15_PRO, LLMModel.GEMINI_15_FLASH]:
        return LLMProvider.GOOGLE
    else:
        raise ValueError(f"Unknown model: {model}")


def select_best_model(
    task_type: str,
    context_length: int = 0,
    requires_reasoning: bool = False,
    user_preference: Optional[str] = None
) -> LLMModel:
    """
    Select the best model for a given task
    
    Args:
        task_type: Type of task (ai_answer, conversation, multi_query, etc.)
        context_length: Length of context in tokens
        requires_reasoning: Whether task requires deep reasoning
        user_preference: User's preferred model (if any)
        
    Returns:
        Selected LLM model
    """
    
    # User preference overrides
    if user_preference:
        try:
            return LLMModel(user_preference)
        except ValueError:
            logger.warning(f"Invalid user preference: {user_preference}, using auto-select")
    
    # Long context? Use Gemini!
    if context_length > 100_000:
        logger.info(f"Long context ({context_length} tokens) - selecting Gemini 1.5 Pro")
        return LLMModel.GEMINI_15_PRO
    
    # Reasoning tasks? Use Claude!
    if requires_reasoning or task_type == "tier3_self_reflection":
        logger.info("Reasoning task - selecting Claude 3.5 Sonnet")
        return LLMModel.CLAUDE_35_SONNET
    
    # Default: GPT-4o (balanced)
    logger.info(f"Standard task ({task_type}) - selecting GPT-4o")
    return LLMModel.GPT_4O


def get_model_info() -> List[Dict[str, Any]]:
    """
    Get information about all available models
    
    Returns:
        List of model info dictionaries
    """
    models = []
    for model, caps in MODEL_CAPABILITIES.items():
        provider = get_provider_for_model(model)
        models.append({
            "model": model.value,
            "provider": provider.value,
            "name": model.name.replace("_", " ").title(),
            "context_window": caps.context_window,
            "max_output": caps.max_output,
            "supports_streaming": caps.supports_streaming,
            "supports_json": caps.supports_json,
            "cost_per_1m_input": caps.cost_per_1m_input,
            "cost_per_1m_output": caps.cost_per_1m_output,
            "description": _get_model_description(model)
        })
    return models


def _get_model_description(model: LLMModel) -> str:
    """Get human-readable model description"""
    descriptions = {
        LLMModel.GPT_4O: "Balanced performance, great for most tasks",
        LLMModel.GPT_4O_MINI: "Fast and cost-effective for simple tasks",
        LLMModel.CLAUDE_35_SONNET: "Best for complex reasoning and analysis",
        LLMModel.CLAUDE_35_HAIKU: "Fast and efficient for quick responses",
        LLMModel.GEMINI_15_PRO: "Massive 2M token context for long documents",
        LLMModel.GEMINI_15_FLASH: "Fast with 1M token context",
    }
    return descriptions.get(model, "")


class LLMRouter:
    """
    Router for LLM requests - handles model selection and routing
    """
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.google_client = None
    
    def get_client(self, model: LLMModel):
        """Get appropriate client for model"""
        provider = get_provider_for_model(model)
        
        if provider == LLMProvider.OPENAI:
            if not self.openai_client:
                from accounts.openai_service import OpenAIService
                self.openai_client = OpenAIService()
            return self.openai_client
        
        elif provider == LLMProvider.ANTHROPIC:
            if not self.anthropic_client:
                from accounts.anthropic_client import AnthropicClient
                self.anthropic_client = AnthropicClient()
            return self.anthropic_client
        
        elif provider == LLMProvider.GOOGLE:
            if not self.google_client:
                from accounts.google_client import GoogleClient
                self.google_client = GoogleClient()
            return self.google_client
        
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def generate(
        self,
        model: LLMModel,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion with specified model
        
        Args:
            model: LLM model to use
            messages: List of message dicts with role and content
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model-specific parameters
            
        Returns:
            Response dict with content, usage, and metadata
        """
        client = self.get_client(model)
        provider = get_provider_for_model(model)
        
        logger.info(f"[LLM Router] Generating with {model.value} (provider: {provider.value})")
        
        try:
            response = client.generate(
                model=model.value,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            logger.info(f"[LLM Router] Success with {model.value}")
            return response
            
        except Exception as e:
            logger.error(f"[LLM Router] Error with {model.value}: {str(e)}")
            
            # Try fallback to GPT-4o if not already using it
            if model != LLMModel.GPT_4O:
                logger.info(f"[LLM Router] Falling back to GPT-4o")
                return self.generate(
                    model=LLMModel.GPT_4O,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            else:
                raise


# Global router instance
router = LLMRouter()
