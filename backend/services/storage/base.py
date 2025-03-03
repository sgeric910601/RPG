"""存儲服務抽象基類，定義所有存儲服務的通用接口。"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class StorageService(ABC):
    """存儲服務抽象基類，定義所有存儲服務的通用接口。"""
    
    @abstractmethod
    def save(self, collection: str, id: str, data: Dict[str, Any]) -> bool:
        """保存數據。
        
        Args:
            collection: 集合名稱
            id: 數據ID
            data: 要保存的數據
            
        Returns:
            保存是否成功
        """
        pass
    
    @abstractmethod
    def load(self, collection: str, id: str) -> Optional[Dict[str, Any]]:
        """加載數據。
        
        Args:
            collection: 集合名稱
            id: 數據ID
            
        Returns:
            加載的數據，如果不存在則返回None
        """
        pass
    
    @abstractmethod
    def delete(self, collection: str, id: str) -> bool:
        """刪除數據。
        
        Args:
            collection: 集合名稱
            id: 數據ID
            
        Returns:
            刪除是否成功
        """
        pass
    
    @abstractmethod
    def list(self, collection: str, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """列出數據。
        
        Args:
            collection: 集合名稱
            query: 查詢條件
            
        Returns:
            數據列表
        """
        pass
    
    @abstractmethod
    def exists(self, collection: str, id: str) -> bool:
        """檢查數據是否存在。
        
        Args:
            collection: 集合名稱
            id: 數據ID
            
        Returns:
            數據是否存在
        """
        pass
    
    @abstractmethod
    def count(self, collection: str, query: Optional[Dict[str, Any]] = None) -> int:
        """計算數據數量。
        
        Args:
            collection: 集合名稱
            query: 查詢條件
            
        Returns:
            數據數量
        """
        pass
    
    @abstractmethod
    def update(self, collection: str, id: str, data: Dict[str, Any], upsert: bool = False) -> bool:
        """更新數據。
        
        Args:
            collection: 集合名稱
            id: 數據ID
            data: 要更新的數據
            upsert: 如果數據不存在，是否插入新數據
            
        Returns:
            更新是否成功
        """
        pass
    
    @abstractmethod
    def clear(self, collection: str) -> bool:
        """清空集合。
        
        Args:
            collection: 集合名稱
            
        Returns:
            清空是否成功
        """
        pass
    
    @abstractmethod
    def ensure_directory(self, path: str) -> None:
        """確保目錄存在。
        
        Args:
            path: 目錄路徑
        """
        pass
    
    @abstractmethod
    def list_files(self, directory: str) -> List[str]:
        """列出目錄中的所有文件。
        
        Args:
            directory: 目錄路徑
            
        Returns:
            文件名列表
        """
        pass
    
    @abstractmethod
    def read_file(self, file_path: str) -> str:
        """讀取文件內容。
        
        Args:
            file_path: 文件路徑
            
        Returns:
            文件內容
        """
        pass
    
    @abstractmethod
    def write_file(self, file_path: str, content: str) -> bool:
        """寫入文件內容。
        
        Args:
            file_path: 文件路徑
            content: 文件內容
        """
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """刪除文件。
        
        Args:
            file_path: 文件路徑
            
        Returns:
            刪除是否成功
        """
        pass
    
    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """檢查文件是否存在。
        
        Args:
            file_path: 文件路徑
            
        Returns:
            文件是否存在
        """
        pass

class StorageServiceFactory:
    """存儲服務工廠類，負責創建和管理存儲服務實例。"""
    
    _services: Dict[str, StorageService] = {}
    _default_service: Optional[str] = None
    
    @classmethod
    def register_service(cls, name: str, service: StorageService, default: bool = False) -> None:
        """註冊存儲服務。
        
        Args:
            name: 服務名稱
            service: 服務實例
            default: 是否設為默認服務
        """
        cls._services[name] = service
        if default or cls._default_service is None:
            cls._default_service = name
    
    @classmethod
    def get_service(cls, name: Optional[str] = None) -> Optional[StorageService]:
        """獲取存儲服務。
        
        Args:
            name: 服務名稱，如果為None則返回默認服務
            
        Returns:
            服務實例，如果不存在則返回None
        """
        if name is None:
            if cls._default_service is None:
                return None
            return cls._services.get(cls._default_service)
        return cls._services.get(name)
    
    @classmethod
    def list_services(cls) -> List[str]:
        """列出所有可用的服務。
        
        Returns:
            服務名稱列表
        """
        return list(cls._services.keys())
    
    @classmethod
    def get_default_service_name(cls) -> Optional[str]:
        """獲取默認服務名稱。
        
        Returns:
            默認服務名稱，如果沒有則返回None
        """
        return cls._default_service
    
    @classmethod
    def set_default_service(cls, name: str) -> bool:
        """設置默認服務。
        
        Args:
            name: 服務名稱
            
        Returns:
            設置是否成功
        """
        if name in cls._services:
            cls._default_service = name
            return True
        return False