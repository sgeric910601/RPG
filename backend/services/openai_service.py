"""OpenAI API服務實現。"""

import os
import tiktoken
import asyncio
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from openai import AsyncOpenAI
from .ai_service import AIService

class OpenAIService(AIService):
    """OpenAI API服務實現類。"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化OpenAI客戶端。
        
        Args:
            api_key: OpenAI API密鑰，如果為None則從環境變量獲取
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """調用OpenAI API生成回覆。"""
        try:
            if stream:
                return self._stream_response(messages, model, temperature, max_tokens, **kwargs)
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API調用失敗: {str(e)}")
    
    async def _stream_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """生成流式回覆。"""
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
            raise Exception(f"OpenAI流式API調用失敗: {str(e)}")
    
    async def generate_with_image(
        self,
        text_prompt: str,
        image_data: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """使用多模態模型生成包含圖像理解的回覆。"""
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
            raise Exception(f"OpenAI多模態API調用失敗: {str(e)}")
    
    def count_tokens(self, text: str, model: str) -> int:
        """計算輸入文本的token數量。"""
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception as e:
            # 如果模型不支持，使用cl100k_base作為後備
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
