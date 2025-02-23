"""RPG遊戲主程式."""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import json
import os
from typing import Dict, List
from dotenv import load_dotenv
from backend.utils.ai_handler import AIHandler
from backend.controllers.story_controller import StoryController
from backend.models.character import Character
from backend.models.story import Story

# 載入環境變數
load_dotenv()

app = Flask(__name__, 
    template_folder='frontend/templates',
    static_folder='frontend/static')
socketio = SocketIO(app, cors_allowed_origins="*")

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key')

# 初始化AI處理器和故事控制器
ai_handler = AIHandler()
story_controller = StoryController(ai_handler)

@app.route('/')
def index():
    """渲染主頁面."""
    return render_template('index.html')

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
        if not story_controller.current_story:
            raise ValueError("沒有活躍的故事")
            
        if not data.get('character'):
            raise ValueError("未指定角色")
            
        response, choices = story_controller.process_user_input(
            user_input=data['message'],
            current_character=data['character']
        )
        
        # 獲取更新後的角色資料
        character = story_controller.current_story.characters.get(data['character'])
        if not character:
            raise ValueError(f"找不到角色: {data['character']}")
        
        socketio.emit('receive_message', {
            'status': 'success',
            'message': response,
            'character': character.to_dict(),
            'choices': choices
        })
    except Exception as e:
        socketio.emit('receive_message', {
            'status': 'error',
            'message': f"處理消息時發生錯誤: {str(e)}"
        })

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

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """獲取故事模板."""
    try:
        with open('data/stories/story_templates.json', 'r', 
                 encoding='utf-8') as f:
            templates = json.load(f)
        return jsonify(templates)
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
                'story': story.to_dict()
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

if __name__ == '__main__':
    socketio.run(app, debug=True)
