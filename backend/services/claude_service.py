"""Anthropic Claude API服務實現。"""

import os
import base64
import anthropic
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from .ai_service import AIService

class ClaudeService(AIService):
    """Anthropic Claude API服務實現類。"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化Claude客戶端。
        
        Args:
            api_key: Anthropic API密鑰，如果為None則從環境變量獲取
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """調用Claude API生成回覆。"""
        try:
            if stream:
                return self._stream_response(messages, model, temperature, max_tokens, **kwargs)
            
            # 將通用消息格式轉換為Claude格式
            claude_messages = []
            for msg in messages:
                claude_messages.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })
            
            max_tokens_to_sample = max_tokens or 2048
            
            response = await self.client.messages.create(
                model=model,
                messages=claude_messages,
                temperature=temperature,
                max_tokens=max_tokens_to_sample,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Claude API調用失敗: {str(e)}")
    
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
            # 將通用消息格式轉換為Claude格式
            claude_messages = []
            for msg in messages:
                claude_messages.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })
            
            max_tokens_to_sample = max_tokens or 2048
            
            with await self.client.messages.stream(
                model=model,
                messages=claude_messages,
                temperature=temperature,
                max_tokens=max_tokens_to_sample,
                **kwargs
            ) as stream:
                async for chunk in stream:
                    if chunk.type == "content_block_delta":
                        yield chunk.delta.text
        except Exception as e:
            raise Exception(f"Claude流式API調用失敗: {str(e)}")
    
    async def generate_with_image(
        self,
        text_prompt: str,
        image_data: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """使用Claude多模態模型生成包含圖像理解的回覆。"""
        try:
            messages = [{"role": "user", "content": []}]
            
            # 添加文本部分
            messages[0]["content"].append({
                "type": "text",
                "text": text_prompt
            })
            
            # 添加圖像部分
            for img in image_data:
                if "url" in img:
                    # Claude目前不支持直接使用URL，需要下載並轉換為base64
                    raise NotImplementedError("Claude暫不支持直接使用圖像URL，請提供base64格式")
                elif "base64" in img:
                    # 注意：這裡的具體實現可能需要根據Claude的API要求調整
                    messages[0]["content"].append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img["base64"]
                        }
                    })
            
            max_tokens_to_sample = max_tokens or 2048
            
            response = await self.client.messages.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens_to_sample,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Claude多模態API調用失敗: {str(e)}")
    
    def count_tokens(self, text: str, model: str) -> int:
        """計算輸入文本的token數量。"""
        try:
            # 使用Anthropic的token計算器
            return anthropic.Anthropic().count_tokens(text)
        except Exception as e:
            # 粗略估算，作為後備方案
            return len(text) // 4  # Claude大約每4個字符算1個token
