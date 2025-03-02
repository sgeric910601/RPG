"""文件存儲服務，使用文件系統存儲數據。"""

import os
import json
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path

from .base import StorageService
from ...utils.error import DatabaseError

class FileStorageService(StorageService):
    """文件存儲服務，使用文件系統存儲數據。"""
    
    def __init__(self, base_dir: str):
        """初始化文件存儲服務。
        
        Args:
            base_dir: 基礎目錄，所有數據將存儲在此目錄下
        """
        self.base_dir = Path(base_dir)
        self._ensure_base_dir()
    
    def _ensure_base_dir(self) -> None:
        """確保基礎目錄存在。"""
        if not self.base_dir.exists():
            self.base_dir.mkdir(parents=True)
    
    def _get_collection_dir(self, collection: str) -> Path:
        """獲取集合目錄。
        
        Args:
            collection: 集合名稱
            
        Returns:
            集合目錄路徑
        """
        collection_dir = self.base_dir / collection
        if not collection_dir.exists():
            collection_dir.mkdir(parents=True)
        return collection_dir
        
    def ensure_directory(self, path: str) -> None:
        """確保目錄存在。
        
        Args:
            path: 目錄路徑
        """
        dir_path = Path(path)
        if not dir_path.exists():
            dir_path.mkdir(parents=True)

    
    def _get_file_path(self, collection: str, id: str) -> Path:
        """獲取文件路徑。
        
        Args:
            collection: 集合名稱
            id: 數據ID
            
        Returns:
            文件路徑
        """
        return self._get_collection_dir(collection) / f"{id}.json"
    
    def list_files(self, directory: str) -> List[str]:
        """列出目錄中的所有文件。
        
        Args:
            directory: 目錄路徑
            
        Returns:
            文件名列表
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            self.ensure_directory(directory)
            return []
        
        return [f.name for f in dir_path.iterdir() if f.is_file()]
    
    def read_file(self, file_path: str) -> str:
        """讀取文件內容。
        
        Args:
            file_path: 文件路徑
            
        Returns:
            文件內容
            
        Raises:
            DatabaseError: 如果讀取文件失敗
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise DatabaseError(f"Failed to read file: {str(e)}")
    
    def write_file(self, file_path: str, content: str) -> bool:
        """寫入文件內容。
        
        Args:
            file_path: 文件路徑
            content: 文件內容
            
        Returns:
            寫入是否成功
        """
        self.ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    def delete_file(self, file_path: str) -> bool:
        """刪除文件。
        
        Args:
            file_path: 文件路徑
            
        Returns:
            刪除是否成功
        """
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            raise DatabaseError(f"Failed to delete file: {str(e)}")
    
    def save(self, collection: str, id: str, data: Dict[str, Any]) -> bool:
        """保存數據。
        
        Args:
            collection: 集合名稱
            id: 數據ID
            data: 要保存的數據
            
        Returns:
            保存是否成功
        """
        try:
            file_path = self._get_file_path(collection, id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            raise DatabaseError(f"Failed to save data: {str(e)}")
    
    def load(self, collection: str, id: str) -> Optional[Dict[str, Any]]:
        """加載數據。
        
        Args:
            collection: 集合名稱
            id: 數據ID
            
        Returns:
            加載的數據，如果不存在則返回None
        """
        file_path = self._get_file_path(collection, id)
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise DatabaseError(f"Failed to load data: {str(e)}")
    
    def delete(self, collection: str, id: str) -> bool:
        """刪除數據。
        
        Args:
            collection: 集合名稱
            id: 數據ID
            
        Returns:
            刪除是否成功
        """
        file_path = self._get_file_path(collection, id)
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except Exception as e:
            raise DatabaseError(f"Failed to delete data: {str(e)}")
    
    def list(self, collection: str, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """列出數據。
        
        Args:
            collection: 集合名稱
            query: 查詢條件
            
        Returns:
            數據列表
        """
        collection_dir = self._get_collection_dir(collection)
        result = []
        
        try:
            for file_path in collection_dir.glob("*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 如果有查詢條件，進行過濾
                    if query:
                        match = True
                        for key, value in query.items():
                            if key not in data or data[key] != value:
                                match = False
                                break
                        
                        if not match:
                            continue
                    
                    result.append(data)
            
            return result
        except Exception as e:
            raise DatabaseError(f"Failed to list data: {str(e)}")
    
    def exists(self, collection: str, id: str) -> bool:
        """檢查數據是否存在。
        
        Args:
            collection: 集合名稱
            id: 數據ID
            
        Returns:
            數據是否存在
        """
        file_path = self._get_file_path(collection, id)
        return file_path.exists()
    
    def count(self, collection: str, query: Optional[Dict[str, Any]] = None) -> int:
        """計算數據數量。
        
        Args:
            collection: 集合名稱
            query: 查詢條件
            
        Returns:
            數據數量
        """
        if query:
            # 如果有查詢條件，需要加載所有數據進行過濾
            return len(self.list(collection, query))
        else:
            # 如果沒有查詢條件，直接計算文件數量
            collection_dir = self._get_collection_dir(collection)
            return len(list(collection_dir.glob("*.json")))
    
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
        file_path = self._get_file_path(collection, id)
        
        if not file_path.exists():
            if upsert:
                return self.save(collection, id, data)
            return False
        
        try:
            # 讀取現有數據
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            # 更新數據
            existing_data.update(data)
            
            # 保存更新後的數據
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            raise DatabaseError(f"Failed to update data: {str(e)}")
    
    def clear(self, collection: str) -> bool:
        """清空集合。
        
        Args:
            collection: 集合名稱
            
        Returns:
            清空是否成功
        """
        collection_dir = self._get_collection_dir(collection)
        
        try:
            # 刪除集合目錄
            shutil.rmtree(collection_dir)
            
            # 重新創建集合目錄
            collection_dir.mkdir(parents=True)
            
            return True
        except Exception as e:
            raise DatabaseError(f"Failed to clear collection: {str(e)}")