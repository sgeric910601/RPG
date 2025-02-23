"""故事模型類."""

from dataclasses import dataclass
from typing import List, Dict, Optional
from .character import Character

@dataclass
class Story:
    """故事類別."""

    world_type: str  # fantasy, scifi, modern, custom
    setting: str
    background: str
    characters: Dict[str, Character]
    current_scene: str
    adult_content: bool
    themes: List[str]
    custom_rules: Optional[Dict[str, str]] = None
    events: List[Dict] = None
    
    def __init__(self, world_type: str, setting: str, background: str,
                 characters: Dict[str, Character], current_scene: str,
                 adult_content: bool, themes: List[str],
                 custom_rules: Optional[Dict[str, str]] = None,
                 events: Optional[List[Dict]] = None):
        """初始化故事實例."""
        self.world_type = world_type
        self.setting = setting
        self.background = background
        self.characters = characters
        self.current_scene = current_scene
        self.adult_content = adult_content
        self.themes = themes or []
        self.custom_rules = custom_rules or {}
        self.events = events or []
    
    def to_dict(self) -> dict:
        """轉換為字典格式."""
        return {
            'world_type': self.world_type,
            'setting': self.setting,
            'background': self.background,
            'characters': {
                name: char.to_dict() 
                for name, char in self.characters.items()
            },
            'current_scene': self.current_scene,
            'adult_content': self.adult_content,
            'themes': self.themes,
            'custom_rules': self.custom_rules or {},
            'events': self.events or []
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Story':
        """從字典創建故事實例."""
        characters = {
            name: Character.from_dict(char_data)
            for name, char_data in data['characters'].items()
        }
        
        return cls(
            world_type=data['world_type'],
            setting=data['setting'],
            background=data['background'],
            characters=characters,
            current_scene=data['current_scene'],
            adult_content=data['adult_content'],
            themes=data['themes'],
            custom_rules=data.get('custom_rules'),
            events=data.get('events', [])
        )
    
    def add_character(self, character: Character) -> None:
        """添加角色到故事中."""
        self.characters[character.name] = character
    
    def add_event(self, event_type: str, description: str, 
                 related_characters: List[str]) -> None:
        """添加事件到故事中."""
        if self.events is None:
            self.events = []
            
        self.events.append({
            'type': event_type,
            'description': description,
            'characters': related_characters
        })
    
    def update_scene(self, new_scene: str) -> None:
        """更新當前場景."""
        self.current_scene = new_scene
        
    def get_character_relationships(self, character_name: str) -> Dict[str, int]:
        """獲取指定角色與其他角色的關係."""
        character = self.characters.get(character_name)
        if not character:
            return {}
        return character.relationships or {}
    
    def validate_content(self, content: str) -> bool:
        """驗證內容是否符合故事設定."""
        # 基本的內容驗證邏輯
        if not self.adult_content and '18+' in content:
            return False
            
        # 可以添加更多驗證規則
        return True
