"""RPG遊戲主程式."""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import logging
import json
import os
from typing import Dict, List, Union
from dotenv import load_dotenv
import eventlet
import asyncio
import traceback

from backend.api import api_bp
from backend.core import CharacterManager, StoryManager, DialogueManager
from backend.services.ai.base import AIServiceFactory, ModelManager
from backend.core.prompt import PromptManager, PromptEnhancer
from backend.utils.error import handle_error, NotFoundError, ServiceError

# 角色名稱到ID的映射
CHARACTER_NAME_MAPPING = {
    "雪": "1",   # Yuki的ID
    "怜": "2",   # Rei的ID
    "明": "3",   # Akira的ID
    "晶": "1"    # 映射到Yuki的ID
}

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化eventlet
eventlet.monkey_patch()

# 載入環境變量
load_dotenv()

app = Flask(__name__, 
    template_folder='frontend/templates',
    static_folder='frontend/static')

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key')
app.config['PORT'] = int(os.getenv('PORT', 5000))
app.config['DEBUG'] = os.getenv('DEBUG', 'True').lower() == 'true'

# Socket.IO 配置
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    ping_timeout=60,
    ping_interval=25,
    logger=True,
    path='socket.io',
    engineio_logger=True
)

def format_error(e: Exception) -> str:
    """格式化錯誤消息。
    
    Args:
        e: 異常實例
    Returns:
        格式化後的錯誤消息
    """
    if isinstance(e, NotFoundError):
        return f"找不到{e.details['resource_type']}: {e.details['resource_id']}"
    elif isinstance(e, ServiceError):
        return f"服務錯誤: {e.message}"
    else:
        return str(e)

def emit_error(error: Union[str, Exception], sid: str = None):
    """發送錯誤消息到客戶端。

    Args:
        error: 錯誤消息或異常實例
        sid: 客戶端的會話ID
    """
    if isinstance(error, Exception):
        error_msg = format_error(error)
    else:
        error_msg = str(error)
    
    logger.error(f"[WebSocket] 發送錯誤消息: {error_msg}")
    socketio.emit('receive_message', {
        'status': 'error',
        'message': error_msg
    }, room=sid)

def emit_message(message: str, character_data: Dict, is_chunk: bool = True, sid: str = None):
    """發送消息到客戶端。

    Args:
        message: 消息內容
        character_data: 角色數據
        is_chunk: 是否為流式片段
        sid: 客戶端的會話ID
    """
    socketio.emit('receive_message', {
        'status': 'success',
        'message': message,
        'character': character_data,
        'is_chunk': is_chunk
    }, room=sid)

def get_character_id(name: str) -> str:
    """獲取角色的標準ID。

    Args:
        name: 輸入的角色名稱
    Returns:
        標準化的角色名稱
    """
    mapped_id = CHARACTER_NAME_MAPPING.get(name)
    if mapped_id:
        logger.info(f"映射角色ID: {name} -> {mapped_id}")
    return mapped_id or name

# 初始化管理器
logger.info("正在初始化管理器...")
character_manager = CharacterManager()
story_manager = StoryManager()
dialogue_manager = DialogueManager()
model_manager = ModelManager()

# 初始化AI服務
logger.info("正在初始化AI服務...")
ai_service = AIServiceFactory.get_service()

# 初始化提示詞管理相關組件
prompt_enhancer = PromptEnhancer(ai_service)
prompt_manager = PromptManager('data/prompts')
prompt_manager.set_enhancer(prompt_enhancer)

# 註冊API藍圖
logger.info("正在註冊API藍圖...")
app.register_blueprint(api_bp)

@app.route('/')
def index():
    """渲染主頁面."""
    server_config = {
        'host': os.getenv('HOST', '0.0.0.0'),
        'port': int(os.getenv('PORT', 5000))
    }
    return render_template('index.html', server_config=server_config)

@app.route('/api/models', methods=['GET'])
def get_models():
    """獲取可用的AI模型列表."""
    try:
        models = model_manager.get_all_models()
        
        # 按照提供商分組模型
        logger.info(f"找到以下模型: {list(models.keys())}")
        
        grouped_models = {
            'openai': [],
            'openai_vision': [],
            'gpt4': [],
            'claude': [],
            'openrouter': []
        }
        
        for model_id, model_info in models.items():
            provider = model_info.get('api_type', 'openai')
            
            # 根據模型ID和api_type進行分組
            if 'gpt-4' in model_id and provider == 'openai':
                grouped_models['gpt4'].append(model_id)
            elif 'vision' in model_id and provider == 'openai':
                grouped_models['openai_vision'].append(model_id)
            elif provider in grouped_models:
                if model_id not in grouped_models[provider]:
                    grouped_models[provider].append(model_id)
            else:
                logger.warning(f"未知的模型提供商: {provider}, model_id: {model_id}")
        
        # 移除空的分組
        grouped_models = {k: v for k, v in grouped_models.items() if v}
        
        # 輸出最終分組結果
        logger.info(f"按提供商分組後的模型: {grouped_models}")
        return jsonify({
            'status': 'success', 
            'data': {
                'models': grouped_models
            }
        })
    except Exception as e:
        logger.error(f"獲取模型列表時發生錯誤: {str(e)}")
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
            
        model_name = data['model']
        logger.info(f"設置模型: {model_name}")
            
        # 使用ModelManager設置模型
        if model_manager.set_model(model_name):
            return jsonify({'status': 'success'})
        else:
            return jsonify({
                'status': 'error',
                'message': '設置模型失敗'
            }), 400
    except Exception as e:
        logger.error(f"設置模型時發生錯誤: {str(e)}")
        return jsonify({
            'status': 'error', 
            'message': f'設置模型時發生錯誤: {str(e)}'
        })

