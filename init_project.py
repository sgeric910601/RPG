#!/usr/bin/env python3
"""初始化專案腳本."""

import os
import json
import shutil
from pathlib import Path

def ensure_directories():
    """確保必要的目錄結構存在."""
    directories = [
        'frontend/static/css',
        'frontend/static/js',
        'frontend/static/images/characters',
        'frontend/templates',
        'backend/models',
        'backend/controllers',
        'backend/utils',
        'data/stories',
        'data/characters',
        'config'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f'確認目錄: {directory}')

def create_example_env():
    """創建範例環境變數文件."""
    if not os.path.exists('.env'):
        shutil.copy('.env.example', '.env')
        print('已創建 .env 文件')

def check_required_files():
    """檢查必要文件是否存在."""
    required_files = [
        'data/stories/story_templates.json',
        'data/characters/default_characters.json',
        'config/config.json',
        'frontend/static/css/style.css',
        'frontend/static/js/main.js',
        'frontend/templates/index.html',
        'backend/models/character.py',
        'backend/models/story.py',
        'backend/controllers/story_controller.py',
        'backend/utils/ai_handler.py',
        'app.py'
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f'警告: 缺少文件 {file_path}')
        else:
            print(f'確認文件: {file_path}')

def check_image_placeholders():
    """檢查角色圖片佔位符."""
    character_images = [
        'yuki.png',
        'akira.png',
        'rei.png'
    ]
    
    image_dir = Path('frontend/static/images/characters')
    for image in character_images:
        if not (image_dir / image).exists():
            print(f'警告: 缺少角色圖片 {image}')

def check_data_files():
    """檢查數據文件的有效性."""
    data_files = {
        'data/stories/story_templates.json': '故事模板',
        'data/characters/default_characters.json': '預設角色',
        'config/config.json': '配置文件'
    }
    
    for file_path, desc in data_files.items():
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                print(f'驗證{desc}成功: {file_path}')
            else:
                print(f'警告: 缺少{desc}文件')
        except json.JSONDecodeError:
            print(f'錯誤: {desc}文件格式無效')

def main():
    """主函數."""
    print('開始初始化專案...')
    
    ensure_directories()
    create_example_env()
    check_required_files()
    check_image_placeholders()
    check_data_files()
    
    print('\n初始化完成!')
    print('請確保:')
    print('1. 設置 .env 中的必要環境變數')
    print('2. 添加缺少的角色圖片')
    print('3. 檢查並修復任何警告或錯誤')

if __name__ == '__main__':
    main()
