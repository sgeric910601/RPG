"""錯誤處理模組，提供統一的錯誤類和錯誤處理機制。"""

from typing import Dict, Any, Optional

class AppError(Exception):
    """應用錯誤基類，所有自定義錯誤都應繼承此類。"""
    
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        """初始化應用錯誤。
        
        Args:
            code: 錯誤代碼
            message: 錯誤消息
            details: 錯誤詳情
        """
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式，用於API響應。
        
        Returns:
            錯誤字典
        """
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }

class ValidationError(AppError):
    """數據驗證錯誤，當輸入數據不符合要求時拋出。"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """初始化驗證錯誤。
        
        Args:
            message: 錯誤消息
            details: 錯誤詳情
        """
        super().__init__("VALIDATION_ERROR", message, details)

class NotFoundError(AppError):
    """資源未找到錯誤，當請求的資源不存在時拋出。"""
    
    def __init__(self, resource_type: str, resource_id: str):
        """初始化資源未找到錯誤。
        
        Args:
            resource_type: 資源類型
            resource_id: 資源ID
        """
        super().__init__(
            "NOT_FOUND_ERROR",
            f"{resource_type} with ID {resource_id} not found",
            {"resource_type": resource_type, "resource_id": resource_id}
        )

class AuthenticationError(AppError):
    """認證錯誤，當用戶認證失敗時拋出。"""
    
    def __init__(self, message: str = "Authentication failed"):
        """初始化認證錯誤。
        
        Args:
            message: 錯誤消息
        """
        super().__init__("AUTHENTICATION_ERROR", message)

class AuthorizationError(AppError):
    """授權錯誤，當用戶沒有權限執行操作時拋出。"""
    
    def __init__(self, message: str = "Permission denied"):
        """初始化授權錯誤。
        
        Args:
            message: 錯誤消息
        """
        super().__init__("AUTHORIZATION_ERROR", message)

class ServiceError(AppError):
    """服務錯誤，當外部服務調用失敗時拋出。"""
    
    def __init__(self, service_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        """初始化服務錯誤。
        
        Args:
            service_name: 服務名稱
            message: 錯誤消息
            details: 錯誤詳情
        """
        error_details = details or {}
        error_details["service_name"] = service_name
        super().__init__("SERVICE_ERROR", message, error_details)

class DatabaseError(AppError):
    """數據庫錯誤，當數據庫操作失敗時拋出。"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """初始化數據庫錯誤。
        
        Args:
            message: 錯誤消息
            details: 錯誤詳情
        """
        super().__init__("DATABASE_ERROR", message, details)

class ConfigurationError(AppError):
    """配置錯誤，當系統配置錯誤時拋出。"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """初始化配置錯誤。
        
        Args:
            message: 錯誤消息
            details: 錯誤詳情
        """
        super().__init__("CONFIGURATION_ERROR", message, details)

def handle_error(error: Exception) -> Dict[str, Any]:
    """統一處理錯誤，轉換為API響應格式。
    
    Args:
        error: 錯誤實例
        
    Returns:
        錯誤響應字典
    """
    if isinstance(error, AppError):
        return error.to_dict()
    else:
        # 未知錯誤
        return {
            "code": "UNKNOWN_ERROR",
            "message": str(error),
            "details": {}
        }