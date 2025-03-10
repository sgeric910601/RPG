"""測試所有AI服務的API."""

import os
import sys
import asyncio
from dotenv import load_dotenv
import logging

# 將項目根目錄添加到Python的導入路徑中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 設置日誌
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 導入AI服務
from backend.services.ai import (
    AIServiceFactory, 
    OpenAIService, 
    ClaudeService, 
    OpenRouterService
)

# 測試提示
SYSTEM_PROMPT = """你是一個2D遊戲中的虛擬角色，名叫Akira。
性格開朗活潑，說話風格充滿活力，經常使用流行語和可愛表情。
請用簡短且生動的方式回應，不要超過30個字。"""

USER_PROMPT = "你好！很高興認識你！"

# 測試消息
TEST_MESSAGES = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": USER_PROMPT}
]

# Claude API需要特殊處理system消息
CLAUDE_TEST_MESSAGES = [
    {"role": "user", "content": USER_PROMPT}
]

async def test_service(service_name, service):
    """測試特定AI服務的所有主要方法."""
    print(f"\n{'='*50}")
    print(f"開始測試 {service_name} 服務...")
    print(f"{'='*50}")
    
    # 測試 is_available
    try:
        available = service.is_available()
        print(f"\n✓ is_available: {available}")
        if not available:
            print(f"⚠️ {service_name} 服務不可用，跳過後續測試")
            return False
    except Exception as e:
        print(f"\n✗ is_available 測試失敗: {str(e)}")
        return False
    
    # 測試 get_model_info
    try:
        model_info = service.get_model_info()
        print(f"\n✓ get_model_info 成功:")
        print(f"  - 名稱: {model_info.get('name')}")
        print(f"  - 描述: {model_info.get('description')}")
        print(f"  - 模型數量: {len(model_info.get('models', []))}")
    except Exception as e:
        print(f"\n✗ get_model_info 測試失敗: {str(e)}")
    
    # 測試 generate_text
    try:
        print(f"\n正在測試 generate_text...")
        # 使用同步方式調用，避免事件循環問題
        if service_name == "OpenAI":
            response = service.client.chat.completions.create(
                model=service.default_model,
                messages=[{"role": "user", "content": USER_PROMPT}]
            ).choices[0].message.content
        elif service_name == "Claude":
            response = service.client.messages.create(
                model=service.default_model,
                messages=[{"role": "user", "content": USER_PROMPT}],
                max_tokens=100
            ).content[0].text
        elif service_name == "OpenRouter":
            import httpx
            headers = {
                "Authorization": f"Bearer {service.api_key}",
                "HTTP-Referer": service.referer,
                "Content-Type": "application/json"
            }
            response = httpx.post(
                f"{service.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": service.default_model,
                    "messages": [{"role": "user", "content": USER_PROMPT}],
                    "max_tokens": 100,
                    "stream": False
                }
            ).json()["choices"][0]["message"]["content"]
        else:
            response = "未知服務"
        print(f"✓ generate_text 成功: {response[:50]}...")
    except Exception as e:
        print(f"✗ generate_text 測試失敗: {str(e)}")
    
    # 測試 generate_chat_response
    try:
        print(f"\n正在測試 generate_chat_response...")
        # 根據服務類型選擇適當的消息格式
        if service_name == "Claude":
            response = await service.generate_chat_response(
                CLAUDE_TEST_MESSAGES,
                system=SYSTEM_PROMPT
            )
        else:
            response = await service.generate_chat_response(TEST_MESSAGES)
        print(f"✓ generate_chat_response 成功: {response[:50]}...")
    except Exception as e:
        print(f"✗ generate_chat_response 測試失敗: {str(e)}")
    
    # 測試 generate_stream_response
    try:
        print(f"\n正在測試 generate_stream_response...")
        full_response = []
        # 根據服務類型選擇適當的消息格式
        if service_name == "Claude":
            stream_gen = service.generate_stream_response(
                CLAUDE_TEST_MESSAGES,
                system=SYSTEM_PROMPT
            )
        else:
            stream_gen = service.generate_stream_response(TEST_MESSAGES)
            
        async for chunk in stream_gen:
            full_response.append(chunk)
            print(f"  片段: {chunk}", end="\r")
        
        if full_response:
            print(f"\n✓ generate_stream_response 成功: {''.join(full_response)[:50]}...")
        else:
            print(f"\n✗ generate_stream_response 沒有返回任何內容")
    except Exception as e:
        print(f"\n✗ generate_stream_response 測試失敗: {str(e)}")
    
    # 測試 generate_response
    try:
        print(f"\n正在測試 generate_response...")
        full_response = []
        # 根據服務類型選擇適當的消息格式
        if service_name == "Claude":
            response_gen = service.generate_response(
                CLAUDE_TEST_MESSAGES,
                system=SYSTEM_PROMPT,
                stream=True
            )
        else:
            response_gen = service.generate_response(TEST_MESSAGES, stream=True)
            
        async for chunk in response_gen:
            full_response.append(chunk)
            print(f"  片段: {chunk}", end="\r")
        
        if full_response:
            print(f"\n✓ generate_response 成功: {''.join(full_response)[:50]}...")
        else:
            print(f"\n✗ generate_response 沒有返回任何內容")
    except Exception as e:
        print(f"\n✗ generate_response 測試失敗: {str(e)}")
    
    # 測試 enhance_prompt
    try:
        print(f"\n正在測試 enhance_prompt...")
        # 對於OpenRouter服務，enhance_prompt不是異步方法
        if service_name == "OpenRouter":
            result = service.enhance_prompt("寫一個關於太空探險的故事")
        else:
            result = await service.enhance_prompt("寫一個關於太空探險的故事")
        print(f"✓ enhance_prompt 成功:")
        print(f"  - 原始提示詞: {result.get('original')[:30]}...")
        print(f"  - 增強提示詞: {result.get('enhanced')[:30]}...")
    except Exception as e:
        print(f"✗ enhance_prompt 測試失敗: {str(e)}")
    
    # 測試 analyze_text
    try:
        print(f"\n正在測試 analyze_text...")
        # 對於OpenRouter服務，analyze_text不是異步方法
        if service_name == "OpenRouter":
            result = service.analyze_text("這是一段測試文本，用於測試AI服務的文本分析功能。")
        else:
            result = await service.analyze_text("這是一段測試文本，用於測試AI服務的文本分析功能。")
        print(f"✓ analyze_text 成功: {str(result)[:50]}...")
    except Exception as e:
        print(f"✗ analyze_text 測試失敗: {str(e)}")
    
    # 測試 set_model
    try:
        print(f"\n正在測試 set_model...")
        # 獲取模型信息中的第一個模型ID
        models = model_info.get('models', [])
        if models:
            model_id = models[0].get('id')
            result = service.set_model(model_id)
            print(f"✓ set_model 成功: {model_id}, 結果: {result}")
        else:
            print(f"⚠️ 沒有可用的模型ID，跳過 set_model 測試")
    except Exception as e:
        print(f"✗ set_model 測試失敗: {str(e)}")
    
    return True

