"""存儲服務模組，提供數據持久化功能。"""

import os
from pathlib import Path
from .base import StorageService, StorageServiceFactory
from .file import FileStorageService

# 獲取數據存儲目錄
def get_data_dir() -> str:
    """獲取數據存儲目錄。
    
    Returns:
        數據存儲目錄路徑
    """
    # 默認使用項目根目錄下的 data 目錄
    base_dir = Path(__file__).parent.parent.parent.parent
    data_dir = base_dir / "data"
    
    # 如果環境變量中指定了數據目錄，則使用環境變量中的值
    if "DATA_DIR" in os.environ:
        data_dir = Path(os.environ["DATA_DIR"])
    
    # 確保目錄存在
    if not data_dir.exists():
        data_dir.mkdir(parents=True)
    
    return str(data_dir)

# 註冊文件存儲服務
file_storage = FileStorageService(get_data_dir())
StorageServiceFactory.register_service("file", file_storage, default=True)

# 導出工廠類和服務類
__all__ = ["StorageService", "StorageServiceFactory", "FileStorageService"]