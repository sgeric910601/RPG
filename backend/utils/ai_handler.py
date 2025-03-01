"""AI處理器類."""

import os
from typing import Dict, List, Optional, Any
import openai
from ..models.character import Character
from ..services.openrouter_service import OpenRouterService
from ..utils.model_manager import ModelManager
from ..models.story import Story

class AIHandler:
    """AI處理器類，負責與不同的AI模型互動."""
    
    # 支持的模型列表
    OPENAI_MODELS = [
        "gpt-4", 
        "gpt-4-turbo", 
        "gpt-4", 
        "gpt-3.5-turbo"
    ]
    
    CLAUDE_MODELS = [
        "claude-3-opus-20240229", 
        "claude-3-sonnet-20240229", 
        "claude-3-haiku-20240307"
    ]
    
    # OpenRouter 模型
    OPENROUTER_MODELS = [
        "deepseek/deepseek-chat:free"
    ]
    
    def __init__(self):
        """初始化AI處理器."""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.current_model = "deepseek/deepseek-chat:free"  # 默認使用DeepSeek模型
        self.temperature = 0.7
        self.max_tokens = 500
        
        # 初始化服務
        try:
            self.openrouter_service = OpenRouterService()
        except Exception as e:
            print(f"[AI處理器] 初始化OpenRouter服務失敗: {e}")
            self.openrouter_service = None
            
        self.model_manager = ModelManager()
        
    def generate_response(self, character: Character, user_input: str,
                         dialogue_history: List[Dict], 
                         story_context: Story) -> str:
        """生成AI回應."""
        # 構建提示
        prompt = self._build_prompt(
            character=character,
            user_input=user_input,
            dialogue_history=dialogue_history,
            story_context=story_context
        )
        print(f"[DEBUG] 生成的提示: {prompt[:200]}...")
        
        try:
            # 根據不同模型調用不同的API
            if 'gpt' in self.current_model:
                print(f"使用OpenAI模型: {self.current_model}")
                response = self._call_openai(prompt)
                print(f"OpenAI回應: {response}")
                return response
            elif 'claude' in self.current_model:
                print(f"使用Claude模型: {self.current_model}")
                response = self._call_anthropic(prompt)
                print(f"Claude回應: {response}")
                return response
            elif 'deepseek' in self.current_model:
                print(f"使用OpenRouter模型: {self.current_model}")
                try:
                    system_prompt = "你是一個2D遊戲中的虛擬角色。請用生動活潑、富有感情的方式來對話，每次回應不要超過30個字。"
                    response = self.openrouter_service.generate_response(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        model=self.current_model
                    )
                    print(f"OpenRouter回應: {response}")
                    return response.strip()
                except Exception as e:
                    print(f"OpenRouter調用失敗: {str(e)}")
                    return self._generate_test_response(prompt)
            else:
                raise ValueError(f"不支援的模型: {self.current_model}")
        except Exception as e:
            print(f"生成回應時發生錯誤: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return self._generate_test_response(prompt)
    
    def _build_prompt(self, character: Character, user_input: str,
                     dialogue_history: List[Dict], 
                     story_context: Story) -> str:
        """構建AI提示."""
        prompt = f"""你現在扮演一個名叫{character.name}的角色。

角色設定：
- 性格: {character.personality}
- 說話風格: {character.dialogue_style}
- 特質: {', '.join(character.traits or [])}

請用簡短且生動的對話方式回應用戶的話。每次回應不要超過30個字。
回應需要富有情感和個性，可以加入表情和動作描述。

用戶的話: {user_input}

請以{character.name}的身份回應:"""
        return prompt
        
    def _call_openai(self, prompt: str) -> str:
        """調用OpenAI API。"""
        if os.getenv('FLASK_ENV') == 'development':
            return self._generate_test_response(prompt)
            
        if not self.openai_api_key:
            raise ValueError("未設置OpenAI API密鑰")
            
        client = openai.OpenAI(api_key=self.openai_api_key)
        
        params = {
            "model": self.current_model,
            "messages": [
                {"role": "system", "content": "You are an AI RPG character."},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        response = client.chat.completions.create(**params)
        return response.choices[0].message.content.strip()
    
    def _call_anthropic(self, prompt: str) -> str:
        """調用Anthropic API。"""
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not anthropic_api_key:
            return self._generate_test_response(prompt)
            
        try:
            import anthropic
            current_model = self.current_model if self.current_model in self.CLAUDE_MODELS else "claude-3-opus-20240229"
            
            client = anthropic.Anthropic(api_key=anthropic_api_key)
            response = client.messages.create(
                model=current_model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system="You are an AI RPG character.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Anthropic API調用失敗: {str(e)}")
            return self._generate_test_response(prompt)
    
    def _generate_test_response(self, prompt: str) -> str:
        """生成測試響應."""
        print(f"[測試模式] 收到提示: {prompt[:100]}...")
        
        default_responses = [
            "嗯...讓我想想該怎麼回答呢... (歪著頭)",
            "啊！這個問題很有趣呢！(眼睛發亮)",
            "嘿嘿，我也是這麼想的！(開心地笑著)",
            "原來如此...你說得對呢！(認真點頭)"
        ]
        import random
        response = random.choice(default_responses)
        print(f"[測試模式] 返回: {response}")
        return response
