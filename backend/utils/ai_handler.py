"""AI處理器類."""

import os
from typing import Dict, List, Optional
import openai
from ..models.character import Character
from ..models.story import Story

class AIHandler:
    """AI處理器類，負責與不同的AI模型互動."""
    
    def __init__(self):
        """初始化AI處理器."""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.current_model = 'gpt-4'
        self.temperature = 0.7
        self.max_tokens = 500
        
    def set_model(self, model_name: str) -> None:
        """設置當前使用的模型."""
        self.current_model = model_name
        
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
            else:
                raise ValueError(f"不支援的模型: {self.current_model}")
        except Exception as e:
            print(f"生成回應時發生錯誤: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return f"AI回應生成失敗: {str(e)}"
    
    def generate_choices(self, character: Character, 
                        current_response: str,
                        story_context: Story) -> List[Dict]:
        """生成對話選項."""
        prompt = f"""
基於以下上下文生成3-4個對話選項:
角色: {character.name}
性格: {character.personality}
當前回應: {current_response}
故事背景: {story_context.background}
當前場景: {story_context.current_scene}

Format:
- 選項1
- 選項2
- 選項3
"""
        
        try:
            if 'gpt' in self.current_model:
                choices_text = self._call_openai(prompt)
            else:
                choices_text = self._call_anthropic(prompt)
                
            # 解析選項
            choices = []
            for line in choices_text.split('\n'):
                if line.startswith('-'):
                    choice_text = line[1:].strip()
                    choices.append({
                        'text': choice_text,
                        'value': len(choices)
                    })
            return choices
            
        except Exception as e:
            return [{'text': '繼續', 'value': 0}]
    
    def _build_prompt(self, character: Character, user_input: str,
                     dialogue_history: List[Dict], 
                     story_context: Story) -> str:
        """構建AI提示."""
        # 基本角色信息
        prompt = f"""
你現在扮演一個名叫{character.name}的角色。

角色設定：
- 性格: {character.personality}
- 說話風格: {character.dialogue_style}
- 性向: {character.orientation or '未指定'}
- 特質: {', '.join(character.traits or [])}

故事背景：
{story_context.background}

當前場景：
{story_context.current_scene}

限制級內容：{'允許' if story_context.adult_content else '不允許'}

對話歷史：
"""
        
        # 添加對話歷史
        for entry in dialogue_history[-5:]:  # 只使用最近5條對話
            prompt += f"{entry['speaker']}: {entry['content']}\n"
            
        # 添加用戶輸入
        prompt += f"\n用戶: {user_input}\n\n請以{character.name}的身份回應:"
        
        return prompt
    
    def _call_openai(self, prompt: str) -> str:
        """調用OpenAI API."""
        if os.getenv('FLASK_ENV') == 'development':
            # 開發模式：返回測試響應
            return self._generate_test_response(prompt)
            
        if not self.openai_api_key:
            raise ValueError("未設置OpenAI API密鑰")
            
        client = openai.OpenAI(api_key=self.openai_api_key)
        response = client.chat.completions.create(
            model=self.current_model,
            messages=[
                {"role": "system", "content": "You are an AI RPG character."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        if hasattr(response.choices[0].message, 'content'):
            return response.choices[0].message.content.strip()
        else:
            raise ValueError("無法從API響應中獲取內容")
    
    def _call_anthropic(self, prompt: str) -> str:
        """調用Anthropic API."""
        if os.getenv('FLASK_ENV') == 'development':
            # 開發模式：返回測試響應
            return self._generate_test_response(prompt)
            
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not anthropic_api_key:
            raise ValueError("未設置Anthropic API密鑰")
            
        try:
            import anthropic
            client = anthropic.Client(api_key=anthropic_api_key)
            response = client.messages.create(
                model="claude-2",
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except ImportError:
            raise ImportError("請安裝anthropic套件: pip install anthropic")
        except Exception as e:
            raise Exception(f"Anthropic API調用失敗: {str(e)}")
            
    def _generate_test_response(self, prompt: str) -> str:
        """生成測試響應."""
        print(f"[測試模式] 接收到提示: {prompt}")
        
        # 檢查是否包含用戶輸入
        if "用戶:" in prompt:
            response = {
                "你好": "哈囉！很高興見到你。我是Yuki，雖然看起來很酷，但其實我很想和你聊天呢...",
                "在嗎": "嗯...我一直都在這裡啊，只是...不太會主動說話而已...",
                "名字": "我叫Yuki...雖然這個名字聽起來很冷，但我其實不是那麼難相處的...",
            }
            
            for key, value in response.items():
                if key in prompt.lower():
                    print(f"[測試模式] 匹配關鍵詞'{key}', 返回: {value}")
                    return value
                    
            default_response = "嗯...（偷偷看了你一眼）要不要聊聊天？"
            print(f"[測試模式] 使用預設回應: {default_response}")
            return default_response
            
        # 生成對話選項
        if "生成3-4個對話選項" in prompt:
            choices = """
- 當然可以！雖然有點害羞，但我很想更了解你呢...
- 你平常都喜歡做什麼？我也想知道你的興趣
- 這裡的氛圍真不錯呢，讓人感覺很放鬆
- 其實...我一直都很想找人聊天的說
"""
            print(f"[測試模式] 生成選項: {choices}")
            return choices
        
        # 預設回應
        responses = [
            "（輕輕點頭）嗯...這個話題很有趣呢",
            "（露出感興趣的表情）原來如此，能說得更詳細一點嗎？",
            "（微笑）雖然我不太會表達，但我真的很認同你的想法",
            "（眼神閃爍）那個...我也有類似的想法呢..."
        ]
        import random
        response = random.choice(responses)
        print(f"[測試模式] 隨機回應: {response}")
        return response
