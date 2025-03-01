"""OpenRouter API客戶端封裝類."""

import os
from typing import Dict, List, Optional, Any
from openai import OpenAI

class OpenRouterClient:
    """OpenRouter API客戶端封裝類."""
    
    SUPPORTED_MODELS = [
        "deepseek/deepseek-chat:free"
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化OpenRouter客戶端."""
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("未提供OpenRouter API密鑰")
            
        try:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
                default_headers={
                    "HTTP-Referer": os.getenv('HOST', 'http://localhost:5000'),
                }
            )
        except ImportError:
            raise ImportError("請安裝openai套件: pip install openai")
            
    def generate_text(self,
                     prompt: str,
                     system_prompt: Optional[str] = None,
                     model: str = "deepseek/deepseek-chat:free",
                     max_tokens: int = 500,
                     temperature: float = 0.7) -> str:
        """生成文本回應."""
        try:
            if model not in self.SUPPORTED_MODELS:
                raise ValueError(f"不支援的模型: {model}")
                
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenRouter API調用失敗: {str(e)}")