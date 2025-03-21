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
        self.current_session_id: Optional[str] = None
        self._ensure_data_directories()
        self.story_templates = self._load_story_templates()
        self.default_characters = self._load_default_characters()
        
    def _ensure_data_directories(self) -> None:
        """確保必要的數據目錄存在."""
        directories = [
            'data/stories',
            'data/characters',
            'data/chat_history',
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
            
    def process_user_input(self, user_input: str, 
                         current_character: str) -> Tuple[str, List[Dict]]:
        """處理用戶輸入並生成回應."""
        print(f"[處理用戶輸入] 輸入: {user_input}, 角色: {current_character}")
        
        if not self.current_story:
            print("[錯誤] 沒有活躍的故事，嘗試載入已保存的故事")
            self.current_story = self.load_story()
            if not self.current_story:
                raise ValueError("沒有活躍的故事，請先創建或選擇一個世界")
            
        # 初始化新的聊天會話
        if not self.current_session_id:
            print("[信息] 創建新的聊天會話")
            self.current_session_id = self._create_new_chat_session(current_character)
            
        # 更新對話歷史
        self.dialogue_history.append({
            'speaker': 'user',
            'content': user_input,
            'timestamp': self._get_timestamp()
        })
        
        # 獲取當前角色
        print(f"[信息] 嘗試獲取角色: {current_character}")
        print(f"[調試] 當前可用角色: {list(self.current_story.characters.keys())}")
        character = self.current_story.characters.get(current_character.lower())
        if not character:
            print(f"[錯誤] 找不到角色 {current_character}")
            raise ValueError(f"找不到角色: {current_character}")
            
        # 使用AI生成回應
        print(f"[調試] 正在生成AI回應...")
        response = self.ai_handler.generate_response(
            character=character,
            user_input=user_input,
            dialogue_history=self.dialogue_history,
            story_context=self.current_story
        )
        print(f"[調試] AI回應: {response}")
        
        # 更新對話歷史
        self.dialogue_history.append({
            'speaker': current_character,
            'content': response,
            'timestamp': self._get_timestamp()
        })
        
        # 保存聊天記錄
        self._save_chat_session()
        
        # 返回回應和空選項列表
        return response, []
        
    def _create_new_chat_session(self, character_name: str) -> str:
        """創建新的聊天會話."""
        import uuid
        session_id = str(uuid.uuid4())
        
        session_data = {
            'id': session_id,
            'character_name': character_name,
            'world_name': self.current_story.setting,
            'timestamp': self._get_timestamp(),
            'dialogue_history': [],
            'story_context': self.current_story.to_dict()
        }
        
        # 保存新會話
        self._save_chat_session_data(session_id, session_data)
        
        return session_id
        
    def _save_chat_session(self) -> None:
        """保存當前聊天會話."""
        if not self.current_session_id or not self.current_story:
            return
            
        # 獲取現有會話數據
        file_path = os.path.join('data', 'chat_history', f'{self.current_session_id}.json')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
        except FileNotFoundError:
            return
            
        # 更新會話數據
        session_data['dialogue_history'] = self.dialogue_history
        session_data['last_message'] = self.dialogue_history[-1]['content'] if self.dialogue_history else ''
        session_data['timestamp'] = self._get_timestamp()
        
        # 保存更新後的數據
        self._save_chat_session_data(self.current_session_id, session_data)
        
    def _save_chat_session_data(self, session_id: str, data: Dict) -> None:
        """保存聊天會話數據到文件."""
        os.makedirs('data/chat_history', exist_ok=True)
        file_path = os.path.join('data', 'chat_history', f'{session_id}.json')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def _get_timestamp(self) -> str:
        """獲取當前時間戳."""
        from datetime import datetime
        return datetime.now().isoformat()
        
    def _save_story(self) -> None:
        """保存當前故事到文件."""
        if not self.current_story:
            return
            
        story_data = {
            'story': self.current_story.to_dict(),
            'dialogue_history': self.dialogue_history,
            'current_session_id': self.current_session_id
        }
        
        os.makedirs('data/stories', exist_ok=True)
        with open('data/stories/current_story.json', 'w', 
                 encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
            
    def load_story(self) -> Optional[Story]:
        """從文件載入故事."""
        try:
            with open('data/stories/current_story.json', 'r', 
                     encoding='utf-8') as f:
                data = json.load(f)
                
                story_data = data.get('story', {})
                self.current_story = Story.from_dict(story_data)
                self.dialogue_history = data.get('dialogue_history', [])
                self.current_session_id = data.get('current_session_id')
                
                return self.current_story
        except FileNotFoundError:
            return None
