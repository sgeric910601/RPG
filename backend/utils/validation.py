"""數據驗證模組，提供數據驗證功能。"""

import re
from typing import Any, Dict, List, Optional, Union, Callable
from .error import ValidationError

class Validator:
    """數據驗證類，提供各種數據驗證方法。"""
    
    @staticmethod
    def validate_required(data: Dict[str, Any], fields: List[str]) -> None:
        """驗證必填字段。
        
        Args:
            data: 要驗證的數據字典
            fields: 必填字段列表
            
        Raises:
            ValidationError: 如果缺少必填字段
        """
        missing_fields = [field for field in fields if field not in data or data[field] is None]
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}",
                {"missing_fields": missing_fields}
            )
    
    @staticmethod
    def validate_string(value: Any, field_name: str, min_length: int = 0, max_length: Optional[int] = None) -> None:
        """驗證字符串。
        
        Args:
            value: 要驗證的值
            field_name: 字段名稱，用於錯誤消息
            min_length: 最小長度
            max_length: 最大長度
            
        Raises:
            ValidationError: 如果驗證失敗
        """
        if not isinstance(value, str):
            raise ValidationError(
                f"Field '{field_name}' must be a string",
                {"field": field_name, "type": type(value).__name__}
            )
        
        if len(value) < min_length:
            raise ValidationError(
                f"Field '{field_name}' must be at least {min_length} characters long",
                {"field": field_name, "min_length": min_length, "actual_length": len(value)}
            )
        
        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"Field '{field_name}' must be at most {max_length} characters long",
                {"field": field_name, "max_length": max_length, "actual_length": len(value)}
            )
    
    @staticmethod
    def validate_number(value: Any, field_name: str, min_value: Optional[Union[int, float]] = None, 
                       max_value: Optional[Union[int, float]] = None, integer: bool = False) -> None:
        """驗證數字。
        
        Args:
            value: 要驗證的值
            field_name: 字段名稱，用於錯誤消息
            min_value: 最小值
            max_value: 最大值
            integer: 是否必須是整數
            
        Raises:
            ValidationError: 如果驗證失敗
        """
        if integer:
            if not isinstance(value, int):
                raise ValidationError(
                    f"Field '{field_name}' must be an integer",
                    {"field": field_name, "type": type(value).__name__}
                )
        else:
            if not isinstance(value, (int, float)):
                raise ValidationError(
                    f"Field '{field_name}' must be a number",
                    {"field": field_name, "type": type(value).__name__}
                )
        
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"Field '{field_name}' must be at least {min_value}",
                {"field": field_name, "min_value": min_value, "actual_value": value}
            )
        
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"Field '{field_name}' must be at most {max_value}",
                {"field": field_name, "max_value": max_value, "actual_value": value}
            )
    
    @staticmethod
    def validate_boolean(value: Any, field_name: str) -> None:
        """驗證布爾值。
        
        Args:
            value: 要驗證的值
            field_name: 字段名稱，用於錯誤消息
            
        Raises:
            ValidationError: 如果驗證失敗
        """
        if not isinstance(value, bool):
            raise ValidationError(
                f"Field '{field_name}' must be a boolean",
                {"field": field_name, "type": type(value).__name__}
            )
    
    @staticmethod
    def validate_list(value: Any, field_name: str, min_length: int = 0, 
                     max_length: Optional[int] = None, item_validator: Optional[Callable[[Any, str], None]] = None) -> None:
        """驗證列表。
        
        Args:
            value: 要驗證的值
            field_name: 字段名稱，用於錯誤消息
            min_length: 最小長度
            max_length: 最大長度
            item_validator: 列表項驗證函數
            
        Raises:
            ValidationError: 如果驗證失敗
        """
        if not isinstance(value, list):
            raise ValidationError(
                f"Field '{field_name}' must be a list",
                {"field": field_name, "type": type(value).__name__}
            )
        
        if len(value) < min_length:
            raise ValidationError(
                f"Field '{field_name}' must have at least {min_length} items",
                {"field": field_name, "min_length": min_length, "actual_length": len(value)}
            )
        
        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"Field '{field_name}' must have at most {max_length} items",
                {"field": field_name, "max_length": max_length, "actual_length": len(value)}
            )
        
        if item_validator:
            for i, item in enumerate(value):
                try:
                    item_validator(item, f"{field_name}[{i}]")
                except ValidationError as e:
                    raise ValidationError(
                        f"Invalid item in '{field_name}' at index {i}: {e.message}",
                        {"field": field_name, "index": i, "details": e.details}
                    )
    
    @staticmethod
    def validate_dict(value: Any, field_name: str, required_keys: Optional[List[str]] = None,
                     key_validator: Optional[Callable[[str, str], None]] = None,
                     value_validator: Optional[Callable[[Any, str], None]] = None) -> None:
        """驗證字典。
        
        Args:
            value: 要驗證的值
            field_name: 字段名稱，用於錯誤消息
            required_keys: 必須包含的鍵列表
            key_validator: 鍵驗證函數
            value_validator: 值驗證函數
            
        Raises:
            ValidationError: 如果驗證失敗
        """
        if not isinstance(value, dict):
            raise ValidationError(
                f"Field '{field_name}' must be a dictionary",
                {"field": field_name, "type": type(value).__name__}
            )
        
        if required_keys:
            missing_keys = [key for key in required_keys if key not in value]
            if missing_keys:
                raise ValidationError(
                    f"Field '{field_name}' is missing required keys: {', '.join(missing_keys)}",
                    {"field": field_name, "missing_keys": missing_keys}
                )
        
        if key_validator or value_validator:
            for k, v in value.items():
                if key_validator:
                    try:
                        key_validator(k, f"{field_name} key")
                    except ValidationError as e:
                        raise ValidationError(
                            f"Invalid key in '{field_name}': {e.message}",
                            {"field": field_name, "key": k, "details": e.details}
                        )
                
                if value_validator:
                    try:
                        value_validator(v, f"{field_name}[{k}]")
                    except ValidationError as e:
                        raise ValidationError(
                            f"Invalid value in '{field_name}' for key '{k}': {e.message}",
                            {"field": field_name, "key": k, "details": e.details}
                        )
    
    @staticmethod
    def validate_email(value: Any, field_name: str) -> None:
        """驗證電子郵件地址。
        
        Args:
            value: 要驗證的值
            field_name: 字段名稱，用於錯誤消息
            
        Raises:
            ValidationError: 如果驗證失敗
        """
        Validator.validate_string(value, field_name)
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValidationError(
                f"Field '{field_name}' must be a valid email address",
                {"field": field_name, "value": value}
            )
    
    @staticmethod
    def validate_url(value: Any, field_name: str) -> None:
        """驗證URL。
        
        Args:
            value: 要驗證的值
            field_name: 字段名稱，用於錯誤消息
            
        Raises:
            ValidationError: 如果驗證失敗
        """
        Validator.validate_string(value, field_name)
        
        url_pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, value):
            raise ValidationError(
                f"Field '{field_name}' must be a valid URL",
                {"field": field_name, "value": value}
            )
    
    @staticmethod
    def validate_enum(value: Any, field_name: str, allowed_values: List[Any]) -> None:
        """驗證枚舉值。
        
        Args:
            value: 要驗證的值
            field_name: 字段名稱，用於錯誤消息
            allowed_values: 允許的值列表
            
        Raises:
            ValidationError: 如果驗證失敗
        """
        if value not in allowed_values:
            raise ValidationError(
                f"Field '{field_name}' must be one of: {', '.join(map(str, allowed_values))}",
                {"field": field_name, "value": value, "allowed_values": allowed_values}
            )