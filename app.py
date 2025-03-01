"""RPG遊戲主程式."""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import json
import os
from backend.utils.prompt_manager import PromptManager
from backend.utils.prompt_enhancer import PromptEnhancer
from typing import Dict, List
from dotenv import load_dotenv
from backend.utils.ai_handler import AIHandler
from backend.controllers.story_controller import StoryController
from backend.models.character import Character
from backend.utils.prompt_manager import PromptManager
from backend.models.story import Story

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
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
    always_connect=True,
    logger=True,
    engineio_logger=True
)

# 初始化AI處理器和故事控制器
ai_handler = AIHandler()
story_controller = StoryController(ai_handler)

# 初始化提示詞管理相關組件
prompt_enhancer = PromptEnhancer(ai_handler)
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

@app.route('/api/init_story', methods=['POST'])
def init_story():
    """初始化故事設定."""
    try:
        data = request.json
        story = story_controller.create_story(
            world_type=data['world_type'],
            setting=data['setting'],
            background=data['background'],
            adult_content=data.get('adult_content', False)
        )
        return jsonify({
            'status': 'success',
            'story': story.to_dict()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/characters', methods=['GET'])
def get_characters():
    """獲取角色列表."""
    if not story_controller.current_story:
        return jsonify({
            'status': 'new_game',
            'message': '請選擇世界觀開始遊戲',
            'characters': []
        })
    
    characters = {
        name: char.to_dict()
        for name, char in story_controller.current_story.characters.items()
    }
    return jsonify({
        'status': 'success',
        'characters': characters
    })

@app.route('/api/characters/<character_name>', methods=['GET'])
def get_character(character_name):
    """獲取特定角色信息."""
    try:
        if not story_controller.current_story:
            raise ValueError("沒有活躍的故事")
            
        character = story_controller.current_story.characters.get(character_name)
        if not character:
            raise ValueError(f"找不到角色: {character_name}")
            
        return jsonify({
            'status': 'success',
            'character': character.to_dict()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404

@app.route('/api/characters', methods=['POST'])
def add_character():
    """添加新角色."""
    try:
        character_data = request.json
        character = story_controller.add_character(character_data)
        return jsonify({
            'status': 'success',
            'character': character.to_dict()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

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
        
        if not story_controller.current_story:
            print("[WebSocket] 嘗試載入已保存的故事...")
            story_controller.current_story = story_controller.load_story()
            if not story_controller.current_story:
                raise ValueError("沒有活躍的故事，請先創建或選擇一個世界")
                
        print(f"[WebSocket] 正在處理用戶輸入: {data['message']}")
        response, choices = story_controller.process_user_input(
            user_input=data['message'],
            current_character=character_name
        )
        print(f"[WebSocket] AI回應: {response}")
        print(f"[WebSocket] 生成選項: {choices}")
        
        # 獲取更新後的角色資料
        character = story_controller.current_story.characters.get(character_name)
        if not character:
            raise ValueError(f"找不到角色: {character_name}")
            
        socketio.emit('receive_message', {
            'status': 'success',
            'message': response,
            'character': character.to_dict(),
            'choices': choices
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

@app.route('/api/set_model', methods=['POST'])
def set_model():
    """設置AI模型."""
    try:
        data = request.json
        ai_handler.set_model(data['model'])
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/save_story', methods=['POST'])
def save_story():
    """手動保存當前故事."""
    try:
        story_controller._save_story()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/chat_history', methods=['GET'])
def get_chat_history():
    """獲取聊天記錄列表."""
    try:
        # 從資料目錄讀取所有聊天記錄
        history_path = os.path.join('data', 'chat_history')
        if not os.path.exists(history_path):
            os.makedirs(history_path)
            
        sessions = []
        for filename in os.listdir(history_path):
            if filename.endswith('.json'):
                with open(os.path.join(history_path, filename), 'r', encoding='utf-8') as f:
                    session = json.load(f)
                    sessions.append({
                        'id': session.get('id'),
                        'character_name': session.get('character_name'),
                        'world_name': session.get('world_name'),
                        'last_message': session.get('last_message'),
                        'timestamp': session.get('timestamp')
                    })
                    
        return jsonify({
            'status': 'success',
            'sessions': sorted(sessions, key=lambda x: x['timestamp'], reverse=True)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/chat_history/<session_id>', methods=['GET'])
def get_chat_session(session_id):
    """獲取特定聊天記錄的詳細內容."""
    try:
        file_path = os.path.join('data', 'chat_history', f'{session_id}.json')
        if not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'message': '找不到指定的聊天記錄'
            }), 404
            
        with open(file_path, 'r', encoding='utf-8') as f:
            session = json.load(f)
            
        return jsonify({
            'status': 'success',
            'session': session
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/world_templates', methods=['GET'])
def get_world_templates():
    """獲取世界觀模板列表."""
    try:
        with open('data/stories/story_templates.json', 'r', encoding='utf-8') as f:
            templates = json.load(f)
            formatted_templates = []
            for key, template in templates.items():
                formatted_templates.append({
                    'id': key,
                    'name': template['setting'],
                    'description': template['background'],
                    'tags': template['themes']
                })
                
        return jsonify({
            'status': 'success',
            'templates': formatted_templates
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/world_templates', methods=['POST'])
def create_world_template():
    """創建新的世界觀模板."""
    try:
        template_data = request.json
        template = {
            'setting': template_data['name'],
            'background': template_data['description'],
            'themes': template_data['tags'],
            'scenes': {
                'introduction': '故事的開始'
            }
        }
        
        with open('data/stories/story_templates.json', 'r+', encoding='utf-8') as f:
            templates = json.load(f)
            templates[template_data['id']] = template
            f.seek(0)
            json.dump(templates, f, ensure_ascii=False, indent=4)
            f.truncate()
            
        return jsonify({
            'status': 'success',
            'template': template
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/load_story', methods=['GET'])
def load_story():
    """載入已保存的故事."""
    try:
        story = story_controller.load_story()
        if story:
            return jsonify({
                'status': 'success',
                'story': story.to_dict(),
                'dialogue_history': story_controller.dialogue_history
            })
        return jsonify({
            'status': 'error',
            'message': '找不到已保存的故事'
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

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
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')  # 默認監聽所有網卡
    port = int(os.getenv('PORT', 5000))  # 默認端口 5000
    debug = os.getenv('DEBUG', 'True').lower() == 'true'  # 默認開啟調試模式
    socketio.run(app, host=host, port=port, debug=debug)
