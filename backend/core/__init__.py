"""核心模組，包含業務邏輯。"""

from .character import Character, CharacterService, CharacterManager
from .story import Story, StoryService, StoryManager
from .dialogue import DialogueService, DialogueManager
from .prompt import Prompt, PromptTemplate, PromptService, PromptManager

# 導出核心類和函數
__all__ = [
    # 角色相關
    "Character",
    "CharacterService",
    "CharacterManager",
    
    # 故事相關
    "Story",
    "StoryService",
    "StoryManager",
    
    # 對話相關
    "DialogueService",
    "DialogueManager",
    
    # 提示詞相關
    "Prompt",
    "PromptTemplate",
    "PromptService",
    "PromptManager"
]