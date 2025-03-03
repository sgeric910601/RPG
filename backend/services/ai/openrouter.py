"""OpenRouter服務實現，提供與OpenRouter API的交互功能。"""

import os
import httpx
import asyncio
import json
from typing import Dict, List, Optional, Any, Union, AsyncGenerator

from ...utils.error import ServiceError
from .base import AIService

class OpenRouterService(AIService):
    """OpenRouter服務實現類，提供與OpenRouter API的交互功能。"""
    
    # 支持的模型列表
    SUPPORTED_MODELS = [
        "deepseek/deepseek-chat:free",
        "anthropic/claude-3-opus:free",
        "anthropic/claude-3-sonnet:free",
        "anthropic/claude-3-haiku:free",
        "google/gemini-pro:free",
        "meta-llama/llama-3-70b-instruct:free",
        "meta-llama/llama-3-8b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "mistralai/mixtral-8x7b-instruct:free"
    ]
    
    def __init__(self, api_key: Optional[str] = None, referer: str = "http://localhost:5000"):
        """初始化OpenRouter服務。
        
        Args:
            api_key: OpenRouter API密鑰，如果為None則從環境變量獲取
            referer: HTTP Referer頭，用於API請求
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        
        if not self.api_key:
            raise ServiceError("openrouter", "Missing API key")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.referer = referer
        
        # 默認模型
        self.default_model = "deepseek/deepseek-chat:free"
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本響應。
        
        Args:
            prompt: 提示詞
            **kwargs: 其他參數
            
        Returns:
            生成的文本
        """
        # 將提示詞轉換為消息格式
        messages = [{"role": "user", "content": prompt}]
        
        # 使用同步方式調用異步方法
        return asyncio.run(self.generate_chat_response(messages, **kwargs))
    
    async def generate_chat_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成聊天響應。
        
        Args:
            messages: 消息列表，每個消息包含 role 和 content
            **kwargs: 其他參數
            
        Returns:
            生成的聊天響應
        """
        # 從kwargs中提取參數，如果沒有則使用默認值
        model = kwargs.get("model", self.default_model)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 500)
        
        # 檢查模型是否支持
        if model not in self.SUPPORTED_MODELS:
            print(f"[OpenRouter] 不支援的模型 {model}, 使用默認模型 {self.default_model}")
            model = self.default_model
        
        # 準備請求數據
        request_data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        # 設置headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.referer,
            "X-Title": "RPG-Dialogue",
            "Content-Type": "application/json"
        }
        
        try:
            # 發送請求
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=request_data,
                    timeout=30.0
                )
                
                # 檢查響應
                if response.status_code != 200:
                    error_text = self._parse_error_response(response)
                    raise ServiceError("openrouter", f"API error: {error_text}")
                    
                # 解析回應
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                return content.strip()
        except Exception as e:
            raise ServiceError("openrouter", f"Failed to generate chat response: {str(e)}")
    
    async def generate_stream_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """生成流式AI回覆。
        
        Args:
            messages: 對話歷史
            model: 要使用的模型名稱
            temperature: 溫度參數
            max_tokens: 最大生成的token數量
            **kwargs: 其他參數
            
        Yields:
            生成的文本片段
        """
        # 檢查模型是否支持
        if model not in self.SUPPORTED_MODELS:
            model = self.default_model
            
        # 準備請求數據
        request_data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens or 500,
            "temperature": temperature,
            "stream": True
        }
        
        # 設置headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.referer,
            "X-Title": "RPG-Dialogue",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=request_data,
                    timeout=60.0
                ) as response:
                    # 檢查響應
                    if response.status_code != 200:
                        error_text = await response.text()
                        raise ServiceError("openrouter", f"API error: {error_text}")
                    
                    # 處理流式響應
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            line = line[6:]  # 移除 "data: " 前綴
                            
                            # 跳過空行或[DONE]
                            if not line or line == "[DONE]":
                                continue
                                
                            try:
                                chunk = json.loads(line)
                                if chunk["choices"] and chunk["choices"][0]["delta"].get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            raise ServiceError("openrouter", f"Failed to generate stream response: {str(e)}")
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """生成AI回覆。
        
        Args:
            messages: 對話歷史
            model: 要使用的模型名稱
            temperature: 溫度參數
            max_tokens: 最大生成的token數量
            stream: 是否使用流式輸出
            **kwargs: 其他參數
            
        Returns:
            生成的回覆或生成器
        """
        if stream:
            # 使用流式響應
            return self.generate_stream_response(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        else:
            # 使用非流式響應
            return await self.generate_chat_response(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型信息。
        
        Returns:
            模型信息，包括名稱、描述、能力等
        """
        return {
            "name": "OpenRouter",
            "description": "OpenRouter API服務，提供多種AI模型的統一接口",
            "models": [
                {
                    "id": "deepseek/deepseek-chat:free",
                    "name": "DeepSeek Chat",
                    "description": "DeepSeek的對話模型",
                    "max_tokens": 4096,
                    "supports_images": False
                },
                {
                    "id": "anthropic/claude-3-opus:free",
                    "name": "Claude 3 Opus",
                    "description": "Anthropic的最強大模型",
                    "max_tokens": 4096,
                    "supports_images": False
                },
                {
                    "id": "anthropic/claude-3-sonnet:free",
                    "name": "Claude 3 Sonnet",
                    "description": "Anthropic的平衡模型",
                    "max_tokens": 4096,
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
    
    def count_tokens(self, text: str, model: str = "deepseek/deepseek-chat:free") -> int:
        """計算文本的token數量。
        
        Args:
            text: 要計算的文本
            model: 使用的模型名稱，不同模型使用不同的tokenizer
            
        Returns:
            token數量
        """
        # OpenRouter沒有提供token計算API，使用粗略估算
        # 不同模型的tokenizer不同，這裡使用一個粗略的估算
        # 大約4個字符算1個token
        return len(text) // 4
    
    def _parse_error_response(self, response) -> str:
        """解析錯誤回應。
        
        Args:
            response: HTTP響應
            
        Returns:
            錯誤消息
        """
        try:
            error_json = response.json()
            if isinstance(error_json, dict):
                error = error_json.get('error', {})
                if isinstance(error, dict):
                    return error.get('message', response.text)
            return response.text
        except:
            return response.text