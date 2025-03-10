"""AI服務抽象基類，定義所有AI服務的通用接口。"""

from abc import ABC, abstractmethod
import json
import os
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
import logging

logger = logging.getLogger(__name__)

class AIService(ABC):
    """AI服務抽象基類，定義所有AI服務的通用接口。"""
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """同步生成文本響應。
        
        Args:
            prompt: 提示詞
            **kwargs: 其他參數
            
        Returns:
            生成的文本
        """
        pass
    
    @abstractmethod
    async def generate_chat_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """異步生成聊天響應。
        
        Args:
            messages: 消息列表，每個消息包含 role 和 content
            **kwargs: 其他參數
            
        Returns:
            生成的聊天響應
        """
        pass
    
    @abstractmethod
    async def generate_stream_response(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """生成流式回應。
        
        Args:
            messages: 對話歷史
            model: 要使用的模型名稱
            temperature: 溫度參數
            max_tokens: 最大生成的token數量
            **kwargs: 其他參數
            
        Yields:
            生成的文本片段
        """
        pass
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = True,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """生成AI回覆。
        
        Args:
            messages: 對話歷史
            model: 要使用的模型名稱
            temperature: 溫度參數
            max_tokens: 最大生成的token數量
            stream: 是否使用流式輸出
            **kwargs: 其他參數
            
        Yields:
            生成的文本片段
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
    
    @abstractmethod
    def set_model(self, model_id: str) -> bool:
        """設置當前使用的模型。
        
        Args:
            model_id: 模型ID
        Returns:
            設置是否成功
        """
        pass

class AIServiceFactory:
    """AI服務工廠類，負責創建和管理AI服務實例。"""
    
    _services: Dict[str, AIService] = {}
    _default_service: Optional[str] = None
    _api_types: Dict[str, str] = {}  # 映射 api_type 到服務名稱
    
    @classmethod
    def register_service(cls, name: str, service: AIService, api_type: str) -> None:
        """註冊AI服務。
        
        Args:
            name: 服務名稱
            service: 服務實例
            api_type: API類型（如 'openai', 'claude', 'openrouter'）
        """
        cls._services[name] = service
        cls._api_types[api_type] = name
        
        # 如果是OpenRouter，設為默認服務
        if api_type == 'openrouter':
            cls._default_service = name
            logger.info(f"[AIServiceFactory] 設置默認服務為: {name} (OpenRouter)")
        elif cls._default_service is None:
            cls._default_service = name
    
    @classmethod
    def get_service(cls, api_type: Optional[str] = None) -> Optional[AIService]:
        """獲取AI服務。
        
        Args:
            api_type: API類型，如果為None則返回默認服務
            
        Returns:
            服務實例，如果不存在則返回None
        """
        if api_type:
            service_name = cls._api_types.get(api_type)
            if service_name:
                logger.info(f"[AIServiceFactory] 使用API類型 {api_type} 的服務: {service_name}")
                return cls._services.get(service_name)
            
        if cls._default_service:
            logger.info(f"[AIServiceFactory] 使用默認服務: {cls._default_service}")
            return cls._services.get(cls._default_service)
            
        return None
    
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
        self.config_dir = 'config'
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        self.config_path = os.path.join(self.config_dir, 'models.json')
        
        # 預設模型配置
        self.default_models = {
            "openrouter/deepseek-chat": {
                "name": "DeepSeek Chat",
                "description": "DeepSeek的對話模型",
                "api_type": "openrouter",
                "max_tokens": 4096,
                "enabled": True
            },
            "openrouter/claude-3-opus": {
                "name": "Claude 3 Opus",
                "description": "Anthropic的最強大模型",
                "api_type": "openrouter",
                "max_tokens": 4096,
                "enabled": True
            }
        }
        
        logger.info("[ModelManager] 初始化，配置路徑: %s", self.config_path)
        
        # 加載模型配置
        self.models = self._load_models()
        self._initialized = True
    
    def _load_models(self) -> Dict[str, Dict[str, Any]]:
        """從配置文件加載模型信息。
        
        Returns:
            模型信息字典，鍵為模型ID，值為模型信息
        """
        # 如果配置文件不存在，創建預設配置
        if not os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.default_models, f, ensure_ascii=False, indent=4)
                logger.info("[ModelManager] 創建預設配置文件")
                return self.default_models
            except Exception as e:
                logger.error("[ModelManager] 創建預設配置失敗: %s", str(e))
                return self.default_models
        
        # 讀取現有配置
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                models = json.load(f)
                return models
        except Exception as e:
            logger.error("[ModelManager] 讀取配置失敗: %s", str(e))
            return {}
    
    def get_all_models(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有可用的模型。
        
        Returns:
            模型信息字典，鍵為模型ID，值為模型信息
        """
        logger.info("[ModelManager] 獲取所有模型: %d 個", len(self.models))
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
        model_info = self.models.get(model_id)
        if model_info:
            logger.info(f"[ModelManager] 獲取模型信息: {model_id} (api_type={model_info.get('api_type')})")
        return model_info
    
    def get_default_model(self) -> Optional[str]:
        """獲取默認模型ID。
        
        Returns:
            默認模型ID，如果沒有則返回None
        """
        # 優先選擇OpenRouter模型
        for model_id, model_info in self.get_all_models().items():
            if model_info.get('api_type') == 'openrouter':
                logger.info(f"[ModelManager] 選擇默認OpenRouter模型: {model_id}")
                return model_id
        
        # 如果沒有OpenRouter模型，返回第一個可用模型
        available_models = self.get_all_models()
        if available_models:
            model_id = next(iter(available_models.keys()))
            logger.info(f"[ModelManager] 選擇默認模型: {model_id}")
            return model_id
        
        return None
    
    def set_model(self, model_id: str) -> bool:
        """設置當前使用的模型。
        
        Args:
            model_id: 模型ID
            
        Returns:
            設置是否成功
        """
        # 檢查模型是否存在
        model_info = self.get_model(model_id)
        if not model_info:
            logger.warning("[ModelManager] 模型不存在: %s", model_id)
            return False
        
        # 檢查模型是否啟用
        if not model_info.get('enabled', True):
            logger.warning("[ModelManager] 模型未啟用: %s", model_id)
            return False
        
        # 獲取對應的AI服務
        api_type = model_info.get('api_type')
        ai_service = AIServiceFactory.get_service(api_type)
        if not ai_service:
            logger.error(f"[ModelManager] 無法獲取API類型為 {api_type} 的服務")
            return False
        
        # 設置模型
        try:
            logger.info(f"[ModelManager] 設置當前模型: {model_id} (api_type={api_type})")
            ai_service.set_model(model_id)
            return True
        except Exception as e:
            logger.error("[ModelManager] 設置模型失敗: %s", str(e))
            return False