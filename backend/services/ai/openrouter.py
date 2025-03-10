"""OpenRouter服務實現，提供與OpenRouter API的交互功能。"""

import os
import httpx
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union, AsyncGenerator

from ...utils.error import ServiceError
from .base import AIService, ModelManager

# 設置日誌
logger = logging.getLogger(__name__)

class OpenRouterService(AIService):
    """OpenRouter服務實現類，提供與OpenRouter API的交互功能。"""
    
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
        
        # 從配置文件加載模型信息
        self.model_manager = ModelManager()
        self.models = self._load_models()
        self.supported_models = self._get_supported_models()
        
        # 設置默認模型
        self.default_model = self._get_default_model()
        
        logger.info(f"[OpenRouter] 初始化完成, API Key: {self.api_key[:8]}...")
    
    def _load_models(self) -> Dict[str, Dict[str, Any]]:
        """從配置文件加載OpenRouter模型信息。"""
        all_models = self.model_manager.get_all_models()
        return {
            model_id: model_info
            for model_id, model_info in all_models.items()
            if model_info.get('api_type') == 'openrouter' and model_info.get('enabled', True)
        }
    
    def _get_supported_models(self) -> List[str]:
        """獲取支持的模型列表。"""
        if not self.models:
            # 如果沒有配置模型，使用默認值
            return [
                "deepseek/deepseek-chat:free",
                "anthropic/claude-3-opus:free",
                "anthropic/claude-3-sonnet:free",
                "anthropic/claude-3-haiku:free",
                "google/gemini-pro:free"
            ]
        
        # 從配置中提取模型ID
        model_ids = []
        for model_id in self.models.keys():
            # 從完整ID (如 "openrouter/deepseek-chat") 中提取模型名稱部分
            if '/' in model_id:
                provider, model_name = model_id.split('/', 1)
                model_ids.append(f"{model_name}:free")
            else:
                model_ids.append(f"{model_id}:free")
        
        return model_ids
    
    def _get_default_model(self) -> str:
        """獲取默認模型ID。"""
        if not self.models:
            return "deepseek/deepseek-chat:free"  # 如果沒有配置模型，使用默認值
        
        # 返回第一個可用模型的ID
        model_id = next(iter(self.models.keys()))
        # 從完整ID (如 "openrouter/deepseek-chat") 中提取模型名稱部分
        if '/' in model_id:
            provider, model_name = model_id.split('/', 1)
            return f"{model_name}:free"
        return f"{model_id}:free"
    
    def set_model(self, model_id: str) -> bool:
        """設置當前使用的模型。
        
        Args:
            model_id: 模型ID
        Returns:
            設置是否成功
        """
        # 檢查完整模型ID (包含:free後綴)
        if model_id in self.supported_models:
            self.default_model = model_id
            logger.info(f"[OpenRouter] 設置當前模型: {model_id}")
            return True
        
        # 檢查是否是短名稱 (不包含:free後綴)
        for full_id in self.supported_models:
            if full_id.startswith(model_id):
                self.default_model = full_id
                logger.info(f"[OpenRouter] 設置當前模型: {full_id}")
                return True
        
        # 檢查是否是配置中的ID
        for config_id in self.models.keys():
            # 從完整ID (如 "openrouter/deepseek-chat") 中提取模型名稱部分
            if '/' in config_id:
                provider, model_name = config_id.split('/', 1)
                if model_id == config_id or model_id == model_name:
                    self.default_model = f"{model_name}:free"
                    logger.info(f"[OpenRouter] 設置當前模型: {self.default_model}")
                    return True
        
        logger.warning(f"[OpenRouter] 不支持的模型: {model_id}")
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
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.generate_chat_response(messages, **kwargs))
        return response
    
    async def generate_chat_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """異步生成聊天響應。
        
        Args:
            messages: 消息列表，每個消息包含 role 和 content
            **kwargs: 其他參數
            
        Returns:
            生成的聊天響應
        """
        model = kwargs.get("model", self.default_model)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 500)
        
        if model not in self.supported_models:
            logger.warning(f"[OpenRouter] 不支援的模型 {model}, 使用默認模型 {self.default_model}")
            model = self.default_model
        
        request_data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.referer,
            "X-Title": "RPG-Dialogue",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"[OpenRouter] 發送請求: {model}, stream=False")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=request_data,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    error_text = self._parse_error_response(response)
                    raise ServiceError("openrouter", f"API error: {error_text}")
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                logger.info(f"[OpenRouter] 收到回應: {content[:50]}...")
                
                return content.strip()
        except Exception as e:
            logger.error(f"[OpenRouter] 生成回應出錯: {str(e)}")
            raise ServiceError("openrouter", f"Failed to generate chat response: {str(e)}")
    
    async def generate_stream_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str = None, 
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
        model = model or self.default_model
        if model not in self.supported_models:
            logger.warning(f"[OpenRouter] 不支援的模型 {model}, 使用默認模型 {self.default_model}")
            model = self.default_model
            
        request_data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens or 500,
            "temperature": temperature,
            "stream": True
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.referer,
            "X-Title": "RPG-Dialogue",
            "Content-Type": "application/json"
        }
        
        # 設置重試參數
        max_retries = 3
        retry_delay = 1  # 初始延遲1秒
        request_timeout = kwargs.get("timeout", 60.0)  # 默認超時60秒
        
        # 移除可能導致問題的參數
        if "timeout" in kwargs:
            del kwargs["timeout"]
        
        # 重試邏輯
        for attempt in range(max_retries):
            try:
                logger.info(f"[OpenRouter] 嘗試生成流式響應 (嘗試 {attempt+1}/{max_retries}), 模型: {model}")
                
                async with httpx.AsyncClient() as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=request_data,
                        timeout=request_timeout
                    ) as response:
                        if response.status_code != 200:
                            error_text = await response.text()
                            raise ServiceError("openrouter", f"API error: {error_text}")
                        
                        logger.info("[OpenRouter] 開始接收流式回應...")
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                line = line[6:]
                                
                                if not line or line == "[DONE]":
                                    continue
                                    
                                try:
                                    chunk = json.loads(line)
                                    content = chunk["choices"][0]["delta"].get("content")
                                    if content:
                                        logger.debug(f"[OpenRouter] 收到片段: {content}")
                                        yield content
                                except json.JSONDecodeError:
                                    logger.warning(f"[OpenRouter] JSON解析錯誤: {line}")
                                    continue
                        
                        logger.info("[OpenRouter] 流式回應完成")
                
                # 如果成功完成，跳出重試循環
                break
                
            except Exception as e:
                # 記錄錯誤
                error_type = type(e).__name__
                error_msg = str(e)
                logger.error(f"[OpenRouter] 生成流式回應出錯 ({error_type}): {error_msg}")
                
                # 如果是最後一次嘗試，拋出異常
                if attempt == max_retries - 1:
                    # 如果是連接錯誤，提供更具體的錯誤信息
                    if "Connection" in error_msg or "timeout" in error_msg.lower():
                        raise ServiceError("openrouter", f"Connection error: Failed to connect to OpenRouter API after {max_retries} attempts. Please check your network connection and API status.")
                    else:
                        raise ServiceError("openrouter", f"Failed to generate stream response: {error_msg}")
                
                # 否則等待後重試
                wait_time = retry_delay * (2 ** attempt)  # 指數退避策略
                logger.info(f"[OpenRouter] 等待 {wait_time} 秒後重試...")
                await asyncio.sleep(wait_time)
                
                # 如果是超時錯誤，增加超時時間
                if "timeout" in error_msg.lower():
                    request_timeout *= 1.5  # 增加50%的超時時間
                    logger.info(f"[OpenRouter] 增加超時時間至 {request_timeout} 秒")
    
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
        logger.info(f"[OpenRouter] 開始生成回應: model={model}, stream={stream}")
        
        async for chunk in self.generate_stream_response(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        ):
            yield chunk
    
    def enhance_prompt(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """增強提示詞。
        
        Args:
            prompt: 原始提示詞
            **kwargs: 其他參數
            
        Returns:
            增強結果，包括增強後的提示詞和分析信息
        """
        # OpenRouter不提供提示詞增強功能，返回原始提示詞
        return {
            "original": prompt,
            "enhanced": prompt,
            "analysis": {
                "complexity": "unknown",
                "context": "unknown",
                "suggestions": []
            }
        }
    
    def analyze_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """分析文本。
        
        Args:
            text: 要分析的文本
            **kwargs: 其他參數
            
        Returns:
            分析結果
        """
        # OpenRouter不提供文本分析功能，返回基本信息
        word_count = len(text.split())
        char_count = len(text)
        return {
            "statistics": {
                "word_count": word_count,
                "character_count": char_count,
                "estimated_tokens": self.count_tokens(text)
            }
        }
    
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
                "max_tokens": model_info.get('max_tokens', 4096),
                "supports_images": model_info.get('supports_images', False)
            })
        
        # 如果沒有配置模型，使用默認值
        if not models_list:
            models_list = [
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
                }
            ]
        
        return {
            "name": "OpenRouter",
            "description": "OpenRouter API服務，提供多種AI模型的統一接口",
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
    
    def count_tokens(self, text: str, model: str = "deepseek/deepseek-chat:free") -> int:
        """計算文本的token數量。
        
        Args:
            text: 要計算的文本
            model: 使用的模型名稱，不同模型使用不同的tokenizer
            
        Returns:
            token數量
        """
        # OpenRouter沒有提供token計算API，使用粗略估算
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