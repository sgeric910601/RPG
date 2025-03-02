"""故事核心邏輯模組，提供故事相關的業務邏輯。"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models.story import Story
from ..models.character import Character
from ..services.storage import StorageServiceFactory
from ..utils.validation import Validator
from ..utils.error import ValidationError, NotFoundError
from .character import CharacterManager


class StoryService:
    """故事服務類，提供故事相關的業務邏輯。"""
    
    def __init__(self):
        """初始化故事服務。"""
        # 獲取存儲服務
        self.storage = StorageServiceFactory.get_service()
        
        # 故事數據存儲路徑
        self.stories_path = "stories"
        
        # 確保故事數據目錄存在
        self.storage.ensure_directory(self.stories_path)
        
        # 故事驗證器
        self.validator = Validator()
        
        # 角色管理器
        self.character_manager = CharacterManager()
    
    def get_all_stories(self) -> List[Dict[str, Any]]:
        """獲取所有故事的摘要信息。
        
        Returns:
            故事摘要列表
        """
        # 獲取故事目錄中的所有文件
        files = self.storage.list_files(self.stories_path)
        
        # 過濾出JSON文件
        story_files = [f for f in files if f.endswith('.json')]
        
        # 讀取每個故事文件的摘要信息
        stories = []
        for file_name in story_files:
            file_path = os.path.join(self.stories_path, file_name)
            try:
                data = json.loads(self.storage.read_file(file_path))
                
                # 創建故事摘要
                summary = {
                    'id': data.get('id', file_name.replace('.json', '')),
                    'title': data.get('title', 'Untitled Story'),
                    'world_type': data.get('world_type', 'unknown'),
                    'setting': data.get('setting', ''),
                    'character_count': len(data.get('characters', {})),
                    'created_at': data.get('created_at', ''),
                    'updated_at': data.get('updated_at', '')
                }
                
                stories.append(summary)
            except Exception as e:
                print(f"讀取故事文件 {file_path} 時出錯: {str(e)}")
        
        return stories
    
    def get_story(self, story_id: str) -> Dict[str, Any]:
        """獲取指定ID的故事。
        
        Args:
            story_id: 故事ID
            
        Returns:
            故事數據字典
            
        Raises:
            NotFoundError: 如果找不到指定ID的故事
        """
        file_path = os.path.join(self.stories_path, f"{story_id}.json")
        
        try:
            data = json.loads(self.storage.read_file(file_path))
            return data
        except Exception as e:
            raise NotFoundError(f"找不到故事: {story_id}")
    
    def create_story(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建新故事。
        
        Args:
            story_data: 故事數據字典
            
        Returns:
            創建的故事數據字典
            
        Raises:
            ValidationError: 如果故事數據無效
        """
        # 驗證故事數據
        self._validate_story_data(story_data)
        
        # 生成故事ID
        story_id = self._generate_story_id()
        
        # 添加元數據
        now = datetime.now().isoformat()
        story_data['id'] = story_id
        story_data['created_at'] = now
        story_data['updated_at'] = now
        
        # 處理角色數據
        if 'characters' not in story_data:
            story_data['characters'] = {}
        
        # 保存故事數據
        self._save_story(story_id, story_data)
        
        return story_data
    
    def update_story(self, story_id: str, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新故事。
        
        Args:
            story_id: 故事ID
            story_data: 故事數據字典
            
        Returns:
            更新後的故事數據字典
            
        Raises:
            NotFoundError: 如果找不到指定ID的故事
            ValidationError: 如果故事數據無效
        """
        # 檢查故事是否存在
        existing_story = self.get_story(story_id)
        
        # 驗證故事數據
        self._validate_story_data(story_data)
        
        # 保留原始元數據
        story_data['id'] = story_id
        story_data['created_at'] = existing_story.get('created_at', datetime.now().isoformat())
        story_data['updated_at'] = datetime.now().isoformat()
        
        # 保存故事數據
        self._save_story(story_id, story_data)
        
        return story_data
    
    def delete_story(self, story_id: str) -> None:
        """刪除故事。
        
        Args:
            story_id: 故事ID
            
        Raises:
            NotFoundError: 如果找不到指定ID的故事
        """
        # 檢查故事是否存在
        self.get_story(story_id)
        
        # 刪除故事文件
        file_path = os.path.join(self.stories_path, f"{story_id}.json")
        self.storage.delete_file(file_path)
    
    def add_character_to_story(self, story_id: str, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加角色到故事中。
        
        Args:
            story_id: 故事ID
            character_data: 角色數據字典
            
        Returns:
            更新後的故事數據字典
            
        Raises:
            NotFoundError: 如果找不到指定ID的故事
            ValidationError: 如果角色數據無效
        """
        # 獲取故事數據
        story_data = self.get_story(story_id)
        
        # 創建角色
        character = Character.from_dict(character_data)
        
        # 添加角色到故事中
        if 'characters' not in story_data:
            story_data['characters'] = {}
        
        story_data['characters'][character.name.lower()] = character.to_dict()
        
        # 更新故事
        return self.update_story(story_id, story_data)
    
    def add_event_to_story(self, story_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加事件到故事中。
        
        Args:
            story_id: 故事ID
            event_data: 事件數據字典
            
        Returns:
            更新後的故事數據字典
            
        Raises:
            NotFoundError: 如果找不到指定ID的故事
            ValidationError: 如果事件數據無效
        """
        # 驗證事件數據
        required_fields = ['type', 'description', 'characters']
        for field in required_fields:
            if field not in event_data:
                raise ValidationError(f"缺少必填字段: {field}")
        
        # 獲取故事數據
        story_data = self.get_story(story_id)
        
        # 添加事件到故事中
        if 'events' not in story_data:
            story_data['events'] = []
        
        # 添加時間戳
        event_data['timestamp'] = datetime.now().isoformat()
        
        story_data['events'].append(event_data)
        
        # 更新故事
        return self.update_story(story_id, story_data)
    
    def update_scene(self, story_id: str, new_scene: str) -> Dict[str, Any]:
        """更新故事的當前場景。
        
        Args:
            story_id: 故事ID
            new_scene: 新場景描述
            
        Returns:
            更新後的故事數據字典
            
        Raises:
            NotFoundError: 如果找不到指定ID的故事
        """
        # 獲取故事數據
        story_data = self.get_story(story_id)
        
        # 更新場景
        story_data['current_scene'] = new_scene
        
        # 更新故事
        return self.update_story(story_id, story_data)
    
    def _save_story(self, story_id: str, story_data: Dict[str, Any]) -> None:
        """保存故事數據到文件。
        
        Args:
            story_id: 故事ID
            story_data: 故事數據字典
        """
        file_path = os.path.join(self.stories_path, f"{story_id}.json")
        self.storage.write_file(file_path, json.dumps(story_data, ensure_ascii=False, indent=2))
    
    def _generate_story_id(self) -> str:
        """生成唯一的故事ID。
        
        Returns:
            故事ID
        """
        import uuid
        return str(uuid.uuid4())
    
    def _validate_story_data(self, data: Dict[str, Any]) -> None:
        """驗證故事數據。
        
        Args:
            data: 故事數據字典
            
        Raises:
            ValidationError: 如果故事數據無效
        """
        # 檢查必填字段
        required_fields = ['world_type', 'setting', 'background', 'current_scene']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"缺少必填字段: {field}")
        
        # 驗證世界類型
        valid_world_types = ['fantasy', 'scifi', 'modern', 'custom']
        if data['world_type'] not in valid_world_types:
            raise ValidationError(f"無效的世界類型: {data['world_type']}")
        
        # 驗證成人內容標誌
        if 'adult_content' in data and not isinstance(data['adult_content'], bool):
            raise ValidationError("成人內容標誌必須是布爾值")
        
        # 驗證主題列表
        if 'themes' in data and data['themes'] is not None:
            if not isinstance(data['themes'], list):
                raise ValidationError("主題必須是列表")
        
        # 驗證自定義規則字典
        if 'custom_rules' in data and data['custom_rules'] is not None:
            if not isinstance(data['custom_rules'], dict):
                raise ValidationError("自定義規則必須是字典")
        
        # 驗證事件列表
        if 'events' in data and data['events'] is not None:
            if not isinstance(data['events'], list):
                raise ValidationError("事件必須是列表")
            
            for event in data['events']:
                if not isinstance(event, dict):
                    raise ValidationError("事件必須是字典")
                
                required_event_fields = ['type', 'description', 'characters']
                for field in required_event_fields:
                    if field not in event:
                        raise ValidationError(f"事件缺少必填字段: {field}")


class StoryManager:
    """故事管理器類，提供故事管理功能。"""
    
    _instance = None
    
    def __new__(cls):
        """創建故事管理器單例。"""
        if cls._instance is None:
            cls._instance = super(StoryManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化故事管理器。"""
        if self._initialized:
            return
        
        self.story_service = StoryService()
        self.character_manager = CharacterManager()
        self._initialized = True
    
    def get_all_stories(self) -> List[Dict[str, Any]]:
        """獲取所有故事的摘要信息。
        
        Returns:
            故事摘要列表
        """
        return self.story_service.get_all_stories()
    
    def get_story(self, story_id: str) -> Dict[str, Any]:
        """獲取指定ID的故事。
        
        Args:
            story_id: 故事ID
            
        Returns:
            故事數據字典
            
        Raises:
            NotFoundError: 如果找不到指定ID的故事
        """
        return self.story_service.get_story(story_id)
    
    def create_story(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建新故事。
        
        Args:
            story_data: 故事數據字典
            
        Returns:
            創建的故事數據字典
            
        Raises:
            ValidationError: 如果故事數據無效
        """
        return self.story_service.create_story(story_data)
    
    def update_story(self, story_id: str, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新故事。
        
        Args:
            story_id: 故事ID
            story_data: 故事數據字典
            
        Returns:
            更新後的故事數據字典
            
        Raises:
            NotFoundError: 如果找不到指定ID的故事
            ValidationError: 如果故事數據無效
        """
        return self.story_service.update_story(story_id, story_data)
    
    def delete_story(self, story_id: str) -> None:
        """刪除故事。
        
        Args:
            story_id: 故事ID
            
        Raises:
            NotFoundError: 如果找不到指定ID的故事
        """
        self.story_service.delete_story(story_id)
    
    def add_character_to_story(self, story_id: str, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加角色到故事中。
        
        Args:
            story_id: 故事ID
            character_data: 角色數據字典
            
        Returns:
            更新後的故事數據字典
            
        Raises:
            NotFoundError: 如果找不到指定ID的故事
            ValidationError: 如果角色數據無效
        """
        return self.story_service.add_character_to_story(story_id, character_data)
    
    def add_event_to_story(self, story_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加事件到故事中。
        
        Args:
            story_id: 故事ID
            event_data: 事件數據字典
            
        Returns:
            更新後的故事數據字典
            
        Raises:
            NotFoundError: 如果找不到指定ID的故事
            ValidationError: 如果事件數據無效
        """
        return self.story_service.add_event_to_story(story_id, event_data)
    
    def update_scene(self, story_id: str, new_scene: str) -> Dict[str, Any]:
        """更新故事的當前場景。
        
        Args:
            story_id: 故事ID
            new_scene: 新場景描述
            
        Returns:
            更新後的故事數據字典
            
        Raises:
            NotFoundError: 如果找不到指定ID的故事
        """
        return self.story_service.update_scene(story_id, new_scene)
    
    def create_default_story(self) -> Dict[str, Any]:
        """創建默認故事。
        
        Returns:
            創建的故事數據字典
        """
        # 載入默認角色
        default_characters = self.character_manager.load_default_characters()
        
        # 創建角色字典
        characters = {
            char.name.lower(): char.to_dict() for char in default_characters
        }
        
        # 創建默認故事數據
        story_data = {
            'title': '神秘的城市冒險',
            'world_type': 'modern',
            'setting': '現代城市',
            'background': '在一個充滿神秘和冒險的現代城市中，幾個性格各異的年輕人相遇，開始了一段不可思議的旅程。',
            'current_scene': '城市中心的咖啡館',
            'adult_content': False,
            'themes': ['冒險', '友情', '神秘'],
            'characters': characters,
            'custom_rules': {
                'magic_allowed': '有限制的魔法存在，但不為大眾所知',
                'technology_level': '現代科技，但有一些超前的實驗性技術'
            },
            'events': []
        }
        
        # 創建故事
        return self.create_story(story_data)