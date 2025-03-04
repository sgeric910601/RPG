"""Claude服務實現，提供與Anthropic Claude API的交互功能。"""

import os
import base64
import anthropic
import logging
from typing import Dict, List, Optional, Any, Union, AsyncGenerator

from ...utils.error import ServiceError
from .base import AIService

# 設置日誌
logger = logging.getLogger(__name__)

class ClaudeService(AIService):
    """Claude服務實現類，提供與Anthropic Claude API的交互功能。"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化Claude服務。
        
        Args:
            api_key: Anthropic API密鑰，如果為None則從環境變量獲取
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ServiceError("claude", "Missing API key")
        
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        # 默認模型
        self.default_model = "claude-3-opus-20240229"
        logger.info(f"[Claude] 初始化完成，使用默認模型: {self.default_model}")
    
    def set_model(self, model_id: str) -> bool:
        """設置當前使用的模型。
        
        Args:
            model_id: 模型ID
        Returns:
            設置是否成功
        """
        supported_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
        if model_id in supported_models:
            self.default_model = model_id
            logger.info(f"[Claude] 設置當前模型: {model_id}")
            return True
        logger.warning(f"[Claude] 不支持的模型: {model_id}")
        return False
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """同步生成文本響應。
        
        Args:
            prompt: 提示詞
            **kwargs: 其他參數
            
        Returns:
            生成的文本
        """
        messages = [{"role": "user", "content": prompt}]
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.generate_chat_response(messages, **kwargs))
    
    async def generate_chat_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """異步生成聊天響應。
        
        Args:
            messages: 消息列表，每個消息包含 role 和 content
            **kwargs: 其他參數
            
        Returns:
            生成的聊天響應
        """
        try:
            model = kwargs.get("model", self.default_model)
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 2048)
            
            response = await self.client.messages.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"[Claude] 生成回應出錯: {str(e)}")
            raise ServiceError("claude", f"Failed to generate chat response: {str(e)}")
    
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
            messages: 對話歷史
            model: 要使用的模型名稱
            temperature: 溫度參數
            max_tokens: 最大生成的token數量
            **kwargs: 其他參數
            
        Yields:
            生成的文本片段
        """
        try:
            model = model or self.default_model
            logger.info(f"[Claude] 開始生成流式回應，使用模型: {model}")
            
            with await self.client.messages.stream(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or 2048,
                **kwargs
            ) as stream:
                async for chunk in stream:
                    if chunk.type == "content_block_delta":
                        logger.debug(f"[Claude] 收到片段: {chunk.delta.text[:50]}...")
                        yield chunk.delta.text
                
                logger.info("[Claude] 流式回應完成")
                
        except Exception as e:
            logger.error(f"[Claude] 生成流式回應出錯: {str(e)}")
            raise ServiceError("claude", f"Failed to generate stream response: {str(e)}")
    
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
        logger.info(f"[Claude] 開始生成回應: model={model}, stream={stream}")
        
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
        messages = [
            {"role": "user", "content": f"Please analyze and improve this prompt: {prompt}"}
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
            logger.error(f"[Claude] 增強提示詞出錯: {str(e)}")
            raise ServiceError("claude", f"Failed to enhance prompt: {str(e)}")
    
    async def analyze_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """分析文本。
        
        Args:
            text: 要分析的文本
            **kwargs: 其他參數
            
        Returns:
            分析結果
        """
        messages = [
            {"role": "user", "content": f"Please analyze this text: {text}"}
        ]
        
        try:
            response = await self.generate_chat_response(messages, **kwargs)
            return {
                "analysis": response,
                "suggestions": [response]
            }
        except Exception as e:
            logger.error(f"[Claude] 分析文本出錯: {str(e)}")
            raise ServiceError("claude", f"Failed to analyze text: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型信息。
        
        Returns:
            模型信息，包括名稱、描述、能力等
        """
        return {
            "name": "Claude",
            "description": "Anthropic Claude API服務，提供Claude系列模型",
            "models": [
                {
                    "id": "claude-3-opus-20240229",
                    "name": "Claude 3 Opus",
                    "description": "Anthropic最強大的模型",
                    "max_tokens": 4096,
                    "supports_images": True
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
    
    def count_tokens(self, text: str, model: str = "claude-3-opus-20240229") -> int:
        """計算文本的token數量。
        
        Args:
            text: 要計算的文本
            model: 使用的模型名稱，不同模型使用不同的tokenizer
            
        Returns:
            token數量
        """
        try:
            # 使用Anthropic的token計算器
            return anthropic.Anthropic().count_tokens(text)
        except Exception as e:
            # 粗略估算，作為後備方案
            logger.warning(f"[Claude] 使用後備token計算方法: {str(e)}")
            return len(text) // 4  # Claude大約每4個字符算1個token