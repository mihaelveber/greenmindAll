"""
Google Gemini API Client
Provides unified interface for Gemini 1.5 models
"""

import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class GoogleClient:
    """
    Client for Google Gemini API
    
    Supports:
    - Gemini 1.5 Pro (gemini-1.5-pro)
    - Gemini 1.5 Flash (gemini-1.5-flash)
    """
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_AI_API_KEY')
        if not self.api_key:
            logger.warning("[Google] GOOGLE_AI_API_KEY not set in environment")
        
        # Import google.generativeai only if API key is available
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.genai = genai
                logger.info("[Google] Client initialized successfully")
            except ImportError:
                logger.error("[Google] 'google-generativeai' package not installed. Run: pip install google-generativeai")
                self.genai = None
        else:
            self.genai = None
    
    def generate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion using Gemini
        
        Args:
            model: Model identifier (gemini-1.5-pro, gemini-1.5-flash)
            messages: List of message dicts with 'role' and 'content'
            temperature: Randomness (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Dict with 'message' and 'usage' keys matching OpenAI format
        """
        
        if not self.genai:
            raise Exception("Google client not initialized. Check GOOGLE_AI_API_KEY.")
        
        try:
            # Convert OpenAI messages to Gemini format
            # Gemini uses 'user' and 'model' roles (not 'assistant')
            system_instruction = None
            gemini_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_instruction = msg['content']
                elif msg['role'] == 'assistant':
                    gemini_messages.append({
                        'role': 'model',  # Gemini uses 'model' instead of 'assistant'
                        'parts': [msg['content']]
                    })
                else:
                    gemini_messages.append({
                        'role': msg['role'],
                        'parts': [msg['content']]
                    })
            
            # Create model
            logger.info(f"[Google] Calling {model} with {len(gemini_messages)} messages")
            
            generation_config = {
                'temperature': temperature,
                'max_output_tokens': max_tokens,
            }
            
            model_instance = self.genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system_instruction if system_instruction else None
            )
            
            # If we have chat history, use chat
            if len(gemini_messages) > 1:
                # Start chat with history (all messages except last)
                chat = model_instance.start_chat(history=gemini_messages[:-1])
                # Send last message
                last_message = gemini_messages[-1]['parts'][0]
                response = chat.send_message(last_message)
            else:
                # Single message - use generate_content
                if gemini_messages:
                    response = model_instance.generate_content(gemini_messages[0]['parts'][0])
                else:
                    raise Exception("No messages provided")
            
            # Extract token counts (Gemini provides this)
            try:
                prompt_tokens = response.usage_metadata.prompt_token_count
                completion_tokens = response.usage_metadata.candidates_token_count
                total_tokens = response.usage_metadata.total_token_count
            except AttributeError:
                # Fallback if usage_metadata not available
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0
            
            # Convert to OpenAI-like format
            result = {
                'message': {
                    'role': 'assistant',
                    'content': response.text
                },
                'usage': {
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens
                },
                'model': model,
                'provider': 'google'
            }
            
            logger.info(f"[Google] Success - {result['usage']['total_tokens']} tokens used")
            
            return result
            
        except Exception as e:
            logger.error(f"[Google] API error: {e}", exc_info=True)
            raise Exception(f"Google API error: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if client is available"""
        return self.genai is not None
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get model capabilities
        
        Returns:
            Dict with context_window, cost_per_1m_input, cost_per_1m_output
        """
        
        model_info = {
            'gemini-1.5-pro': {
                'context_window': 2_000_000,  # 2M tokens!
                'cost_per_1m_input': 1.25,
                'cost_per_1m_output': 5.00,
                'description': 'Most capable Gemini model - excellent for long documents'
            },
            'gemini-1.5-flash': {
                'context_window': 1_000_000,  # 1M tokens
                'cost_per_1m_input': 0.075,
                'cost_per_1m_output': 0.30,
                'description': 'Fast and efficient Gemini model - very cost-effective'
            }
        }
        
        return model_info.get(model, {
            'context_window': 1_000_000,
            'cost_per_1m_input': 1.25,
            'cost_per_1m_output': 5.00,
            'description': 'Gemini model'
        })
