"""AI服務模組，提供與不同AI模型的交互功能。"""

import os
from .base import AIService, AIServiceFactory
from .openai import OpenAIService
from .claude import ClaudeService
from .openrouter import OpenRouterService

# 如果環境變量中有OpenRouter API密鑰，則優先註冊OpenRouter服務
if "OPENROUTER_API_KEY" in os.environ:
    try:
        openrouter_service = OpenRouterService()
        AIServiceFactory.register_service("openrouter", openrouter_service, "openrouter")
        print("[AI Service] Successfully initialized OpenRouter service")
    except Exception as e:
        print(f"Failed to initialize OpenRouter service: {str(e)}")

# 如果環境變量中有OpenAI API密鑰，則註冊OpenAI服務
if "OPENAI_API_KEY" in os.environ:
    try:
        openai_service = OpenAIService()
        AIServiceFactory.register_service("openai", openai_service, "openai")
        print("[AI Service] Successfully initialized OpenAI service")
    except Exception as e:
        print(f"Failed to initialize OpenAI service: {str(e)}")

# 如果環境變量中有Anthropic API密鑰，則註冊Claude服務
if "ANTHROPIC_API_KEY" in os.environ:
    try:
        claude_service = ClaudeService()
        AIServiceFactory.register_service("claude", claude_service, "claude")
        print("[AI Service] Successfully initialized Claude service")
    except Exception as e:
        print(f"Failed to initialize Claude service: {str(e)}")

# 導出工廠類和服務類
__all__ = [
    "AIService", 
    "AIServiceFactory", 
    "OpenAIService", 
    "ClaudeService", 
    "OpenRouterService"
]