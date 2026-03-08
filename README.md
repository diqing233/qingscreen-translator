# ScreenTranslator 屏幕翻译工具

基于 OCR 的屏幕翻译工具，支持框选任意屏幕区域进行翻译。

## 功能特性

- **框选翻译**：拖拽框选屏幕任意区域，OCR 识别后立即翻译
- **三种框模式**：
  - 临时翻译：翻译完成后自动消失（可设置时间）
  - 固定位置翻译：框保留在屏幕上，可手动/自动持续翻译
  - 多框翻译：在屏幕上放置多个翻译框
- **浮动结果条**：始终置顶的深色半透明显示栏，可拖动
- **多种翻译后端**：本地词典、谷歌翻译、百度翻译、DeepL、DeepSeek、OpenAI、Claude
- **AI 解释**：对单词或语句进行详细 AI 解释（需配置 AI API Key）
- **翻译历史**：记录所有翻译，支持搜索查看

## 安装

### 环境要求
- Python 3.10+
- Windows 10/11

### 安装依赖

```bash
pip install -r requirements.txt
```

### 下载 NLTK 词典数据（首次运行需要）

```bash
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

### 安装 PaddleOCR（可选，用于 OCR 识别）

```bash
pip install paddlepaddle paddleocr
```

> 如果不安装 PaddleOCR，将无法使用 OCR 功能。首次运行时 PaddleOCR 会自动下载模型文件（约 200MB）。

## 使用方法

### 启动

```bash
python src/main.py
```

启动后系统托盘会出现蓝色图标。

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Alt+Q` | 开始框选翻译 |
| `Alt+E` | 对当前翻译结果进行 AI 解释 |

### 首次配置

1. 右键托盘图标 → **设置**
2. 在**翻译来源**标签中勾选要使用的后端
3. 在 **API 密钥**标签中填写对应密钥
4. 保存设置

### 翻译后端配置

| 后端 | 是否需要 Key | 速度 | 说明 |
|------|------------|------|------|
| 本地词典 | 否 | ⚡ 极快 | 离线，适合单词查询 |
| 谷歌翻译 | 否 | 快 | 免费，需要网络 |
| 百度翻译 | 需要 AppID + Key | 快 | 免费额度，中文优化 |
| DeepL | 需要 Key（免费版可用）| 快 | 欧洲语言极准 |
| DeepSeek | 需要 Key（极便宜）| 中 | AI 翻译，高质量 |
| OpenAI | 需要 Key | 中 | GPT-4o-mini |
| Claude | 需要 Key | 中 | claude-haiku |

> 💡 提示：追求高效稳定？在设置中将配置好的 AI 翻译拖到免费 API 前面。

## 项目结构

```
src/
├── main.py              # 入口
├── core/
│   ├── controller.py    # 核心调度器
│   ├── settings.py      # 配置管理
│   ├── history.py       # 历史记录
│   └── box_manager.py   # 框实例管理
├── ui/
│   ├── selection_overlay.py  # 框选覆盖层
│   ├── translation_box.py    # 翻译框
│   ├── result_bar.py         # 结果显示条
│   ├── tray.py               # 系统托盘
│   ├── settings_window.py    # 设置窗口
│   └── history_window.py     # 历史窗口
├── ocr/
│   └── ocr_worker.py    # OCR/翻译/解释工作线程
└── translation/
    ├── router.py        # 翻译路由
    ├── dictionary.py    # 本地词典
    ├── google_trans.py  # 谷歌翻译
    ├── baidu_trans.py   # 百度翻译
    ├── deepl_trans.py   # DeepL
    └── ai_trans.py      # AI 翻译（DeepSeek/OpenAI/Claude）
```

## 数据存储

配置和历史记录保存在 `~/.screen_translator/` 目录：
- `settings.json`：设置文件
- `history.db`：翻译历史（SQLite）
- `app.log`：日志文件
