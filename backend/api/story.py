"""故事API模組，提供故事相關的HTTP接口。"""

from flask import Blueprint, request, jsonify
from ..core.story import StoryManager
from ..utils.error import ValidationError, NotFoundError, handle_error

# 創建藍圖
story_bp = Blueprint('story', __name__)
story_manager = StoryManager()

@story_bp.route('/load', methods=['GET'])
def load_story():
    """加載當前故事狀態。
    
    返回格式：
    {
        "status": "success",
        "data": {
            "story": {
                "id": "故事ID",
                "title": "故事標題",
                "current_character": {
                    "name": "角色名稱",
                    ...
                },
                ...
            },
            "dialogue_history": [
                {"role": "user", "content": "用戶消息"},
                {"role": "assistant", "content": "AI回應"}
            ]
        }
    }
    """
    try:
        current_state = story_manager.get_current_story()
        return jsonify({
            'status': 'success',
            'data': current_state
        })
    except Exception as e:
        return handle_error(e, '加載故事狀態時發生錯誤')

@story_bp.route('/', methods=['GET'])
def get_all_stories():
    """獲取所有故事的摘要信息。"""
    try:
        stories = story_manager.get_all_stories()
        return jsonify({
            'status': 'success',
            'data': {
                'stories': stories
            }
        })
    except Exception as e:
        return handle_error(e, '獲取故事列表時發生錯誤')

@story_bp.route('/<story_id>', methods=['GET'])
def get_story(story_id):
    """獲取指定ID的故事。"""
    try:
        story = story_manager.get_story(story_id)
        return jsonify({
            'status': 'success',
            'data': {
                'story': story
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到故事: {story_id}')
    except Exception as e:
        return handle_error(e, f'獲取故事 {story_id} 時發生錯誤')

@story_bp.route('/', methods=['POST'])
def create_story():
    """創建新故事。"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '缺少請求體'
            }), 400
        
        story = story_manager.create_story(data)
        return jsonify({
            'status': 'success',
            'data': {
                'story': story
            }
        }), 201
    except ValidationError as e:
        return handle_error(e, '創建故事時驗證失敗')
    except Exception as e:
        return handle_error(e, '創建故事時發生錯誤')

@story_bp.route('/<story_id>', methods=['PUT'])
def update_story(story_id):
    """更新故事。"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '缺少請求體'
            }), 400
        
        story = story_manager.update_story(story_id, data)
        return jsonify({
            'status': 'success',
            'data': {
                'story': story
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到故事: {story_id}')
    except ValidationError as e:
        return handle_error(e, '更新故事時驗證失敗')
    except Exception as e:
        return handle_error(e, f'更新故事 {story_id} 時發生錯誤')

@story_bp.route('/<story_id>', methods=['DELETE'])
def delete_story(story_id):
    """刪除故事。"""
    try:
        story_manager.delete_story(story_id)
        return jsonify({
            'status': 'success',
            'message': f'故事 {story_id} 已刪除'
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到故事: {story_id}')
    except Exception as e:
        return handle_error(e, f'刪除故事 {story_id} 時發生錯誤')

@story_bp.route('/<story_id>/characters', methods=['POST'])
def add_character_to_story(story_id):
    """添加角色到故事中。"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '缺少請求體'
            }), 400
        
        story = story_manager.add_character_to_story(story_id, data)
        return jsonify({
            'status': 'success',
            'data': {
                'story': story
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到故事: {story_id}')
    except ValidationError as e:
        return handle_error(e, '添加角色時驗證失敗')
    except Exception as e:
        return handle_error(e, f'添加角色到故事 {story_id} 時發生錯誤')

@story_bp.route('/default', methods=['POST'])
def create_default_story():
    """創建默認故事。"""
    try:
        story = story_manager.create_default_story()
        return jsonify({
            'status': 'success',
            'data': {
                'story': story
            }
        }), 201
    except Exception as e:
        return handle_error(e, '創建默認故事時發生錯誤')