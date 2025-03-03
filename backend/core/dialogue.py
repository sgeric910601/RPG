"""對話核心邏輯模組，提供對話相關的業務邏輯。"""

import json
import os
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..models.conversation import Conversation, Message
from ..models.character import Character
from ..services.storage import StorageServiceFactory
from ..services.ai import AIServiceFactory
from ..utils.validation import Validator
from ..utils.error import ValidationError, NotFoundError, ServiceError
from .character import CharacterManager
from .story import StoryManager


class DialogueService:
    """對話服務類，提供對話相關的業務邏輯。"""
    
    def __init__(self):
        """初始化對話服務。"""
        # 獲取存儲服務
        self.storage = StorageServiceFactory.get_service()
        
        # 獲取AI服務
        self.ai_service = AIServiceFactory.get_service("deepseek/deepseek-chat:free")
        
        # 對話數據存儲路徑
        self.dialogues_path = "data/dialogues"
        
        # 確保對話數據目錄存在
        self.storage.ensure_directory(self.dialogues_path)
        
        # 對話驗證器
        self.validator = Validator()
        
        # 角色管理器
        self.character_manager = CharacterManager()
        
        # 故事管理器
        self.story_manager = StoryManager()
    
    def get_all_dialogue_sessions(self) -> List[Dict[str, Any]]:
        """獲取所有對話會話的摘要信息。
        
        Returns:
            對話會話摘要列表
        """
        # 獲取對話目錄中的所有文件
        files = self.storage.list_files(self.dialogues_path)
        
        # 過濾出JSON文件
        dialogue_files = [f for f in files if f.endswith('.json')]
        
        # 讀取每個對話文件的摘要信息
        sessions = []
        for file_name in dialogue_files:
            file_path = os.path.join(self.dialogues_path, file_name)
            try:
                data = json.loads(self.storage.read_file(file_path))
                conversation = Conversation.from_dict(data)
                
                # 創建對話會話摘要
                summary = {
                    'id': conversation.id,
                    'character_name': conversation.character_name,
                    'story_id': conversation.story_id,
                    'message_count': conversation.get_message_count(),
                    'created_at': conversation.created_at,
                    'updated_at': conversation.updated_at
                }
                
                sessions.append(summary)
            except Exception as e:
                print(f"讀取對話文件 {file_path} 時出錯: {str(e)}")
        
        # 按更新時間排序
        sessions.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        return sessions
    
    def get_dialogue_session(self, session_id: str) -> Conversation:
        """獲取指定ID的對話會話。
        
        Args:
            session_id: 對話會話ID
            
        Returns:
            對話會話實例
            
        Raises:
            NotFoundError: 如果找不到指定ID的對話會話
        """
        file_path = os.path.join(self.dialogues_path, f"{session_id}.json")
        
        try:
            data = json.loads(self.storage.read_file(file_path))
            return Conversation.from_dict(data)
        except Exception as e:
            raise NotFoundError(f"找不到對話會話: {session_id}")
    
    def create_dialogue_session(self, character_name: str, story_id: str) -> Conversation:
        """創建新的對話會話。
        
        Args:
            character_name: 角色名稱
            story_id: 故事ID
            
        Returns:
            創建的對話會話實例
            
        Raises:
            NotFoundError: 如果找不到指定名稱的角色或指定ID的故事
        """
        # 檢查角色是否存在
        try:
            character = self.character_manager.get_character(character_name)
        except NotFoundError:
            raise NotFoundError(f"找不到角色: {character_name}")
        
        # 檢查故事是否存在
        try:
            story = self.story_manager.get_story(story_id)
        except NotFoundError:
            raise NotFoundError(f"找不到故事: {story_id}")
        
        # 生成對話會話ID
        session_id = str(uuid.uuid4())
        
        # 創建對話會話
        conversation = Conversation(
            id=session_id,
            character_name=character_name,
            story_id=story_id
        )
        
        # 保存對話會話
        self._save_dialogue_session(conversation)
        
        return conversation
    
    def add_message(self, session_id: str, message_data: Dict[str, Any]) -> Conversation:
        """添加消息到對話會話中。
        
        Args:
            session_id: 對話會話ID
            message_data: 消息數據字典
            
        Returns:
            更新後的對話會話實例
            
        Raises:
            NotFoundError: 如果找不到指定ID的對話會話
            ValidationError: 如果消息數據無效
        """
        # 驗證消息數據
        self._validate_message_data(message_data)
        
        # 獲取對話會話
        conversation = self.get_dialogue_session(session_id)
        
        # 創建消息
        message = Message.from_dict(message_data)
        
        # 添加消息到對話會話中
        conversation.add_message(message)
        
        # 保存對話會話
        self._save_dialogue_session(conversation)
        
        return conversation
    
    def generate_response(self, session_id: str, user_message: str) -> Tuple[Conversation, str]:
        """生成AI回應。
        
        Args:
            session_id: 對話會話ID
            user_message: 用戶消息
            
        Returns:
            更新後的對話會話實例和AI回應
            
        Raises:
            NotFoundError: 如果找不到指定ID的對話會話
            ServiceError: 如果生成回應時出錯
        """
        # 獲取對話會話
        conversation = self.get_dialogue_session(session_id)
        
        # 獲取角色
        character_name = conversation.character_name
        try:
            character = self.character_manager.get_character(character_name)
        except NotFoundError:
            raise NotFoundError(f"找不到角色: {character_name}")
        
        # 獲取故事
        story_id = conversation.story_id
        try:
            story = self.story_manager.get_story(story_id)
        except NotFoundError:
            raise NotFoundError(f"找不到故事: {story_id}")
        
        # 添加用戶消息
        conversation.add_user_message(user_message)
        
        # 構建提示詞
        prompt = self._build_prompt(character, story, conversation.messages)
        
        # 生成AI回應
        try:
            ai_response = self.ai_service.generate_text(prompt)
        except Exception as e:
            raise ServiceError("ai", f"生成回應時出錯: {str(e)}")
        
        # 添加AI回應
        conversation.add_assistant_message(ai_response, character_name)
        
        # 保存對話會話
        self._save_dialogue_session(conversation)
        
        return conversation, ai_response
    
    def delete_dialogue_session(self, session_id: str) -> None:
        """刪除對話會話。
        
        Args:
            session_id: 對話會話ID
            
        Raises:
            NotFoundError: 如果找不到指定ID的對話會話
        """
        # 檢查對話會話是否存在
        self.get_dialogue_session(session_id)
        
        # 刪除對話會話文件
        file_path = os.path.join(self.dialogues_path, f"{session_id}.json")
        self.storage.delete_file(file_path)
    
    def _save_dialogue_session(self, conversation: Conversation) -> None:
        """保存對話會話到文件。
        
        Args:
            conversation: 對話會話實例
        """
        file_path = os.path.join(self.dialogues_path, f"{conversation.id}.json")
        self.storage.write_file(file_path, json.dumps(conversation.to_dict(), ensure_ascii=False, indent=2))
    
    def _validate_message_data(self, data: Dict[str, Any]) -> None:
        """驗證消息數據。
        
        Args:
            data: 消息數據字典
            
        Raises:
            ValidationError: 如果消息數據無效
        """
        # 檢查必填字段
        required_fields = ['role', 'content']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"缺少必填字段: {field}")
        
        # 驗證角色
        valid_roles = ['user', 'assistant', 'system']
        if data['role'] not in valid_roles:
            raise ValidationError(f"無效的角色: {data['role']}")
    
    def _build_prompt(self, character: Character, story: Dict[str, Any], messages: List[Message]) -> str:
        """構建AI提示詞。
        
        Args:
            character: 角色實例
            story: 故事數據字典
            messages: 消息列表
            
        Returns:
            AI提示詞
        """
        # 構建角色描述
        character_desc = f"""你現在扮演一個名叫{character.name}的角色。

角色設定：
- 性格: {character.personality}
- 說話風格: {character.dialogue_style}
- 特質: {', '.join(character.traits or [])}
- 背景: {character.background or '無特定背景'}
"""
        
        # 構建故事背景
        story_desc = f"""故事背景：
- 世界類型: {story['world_type']}
- 設定: {story['setting']}
- 背景: {story['background']}
- 當前場景: {story['current_scene']}
- 主題: {', '.join(story.get('themes', []))}
"""
        
        # 構建對話歷史
        dialogue_history = ""
        recent_messages = messages[-10:] if len(messages) > 10 else messages  # 只使用最近的10條消息
        for msg in recent_messages:
            if msg.role == 'user':
                dialogue_history += f"用戶: {msg.content}\n"
            elif msg.role == 'assistant':
                dialogue_history += f"{character.name}: {msg.content}\n"
        
        # 構建最終提示詞
        prompt = f"""{character_desc}

{story_desc}

對話歷史：
{dialogue_history}

請以{character.name}的身份回應最後一條消息。回應應該符合角色的性格和說話風格，並考慮故事背景和對話歷史。
回應需要簡短、生動，不超過50個字，可以加入表情和動作描述。
"""
        
        return prompt


