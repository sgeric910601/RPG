"""角色核心邏輯模組，提供角色相關的業務邏輯。"""

import json
import os
from typing import Dict, List, Optional, Any

from ..models.character import Character
from ..services.storage import StorageServiceFactory
from ..utils.validation import Validator
from ..utils.error import ValidationError, NotFoundError


class CharacterService:
    """角色服務類，提供角色相關的業務邏輯。"""
    
    def __init__(self):
        """初始化角色服務。"""
        # 獲取存儲服務
        self.storage = StorageServiceFactory.get_service()
        
        # 角色數據存儲路徑
        self.characters_path = "characters"
        
        # 確保角色數據目錄存在
        self.storage.ensure_directory(self.characters_path)
        
        # 角色驗證器
        self.validator = Validator()
    
    def get_all_characters(self) -> List[Character]:
        """獲取所有角色。
        
        Returns:
            角色列表
        """
        # 獲取角色目錄中的所有文件
        files = self.storage.list_files(self.characters_path)
        
        # 過濾出JSON文件
        character_files = [f for f in files if f.endswith('.json')]
        
        # 讀取每個角色文件
        characters = []
        for file_name in character_files:
            file_path = os.path.join(self.characters_path, file_name)
            try:
                data = json.loads(self.storage.read_file(file_path))
                characters.append(Character.from_dict(data))
            except Exception as e:
                print(f"讀取角色文件 {file_path} 時出錯: {str(e)}")
        
        return characters
    
    def get_character(self, name: str) -> Character:
        """獲取指定名稱的角色。
        
        Args:
            name: 角色名稱
            
        Returns:
            角色實例
            
        Raises:
            NotFoundError: 如果找不到指定名稱的角色
        """
        file_path = os.path.join(self.characters_path, f"{name.lower()}.json")
        
        try:
            data = json.loads(self.storage.read_file(file_path))
            return Character.from_dict(data)
        except Exception as e:
            raise NotFoundError(f"找不到角色: {name}")
    
    def create_character(self, character_data: Dict[str, Any]) -> Character:
        """創建新角色。
        
        Args:
            character_data: 角色數據字典
            
        Returns:
            創建的角色實例
            
        Raises:
            ValidationError: 如果角色數據無效
        """
        # 驗證角色數據
        self._validate_character_data(character_data)
        
        # 創建角色實例
        character = Character.from_dict(character_data)
        
        # 保存角色數據
        self._save_character(character)
        
        return character
    
    def update_character(self, name: str, character_data: Dict[str, Any]) -> Character:
        """更新角色。
        
        Args:
            name: 角色名稱
            character_data: 角色數據字典
            
        Returns:
            更新後的角色實例
            
        Raises:
            NotFoundError: 如果找不到指定名稱的角色
            ValidationError: 如果角色數據無效
        """
        # 檢查角色是否存在
        existing_character = self.get_character(name)
        
        # 驗證角色數據
        self._validate_character_data(character_data)
        
        # 創建更新後的角色實例
        updated_character = Character.from_dict(character_data)
        
        # 保存角色數據
        self._save_character(updated_character)
        
        return updated_character
    
    def delete_character(self, name: str) -> None:
        """刪除角色。
        
        Args:
            name: 角色名稱
            
        Raises:
            NotFoundError: 如果找不到指定名稱的角色
        """
        # 檢查角色是否存在
        self.get_character(name)
        
        # 刪除角色文件
        file_path = os.path.join(self.characters_path, f"{name.lower()}.json")
        self.storage.delete_file(file_path)
    
    def _save_character(self, character: Character) -> None:
        """保存角色數據到文件。
        
        Args:
            character: 角色實例
        """
        file_path = os.path.join(self.characters_path, f"{character.name.lower()}.json")
        self.storage.write_file(file_path, json.dumps(character.to_dict(), ensure_ascii=False, indent=2))
    
    def _validate_character_data(self, data: Dict[str, Any]) -> None:
        """驗證角色數據。
        
        Args:
            data: 角色數據字典
            
        Raises:
            ValidationError: 如果角色數據無效
        """
        # 檢查必填字段
        required_fields = ['name', 'personality', 'dialogue_style']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"缺少必填字段: {field}")
        
        # 驗證好感度範圍
        if 'affection' in data and data['affection'] is not None:
            if not isinstance(data['affection'], int) or data['affection'] < 0 or data['affection'] > 5:
                raise ValidationError("好感度必須是0到5之間的整數")
        
        # 驗證特質列表
        if 'traits' in data and data['traits'] is not None:
            if not isinstance(data['traits'], list):
                raise ValidationError("特質必須是列表")
        
        # 驗證關係字典
        if 'relationships' in data and data['relationships'] is not None:
            if not isinstance(data['relationships'], dict):
                raise ValidationError("關係必須是字典")
            
            for name, value in data['relationships'].items():
                if not isinstance(value, int):
                    raise ValidationError(f"關係值必須是整數: {name}")


