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
        import asyncio
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
            "temperature": temperature
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
        except httpx.HTTPError as e:
            raise ServiceError("openrouter", f"HTTP error: {str(e)}")
        except Exception as e:
            raise ServiceError("openrouter", f"Failed to generate chat response: {str(e)}")
    
    async def _stream_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """生成流式回覆。
        
        Args:
            messages: 消息列表
            model: 模型名稱
            temperature: 溫度參數
            max_tokens: 最大生成的token數量
            **kwargs: 其他參數
            
        Returns:
            流式響應生成器
        """
        # 檢查模型是否支持
        if model not in self.SUPPORTED_MODELS:
            model = self.default_model
        
        # 準備請求數據
        request_data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
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
            # 發送請求
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
        except httpx.HTTPError as e:
            raise ServiceError("openrouter", f"HTTP error: {str(e)}")
        except Exception as e:
            raise ServiceError("openrouter", f"Failed to generate stream response: {str(e)}")
    
    async def enhance_prompt(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """增強提示詞。
        
        Args:
            prompt: 原始提示詞
            **kwargs: 其他參數
            
        Returns:
            增強結果，包括增強後的提示詞和分析信息
        """
        # 構建系統提示詞
        system_prompt = """你是一個專業的提示詞工程師。你的任務是分析並改進用戶提供的提示詞，使其更加清晰、具體和有效。
請從以下幾個方面分析提示詞：
1. 清晰度：提示詞是否表達清晰
2. 上下文：提示詞是否提供了足夠的上下文信息
3. 具體性：提示詞是否足夠具體
4. 結構：提示詞的結構是否合理

然後，請提供一個改進後的版本，並解釋你做出的改變。

請按照以下JSON格式返回結果：
{
  "analysis": {
    "clarity_score": 0.8,  // 0-1之間的分數
    "context_score": 0.7,  // 0-1之間的分數
    "specificity_score": 0.6,  // 0-1之間的分數
    "structure_score": 0.9,  // 0-1之間的分數
    "overall_score": 0.75  // 以上四項的平均分
  },
  "enhanced_prompt": "改進後的提示詞",
  "suggestions": [
    "改進建議1",
    "改進建議2"
  ]
}"""
        
        # 構建消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # 調用API
        try:
            model = kwargs.get("model", "anthropic/claude-3-haiku:free")  # 使用較輕量的模型
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1000)
            
            response = await self.generate_chat_response(messages, model=model, temperature=temperature, max_tokens=max_tokens)
            
            # 嘗試解析JSON
            import json
            try:
                # 尋找JSON部分
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
                
                result_json = json.loads(response)
                return result_json
            except json.JSONDecodeError:
                # 如果解析失敗，返回原始響應
                return {
                    "enhanced_prompt": response,
                    "analysis": {
                        "clarity_score": 0.5,
                        "context_score": 0.5,
                        "specificity_score": 0.5,
                        "structure_score": 0.5,
                        "overall_score": 0.5
                    },
                    "suggestions": ["無法解析JSON響應"]
                }
        except Exception as e:
            raise ServiceError("openrouter", f"Failed to enhance prompt: {str(e)}")
    
    async def analyze_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """分析文本。
        
        Args:
            text: 要分析的文本
            **kwargs: 其他參數
            
        Returns:
            分析結果
        """
        # 構建系統提示詞
        system_prompt = """你是一個專業的文本分析師。你的任務是分析用戶提供的文本，並提供詳細的分析結果。
請從以下幾個方面分析文本：
1. 主題：文本的主要主題是什麼
2. 情感：文本的情感傾向是什麼
3. 關鍵詞：文本中的關鍵詞有哪些
4. 結構：文本的結構是怎樣的
5. 建議：如何改進這段文本

請按照以下JSON格式返回結果：
{
  "topic": "文本的主題",
  "sentiment": {
    "score": 0.8,  // -1到1之間的分數，負數表示負面情感，正數表示正面情感
    "label": "正面/負面/中性"
  },
  "keywords": ["關鍵詞1", "關鍵詞2", "關鍵詞3"],
  "structure": "文本結構分析",
  "suggestions": [
    "改進建議1",
    "改進建議2"
  ]
}"""
        
        # 構建消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        
        # 調用API
        try:
            model = kwargs.get("model", "anthropic/claude-3-haiku:free")  # 使用較輕量的模型
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1000)
            
            response = await self.generate_chat_response(messages, model=model, temperature=temperature, max_tokens=max_tokens)
            
            # 嘗試解析JSON
            import json
            try:
                # 尋找JSON部分
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
                
                result_json = json.loads(response)
                return result_json
            except json.JSONDecodeError:
                # 如果解析失敗，返回原始響應
                return {
                    "topic": "無法解析",
                    "sentiment": {
                        "score": 0,
                        "label": "中性"
                    },
                    "keywords": [],
                    "structure": "無法解析",
                    "suggestions": ["無法解析JSON響應"]
                }
        except Exception as e:
            raise ServiceError("openrouter", f"Failed to analyze text: {str(e)}")
    
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
                },
                {
                    "id": "anthropic/claude-3-haiku:free",
                    "name": "Claude 3 Haiku",
                    "description": "Anthropic的高效模型",
                    "max_tokens": 4096,
                    "supports_images": False
                },
                {
                    "id": "google/gemini-pro:free",
                    "name": "Gemini Pro",
                    "description": "Google的Gemini Pro模型",
                    "max_tokens": 4096,
                    "supports_images": False
                },
                {
                    "id": "meta-llama/llama-3-70b-instruct:free",
                    "name": "Llama 3 70B Instruct",
                    "description": "Meta的Llama 3 70B指令模型",
                    "max_tokens": 4096,
                    "supports_images": False
                },
                {
                    "id": "meta-llama/llama-3-8b-instruct:free",
                    "name": "Llama 3 8B Instruct",
                    "description": "Meta的Llama 3 8B指令模型",
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
    
    # 兼容現有的OpenRouterService接口
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
            生成的回覆
        """
        kwargs["model"] = model
        kwargs["temperature"] = temperature
        kwargs["max_tokens"] = max_tokens or 500
        
        if stream:
            return self._stream_response(messages, model, temperature, max_tokens or 500, **kwargs)
        else:
            return await self.generate_chat_response(messages, **kwargs)
    
    async def generate_with_image(
        self,
        text_prompt: str,
        image_data: List[Dict[str, Any]],
        model: str = "anthropic/claude-3-opus:free",
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
            **kwargs: 其他參數
            
        Returns:
            模型生成的回覆文本
        """
        # OpenRouter目前不支持多模態輸入
        raise ServiceError("openrouter", "OpenRouter does not support image input yet")