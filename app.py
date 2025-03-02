"""RPG遊戲主程式."""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import json
import os
from typing import Dict, List
from dotenv import load_dotenv

from backend.api import api_bp
from backend.core import CharacterManager, StoryManager, DialogueManager
from backend.services.ai.base import AIServiceFactory, ModelManager
from backend.core.prompt import PromptManager, PromptEnhancer
from backend.utils.error import handle_error, NotFoundError

load_dotenv()

app = Flask(__name__, 
    template_folder='frontend/templates',
    static_folder='frontend/static')

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key')
app.config['PORT'] = int(os.getenv('PORT', 5000))
app.config['DEBUG'] = os.getenv('DEBUG', 'True').lower() == 'true'

# 註冊API藍圖
app.register_blueprint(api_bp)

# Socket.IO 配置
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
    always_connect=True,
    logger=True,
    engineio_logger=True
)

# 初始化管理器
character_manager = CharacterManager()
story_manager = StoryManager()
dialogue_manager = DialogueManager()
model_manager = ModelManager()

# 初始化AI服務
ai_service = AIServiceFactory.get_service()

# 初始化提示詞管理相關組件
prompt_enhancer = PromptEnhancer(ai_service)
prompt_manager = PromptManager('data/prompts')
prompt_manager.set_enhancer(prompt_enhancer)


@app.route('/')
def index():
    """渲染主頁面."""
    server_config = {
        'host': os.getenv('HOST', '0.0.0.0'),
        'port': int(os.getenv('PORT', 5000))
    }
    return render_template('index.html', server_config=server_config)


@socketio.on('send_message')
def handle_message(data):
    """處理用戶消息."""
    try:
        print(f"[WebSocket] 接收到消息: {data}")
        
        if not data or not isinstance(data, dict):
            raise ValueError("無效的消息格式")
            
        if 'message' not in data:
            raise ValueError("消息內容不能為空")
            
        character_name = data.get('character')
        if not character_name:
            raise ValueError("未指定角色")
            
        # 確保character是字符串類型的名稱
        if isinstance(character_name, dict):
            character_name = character_name.get('name')
            
        if not character_name:
            raise ValueError("無效的角色名稱")
            
        print(f"[WebSocket] 處理角色 {character_name} 的消息...")
        
        # 獲取或創建對話會話
        try:
            # 嘗試獲取最近的對話會話
            sessions = dialogue_manager.get_all_dialogue_sessions()
            if sessions:
                session_id = sessions[0]['id']
                session = dialogue_manager.get_dialogue_session(session_id)
            else:
                # 如果沒有對話會話，則創建一個新的
                session = dialogue_manager.start_new_conversation(character_name)
        except Exception as e:
            print(f"[WebSocket] 獲取或創建對話會話時出錯: {str(e)}")
            # 創建一個新的對話會話
            session = dialogue_manager.start_new_conversation(character_name)
        
        # 生成AI回應
        print(f"[WebSocket] 正在處理用戶輸入: {data['message']}")
        session, response = dialogue_manager.generate_response(
            session['id'],
            data['message']
        )
        print(f"[WebSocket Debug] 準備發送回應: {response}")
        print(f"[WebSocket] AI回應: {response}")
        
        # 獲取更新後的角色資料
        try:
            character = character_manager.get_character(character_name)
            character_data = character.to_dict()
        except NotFoundError:
            # 如果找不到角色，則使用會話中的角色名稱
            character_data = {'name': character_name}
            
        socketio.emit('receive_message', {
            'status': 'success',
            'message': response.strip(),  # 確保移除任何前後空白
            'character': character_data
        }, room=request.sid)
        print("[WebSocket] 消息發送成功")
        
    except Exception as e:
        import traceback
        print(f"[WebSocket] 錯誤: {str(e)}")
        print(traceback.format_exc())
        socketio.emit('receive_message', {
            'status': 'error',
            'message': f"處理消息時發生錯誤: {str(e)}"
        }, room=request.sid)


@app.route('/api/models', methods=['GET'])
def get_models():
    """獲取可用的AI模型列表."""
    try:
        models = model_manager.get_all_models()
        return jsonify({
            'status': 'success', 
            'models': model_manager.get_model_names()
        })
    except Exception as e:
        return handle_error(e, '獲取模型列表時發生錯誤')


@app.route('/api/set_model', methods=['POST'])
def set_model():
    """設置AI模型."""
    try:
        data = request.json
        if not data or 'model' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少模型參數'
            }), 400
            
        # 獲取AI服務
        ai_service = AIServiceFactory.get_service()
        
        # 設置模型
        ai_service.set_model(data['model'])
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return handle_error(e, '設置模型時發生錯誤')


@app.route('/api/prompt/enhance', methods=['POST'])
def enhance_prompt():
    """提示詞增強功能."""
    try:
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必要的提示詞參數'
            }), 400

        prompt = data['prompt']
        options = data.get('options', {})
        detailed = options.get('detailed_analysis', False)

        result = prompt_manager.enhance_prompt(prompt)
        if not detailed:
            result.pop('analysis', None)

        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        return handle_error(e, '增強提示詞時發生錯誤')


if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')  # 默認監聽所有網卡
    port = int(os.getenv('PORT', 5000))  # 默認端口 5000
    debug = os.getenv('DEBUG', 'True').lower() == 'true'  # 默認開啟調試模式
    socketio.run(app, host=host, port=port, debug=debug)
