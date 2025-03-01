"""OpenRouter API客戶端封裝類."""

import os
from typing import Dict, List, Optional, Any
from openai import OpenAI
import json

class OpenRouterClient:
    """OpenRouter API客戶端封裝類."""
    
    SUPPORTED_MODELS = [
        "deepseek/deepseek-chat:free",
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化OpenRouter客戶端."""
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        print(f"[OpenRouter] API密鑰存在: {bool(self.api_key)}")
        
        if not self.api_key:
            print("[OpenRouter錯誤] 找不到API密鑰，檢查環境變量OPENROUTER_API_KEY")
            raise ValueError("未提供OpenRouter API密鑰")
            
        try:
            # 設置基本配置
            self.base_url = "https://openrouter.ai/api/v1"
            self.api_key = self.api_key
            
            # 創建client實例，不在初始化時設置headers
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
            
        except ImportError:
            raise ImportError("請安裝openai套件: pip install openai")
            
    def generate_text(self,
                     prompt: str,
                     system_prompt: Optional[str] = None,
                     model: str = "deepseek/deepseek-chat:free",  # 更新默認模型
                     max_tokens: int = 500,
                     temperature: float = 0.7) -> str:
        """生成文本回應."""
        try:
            print(f"[OpenRouter] 開始生成文本")
            print(f"[OpenRouter] 使用模型: {model}")
            print(f"[OpenRouter] 系統提示: {system_prompt}")
            print(f"[OpenRouter] 用戶提示: {prompt}")
            
            if model not in self.SUPPORTED_MODELS:
                print(f"[OpenRouter警告] 不支援的模型: {model}, 使用默認模型")
                model = self.SUPPORTED_MODELS[0]
                
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # 創建請求數據
            request_data = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # 手動發送請求
            import httpx
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "RPG-Dialogue",
                "Content-Type": "application/json"
            }
            
            print(f"[OpenRouter] 發送請求...")
            print(f"[OpenRouter] 請求URL: {self.base_url}/chat/completions")
            print(f"[OpenRouter] 請求數據: {json.dumps(request_data, ensure_ascii=False)}")
            
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=request_data,
                    timeout=30.0
                )
                
            if response.status_code != 200:
                error_text = response.text
                try:
                    error_json = response.json()
                    error_text = error_json.get('error', {}).get('message', response.text)
                except:
                    pass
                raise Exception(f"API返回錯誤: {response.status_code} - {error_text}")
                
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"[OpenRouter] 成功獲得回應: {content[:100]}...")
            return content.strip()
            
        except Exception as e:
            print(f"[OpenRouter錯誤] API調用失敗: {str(e)}")
            import traceback
            print("[OpenRouter錯誤] 堆棧跟蹤:", traceback.format_exc())
            raise Exception(f"OpenRouter API調用失敗: {str(e)}")
