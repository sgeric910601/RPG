"""AI服務抽象基類，定義所有AI服務的通用接口。"""

from abc import ABC, abstractmethod
import json
import os
from typing import Dict, List, Any, Optional

class AIService(ABC):
    """AI服務抽象基類，定義所有AI服務的通用接口。"""
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本響應。
        
        Args:
            prompt: 提示詞
            **kwargs: 其他參數
            
        Returns:
            生成的文本
        """
        pass
    
    @abstractmethod
    def generate_chat_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成聊天響應。
        
        Args:
            messages: 消息列表，每個消息包含 role 和 content
            **kwargs: 其他參數
            
        Returns:
            生成的聊天響應
        """
        pass
    
    @abstractmethod
    def enhance_prompt(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """增強提示詞。
        
        Args:
            prompt: 原始提示詞
            **kwargs: 其他參數
            
        Returns:
            增強結果，包括增強後的提示詞和分析信息
        """
        pass
    
    @abstractmethod
    def analyze_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """分析文本。
        
        Args:
            text: 要分析的文本
            **kwargs: 其他參數
            
        Returns:
            分析結果
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型信息。
        
        Returns:
            模型信息，包括名稱、描述、能力等
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """檢查服務是否可用。
        
        Returns:
            服務是否可用
        """
        pass

class AIServiceFactory:
    """AI服務工廠類，負責創建和管理AI服務實例。"""
    
    _services: Dict[str, AIService] = {}
    _default_service: Optional[str] = None
    
    @classmethod
    def register_service(cls, name: str, service: AIService) -> None:
        """註冊AI服務。
        
        Args:
            name: 服務名稱
            service: 服務實例
        """
        cls._services[name] = service
        if cls._default_service is None:
            cls._default_service = name
    
    @classmethod
    def get_service(cls, name: Optional[str] = None) -> Optional[AIService]:
        """獲取AI服務。
        
        Args:
            name: 服務名稱，如果為None則返回默認服務
            
        Returns:
            服務實例，如果不存在則返回None
        """
        if name is None and cls._default_service is not None:
            return cls._services.get(cls._default_service)
        return cls._services.get(name) if name else None
    
    @classmethod
    def list_services(cls) -> List[str]:
        """列出所有可用的服務。
        
        Returns:
            服務名稱列表
        """
        return list(cls._services.keys())
    
    @classmethod
    def get_available_services(cls) -> List[str]:
        """列出所有可用的服務。
        
        Returns:
            可用的服務名稱列表
        """
        return [name for name, service in cls._services.items() if service.is_available()]


class ModelManager:
    """模型管理器類，提供AI模型管理功能。"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """創建模型管理器單例。"""
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化模型管理器。"""
        if self._initialized:
            return
        
        # 從配置文件加載模型信息
        self.config_path = os.path.join('config', 'config.json')
        self.models = self._load_models()
        self._initialized = True
    
    def _load_models(self) -> Dict[str, Dict[str, Any]]:
        """從配置文件加載模型信息。
        
        Returns:
            模型信息字典，鍵為模型ID，值為模型信息
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('models', {})
        except Exception as e:
            print(f"加載模型配置時出錯: {str(e)}")
            return {}
    
    def get_all_models(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有可用的模型。
        
        Returns:
            模型信息字典，鍵為模型ID，值為模型信息
        """
        return {
            model_id: model_info
            for model_id, model_info in self.models.items()
            if model_info.get('enabled', True)
        }
    
    def get_model_names(self) -> List[str]:
        """獲取所有可用模型的名稱。
        
        Returns:
            模型名稱列表
        """
        return [
            model_info.get('name', model_id)
            for model_id, model_info in self.get_all_models().items()
        ]
    
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """獲取指定ID的模型信息。
        
        Args:
            model_id: 模型ID
            
        Returns:
            模型信息字典，如果不存在則返回None
        """
        return self.models.get(model_id)
    
    def get_default_model(self) -> Optional[str]:
        """獲取默認模型ID。
        
        Returns:
            默認模型ID，如果沒有則返回None
        """
        # 獲取所有可用模型
        available_models = self.get_all_models()
        if not available_models:
            return None
        
        # 返回第一個可用模型的ID
        return next(iter(available_models.keys()))
    
    def set_model(self, model_id: str) -> bool:
        """設置當前使用的模型。
        
        Args:
            model_id: 模型ID
            
        Returns:
            設置是否成功
        """
        # 檢查模型是否存在
        if model_id not in self.models:
            return False
        
        # 檢查模型是否啟用
        if not self.models[model_id].get('enabled', True):
            return False
        
        # 獲取AI服務
        ai_service = AIServiceFactory.get_service()
        if not ai_service:
            return False
        
        # 設置模型
        try:
            ai_service.set_model(model_id)
            return True
        except Exception as e:
            print(f"設置模型時出錯: {str(e)}")
            return False