@socketio.on('send_message')
def handle_message(data):
    """處理用戶消息."""
    try:
        logger.info(f"[WebSocket] 接收到消息: {data}")
        
        # 驗證消息格式
        if not data or not isinstance(data, dict):
            raise ValueError("無效的消息格式")
        if 'message' not in data:
            raise ValueError("消息內容不能為空")

        # 獲取角色標識符
        character_name = data.get('character')
        if not character_name:
            raise ValueError("未指定角色")
        logger.info(f"[WebSocket] 收到的原始數據: {data}")
            
        # 檢查是否已經是ID
        if character_name in ['1', '2', '3']:
            logger.info(f"[WebSocket] 直接使用角色ID: {character_name}")
            character_id = character_name
            original_name = f"角色{character_id}"
        else:
            # 如果不是ID，則進行轉換
            original_name = character_name
            character_id = get_character_id(character_name)
            if not character_id:
                raise ValueError(f"無法將角色名稱 '{character_name}' 轉換為有效的ID")

        logger.info(f"[WebSocket] 角色名稱轉換: {original_name} -> ID: {character_id}")
            
        # 保存當前的sid
        current_sid = request.sid
        logger.info(f"[WebSocket] 處理角色 {character_id} 的消息，SID: {current_sid}")

        async def process_response():
            try:
                # 使用角色ID獲取或創建對話會話
                try:
                    sessions = dialogue_manager.dialogue_service.get_all_dialogue_sessions()
                    if sessions:
                        session_id = sessions[0]['id']
                        session = dialogue_manager.dialogue_service.get_dialogue_session(session_id)
                    else:
                        logger.info(f"[WebSocket] 創建新的對話會話，使用角色ID: {character_id}")
                        session = dialogue_manager.start_new_conversation(character_id)
                    logger.info(f"[WebSocket] 使用會話ID: {session.id}")
                except Exception as e:
                    logger.error(f"[WebSocket] 獲取會話時出錯: {format_error(e)}")
                    raise

                # 獲取角色數據
                try:
                    character = character_manager.get_character(character_id)
                    character_data = character.to_dict()
                    logger.info(f"[WebSocket] 獲取到角色數據:")
                    logger.info(f"  - ID: {character_data.get('id')}")
                    logger.info(f"  - 名稱: {character_data.get('name')}")
                    logger.info(f"  - 對話風格: {character_data.get('dialogue_style')}")
                except Exception as e:
                    logger.error(f"[WebSocket] 獲取角色數據時出錯: {format_error(e)}")
                    raise

                # 生成回應
                try:
                    full_response = []
                    logger.info(f"[WebSocket] 開始生成回應，使用角色ID: {character_id}")
                    
                    async for chunk in dialogue_manager.dialogue_service.generate_response(
                        session.id,
                        data['message']
                    ):
                        full_response.append(chunk)
                        emit_message(chunk, character_data, True, current_sid)
                        eventlet.sleep(0)

                    if full_response:
                        final_response = ''.join(full_response)
                        emit_message(final_response, character_data, False, current_sid)
                        logger.info("[WebSocket] 回應生成完成")
                    else:
                        raise ValueError("未生成任何回應")

                except Exception as e:
                    logger.error(f"[WebSocket] 生成回應時出錯: {format_error(e)}")
                    raise

            except Exception as e:
                error_msg = format_error(e)
                logger.error(f"[WebSocket] 處理回應時出錯: {error_msg}")
                emit_error(e, current_sid)

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(process_response())
            except Exception as e:
                logger.error(f"[WebSocket] 異步執行時出錯: {format_error(e)}")
                emit_error(e, current_sid)
            finally:
                loop.close()

        eventlet.spawn(run_async)

    except Exception as e:
        error_msg = format_error(e)
        logger.error(f"[WebSocket] 請求處理出錯: {error_msg}")
        if hasattr(request, 'sid') and request.sid:
            emit_error(e, request.sid)
        else:
            logger.error("[WebSocket] 無法獲取request.sid")

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')  # 默認監聽所有網卡
    port = int(os.getenv('PORT', 5000))  # 默認端口 5000
    debug = os.getenv('DEBUG', 'True').lower() == 'true'  # 默認開啟調試模式
    
    logger.info(f"正在啟動服務器... 監聽: {host}:{port} 調試模式: {debug}")
    socketio.run(app, host=host, port=port, debug=debug)
    logger.info("服務器啟動完成")
