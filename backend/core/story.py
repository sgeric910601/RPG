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
        self.stories_path = "data/stories"
        
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
            raise NotFoundError("story", story_id)
    
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
    
    def get_current_story(self) -> Dict[str, Any]:
        """獲取當前故事的狀態。

        Returns:
            包含當前故事和對話歷史的字典
        """
        try:
            # 獲取最新的故事
            stories = self.get_all_stories()
            if not stories:
                # 如果沒有故事，創建一個默認故事
                stories = [self.create_default_story()]
            
            # 獲取最新故事的完整數據
            latest_story = self.get_story(stories[0]['id'])

            return {
                'story': latest_story,
                'dialogue_history': []  # 對話歷史初始為空
            }
        except Exception as e:
            print(f"獲取當前故事時出錯: {str(e)}")
            return {'story': None, 'dialogue_history': []}

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
    
    def get_current_story(self) -> Dict[str, Any]:
        """獲取當前故事的狀態。
        
        Returns:
            當前故事和對話歷史的字典
        """
        return self.story_service.get_current_story()
    
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