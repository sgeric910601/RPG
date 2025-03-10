"""配置管理模組，負責加載和管理系統配置。"""

import os
import json
from typing import Dict, List, Any, Optional

class Config:
    """配置管理類，負責加載和管理配置。"""
    
    _instance = None
    
    def __new__(cls, config_path=None):
        """實現單例模式，確保整個應用程序中只有一個配置實例。"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._init(config_path)
        return cls._instance
    
    def _init(self, config_path: Optional[str] = None):
        """初始化配置管理器。
        
        Args:
            config_path: 配置文件路徑，如果為None則使用默認路徑
        """
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), '../../config/config.json')
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加載配置文件。
        
        Returns:
            配置字典
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加載配置文件失敗: {str(e)}")
            return {}
            
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值。
        
        Args:
            key: 配置鍵，支持點號分隔的路徑，如 'server.port'
            default: 默認值，如果配置不存在則返回此值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
        
    def set(self, key: str, value: Any) -> None:
        """設置配置值。
        
        Args:
            key: 配置鍵，支持點號分隔的路徑，如 'server.port'
            value: 配置值
        """
        keys = key.split('.')
        target = self.config
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        
    def save(self) -> bool:
        """保存配置到文件。
        
        Returns:
            保存是否成功
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失敗: {str(e)}")
            return False