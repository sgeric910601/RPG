"""角色數據模型模組，定義角色數據結構。"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class Character:
    """角色數據類，表示遊戲中的角色。"""
    
    name: str
    personality: str
    dialogue_style: str
    image: Optional[str] = None
    affection: int = 0
    background: Optional[str] = None
    traits: List[str] = field(default_factory=list)
    relationships: Dict[str, int] = field(default_factory=dict)
    orientation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """將角色轉換為字典格式。
        
        Returns:
            角色的字典表示
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """從字典創建角色實例。
        
        Args:
            data: 角色數據字典
            
        Returns:
            創建的角色實例
        """
        return cls(
            name=data['name'],
            personality=data['personality'],
            dialogue_style=data['dialogue_style'],
            image=data.get('image'),
            affection=data.get('affection', 0),
            background=data.get('background'),
            traits=data.get('traits', []),
            relationships=data.get('relationships', {}),
            orientation=data.get('orientation')
        )
    
    def update_affection(self, value: int) -> None:
        """更新好感度。
        
        Args:
            value: 好感度變化值，可以是正數或負數
        """
        self.affection = max(0, min(5, self.affection + value))
    
    def add_trait(self, trait: str) -> None:
        """添加特質。
        
        Args:
            trait: 要添加的特質
        """
        if trait not in self.traits:
            self.traits.append(trait)
    
    def update_relationship(self, character_name: str, value: int) -> None:
        """更新與其他角色的關係。
        
        Args:
            character_name: 其他角色的名稱
            value: 關係值
        """
        self.relationships[character_name] = value