async def main():
    """主測試函數."""
    # 載入環境變量
    load_dotenv()
    
    print("\n開始測試所有AI服務...")
    
    # 測試 OpenAI 服務
    if "OPENAI_API_KEY" in os.environ:
        try:
            openai_service = OpenAIService()
            await test_service("OpenAI", openai_service)
        except Exception as e:
            print(f"\n✗ OpenAI 服務初始化失敗: {str(e)}")
            print("\n請確認:")
            print("1. .env文件中是否包含有效的OPENAI_API_KEY")
            print("2. OpenAI API是否可以正常訪問")
            print("3. 網絡連接是否正常")
    else:
        print("\n⚠️ 未找到OPENAI_API_KEY環境變量，跳過OpenAI服務測試")
    
    # 測試 Claude 服務
    if "ANTHROPIC_API_KEY" in os.environ:
        try:
            claude_service = ClaudeService()
            await test_service("Claude", claude_service)
        except Exception as e:
            print(f"\n✗ Claude 服務初始化失敗: {str(e)}")
            print("\n請確認:")
            print("1. .env文件中是否包含有效的ANTHROPIC_API_KEY")
            print("2. Anthropic API是否可以正常訪問")
            print("3. 網絡連接是否正常")
    else:
        print("\n⚠️ 未找到ANTHROPIC_API_KEY環境變量，跳過Claude服務測試")
    
    # 測試 OpenRouter 服務
    if "OPENROUTER_API_KEY" in os.environ:
        try:
            openrouter_service = OpenRouterService()
            await test_service("OpenRouter", openrouter_service)
        except Exception as e:
            print(f"\n✗ OpenRouter 服務初始化失敗: {str(e)}")
            print("\n請確認:")
            print("1. .env文件中是否包含有效的OPENROUTER_API_KEY")
            print("2. OpenRouter API是否可以正常訪問")
            print("3. 網絡連接是否正常")
    else:
        print("\n⚠️ 未找到OPENROUTER_API_KEY環境變量，跳過OpenRouter服務測試")
    
    # 測試 AIServiceFactory
    try:
        print(f"\n{'='*50}")
        print("測試 AIServiceFactory...")
        print(f"{'='*50}")
        
        # 列出所有服務
        services = AIServiceFactory.list_services()
        print(f"\n✓ 可用服務列表: {services}")
        
        # 獲取默認服務
        default_service = AIServiceFactory.get_service()
        if default_service:
            print(f"\n✓ 獲取默認服務成功: {type(default_service).__name__}")
        else:
            print(f"\n⚠️ 沒有默認服務")
        
        # 獲取可用服務
        available_services = AIServiceFactory.get_available_services()
        print(f"\n✓ 可用服務: {available_services}")
        
    except Exception as e:
        print(f"\n✗ AIServiceFactory 測試失敗: {str(e)}")
    
    print("\n測試完成!")

if __name__ == "__main__":
    asyncio.run(main())