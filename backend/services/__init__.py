"""服務模組，提供各種外部服務的集成。"""

from .ai import (
    AIService, AIServiceFactory, 
    OpenAIService, ClaudeService, OpenRouterService
)
from .storage import StorageService, StorageServiceFactory, FileStorageService

# 導出服務類和工廠類
__all__ = [
    # AI服務
    "AIService", 
    "AIServiceFactory",
    "OpenAIService", 
    "ClaudeService", 
    "OpenRouterService",
    
    # 存儲服務
    "StorageService", 
    "StorageServiceFactory",
    "FileStorageService"
]