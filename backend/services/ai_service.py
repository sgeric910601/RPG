"""AI服務接口模組，定義與AI模型通信的統一介面。"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union

class AIService(ABC):
    """AI服務抽象基類，定義所有AI服務實現必須提供的方法。"""
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """生成AI回覆的抽象方法。
        
        Args:
            messages: 對話歷史，格式為[{"role": "user", "content": "用戶輸入"}, ...]
            model: 要使用的模型名稱
            temperature: 溫度參數，控制回覆的隨機性
            max_tokens: 最大生成的token數量
            stream: 是否使用流式輸出
            **kwargs: 其他模型特定參數
            
        Returns:
            完整的回覆文本，或者在stream=True時返回文本流生成器
        """
        pass
    
    @abstractmethod
    async def generate_with_image(
        self,
        text_prompt: str,
        image_data: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """使用多模態模型生成包含圖像理解的回覆。
        
        Args:
            text_prompt: 文本提示
            image_data: 圖像數據列表，每個元素包含圖像URL或base64數據
            model: 要使用的模型名稱
            temperature: 溫度參數
            max_tokens: 最大生成的token數量
            **kwargs: 其他模型特定參數
            
        Returns:
            模型生成的回覆文本
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        """計算文本的token數量。
        
        Args:
            text: 要計算的文本
            model: 使用的模型名稱，不同模型使用不同的tokenizer
            
        Returns:
            token數量
        """
        pass
