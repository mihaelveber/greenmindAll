"""
Anthropic Claude API Client
Provides unified interface for Claude 3.5 models
"""

import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class AnthropicClient:
    """
    Client for Anthropic Claude API
    
    Supports:
    - Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
    - Claude 3.5 Haiku (claude-3-5-haiku-20241022)
    """
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            logger.warning("[Anthropic] ANTHROPIC_API_KEY not set in environment")
        
        # Import anthropic only if API key is available
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("[Anthropic] Client initialized successfully")
            except ImportError:
                logger.error("[Anthropic] 'anthropic' package not installed. Run: pip install anthropic")
                self.client = None
        else:
            self.client = None
    
    def generate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion using Claude
        
        Args:
            model: Model identifier (claude-3-5-sonnet-20241022, etc.)
            messages: List of message dicts with 'role' and 'content'
            temperature: Randomness (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Dict with 'message' and 'usage' keys matching OpenAI format
        """
        
        if not self.client:
            raise Exception("Anthropic client not initialized. Check ANTHROPIC_API_KEY.")
        
        try:
            # Claude uses separate system parameter instead of system message
            system_message = None
            claude_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    claude_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            # Make API call
            logger.info(f"[Anthropic] Calling {model} with {len(claude_messages)} messages")
            
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message if system_message else "",
                messages=claude_messages
            )
            
            # Convert to OpenAI-like format
            result = {
                'message': {
                    'role': 'assistant',
                    'content': response.content[0].text
                },
                'usage': {
                    'prompt_tokens': response.usage.input_tokens,
                    'completion_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                },
                'model': response.model,
                'provider': 'anthropic'
            }
            
            logger.info(f"[Anthropic] Success - {result['usage']['total_tokens']} tokens used")
            
            return result
            
        except Exception as e:
            logger.error(f"[Anthropic] API error: {e}", exc_info=True)
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if client is available"""
        return self.client is not None
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get model capabilities
        
        Returns:
            Dict with context_window, cost_per_1m_input, cost_per_1m_output
        """
        
        model_info = {
            'claude-3-5-sonnet-20241022': {
                'context_window': 200_000,
                'cost_per_1m_input': 3.00,
                'cost_per_1m_output': 15.00,
                'description': 'Most capable Claude model - excellent for reasoning and analysis'
            },
            'claude-3-5-haiku-20241022': {
                'context_window': 200_000,
                'cost_per_1m_input': 0.80,
                'cost_per_1m_output': 4.00,
                'description': 'Fast and efficient Claude model - good for simpler tasks'
            }
        }
        
        return model_info.get(model, {
            'context_window': 200_000,
            'cost_per_1m_input': 3.00,
            'cost_per_1m_output': 15.00,
            'description': 'Claude model'
        })
