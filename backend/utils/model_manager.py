"""模型管理模組，提供AI模型管理功能。"""

import json
import os
from typing import Dict, List, Any, Optional

from ..services.ai import AIServiceFactory


class ModelManager:
    """模型管理器類，提供AI模型管理功能。"""
    
    _instance = None
    
    def __new__(cls):
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