class DialogueManager:
    """對話管理器類，提供對話管理功能。"""
    
    _instance = None
    
    def __new__(cls):
        """創建對話管理器單例。"""
        if cls._instance is None:
            cls._instance = super(DialogueManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化對話管理器。"""
        if self._initialized:
            return
        
        self.dialogue_service = DialogueService()
        self.character_manager = CharacterManager()
        self.story_manager = StoryManager()
        self._initialized = True
    
    def get_all_dialogue_sessions(self) -> List[Dict[str, Any]]:
        """獲取所有對話會話的摘要信息。
        
        Returns:
            對話會話摘要列表
        """
        return self.dialogue_service.get_all_dialogue_sessions()
    
    def get_dialogue_session(self, session_id: str) -> Conversation:
        """獲取指定ID的對話會話。
        
        Args:
            session_id: 對話會話ID
            
        Returns:
            對話會話實例
            
        Raises:
            NotFoundError: 如果找不到指定ID的對話會話
        """
        return self.dialogue_service.get_dialogue_session(session_id)
    
    def create_dialogue_session(self, character_name: str, story_id: str) -> Conversation:
        """創建新的對話會話。
        
        Args:
            character_name: 角色名稱
            story_id: 故事ID
            
        Returns:
            創建的對話會話實例
            
        Raises:
            NotFoundError: 如果找不到指定名稱的角色或指定ID的故事
        """
        return self.dialogue_service.create_dialogue_session(character_name, story_id)
    
    def add_message(self, session_id: str, message_data: Dict[str, Any]) -> Conversation:
        """添加消息到對話會話中。
        
        Args:
            session_id: 對話會話ID
            message_data: 消息數據字典
            
        Returns:
            更新後的對話會話實例
            
        Raises:
            NotFoundError: 如果找不到指定ID的對話會話
            ValidationError: 如果消息數據無效
        """
        return self.dialogue_service.add_message(session_id, message_data)
    
    def generate_response(self, session_id: str, user_message: str) -> Tuple[Conversation, str]:
        """生成AI回應。
        
        Args:
            session_id: 對話會話ID
            user_message: 用戶消息
            
        Returns:
            更新後的對話會話實例和AI回應
            
        Raises:
            NotFoundError: 如果找不到指定ID的對話會話
            ServiceError: 如果生成回應時出錯
        """
        return self.dialogue_service.generate_response(session_id, user_message)
    
    def delete_dialogue_session(self, session_id: str) -> None:
        """刪除對話會話。
        
        Args:
            session_id: 對話會話ID
            
        Raises:
            NotFoundError: 如果找不到指定ID的對話會話
        """
        self.dialogue_service.delete_dialogue_session(session_id)
    
    def start_new_conversation(self, character_name: str = None, story_id: str = None) -> Conversation:
        """開始新的對話。
        
        Args:
            character_name: 角色名稱，如果為None則使用默認角色
            story_id: 故事ID，如果為None則使用默認故事
            
        Returns:
            創建的對話會話實例
        """
        # 如果沒有指定角色，則使用默認角色
        if character_name is None:
            # 載入默認角色
            default_characters = self.character_manager.load_default_characters()
            if default_characters:
                character_name = default_characters[0].name
            else:
                raise NotFoundError("沒有可用的角色")
        
        # 如果沒有指定故事，則使用默認故事
        if story_id is None:
            # 獲取所有故事
            stories = self.story_manager.get_all_stories()
            if stories:
                story_id = stories[0]['id']
            else:
                # 創建默認故事
                story = self.story_manager.create_default_story()
                story_id = story['id']
        
        # 創建對話會話
        return self.create_dialogue_session(character_name, story_id)