"""Anthropic API客戶端封裝類."""

import os
from typing import Dict, List, Optional, Any, Union

class AnthropicClient:
    """Anthropic API客戶端封裝類."""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化Anthropic客戶端."""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("未提供Anthropic API密鑰")
            
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("請安裝anthropic套件: pip install anthropic")
    
    def generate_text(self, 
                    prompt: str, 
                    system_prompt: Optional[str] = None,
                    model: str = "claude-3.7-sonnet",  # 更新為最新模型
                    max_tokens: int = 500,
                    temperature: float = 0.7,
                    top_p: Optional[float] = None,
                    top_k: Optional[int] = None) -> str:
        """生成文本回應."""
        try:
            params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            # 添加可選參數
            if system_prompt:
                params["system"] = system_prompt
                
            if top_p is not None:
                params["top_p"] = top_p
                
            if top_k is not None:
                params["top_k"] = top_k
                
            response = self.client.messages.create(**params)
            
            if hasattr(response, 'content') and len(response.content) > 0:
                return response.content[0].text
            else:
                return ""
                
        except Exception as e:
            raise Exception(f"Anthropic API調用失敗: {str(e)}")
            
    def generate_with_images(self, 
                           text_prompt: str,
                           image_urls: List[str],
                           system_prompt: Optional[str] = None,
                           model: str = "claude-3.7-sonnet",  # 更新為最新模型
                           max_tokens: int = 500,
                           temperature: float = 0.7) -> str:
        """生成包含圖像理解的回應."""
        try:
            # 構建消息內容，包括文本和圖像
            content = [{"type": "text", "text": text_prompt}]
            
            # 添加圖像
            for url in image_urls:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": url
                    }
                })
                
            params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": content}]
            }
            
            # 添加系統提示
            if system_prompt:
                params["system"] = system_prompt
                
            response = self.client.messages.create(**params)
            
            if hasattr(response, 'content') and len(response.content) > 0:
                return response.content[0].text
            else:
                return ""
                
        except Exception as e:
            raise Exception(f"Anthropic多模態API調用失敗: {str(e)}")
            
    def count_tokens(self, text: str) -> int:
        """計算文本的token數量."""
        try:
            from anthropic import Anthropic
            tokenizer = Anthropic().get_tokenizer()
            return len(tokenizer.encode(text).ids)
        except:
            # 如果無法使用精確計算，使用估算
            # 英文約每4個字符1個token，中文約每1.5個字符1個token
            chinese_char_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            other_char_count = len(text) - chinese_char_count
            return int(chinese_char_count / 1.5 + other_char_count / 4)
