"""日誌管理模組，負責統一記錄系統日誌。"""

import logging
import os
from typing import Optional, Dict

class Logger:
    """日誌記錄類，負責記錄系統日誌。"""
    
    # 保存所有已創建的日誌記錄器實例
    _loggers: Dict[str, 'Logger'] = {}
    
    @classmethod
    def get_logger(cls, name: str, log_level: int = logging.INFO, log_file: Optional[str] = None):
        """獲取日誌記錄器實例。
        
        Args:
            name: 日誌記錄器名稱
            log_level: 日誌級別
            log_file: 日誌文件路徑，如果為None則只輸出到控制台
            
        Returns:
            日誌記錄器實例
        """
        if name not in cls._loggers:
            cls._loggers[name] = cls(name, log_level, log_file)
        return cls._loggers[name]
    
    def __init__(self, name: str, log_level: int = logging.INFO, log_file: Optional[str] = None):
        """初始化日誌記錄器。
        
        Args:
            name: 日誌記錄器名稱
            log_level: 日誌級別
            log_file: 日誌文件路徑，如果為None則只輸出到控制台
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # 清除現有的處理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 添加控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 如果提供了日誌文件路徑，添加文件處理器
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
    def debug(self, message: str) -> None:
        """記錄調試級別日誌。
        
        Args:
            message: 日誌消息
        """
        self.logger.debug(message)
        
    def info(self, message: str) -> None:
        """記錄信息級別日誌。
        
        Args:
            message: 日誌消息
        """
        self.logger.info(message)
        
    def warning(self, message: str) -> None:
        """記錄警告級別日誌。
        
        Args:
            message: 日誌消息
        """
        self.logger.warning(message)
        
    def error(self, message: str) -> None:
        """記錄錯誤級別日誌。
        
        Args:
            message: 日誌消息
        """
        self.logger.error(message)
        
    def critical(self, message: str) -> None:
        """記錄嚴重錯誤級別日誌。
        
        Args:
            message: 日誌消息
        """
        self.logger.critical(message)
        
    def exception(self, message: str) -> None:
        """記錄異常信息，包括堆棧跟踪。
        
        Args:
            message: 日誌消息
        """
        self.logger.exception(message)