class CharacterManager:
    """角色管理器類，提供角色管理功能。"""
    
    _instance = None
    
    def __new__(cls):
        """創建角色管理器單例。"""
        if cls._instance is None:
            cls._instance = super(CharacterManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化角色管理器。"""
        if self._initialized:
            return
        
        self.character_service = CharacterService()
        self._initialized = True
    
    def get_all_characters(self) -> List[Character]:
        """獲取所有角色。
        
        Returns:
            角色列表
        """
        return self.character_service.get_all_characters()
    
    def get_character(self, name: str) -> Character:
        """獲取指定名稱的角色。
        
        Args:
            name: 角色名稱
            
        Returns:
            角色實例
            
        Raises:
            NotFoundError: 如果找不到指定名稱的角色
        """
        return self.character_service.get_character(name)
    
    def create_character(self, character_data: Dict[str, Any]) -> Character:
        """創建新角色。
        
        Args:
            character_data: 角色數據字典
            
        Returns:
            創建的角色實例
            
        Raises:
            ValidationError: 如果角色數據無效
        """
        return self.character_service.create_character(character_data)
    
    def update_character(self, name: str, character_data: Dict[str, Any]) -> Character:
        """更新角色。
        
        Args:
            name: 角色名稱
            character_data: 角色數據字典
            
        Returns:
            更新後的角色實例
            
        Raises:
            NotFoundError: 如果找不到指定名稱的角色
            ValidationError: 如果角色數據無效
        """
        return self.character_service.update_character(name, character_data)
    
    def delete_character(self, name: str) -> None:
        """刪除角色。
        
        Args:
            name: 角色名稱
            
        Raises:
            NotFoundError: 如果找不到指定名稱的角色
        """
        self.character_service.delete_character(name)
    
    def load_default_characters(self) -> List[Character]:
        """載入預設角色。
        
        Returns:
            預設角色列表
        """
        # 預設角色數據
        default_characters = [
            {
                "name": "Yuki",
                "personality": "冷靜、理性、聰明，但有時顯得有些疏離。她喜歡閱讀和思考，對世界充滿好奇。",
                "dialogue_style": "說話簡潔有力，用詞精確，偶爾會使用一些學術性詞彙。",
                "image": "yuki.png",
                "background": "Yuki是一名大學生，主修物理學。她喜歡探索宇宙的奧秘，夢想成為一名科學家。",
                "traits": ["聰明", "理性", "好奇心強"],
                "orientation": "異性戀"
            },
            {
                "name": "Rei",
                "personality": "熱情、活潑、開朗，喜歡冒險和挑戰。她對生活充滿熱情，總是能給周圍的人帶來歡樂。",
                "dialogue_style": "說話活潑生動，經常使用口語化表達和感嘆詞，喜歡開玩笑。",
                "image": "rei.png",
                "background": "Rei是一名自由攝影師，喜歡旅行和探險。她的作品曾在多個雜誌上發表。",
                "traits": ["熱情", "勇敢", "樂觀"],
                "orientation": "雙性戀"
            },
            {
                "name": "Akira",
                "personality": "神秘、內向、敏感，有著豐富的內心世界。他喜歡音樂和藝術，對美有著獨特的感受力。",
                "dialogue_style": "說話溫柔而含蓄，經常使用比喻和隱喻，有時會突然陷入沉思。",
                "image": "akira.png",
                "background": "Akira是一名音樂家，擅長鋼琴和作曲。他的音樂充滿情感和想像力，能觸動人心。",
                "traits": ["敏感", "藝術氣質", "內向"],
                "orientation": "同性戀"
            }
        ]
        
        # 創建角色實例
        characters = []
        for data in default_characters:
            try:
                # 檢查角色是否已存在
                try:
                    character = self.get_character(data['name'])
                    characters.append(character)
                except NotFoundError:
                    # 如果不存在，則創建新角色
                    character = self.create_character(data)
                    characters.append(character)
            except Exception as e:
                print(f"載入預設角色 {data['name']} 時出錯: {str(e)}")
        
        return characters