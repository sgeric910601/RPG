"""對話數據模型模組，定義對話數據結構。"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Message:
    """消息數據類，表示對話中的一條消息。"""
    
    role: str  # user, assistant, system
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    character: Optional[str] = None  # 角色名稱，僅當role為assistant時有效
    
    def to_dict(self) -> Dict[str, Any]:
        """將消息轉換為字典格式。
        
        Returns:
            消息的字典表示
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """從字典創建消息實例。
        
        Args:
            data: 消息數據字典
            
        Returns:
            創建的消息實例
        """
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            character=data.get('character')
        )


@dataclass
class Conversation:
    """對話數據類，表示一個對話會話。"""
    
    id: str
    character_name: str
    story_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """將對話會話轉換為字典格式。
        
        Returns:
            對話會話的字典表示
        """
        return {
            'id': self.id,
            'character_name': self.character_name,
            'story_id': self.story_id,
            'messages': [message.to_dict() for message in self.messages],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """從字典創建對話會話實例。
        
        Args:
            data: 對話會話數據字典
            
        Returns:
            創建的對話會話實例
        """
        messages = [
            Message.from_dict(message_data)
            for message_data in data.get('messages', [])
        ]
        
        return cls(
            id=data['id'],
            character_name=data['character_name'],
            story_id=data['story_id'],
            messages=messages,
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat())
        )
    
    def add_message(self, message: Message) -> None:
        """添加消息到對話會話中。
        
        Args:
            message: 要添加的消息
        """
        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()
    
    def add_user_message(self, content: str) -> None:
        """添加用戶消息到對話會話中。
        
        Args:
            content: 消息內容
        """
        message = Message(
            role='user',
            content=content
        )
        self.add_message(message)
    
    def add_assistant_message(self, content: str, character: str) -> None:
        """添加助手消息到對話會話中。
        
        Args:
            content: 消息內容
            character: 角色名稱
        """
        message = Message(
            role='assistant',
            content=content,
            character=character
        )
        self.add_message(message)
    
    def add_system_message(self, content: str) -> None:
        """添加系統消息到對話會話中。
        
        Args:
            content: 消息內容
        """
        message = Message(
            role='system',
            content=content
        )
        self.add_message(message)
    
    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """獲取最近的消息。
        
        Args:
            count: 要獲取的消息數量
            
        Returns:
            最近的消息列表
        """
        return self.messages[-count:] if self.messages else []
    
    def get_message_count(self) -> int:
        """獲取消息數量。
        
        Returns:
            消息數量
        """
        return len(self.messages)