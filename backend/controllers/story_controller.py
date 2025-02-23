"""故事控制器."""

import json
import os
from typing import Dict, List, Optional, Tuple
from ..models.story import Story
from ..models.character import Character
from ..utils.ai_handler import AIHandler

class StoryController:
    """故事控制器類."""
    
    def __init__(self, ai_handler: AIHandler):
        """初始化故事控制器."""
        self.ai_handler = ai_handler
        self.current_story: Optional[Story] = None
        self.dialogue_history: List[Dict] = []
        self._ensure_data_directories()
        self.story_templates = self._load_story_templates()
        self.default_characters = self._load_default_characters()
        
    def _ensure_data_directories(self) -> None:
        """確保必要的數據目錄存在."""
        directories = [
            'data/stories',
            'data/characters',
            'frontend/static/images/characters'
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _load_default_characters(self) -> Dict[str, Character]:
        """載入預設角色."""
        try:
            with open('data/characters/default_characters.json', 'r',
                     encoding='utf-8') as f:
                characters_data = json.load(f)
                return {
                    name: Character.from_dict({**data, 'name': name})
                    for name, data in characters_data.items()
                }
        except FileNotFoundError:
            raise RuntimeError("找不到預設角色文件：data/characters/default_characters.json")
            
    def _load_story_templates(self) -> Dict:
        """載入故事模板."""
        try:
            with open('data/stories/story_templates.json', 'r', 
                     encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise RuntimeError("找不到故事模板文件：data/stories/story_templates.json")
        
    def create_story(self, world_type: str, setting: str, 
                    background: str, adult_content: bool = False) -> Story:
        """創建新故事."""
        # 檢查是否為預設世界類型
        if world_type in self.story_templates:
            template = self.story_templates[world_type]
            story = Story(
                world_type=world_type,
                setting=template['setting'] if not setting else setting,
                background=template['background'] if not background else background,
                characters={},
                current_scene='introduction',
                adult_content=adult_content,
                themes=template.get('themes', [])
            )
        else:
            # 自訂義世界
            story = Story(
                world_type=world_type,
                setting=setting,
                background=background,
                characters={},
                current_scene='introduction',
                adult_content=adult_content,
                themes=[]
            )
        # 添加預設角色
        for char_name, character in self.default_characters.items():
            story.add_character(character)
            
        self.current_story = story
        self._save_story()
        self.dialogue_history = []  # 重置對話歷史
        return story
        
    def add_character(self, character_data: Dict) -> Character:
        """添加角色到當前故事."""
        if not self.current_story:
            raise ValueError("沒有活躍的故事")
            
        character = Character.from_dict(character_data)
        self.current_story.add_character(character)
        self._save_story()
        return character
        
    def process_user_input(self, user_input: str, 
                          current_character: str) -> Tuple[str, List[Dict]]:
        """處理用戶輸入並生成回應."""
        if not self.current_story:
            raise ValueError("沒有活躍的故事")
            
        # 更新對話歷史
        self.dialogue_history.append({
            'speaker': 'user',
            'content': user_input
        })
        
        # 獲取當前角色
        character = self.current_story.characters.get(current_character)
        if not character:
            raise ValueError(f"找不到角色: {current_character}")
            
        # 使用AI生成回應
        response = self.ai_handler.generate_response(
            character=character,
            user_input=user_input,
            dialogue_history=self.dialogue_history,
            story_context=self.current_story
        )
        
        # 生成選項
        choices = self.ai_handler.generate_choices(
            character=character,
            current_response=response,
            story_context=self.current_story
        )
        
        # 更新對話歷史
        self.dialogue_history.append({
            'speaker': current_character,
            'content': response
        })
        
        return response, choices
        
    def update_relationship(self, character1: str, 
                          character2: str, value: int) -> None:
        """更新角色間的關係."""
        if not self.current_story:
            raise ValueError("沒有活躍的故事")
            
        char1 = self.current_story.characters.get(character1)
        char2 = self.current_story.characters.get(character2)
        
        if not char1 or not char2:
            raise ValueError("找不到指定角色")
            
        char1.update_relationship(character2, value)
        char2.update_relationship(character1, value)
        self._save_story()
        
    def _save_story(self) -> None:
        """保存當前故事到文件."""
        if not self.current_story:
            return
            
        os.makedirs('data/stories', exist_ok=True)
        
        story_data = self.current_story.to_dict()
        with open('data/stories/current_story.json', 'w', 
                 encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
            
    def load_story(self) -> Optional[Story]:
        """從文件載入故事."""
        try:
            with open('data/stories/current_story.json', 'r', 
                     encoding='utf-8') as f:
                story_data = json.load(f)
                self.current_story = Story.from_dict(story_data)
                return self.current_story
        except FileNotFoundError:
            return None
