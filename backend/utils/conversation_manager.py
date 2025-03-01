"""會話歷史管理模組，負責維護用戶與AI之間的對話歷史。"""

import time
from typing import Dict, List, Optional, Any
from uuid import uuid4

class Conversation:
    """單一會話類，包含會話的基本信息和消息歷史。"""
    
    def __init__(
        self, 
        conversation_id: Optional[str] = None, 
        title: str = "新會話",
        system_prompt: Optional[str] = None,
        max_history: int = 100
    ):
        """初始化會話。
        
        Args:
            conversation_id: 會話ID，如果為None則自動生成
            title: 會話標題
            system_prompt: 系統提示詞
            max_history: 最大歷史消息數量
        """
        self.conversation_id = conversation_id or str(uuid4())
        self.title = title
        self.created_at = time.time()
        self.updated_at = time.time()
        self.messages: List[Dict[str, Any]] = []
        self.max_history = max_history
        
        # 如果提供了系統提示詞，添加為第一條消息
        if system_prompt:
            self.add_message("system", system_prompt)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """添加新消息到會話歷史。
        
        Args:
            role: 消息角色 ("system", "user", "assistant")
            content: 消息內容
            metadata: 與消息相關的元數據
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        if metadata:
            message["metadata"] = metadata
            
        self.messages.append(message)
        self.updated_at = time.time()
        
        # 如果超過最大歷史限制，移除最早的非系統消息
        if len(self.messages) > self.max_history:
            # 保留系統消息
            if self.messages[0]["role"] == "system":
                self.messages = [self.messages[0]] + self.messages[-(self.max_history-1):]
            else:
                self.messages = self.messages[-self.max_history:]
    
    def get_messages(self, include_system: bool = True) -> List[Dict[str, str]]:
        """獲取格式化的消息歷史，適用於發送給AI API。
        
        Args:
            include_system: 是否包括系統消息
            
        Returns:
            消息列表，每個消息包含role和content
        """
        formatted_messages = []
        for message in self.messages:
            if not include_system and message["role"] == "system":
                continue
            formatted_messages.append({
                "role": message["role"],
                "content": message["content"]
            })
        return formatted_messages
    
    def clear_history(self, preserve_system: bool = True) -> None:
        """清除會話歷史。
        
        Args:
            preserve_system: 是否保留系統消息
        """
        if preserve_system and self.messages and self.messages[0]["role"] == "system":
            self.messages = [self.messages[0]]
        else:
            self.messages = []


class ConversationManager:
    """會話管理器，負責管理多個會話。"""
    
    def __init__(self):
        """初始化會話管理器。"""
        self.conversations: Dict[str, Conversation] = {}
    
    def create_conversation(
        self, 
        title: str = "新會話",
        system_prompt: Optional[str] = None,
        max_history: int = 100
    ) -> Conversation:
        """創建新會話。
        
        Args:
            title: 會話標題
            system_prompt: 系統提示詞
            max_history: 最大歷史消息數量
            
        Returns:
            新創建的會話對象
        """
        conversation = Conversation(
            title=title,
            system_prompt=system_prompt,
            max_history=max_history
        )
        self.conversations[conversation.conversation_id] = conversation
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """獲取指定ID的會話。
        
        Args:
            conversation_id: 會話ID
            
        Returns:
            會話對象，如果不存在則返回None
        """
        return self.conversations.get(conversation_id)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """刪除指定ID的會話。
        
        Args:
            conversation_id: 會話ID
            
        Returns:
            刪除是否成功
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """獲取所有會話的摘要信息。
        
        Returns:
            會話摘要列表
        """
        return [
            {
                "conversation_id": conv.conversation_id,
                "title": conv.title,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "message_count": len(conv.messages)
            }
            for conv in self.conversations.values()
        ]
