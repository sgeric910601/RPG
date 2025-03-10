"""故事API模組，提供故事相關的HTTP接口。"""

from flask import Blueprint, request, jsonify
from ..core.story import StoryManager
from ..utils.error import ValidationError, NotFoundError, handle_error

# 創建藍圖
story_bp = Blueprint('story', __name__)
story_manager = StoryManager()

@story_bp.route('/load', methods=['GET'])
def load_story():
    """加載當前故事狀態。"""
    try:
        current_state = story_manager.get_current_story()
        return jsonify({
            'status': 'success',
            'data': current_state
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': '加載故事狀態時發生錯誤', 'details': str(e)}), 500

@story_bp.route('/templates', methods=['GET'])
def get_templates():
    """獲取故事模板列表。"""
    try:
        # 返回預設模板列表
        templates = [
            {
                "id": "modern_mystery",
                "name": "現代都市懸疑",
                "description": "在現代都市中展開的神秘事件調查",
                "tags": ["懸疑", "現代", "都市"]
            },
            {
                "id": "fantasy_adventure",
                "name": "奇幻冒險",
                "description": "在魔法世界中展開的冒險故事",
                "tags": ["奇幻", "冒險", "魔法"]
            },
            {
                "id": "school_life",
                "name": "校園生活",
                "description": "發生在學校的日常故事",
                "tags": ["校園", "日常", "青春"]
            }
        ]
        
        return jsonify({
            'status': 'success',
            'data': {
                'templates': templates
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': '獲取故事模板時發生錯誤', 'details': str(e)}), 500

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
        return jsonify({'status': 'error', 'message': '獲取故事列表時發生錯誤', 'details': str(e)}), 500

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
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'獲取故事 {story_id} 時發生錯誤', 'details': str(e)}), 500

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
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': '創建故事時發生錯誤', 'details': str(e)}), 500

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
        return jsonify(handle_error(e))
    except ValidationError as e:
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'更新故事 {story_id} 時發生錯誤', 'details': str(e)}), 500

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
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'刪除故事 {story_id} 時發生錯誤', 'details': str(e)}), 500

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
        return jsonify(handle_error(e))
    except ValidationError as e:
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'添加角色到故事 {story_id} 時發生錯誤', 'details': str(e)}), 500

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
        return jsonify({'status': 'error', 'message': '創建默認故事時發生錯誤', 'details': str(e)}), 500
