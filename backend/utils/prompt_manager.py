"""提示詞模板管理模組，用於管理不同場景的提示詞模板。"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

class PromptTemplate:
    """提示詞模板類，包含模板內容和插值功能。"""
    
    def __init__(self, name: str, content: str, description: str = "", metadata: Optional[Dict[str, Any]] = None):
        """初始化提示詞模板。
        
        Args:
            name: 模板名稱
            content: 模板內容
            description: 模板描述
            metadata: 與模板相關的元數據
        """
        self.name = name
        self.content = content
        self.description = description
        self.metadata = metadata or {}
    
    def format(self, **kwargs) -> str:
        """使用提供的參數格式化模板。
        
        Args:
            **kwargs: 格式化參數
            
        Returns:
            格式化後的提示詞內容
        """
        try:
            return self.content.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"模板格式化失敗，缺少參數: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """將模板轉換為字典格式。"""
        return {
            "name": self.name,
            "content": self.content,
            "description": self.description,
            "metadata": self.metadata
        }


class PromptManager:
    """提示詞模板管理器，負責加載和管理提示詞模板。"""
    
    DEFAULT_SYSTEM_PROMPT = """你是一個有用的AI助手。請根據用戶的問題提供準確、有益的回答。"""
    
    ROLEPLAY_PROMPT = """你現在扮演{character_name}，具有以下特點：
{character_description}

請以{character_name}的身份與我對話，保持角色一致性。請注意以下規則：
1. 始終保持角色身份，不要暴露你是AI的事實
2. 用{character_name}的方式說話和思考，包括語氣、詞彙選擇等
3. 回應要符合{character_name}的背景故事和世界觀
4. 如果問題讓你無法以角色身份回答，請創造性地保持在角色中轉移話題

現在，請以{character_name}的身份開始回應。"""
    
    STORY_PROMPT = """你是一位出色的故事創作者。請根據以下要素創作一個引人入勝的故事：

背景設定：{setting}
主要人物：{characters}
故事主題：{theme}
故事風格：{style}

請創作一個結構完整、情節有趣、對話生動的故事。故事長度應為{length}字左右。"""
    
    def __init__(self, templates_dir: Optional[str] = None):
        """初始化提示詞管理器。
        
        Args:
            templates_dir: 模板文件目錄，如果提供則加載該目錄中的模板
        """
        self.templates: Dict[str, PromptTemplate] = {}
        self.enhancer = None  # 將由外部設置
        
        # 添加默認模板
        self.add_template("default_system", self.DEFAULT_SYSTEM_PROMPT, "默認系統提示詞")
        self.add_template("roleplay", self.ROLEPLAY_PROMPT, "角色扮演提示詞")
        self.add_template("story_generation", self.STORY_PROMPT, "故事生成提示詞")
        
        # 如果提供了模板目錄，從目錄加載模板
        if templates_dir and os.path.exists(templates_dir):
            self.load_templates_from_directory(templates_dir)
    
    def add_template(self, name: str, content: str, description: str = "", metadata: Optional[Dict[str, Any]] = None) -> None:
        """添加新的提示詞模板。
        
        Args:
            name: 模板名稱
            content: 模板內容
            description: 模板描述
            metadata: 與模板相關的元數據
        """
        self.templates[name] = PromptTemplate(name, content, description, metadata)
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """獲取指定名稱的模板。
        
        Args:
            name: 模板名稱
            
        Returns:
            提示詞模板，如果不存在則返回None
        """
        return self.templates.get(name)
    
    def delete_template(self, name: str) -> bool:
        """刪除指定名稱的模板。
        
        Args:
            name: 模板名稱
            
        Returns:
            刪除是否成功
        """
        if name in self.templates:
            del self.templates[name]
            return True
        return False
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有可用的模板。
        
        Returns:
            模板信息列表
        """
        return [
            {
                "name": template.name,
                "description": template.description,
                "metadata": template.metadata
            }
            for template in self.templates.values()
        ]
    
    def load_templates_from_directory(self, directory: str) -> int:
        """從目錄中加載JSON格式的模板文件。
        
        Args:
            directory: 模板文件目錄
            
        Returns:
            成功加載的模板數量
        """
        loaded_count = 0
        template_dir = Path(directory)
        
        if not template_dir.exists() or not template_dir.is_dir():
            return 0
            
        for file_path in template_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    template_data = json.load(f)
                
                name = template_data.get("name") or file_path.stem
                content = template_data.get("content")
                description = template_data.get("description", "")
                metadata = template_data.get("metadata", {})
                
                if content:
                    self.add_template(name, content, description, metadata)
                    loaded_count += 1
            except Exception as e:
                print(f"加載模板文件 {file_path} 失敗: {str(e)}")
        
        return loaded_count
    
    def save_templates_to_directory(self, directory: str) -> int:
        """將模板保存到目錄中的JSON文件。
        
        Args:
            directory: 目標目錄
            
        Returns:
            成功保存的模板數量
        """
        saved_count = 0
        template_dir = Path(directory)
        
        # 確保目錄存在
        template_dir.mkdir(parents=True, exist_ok=True)
            
        for template in self.templates.values():
            try:
                file_path = template_dir / f"{template.name}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
                saved_count += 1
            except Exception as e:
                print(f"保存模板 {template.name} 失敗: {str(e)}")
        
        return saved_count

    def set_enhancer(self, enhancer) -> None:
        """設置提示詞增強器實例。"""
        self.enhancer = enhancer
        
    def get_enhancer(self):
        """獲取提示詞增強器實例。"""
        return self.enhancer
        
    def enhance_prompt(self, prompt: str) -> Dict[str, Any]:
        """使用提示詞增強器優化提示詞。
        
        Args:
            prompt: 要增強的提示詞
            
        Returns:
            包含增強結果的字典，包括：
            - enhanced_prompt: 優化後的提示詞
            - analysis: 提示詞分析結果
            - suggestions: 改進建議列表
        """
        self._ensure_enhancer()
        
        # 進行提示詞分析
        analysis = self.enhancer.analyze_prompt(prompt)
        
        # 生成增強後的提示詞
        enhanced_prompt = self.enhancer.enhance_prompt(prompt)
        
        return {
            "enhanced_prompt": enhanced_prompt,
            "analysis": {
                "clarity_score": analysis.clarity_score,
                "context_score": analysis.context_score,
                "specificity_score": analysis.specificity_score,
                "structure_score": analysis.structure_score,
                "overall_score": analysis.overall_score
            },
            "suggestions": analysis.suggestions
        }

    def _ensure_enhancer(self):
        """確保存在提示詞增強器實例。"""
        if not self.enhancer:
            from .prompt_enhancer import PromptEnhancer
            self.enhancer = PromptEnhancer()
