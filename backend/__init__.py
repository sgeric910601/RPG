"""RPG遊戲後端模組，提供遊戲的核心功能和API。"""

from .utils import (
    Config, Logger, AppError, ValidationError, NotFoundError, 
    AuthenticationError, AuthorizationError, ServiceError, 
    DatabaseError, ConfigurationError, handle_error, Validator
)
from .services import (
    AIService, AIServiceFactory, 
    OpenAIService, ClaudeService, OpenRouterService,
    StorageService, StorageServiceFactory, FileStorageService
)
from .models import (
    Character, Story, Conversation, Message
)
from .core import (
    CharacterService, CharacterManager,
    StoryService, StoryManager,
    DialogueService, DialogueManager,
    Prompt, PromptTemplate, PromptService, PromptManager
)

# 導出類和函數
__all__ = [
    # 工具類
    "Config", 
    "Logger", 
    "AppError", 
    "ValidationError", 
    "NotFoundError", 
    "AuthenticationError", 
    "AuthorizationError", 
    "ServiceError", 
    "DatabaseError", 
    "ConfigurationError", 
    "handle_error", 
    "Validator",
    
    # AI服務類
    "AIService", 
    "AIServiceFactory", 
    "OpenAIService", 
    "ClaudeService", 
    "OpenRouterService",
    
    # 存儲服務類
    "StorageService", 
    "StorageServiceFactory", 
    "FileStorageService",
    
    # 數據模型類
    "Character",
    "Story",
    "Conversation",
    "Message",
    
    # 核心類
    "CharacterService",
    "CharacterManager",
    "StoryService",
    "StoryManager",
    "DialogueService",
    "DialogueManager",
    "Prompt",
    "PromptTemplate",
    "PromptService",
    "PromptManager"
]

# 版本信息
__version__ = "0.1.0"