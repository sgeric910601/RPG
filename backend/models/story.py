"""故事數據模型模組，定義故事數據結構。"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

from .character import Character


@dataclass
class Story:
    """故事數據類，表示遊戲中的故事。"""
    
    world_type: str  # fantasy, scifi, modern, custom
    setting: str
    background: str
    characters: Dict[str, Character]
    current_scene: str
    adult_content: bool
    themes: List[str] = field(default_factory=list)
    custom_rules: Dict[str, str] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """將故事轉換為字典格式。
        
        Returns:
            故事的字典表示
        """
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
            'custom_rules': self.custom_rules,
            'events': self.events
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Story':
        """從字典創建故事實例。
        
        Args:
            data: 故事數據字典
            
        Returns:
            創建的故事實例
        """
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
            themes=data.get('themes', []),
            custom_rules=data.get('custom_rules', {}),
            events=data.get('events', [])
        )
    
    def add_character(self, character: Character) -> None:
        """添加角色到故事中。
        
        Args:
            character: 要添加的角色
        """
        self.characters[character.name.lower()] = character
    
    def add_event(self, event_type: str, description: str, 
                 related_characters: List[str]) -> None:
        """添加事件到故事中。
        
        Args:
            event_type: 事件類型
            description: 事件描述
            related_characters: 相關角色列表
        """
        self.events.append({
            'type': event_type,
            'description': description,
            'characters': related_characters,
            'timestamp': datetime.now().isoformat()
        })
    
    def update_scene(self, new_scene: str) -> None:
        """更新當前場景。
        
        Args:
            new_scene: 新場景描述
        """
        self.current_scene = new_scene
        
    def get_character_relationships(self, character_name: str) -> Dict[str, int]:
        """獲取指定角色與其他角色的關係。
        
        Args:
            character_name: 角色名稱
            
        Returns:
            角色關係字典，鍵為角色名稱，值為關係值
        """
        character = self.characters.get(character_name.lower())
        if not character:
            return {}
        return character.relationships
    
    def validate_content(self, content: str) -> bool:
        """驗證內容是否符合故事設定。
        
        Args:
            content: 要驗證的內容
            
        Returns:
            內容是否有效
        """
        # 基本的內容驗證邏輯
        if not self.adult_content and '18+' in content:
            return False
            
        # 可以添加更多驗證規則
        return True
