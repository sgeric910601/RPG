"""角色模型類."""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class Character:
    """角色類別."""

    name: str
    personality: str
    dialogue_style: str
    image: Optional[str] = None
    affection: int = 0
    background: Optional[str] = None
    traits: List[str] = None
    relationships: Dict[str, int] = None
    orientation: Optional[str] = None

    def to_dict(self) -> dict:
        """轉換為字典格式."""
        return {
            'name': self.name,
            'personality': self.personality,
            'dialogue_style': self.dialogue_style,
            'image': self.image,
            'affection': self.affection,
            'background': self.background,
            'traits': self.traits or [],
            'relationships': self.relationships or {},
            'orientation': self.orientation
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Character':
        """從字典創建角色實例."""
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
        """更新好感度."""
        self.affection = max(0, min(5, self.affection + value))

    def add_trait(self, trait: str) -> None:
        """添加特質."""
        if self.traits is None:
            self.traits = []
        if trait not in self.traits:
            self.traits.append(trait)

    def update_relationship(self, character_name: str, value: int) -> None:
        """更新與其他角色的關係."""
        if self.relationships is None:
            self.relationships = {}
        self.relationships[character_name] = value
