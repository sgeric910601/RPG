"""OpenAI服務實現，提供與OpenAI API的交互功能。"""

import os
import tiktoken
import asyncio
from typing import Dict, List, Optional, Any, Union, AsyncGenerator

from openai import OpenAI
from ...utils.error import ServiceError
from .base import AIService

class OpenAIService(AIService):
    """OpenAI服務實現類，提供與OpenAI API的交互功能。"""
    
    def __init__(self, api_key: Optional[str] = None, organization: Optional[str] = None):
        """初始化OpenAI服務。
        
        Args:
            api_key: OpenAI API密鑰，如果為None則從環境變量獲取
            organization: OpenAI組織ID，如果為None則從環境變量獲取
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.organization = organization or os.environ.get("OPENAI_ORGANIZATION")
        
        if not self.api_key:
            raise ServiceError("openai", "Missing API key")
        
        self.client = OpenAI(
            api_key=self.api_key,
            organization=self.organization if self.organization else None
        )
        
        # 默認模型
        self.default_model = "gpt-4o-mini"
    
    def set_model(self, model_id: str) -> bool:
        """設置當前使用的模型。
        
        Args:
            model_id: 模型ID
            
        Returns:
            設置是否成功
        """
        supported_models = ["gpt-4o-mini"]
        if model_id in supported_models:
            self.default_model = model_id
            logger.info(f"[OpenAI] 設置當前模型: {model_id}")
            return True
        logger.warning(f"[OpenAI] 不支持的模型: {model_id}")
        return False
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本響應。
        
        Args:
            prompt: 提示詞
            **kwargs: 其他參數
            
        Returns:
            生成的文本
        """
        messages = [{"role": "user", "content": prompt}]
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.generate_chat_response(messages, **kwargs))
    
    async def generate_chat_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成聊天響應。
        
        Args:
            messages: 消息列表，每個消息包含 role 和 content
            **kwargs: 其他參數
            
        Returns:
            生成的聊天響應
        """
        model = kwargs.get("model", self.default_model)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", None)
        stream = kwargs.get("stream", False)
        
        if stream:
            async for chunk in self.generate_stream_response(messages, model, temperature, max_tokens):
                return chunk  # 只返回第一個片段
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ServiceError("openai", f"Failed to generate chat response: {str(e)}")
    
    async def generate_stream_response(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """生成流式回覆。
        
        Args:
            messages: 消息列表
            model: 模型名稱
            temperature: 溫度參數
            max_tokens: 最大生成的token數量
            **kwargs: 其他參數
            
        Yields:
            流式響應生成器
        """
        model = model or self.default_model
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            for chunk in stream:
                content = chunk.choices[0].delta.content if hasattr(chunk.choices[0].delta, 'content') else None
                if content is not None:
                    yield content
        except Exception as e:
            logger.error(f"[OpenAI] 生成流式響應時出錯: {str(e)}")
            raise ServiceError("openai", f"Failed to generate stream response: {str(e)}")
    
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
        async for chunk in self.generate_stream_response(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        ):
            yield chunk
    
    async def enhance_prompt(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """增強提示詞。
        
        Args:
            prompt: 原始提示詞
            **kwargs: 其他參數
            
        Returns:
            增強結果，包括增強後的提示詞和分析信息
        """
        # 構建系統提示詞
        system_prompt = """你是一個專業的提示詞工程師。你的任務是分析並改進用戶提供的提示詞。
請分析並改進提示詞的清晰度、上下文和具體性。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.generate_chat_response(messages, **kwargs)
            return {
                "original": prompt,
                "enhanced": response,
                "analysis": {
                    "suggestions": [response]
                }
            }
        except Exception as e:
            raise ServiceError("openai", f"Failed to enhance prompt: {str(e)}")
    
    async def analyze_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """分析文本。
        
        Args:
            text: 要分析的文本
            **kwargs: 其他參數
            
        Returns:
            分析結果
        """
        system_prompt = "你是一個專業的文本分析師。請分析提供的文本並提供見解。"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        
        try:
            response = await self.generate_chat_response(messages, **kwargs)
            return {
                "analysis": response,
                "suggestions": [response]
            }
        except Exception as e:
            raise ServiceError("openai", f"Failed to analyze text: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型信息。
        
        Returns:
            模型信息，包括名稱、描述、能力等
        """
        return {
            "name": "OpenAI",
            "description": "OpenAI API服務，提供GPT系列模型",
            "models": [
                {
                    "id": "gpt-4o-mini",
                    "name": "gpt-4o-mini",
                    "description": "OpenAI的模型",
                    "max_tokens": 8192,
                    "supports_images": False
                }
            ],
            "capabilities": [
                "text_generation",
                "chat"
            ]
        }
    
    def is_available(self) -> bool:
        """檢查服務是否可用。
        
        Returns:
            服務是否可用
        """
        return self.api_key is not None
    
    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """計算文本的token數量。
        
        Args:
            text: 要計算的文本
            model: 使用的模型名稱，不同模型使用不同的tokenizer
            
        Returns:
            token數量
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            except Exception as e:
                raise ServiceError("openai", f"Failed to count tokens: {str(e)}")