# ScreenTranslator 设计文档

**日期：** 2026-03-09
**技术栈：** Python + PyQt5 + PaddleOCR
**平台：** Windows 11

---

## 一、项目概述

一款基于屏幕区域截图+OCR的翻译工具，支持框选任意屏幕区域进行翻译，提供透明虚线"框"覆盖层和深色浮动结果条，类似飞书截图框选+音乐播放器字幕条的组合体验。

---

## 二、整体架构

```
ScreenTranslator
├── SystemTray          # 托盘图标、右键菜单、全局入口
├── GlobalHotkeys       # 全局热键监听（pynput）
├── SettingsStore       # 配置持久化（JSON）
├── CoreController      # 核心调度器
│   ├── SelectionOverlay    # 全屏透明框选覆盖层
│   ├── BoxManager          # 管理所有"框"实例
│   │   └── TranslationBox  # 单个虚线框窗口
│   ├── ResultBar           # 深色浮动结果条
│   ├── OCRWorker           # PaddleOCR后台线程
│   ├── TranslationWorker   # 翻译API后台线程
│   └── HistoryDB           # SQLite历史记录
```

---

## 三、UI组件设计

### 3.1 SelectionOverlay（框选覆盖层）
- 全屏透明无边框窗口，覆盖所有内容
- 左键拖拽画出红色虚线矩形
- 松开左键 → 创建 TranslationBox，覆盖层自动消失
- ESC键 → 取消框选

### 3.2 TranslationBox（"框"）
```
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
  [🔄][📌][👁][✕]   ← 悬停显示控制按钮
│  半透明背景 + 虚线边框        │
   框内小字显示：识别到的原文
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```
- 🔄 立即翻译
- 📌 切换固定/临时模式
- 👁 隐藏框（不删除，可从托盘恢复）
- ✕ 关闭删除

**三种模式：**
| 模式 | 行为 |
|------|------|
| 临时翻译 | 翻译完成后N秒自动关闭（N可设置） |
| 固定翻译 | 框常驻，手动🔄或自动轮询翻译 |
| 多框模式 | 创建多个独立框，各自独立配置 |

### 3.3 ResultBar（结果条）
```
┌──────────────────────────────────────────────────────┐
│ ▶ ✏ ⚙  [EN → 简中] [手动]  ♪  🔓  🕐  🖼  ─  ✕   │
│ 译文: 那只敏捷的棕色狐狸跳过了那只懒狗...              │
│ [原文 ▼]  📋复制  💬AI解释  来源: DeepSeek            │
└──────────────────────────────────────────────────────┘
```
- 始终置顶，可自由拖动
- [原文 ▼] 折叠按钮，点击展开/收起原文
- 译文区域支持滚动（长文本）
- AI解释面板在ResultBar下方展开，不另开窗口

---

## 四、翻译引擎

### 4.1 后端列表
| 后端 | 类型 | 速度 | 适用场景 |
|------|------|------|---------|
| 本地词典（WordNet） | 免费离线 | ⚡极快 | 单词/短语 |
| 谷歌翻译（非官方） | 免费在线 | 快 | 通用文本 |
| 百度翻译API | 免费（需Key） | 快 | 中文场景 |
| DeepL免费版 | 免费（需Key） | 快 | 欧洲语言 |
| DeepSeek API | 付费（极便宜） | 中 | AI翻译+解释 |
| OpenAI GPT | 付费 | 中 | 高质量AI |
| Claude API | 付费 | 中 | 高质量AI |

### 4.2 智能路由
```
输入文字
  ├─ 单词/短语 (<5词) → 本地词典优先 → 失败则API
  ├─ 短文本 (<200字) → 免费API（按优先级顺序）
  └─ 长文本/需AI     → 配置的AI后端
```

---

## 五、设置项

```
通用设置
  ├─ 默认翻译方向：[自动检测] → [简体中文]
  ├─ 临时框消失时间：3 秒
  ├─ 固定框自动翻译间隔：2 秒
  └─ 全局热键：框选=[Alt+Q]  AI解释=[Alt+E]

翻译来源（拖拽排序优先级）
  💡 提示：追求高效稳定？可将已配置的AI翻译拖到免费API前面
  ├─ ✅ 本地词典
  ├─ ✅ 谷歌翻译
  ├─ ☐ 百度翻译  [AppID] [Key]
  ├─ ☐ DeepL     [Key]
  ├─ ☐ DeepSeek  [Key]
  ├─ ☐ OpenAI    [Key]
  └─ ☐ Claude    [Key]

结果条
  ├─ 显示位置：顶部/底部/自由拖动
  └─ 透明度：80%
```

---

## 六、AI解释功能

- 触发方式：点击ResultBar的[💬AI解释]按钮 或 按 Alt+E
- 支持对象：单个单词 / 短语 / 整句话
- 调用：配置的AI后端（DeepSeek/GPT/Claude）
- 展示：在ResultBar下方展开，不另开窗口

**单词示例输出：**
- 词条、含义、用法说明、例句

**句子示例输出：**
- 原句、含义、背景/语境说明

---

## 七、翻译历史

- 存储：SQLite（`history.db`）
- 字段：时间、原文、译文、来源、语言对
- 功能：搜索、清空、点击展开全文、复制、重新AI解释

---

## 八、项目目录结构

```
my-todo/
├── src/
│   ├── main.py                 # 入口，启动应用
│   ├── core/
│   │   ├── controller.py       # CoreController
│   │   ├── settings.py         # SettingsStore
│   │   └── history.py          # HistoryDB (SQLite)
│   ├── ui/
│   │   ├── tray.py             # SystemTray
│   │   ├── selection_overlay.py # 框选覆盖层
│   │   ├── translation_box.py  # 单个"框"
│   │   ├── result_bar.py       # 结果条
│   │   ├── settings_window.py  # 设置窗口
│   │   └── history_window.py   # 历史记录窗口
│   ├── ocr/
│   │   └── ocr_worker.py       # PaddleOCR后台线程
│   └── translation/
│       ├── router.py           # 智能路由
│       ├── google_trans.py     # 谷歌翻译
│       ├── baidu_trans.py      # 百度翻译
│       ├── deepl_trans.py      # DeepL
│       ├── dictionary.py       # 本地词典
│       └── ai_trans.py         # AI后端（DeepSeek/OpenAI/Claude）
├── docs/
│   └── plans/
│       └── 2026-03-09-screen-translator-design.md
├── requirements.txt
└── README.md
```

---

## 九、依赖库

```
PyQt5>=5.15
paddlepaddle
paddleocr
mss                  # 快速屏幕截图
pynput               # 全局热键
googletrans==4.0.0rc1
deepl
openai
anthropic
nltk                 # WordNet词典
requests
```
