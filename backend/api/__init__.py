"""API模組，提供HTTP接口。"""

from flask import Blueprint
from .character import character_bp
from .story import story_bp
from .dialogue import dialogue_bp
from .prompt import prompt_bp

# 創建API藍圖
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 註冊子藍圖
api_bp.register_blueprint(character_bp, url_prefix='/characters')
api_bp.register_blueprint(story_bp, url_prefix='/stories')
api_bp.register_blueprint(dialogue_bp, url_prefix='/dialogues')
api_bp.register_blueprint(prompt_bp, url_prefix='/prompts')

# 導出藍圖
__all__ = ['api_bp']