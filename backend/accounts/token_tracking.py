"""
Token usage tracking utilities for OpenAI API calls
"""
import time
from typing import Optional, Dict, Any
from django.utils import timezone
from accounts.token_models import TokenUsage
import logging

logger = logging.getLogger(__name__)


def track_openai_usage(
    user_id: int,
    organization_id: int,
    action_type: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    disclosure_id: Optional[int] = None,
    request_duration_ms: Optional[int] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> TokenUsage:
    """
    Track OpenAI API usage and cost.
    
    Args:
        user_id: User who made the request
        organization_id: Organization owner (for billing)
        action_type: Type of action ('ai_answer', 'conversation', 'rag_search', etc.)
        model: OpenAI model used (e.g., 'gpt-4o', 'text-embedding-3-small')
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        disclosure_id: Related disclosure (optional)
        request_duration_ms: API request duration in milliseconds (optional)
        error: Error message if request failed (optional)
        metadata: Additional context (optional)
    
    Returns:
        TokenUsage instance
    """
    from accounts.models import User, ESRSDisclosure
    
    try:
        user = User.objects.get(id=user_id)
        organization = User.objects.get(id=organization_id)
        
        # Get disclosure if provided
        disclosure = None
        if disclosure_id:
            try:
                disclosure = ESRSDisclosure.objects.get(id=disclosure_id)
            except ESRSDisclosure.DoesNotExist:
                logger.warning(f'Disclosure {disclosure_id} not found for token tracking')
        
        # Calculate cost using TokenUsage model method
        cost = TokenUsage.calculate_cost(model, prompt_tokens, completion_tokens)
        
        # Create token usage record
        usage = TokenUsage.objects.create(
            user=user,
            organization=organization,
            action_type=action_type,
            disclosure=disclosure,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost,
            request_duration_ms=request_duration_ms,
            error=error,
            metadata=metadata or {}
        )
        
        logger.info(
            f'Token usage tracked: {user.email} - {action_type} - '
            f'{usage.total_tokens} tokens (${cost:.6f}) - model: {model}'
        )
        
        return usage
        
    except User.DoesNotExist as e:
        logger.error(f'User not found for token tracking: {e}')
        raise
    except Exception as e:
        logger.error(f'Error tracking token usage: {e}')
        raise


class OpenAIUsageTracker:
    """
    Context manager for tracking OpenAI API calls with timing.
    
    Usage:
        with OpenAIUsageTracker(user_id, org_id, 'ai_answer', disclosure_id) as tracker:
            response = client.chat.completions.create(...)
            tracker.record(response, model='gpt-4o')
    """
    
    def __init__(
        self,
        user_id: int,
        organization_id: int,
        action_type: str,
        disclosure_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.user_id = user_id
        self.organization_id = organization_id
        self.action_type = action_type
        self.disclosure_id = disclosure_id
        self.metadata = metadata or {}
        self.start_time = None
        self.usage_record = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Record error if exception occurred
            duration_ms = int((time.time() - self.start_time) * 1000) if self.start_time else None
            try:
                track_openai_usage(
                    user_id=self.user_id,
                    organization_id=self.organization_id,
                    action_type=self.action_type,
                    model='unknown',
                    prompt_tokens=0,
                    completion_tokens=0,
                    disclosure_id=self.disclosure_id,
                    request_duration_ms=duration_ms,
                    error=str(exc_val),
                    metadata=self.metadata
                )
            except Exception as e:
                logger.error(f'Error recording failed API call: {e}')
        return False
    
    def record(self, response, model: str):
        """
        Record successful OpenAI API call.
        
        Args:
            response: OpenAI API response object (ChatCompletion or Embedding)
            model: Model name used in the request
        """
        duration_ms = int((time.time() - self.start_time) * 1000) if self.start_time else None
        
        # Extract token usage from response
        usage = response.usage
        
        self.usage_record = track_openai_usage(
            user_id=self.user_id,
            organization_id=self.organization_id,
            action_type=self.action_type,
            model=model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=getattr(usage, 'completion_tokens', 0),
            disclosure_id=self.disclosure_id,
            request_duration_ms=duration_ms,
            metadata=self.metadata
        )
        
        return self.usage_record
