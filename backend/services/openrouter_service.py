"""OpenRouter服務類."""

import os
from typing import Dict, List, Optional, Any
import httpx
import json

class OpenRouterService:
    """處理OpenRouter API相關的所有操作."""
    
    SUPPORTED_MODELS = [
        "deepseek/deepseek-chat:free",
    ]
    
    def __init__(self):
        """初始化OpenRouter服務."""
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("[OpenRouter] API密鑰未設置")
            
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = "deepseek/deepseek-chat:free"
        
    def generate_response(self, 
                         prompt: str, 
                         system_prompt: Optional[str] = None,
                         model: str = "deepseek/deepseek-chat:free",
                         max_tokens: int = 500,
                         temperature: float = 0.7) -> str:
        """生成AI回應."""
        print(f"[OpenRouter] 開始生成回應")
        print(f"[OpenRouter] 模型: {model}")
        print(f"[OpenRouter] 系統提示: {system_prompt}")
        print(f"[OpenRouter] 用戶提示: {prompt}")
        
        if model not in self.SUPPORTED_MODELS:
            print(f"[OpenRouter] 不支援的模型 {model}, 使用默認模型 {self.default_model}")
            model = self.default_model
            
        # 準備消息
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
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
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "RPG-Dialogue",
            "Content-Type": "application/json"
        }
        
        try:
            # 發送請求
            print(f"[OpenRouter] 發送請求...")
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=request_data,
                    timeout=30.0
                )
                
            # 檢查響應
            if response.status_code != 200:
                error_text = self._parse_error_response(response)
                raise Exception(f"API錯誤: {error_text}")
                
            # 解析回應
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"[OpenRouter] 成功獲得回應: {content[:100]}...")
            
            return content.strip()
            
        except Exception as e:
            print(f"[OpenRouter錯誤] {str(e)}")
            import traceback
            print(f"[OpenRouter錯誤] 堆棧跟踪: {traceback.format_exc()}")
            raise
            
    def _parse_error_response(self, response) -> str:
        """解析錯誤回應."""
        try:
            error_json = response.json()
            if isinstance(error_json, dict):
                error = error_json.get('error', {})
                if isinstance(error, dict):
                    return error.get('message', response.text)
            return response.text
        except:
            return response.text
