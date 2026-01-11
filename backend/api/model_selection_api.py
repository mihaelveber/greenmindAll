"""
Model Selection API - Allow users to choose and configure LLM models
"""

import logging
from ninja import Router
from typing import List, Dict, Any
from accounts.models import User
from accounts.llm_router import get_model_info, LLMModel
from accounts.schemas import ErrorSchema

logger = logging.getLogger(__name__)

router = Router(tags=["AI Models"])


@router.get("/models", response={200: List[Dict[str, Any]], 401: ErrorSchema})
def list_available_models(request):
    """
    Get list of all available LLM models with capabilities and pricing
    
    Returns:
        List of model information including:
        - model: Model identifier
        - provider: Provider name (openai, anthropic, google)
        - name: Human-readable name
        - context_window: Maximum context size in tokens
        - max_output: Maximum output tokens
        - supports_streaming: Whether streaming is supported
        - supports_json: Whether JSON mode is supported
        - cost_per_1m_input: Cost per 1M input tokens (USD)
        - cost_per_1m_output: Cost per 1M output tokens (USD)
        - description: Model description
    """
    if not request.auth:
        return 401, {"error": "Authentication required"}
    
    try:
        models = get_model_info()
        
        # Add user's current preference
        user = User.objects.get(id=request.auth.id)
        current_model = getattr(user, 'preferred_llm_model', 'gpt-4o')
        
        # Mark current model
        for model in models:
            model['is_current'] = (model['model'] == current_model)
        
        logger.info(f"[Model Selection] User {user.email} listed {len(models)} models")
        
        return 200, models
        
    except Exception as e:
        logger.error(f"[Model Selection] Error listing models: {e}", exc_info=True)
        return 401, {"error": str(e)}


@router.get("/user/preferred-model", response={200: Dict[str, Any], 401: ErrorSchema})
def get_user_preferred_model(request):
    """
    Get user's currently preferred LLM model
    
    Returns:
        {
            "model": "gpt-4o",
            "provider": "openai",
            "name": "GPT-4o"
        }
    """
    if not request.auth:
        return 401, {"error": "Authentication required"}
    
    try:
        user = User.objects.get(id=request.auth.id)
        current_model = getattr(user, 'preferred_llm_model', 'gpt-4o')
        
        # Get model info
        all_models = get_model_info()
        model_info = next((m for m in all_models if m['model'] == current_model), None)
        
        if not model_info:
            model_info = {
                "model": "gpt-4o",
                "provider": "openai",
                "name": "GPT-4o"
            }
        
        logger.info(f"[Model Selection] User {user.email} preference: {current_model}")
        
        return 200, model_info
        
    except Exception as e:
        logger.error(f"[Model Selection] Error getting preference: {e}", exc_info=True)
        return 401, {"error": str(e)}


@router.put("/user/preferred-model", response={200: Dict[str, str], 400: ErrorSchema, 401: ErrorSchema})
def set_user_preferred_model(request, model: str):
    """
    Set user's preferred LLM model
    
    Args:
        model: Model identifier (e.g., 'gpt-4o', 'claude-3-5-sonnet-20241022', 'gemini-1.5-pro')
    
    Returns:
        {"status": "success", "model": "gpt-4o"}
    """
    if not request.auth:
        return 401, {"error": "Authentication required"}
    
    try:
        # Validate model
        try:
            LLMModel(model)
        except ValueError:
            return 400, {"error": f"Invalid model: {model}. Must be one of: {[m.value for m in LLMModel]}"}
        
        # Update user preference
        user = User.objects.get(id=request.auth.id)
        user.preferred_llm_model = model
        user.save()
        
        logger.info(f"[Model Selection] User {user.email} set preference to: {model}")
        
        return 200, {"status": "success", "model": model}
        
    except Exception as e:
        logger.error(f"[Model Selection] Error setting preference: {e}", exc_info=True)
        return 401, {"error": str(e)}


@router.get("/models/recommended", response={200: Dict[str, Any], 401: ErrorSchema})
def get_recommended_model(request, task_type: str = "ai_answer", context_length: int = 0):
    """
    Get recommended model for a specific task type
    
    Args:
        task_type: Type of task (ai_answer, conversation, multi_query, tier3_self_reflection)
        context_length: Length of context in tokens
    
    Returns:
        {
            "model": "gemini-1.5-pro",
            "provider": "google",
            "name": "Gemini 1.5 Pro",
            "reason": "Best for long documents (2M token context)"
        }
    """
    if not request.auth:
        return 401, {"error": "Authentication required"}
    
    try:
        from accounts.llm_router import select_best_model
        
        # Get user preference
        user = User.objects.get(id=request.auth.id)
        user_preference = getattr(user, 'preferred_llm_model', None)
        
        # Select best model
        requires_reasoning = (task_type == "tier3_self_reflection")
        selected_model = select_best_model(
            task_type=task_type,
            context_length=context_length,
            requires_reasoning=requires_reasoning,
            user_preference=user_preference
        )
        
        # Get model info
        all_models = get_model_info()
        model_info = next((m for m in all_models if m['model'] == selected_model.value), None)
        
        if model_info:
            # Add reason
            if context_length > 100_000:
                reason = "Best for long documents (large context window)"
            elif requires_reasoning:
                reason = "Best for complex reasoning and analysis"
            else:
                reason = "Balanced performance for most tasks"
            
            model_info['reason'] = reason
        
        logger.info(f"[Model Selection] Recommended {selected_model.value} for {task_type}")
        
        return 200, model_info
        
    except Exception as e:
        logger.error(f"[Model Selection] Error getting recommendation: {e}", exc_info=True)
        return 401, {"error": str(e)}
