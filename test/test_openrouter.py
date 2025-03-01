"""測試OpenRouter服務."""

import os
from backend.services.openrouter_service import OpenRouterService
from dotenv import load_dotenv

def main():
    """主測試函數."""
    # 載入環境變量
    load_dotenv()
    
    print("\n開始測試 OpenRouter 服務...")
    
    try:
        # 初始化服務
        service = OpenRouterService()
        
        # 測試提示
        system_prompt = """你是一個2D遊戲中的虛擬角色，名叫Akira。
性格開朗活潑，說話風格充滿活力，經常使用流行語和可愛表情。
請用簡短且生動的方式回應，不要超過30個字。"""
        
        user_prompt = "你好！很高興認識你！"
        
        print("\n發送測試請求...")
        print(f"系統提示: {system_prompt}")
        print(f"用戶提示: {user_prompt}")
        
        # 測試生成
        response = service.generate_response(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model="deepseek/deepseek-chat:free"
        )
        
        print("\n測試成功!")
        print(f"AI回應: {response}")
        
    except Exception as e:
        print("\n測試失敗!")
        print(f"錯誤信息: {str(e)}")
        print("\n請確認:")
        print("1. .env文件中是否包含有效的OPENROUTER_API_KEY")
        print("2. OpenRouter API是否可以正常訪問")
        print("3. 網絡連接是否正常")
        
if __name__ == "__main__":
    main()