"""OpenAI服務實現，提供與OpenAI API的交互功能。"""

import os
import tiktoken
import asyncio
import time
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
import logging

logger = logging.getLogger(__name__)

from openai import OpenAI
from ...utils.error import ServiceError
from .base import AIService, ModelManager

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
        
        # 從配置文件加載模型信息
        self.model_manager = ModelManager()
        self.models = self._load_models()
        
        # 設置默認模型
        self.default_model = self._get_default_model()
        logger.info(f"[OpenAI] 初始化完成，使用默認模型: {self.default_model}")
    
    def _load_models(self) -> Dict[str, Dict[str, Any]]:
        """從配置文件加載OpenAI模型信息。"""
        all_models = self.model_manager.get_all_models()
        return {
            model_id: model_info
            for model_id, model_info in all_models.items()
            if model_info.get('api_type') == 'openai' and model_info.get('enabled', True)
        }
    
    def _get_default_model(self) -> str:
        """獲取默認模型ID。"""
        if not self.models:
            return "gpt-4o-mini"  # 如果沒有配置模型，使用默認值
        
        # 返回第一個可用模型的ID
        model_id = next(iter(self.models.keys()))
        # 從完整ID (如 "openai/gpt-4o-mini") 中提取模型名稱部分
        if '/' in model_id:
            return model_id.split('/')[-1]
        return model_id
    
    def set_model(self, model_id: str) -> bool:
        """設置當前使用的模型。
        
        Args:
            model_id: 模型ID
            
        Returns:
            設置是否成功
        """
        # 檢查模型ID是否在配置中
        if model_id in self.models:
            # 直接使用配置中的ID
            self.default_model = model_id.split('/')[-1] if '/' in model_id else model_id
            logger.info(f"[OpenAI] 設置當前模型: {model_id}")
            return True
        
        # 檢查是否是短名稱 (不包含提供商前綴)
        for full_id in self.models.keys():
            if full_id.endswith('/' + model_id) or full_id == model_id:
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
        # 設置重試參數
        max_retries = 3
        retry_delay = 1  # 初始延遲1秒
        timeout = kwargs.get("timeout", 60.0)  # 默認超時60秒
        
        # 移除可能導致問題的參數
        if "timeout" in kwargs:
            del kwargs["timeout"]
        
        last_error = None
        base_timeout = timeout

        # 重試邏輯
        for attempt in range(max_retries):
            try:
                logger.info(f"[OpenAI] 嘗試生成流式響應 (嘗試 {attempt+1}/{max_retries})")
                
                # 使用動態timeout參數創建流
                stream = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    timeout=timeout,
                    **kwargs
                )
                
                # 處理流式響應
                async for chunk in stream:
                    if chunk and chunk.choices:
                        content = chunk.choices[0].delta.content if hasattr(chunk.choices[0].delta, 'content') else None
                        if content is not None:
                            yield content
                
                # 如果成功完成，跳出重試循環
                logger.info("[OpenAI] 流式響應生成成功")
                return
                
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e)
                logger.error(f"[OpenAI] 生成流式響應時出錯 ({error_type}): {error_msg}")
                
                # 如果不是最後一次嘗試，進行重試
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # 指數退避策略
                    logger.info(f"[OpenAI] 等待 {wait_time} 秒後重試...")
                    await asyncio.sleep(wait_time)
                    
                    # 根據錯誤類型調整重試策略
                    if "timeout" in error_msg.lower():
                        timeout = base_timeout * (1.5 ** (attempt + 1))  # 每次重試增加50%超時時間
                        logger.info(f"[OpenAI] 增加超時時間至 {timeout} 秒")
                    elif "rate" in error_msg.lower():  # 處理速率限制
                        wait_time *= 2  # 速率限制情況下等待更長時間
                        logger.info(f"[OpenAI] 遇到速率限制，增加等待時間至 {wait_time} 秒")
                    elif "Connection" in error_msg:
                        # 連接錯誤時檢查網絡
                        logger.warning("[OpenAI] 檢測到連接問題，請確認網絡連接正常")
                        
        # 所有重試都失敗後，拋出最後一個錯誤
        error_msg = str(last_error)
        if "Connection" in error_msg:
            raise ServiceError(
                "openai",
                f"Connection error: Failed to connect to OpenAI API after {max_retries} attempts. "
                "Please check:\n"
                "1. Your network connection\n"
                "2. OpenAI API status\n"
                "3. Any VPN or proxy settings"
            )
        elif "timeout" in error_msg.lower():
            raise ServiceError(
                "openai", 
                f"Request timeout after {max_retries} attempts with maximum timeout of {timeout} seconds. "
                "The API is currently experiencing high latency."
            )
        else:
            raise ServiceError("openai", f"Failed to generate stream response after {max_retries} attempts: {error_msg}")
    
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
        # 從配置文件獲取模型信息
        models_list = []
        for model_id, model_info in self.models.items():
            models_list.append({
                "id": model_id,
                "name": model_info.get('name', model_id),
                "description": model_info.get('description', ''),
                "max_tokens": model_info.get('max_tokens', 8192),
                "supports_images": model_info.get('supports_images', False)
            })
        
        # 如果沒有配置模型，使用默認值
        if not models_list:
            models_list = [{
                "id": "gpt-4o-mini",
                "name": "gpt-4o-mini",
                "description": "OpenAI的模型",
                "max_tokens": 8192,
                "supports_images": False
            }]
        
        return {
            "name": "OpenAI",
            "description": "OpenAI API服務，提供GPT系列模型",
            "models": models_list,
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
