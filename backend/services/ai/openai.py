"""OpenAI服務實現，提供與OpenAI API的交互功能。"""

import os
import tiktoken
import asyncio
from typing import Dict, List, Optional, Any, Union, AsyncGenerator

from openai import AsyncOpenAI
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
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            organization=self.organization if self.organization else None
        )
        
        # 默認模型
        self.default_model = "gpt-4"
    
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
        max_tokens = kwargs.get("max_tokens", None)
        stream = kwargs.get("stream", False)
        
        # 如果stream為True，則返回流式響應
        if stream:
            return self._stream_response(messages, model, temperature, max_tokens, **kwargs)
        
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
    
    async def _stream_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
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
            
        Returns:
            流式響應生成器
        """
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content is not None:
                    yield content
        except Exception as e:
            raise ServiceError("openai", f"Failed to generate stream response: {str(e)}")
    
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
            response = await self.client.chat.completions.create(
                model=kwargs.get("model", "gpt-4"),
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", None),
                response_format={"type": "json_object"}
            )
            
            # 解析響應
            result = response.choices[0].message.content
            
            # 嘗試解析JSON
            import json
            try:
                result_json = json.loads(result)
                return result_json
            except json.JSONDecodeError:
                # 如果解析失敗，返回原始響應
                return {
                    "enhanced_prompt": result,
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
            raise ServiceError("openai", f"Failed to enhance prompt: {str(e)}")
    
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
            response = await self.client.chat.completions.create(
                model=kwargs.get("model", "gpt-4"),
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", None),
                response_format={"type": "json_object"}
            )
            
            # 解析響應
            result = response.choices[0].message.content
            
            # 嘗試解析JSON
            import json
            try:
                result_json = json.loads(result)
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
                    "id": "gpt-4",
                    "name": "GPT-4",
                    "description": "OpenAI最強大的模型",
                    "max_tokens": 8192,
                    "supports_images": False
                },
                {
                    "id": "gpt-4-vision-preview",
                    "name": "GPT-4 Vision",
                    "description": "支持圖像理解的GPT-4模型",
                    "max_tokens": 4096,
                    "supports_images": True
                },
                {
                    "id": "gpt-3.5-turbo",
                    "name": "GPT-3.5 Turbo",
                    "description": "OpenAI的高效模型",
                    "max_tokens": 4096,
                    "supports_images": False
                }
            ],
            "capabilities": [
                "text_generation",
                "chat",
                "image_understanding",
                "code_generation"
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
        except Exception as e:
            # 如果模型不支持，使用cl100k_base作為後備
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            except Exception as e:
                raise ServiceError("openai", f"Failed to count tokens: {str(e)}")
    
    # 兼容現有的AIService接口
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
        kwargs["max_tokens"] = max_tokens
        kwargs["stream"] = stream
        
        return await self.generate_chat_response(messages, **kwargs)
    
    async def generate_with_image(
        self,
        text_prompt: str,
        image_data: List[Dict[str, Any]],
        model: str = "gpt-4-vision-preview",
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
        # 構建包含圖像的消息
        messages = [{"role": "user", "content": []}]
        
        # 添加文本部分
        messages[0]["content"].append({
            "type": "text",
            "text": text_prompt
        })
        
        # 添加圖像部分
        for img in image_data:
            if "url" in img:
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": img["url"]}
                })
            elif "base64" in img:
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img['base64']}"
                    }
                })
        
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
            raise ServiceError("openai", f"Failed to generate response with image: {str(e)}")