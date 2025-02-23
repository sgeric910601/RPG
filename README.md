# AI RPG 對話遊戲

一個基於AI的互動式RPG對話遊戲，支援多元化的角色互動和故事發展。

## 特色功能

- 多種預設世界觀（魔法學院、現代都市、未來太空站等）
- 支援自訂義世界觀和故事背景
- 多元化角色設定與互動
- 即時對話生成
- 動態對話選項
- 好感度系統
- 支援多個AI模型（GPT-4、Claude-2）
- 現代簡約的UI設計
- 角色立繪顯示
- 即時互動效果

## 系統需求

- Python 3.8+
- Node.js 14+（用於前端開發）
- 現代網頁瀏覽器

## 安裝步驟

1. 建立 Conda 環境：
```bash
conda create -n rpg python=3.8
conda activate rpg
```

2. 安裝依賴：
```bash
pip install -r requirements.txt
```

3. 設定環境變數：
```bash
cp .env.example .env
```
編輯 .env 文件，填入必要的API密鑰

4. 準備角色圖片：
將角色圖片放置在 `frontend/static/images/characters/` 目錄下

## 運行方式

1. 啟動服務器：
```bash
python app.py
```

2. 在瀏覽器中訪問：
```
http://localhost:5000
```

## 配置說明

### AI模型配置
在 `config/config.json` 中可以配置：
- 支援的AI模型
- 模型參數
- UI主題設定

### 角色配置
在 `data/characters/default_characters.json` 中可以：
- 修改預設角色設定
- 添加新角色
- 設定角色屬性

### 故事模板
在 `data/stories/story_templates.json` 中可以：
- 修改預設故事模板
- 添加新的世界觀設定
- 自定義場景描述

## 開發指南

### 目錄結構
```
RPG/
├── frontend/              # 前端文件
│   ├── static/           # 靜態資源
│   │   ├── css/         # 樣式文件
│   │   ├── js/          # JavaScript文件
│   │   └── images/      # 圖片資源
│   └── templates/        # HTML模板
├── backend/              # 後端文件
│   ├── models/          # 數據模型
│   ├── controllers/     # 控制器
│   └── utils/           # 工具函數
├── data/                # 數據文件
│   ├── characters/      # 角色數據
│   └── stories/        # 故事數據
└── config/             # 配置文件
```

### 擴展功能
1. 添加新角色：
   - 在 `data/characters/` 中添加角色配置
   - 在 `frontend/static/images/characters/` 中添加角色圖片

2. 添加新故事模板：
   - 在 `data/stories/` 中添加故事配置
   - 在前端添加相應的場景描述

3. 自定義UI主題：
   - 修改 `frontend/static/css/style.css`
   - 更新 `config/config.json` 中的主題配置

## 注意事項

- 請確保API密鑰安全，不要提交到版本控制系統
- 角色圖片需要遵守版權規定
- 限制級內容需要適當的內容警告
- 定期備份對話歷史和遊戲進度

## 授權說明

本項目採用 MIT 授權協議。
