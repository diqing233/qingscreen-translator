from __future__ import annotations

from html import escape
from pathlib import Path


DEFAULT_OUTPUT_PATH = Path("docs/previews/result-bar-button-preview.html")


DIRECTIONS = (
    {
        "id": "calm",
        "name": "Calm Hierarchy",
        "summary": "保留深色桌面工具感，重点强化主次、风险和展开状态。",
        "tokens": {
            "bg": "#121722",
            "bg_alt": "#18202e",
            "surface": "rgba(17, 23, 35, 0.82)",
            "surface_strong": "rgba(20, 28, 43, 0.94)",
            "line": "rgba(202, 222, 255, 0.12)",
            "text": "#edf3ff",
            "muted": "#92a0be",
            "glow": "rgba(90, 152, 255, 0.22)",
            "primary": "#4a84ec",
            "primary_hover": "#6196f6",
            "active": "#3b4e78",
            "ai": "#4f9f88",
            "danger": "#bb6546",
            "danger_hover": "#d97450",
            "neutral": "#2a3244",
            "neutral_hover": "#344057",
            "ghost": "rgba(255, 255, 255, 0.08)",
        },
    },
    {
        "id": "functional",
        "name": "Functional Color",
        "summary": "按功能语义分色，让开始、AI、工具、风险一眼可分。",
        "tokens": {
            "bg": "#10161e",
            "bg_alt": "#1a232c",
            "surface": "rgba(16, 23, 31, 0.84)",
            "surface_strong": "rgba(20, 30, 40, 0.95)",
            "line": "rgba(214, 232, 255, 0.12)",
            "text": "#eff8ff",
            "muted": "#9db1c5",
            "glow": "rgba(37, 99, 235, 0.24)",
            "primary": "#2f7ef9",
            "primary_hover": "#4f94ff",
            "active": "#295ab1",
            "ai": "#159a8a",
            "danger": "#d15a45",
            "danger_hover": "#ed6d58",
            "neutral": "#334251",
            "neutral_hover": "#415569",
            "ghost": "rgba(255, 255, 255, 0.09)",
        },
    },
)


BUTTON_GROUPS = (
    {
        "title": "Start & Session",
        "description": "启动、停止与会话层级，主动作最强，风险动作最热。",
        "buttons": (
            ("开始框选", "primary"),
            ("停止/清空", "danger"),
            ("恢复大小", "subtle"),
            ("自动 / 手动", "mode"),
        ),
    },
    {
        "title": "Modes & Languages",
        "description": "模式和语种需要稳态清晰，但不应压过翻译内容。",
        "buttons": (
            ("框选模式", "mode"),
            ("AI 模式", "ai"),
            ("源语言", "neutral"),
            ("目标语言", "neutral"),
        ),
    },
    {
        "title": "Toolbar Utilities",
        "description": "复制、历史、设置和编号显示属于辅助工具，保持安静但可感知。",
        "buttons": (
            ("复制译文", "neutral"),
            ("复制原文", "neutral"),
            ("历史", "ghost"),
            ("设置", "ghost"),
            ("段落编号", "subtle"),
        ),
    },
    {
        "title": "Source & Explain",
        "description": "原文、重新翻译、AI 科普需要体现可编辑流程和次级展开关系。",
        "buttons": (
            ("原文", "subtle"),
            ("重新翻译", "primary"),
            ("AI 科普", "split"),
        ),
    },
    {
        "title": "Window Controls",
        "description": "窗口级控制保持轻量，只有关闭进入明显风险反馈。",
        "buttons": (
            ("最小化", "ghost"),
            ("关闭", "ghost-danger"),
        ),
    },
)


STATE_ORDER = ("normal", "hover", "pressed", "active", "disabled")


def _token_style(tokens: dict[str, str]) -> str:
    return "; ".join(f"--{key.replace('_', '-')}: {value}" for key, value in tokens.items())


def _button_markup(label: str, tone: str, state: str = "normal", extra: str = "") -> str:
    state_class = "" if state == "normal" else f" is-{state}"
    data_state = escape(state)
    return (
        f'<button class="btn tone-{escape(tone)}{state_class}" data-state="{data_state}" '
        f'type="button">{escape(label)}{extra}</button>'
    )


def _state_board(direction: dict[str, object]) -> str:
    groups = []
    for group in BUTTON_GROUPS:
        cells = []
        for label, tone in group["buttons"]:
            states = "".join(
                f"""
                <div class="state-cell">
                  <div class="state-label">{escape(state)}</div>
                  {_button_markup(label, tone, state, " ▾" if label in {"源语言", "目标语言"} else "")}
                </div>
                """
                for state in STATE_ORDER
            )
            cells.append(
                f"""
                <article class="button-card">
                  <header>
                    <h4>{escape(label)}</h4>
                    <p>{escape(group["description"])}</p>
                  </header>
                  <div class="state-grid">{states}</div>
                </article>
                """
            )

        groups.append(
            f"""
            <section class="lab-group">
              <div class="lab-group-heading">
                <h3>{escape(group["title"])}</h3>
                <p>{escape(group["description"])}</p>
              </div>
              <div class="button-card-grid">
                {''.join(cells)}
              </div>
            </section>
            """
        )

    return f"""
    <section class="direction-lab" style="{_token_style(direction['tokens'])}">
      <div class="section-heading">
        <span class="eyebrow">Button Function Lab</span>
        <h2>{escape(direction['name'])}</h2>
        <p>{escape(direction['summary'])}</p>
      </div>
      {''.join(groups)}
    </section>
    """


def _mockup(direction: dict[str, object]) -> str:
    name = escape(direction["name"])
    summary = escape(direction["summary"])
    identifier = escape(direction["id"])
    return f"""
    <article class="preview-shell" data-preview="full-mockup" data-direction="{identifier}" style="{_token_style(direction['tokens'])}">
      <div class="preview-topline">
        <div>
          <span class="eyebrow">Direction</span>
          <h2>{name}</h2>
        </div>
        <p>{summary}</p>
      </div>
      <div class="toolbar-row">
        <div class="toolbar-group">
          {_button_markup("▶", "primary")}
          {_button_markup("■", "danger")}
          {_button_markup("↺", "subtle")}
          {_button_markup("固定", "mode")}
          {_button_markup("AI", "ai")}
        </div>
        <div class="toolbar-group">
          {_button_markup("AUTO ▾", "neutral")}
          {_button_markup("简中 ▾", "neutral")}
          {_button_markup("复制", "neutral")}
        </div>
        <div class="toolbar-group toolbar-group-right">
          <div class="toggle-pill">
            <span class="is-on">手动</span>
            <span>自动</span>
          </div>
          {_button_markup("历史", "ghost")}
          {_button_markup("设置", "ghost")}
          {_button_markup("—", "ghost")}
          {_button_markup("×", "ghost-danger")}
        </div>
      </div>
      <div class="content-wrap">
        <div class="translation-panel">
          <div class="translation-meta">
            <span class="meta-pill">EN → 简中</span>
            <span class="meta-pill meta-pill-soft">test backend</span>
          </div>
          <div class="translation-copy">
            <h3>Translate once, inspect twice.</h3>
            <p>
              这块是接近真实结果栏的内容区，用来看按钮层级是否会压过译文本身。
            </p>
          </div>
          <div class="action-row">
            <div class="action-left">
              {_button_markup("原文 ▾", "subtle")}
              {_button_markup("复制原文", "neutral")}
              {_button_markup("翻译", "primary is-scene-enabled")}
            </div>
            <div class="action-right">
              {_button_markup("AI 科普 ▸", "split")}
              {_button_markup("[#]", "subtle")}
            </div>
          </div>
        </div>
        <div class="expand-panel source-panel">
          <div class="panel-heading">
            <span class="panel-tag">Source</span>
            <span>OCR 原文可编辑区域</span>
          </div>
          <p>Hover over the controls to check whether expanded actions still stay secondary.</p>
        </div>
        <div class="expand-panel ai-panel">
          <div class="panel-heading">
            <span class="panel-tag panel-tag-ai">AI</span>
            <span>Explain panel remains a lower-priority expansion.</span>
          </div>
          <p>AI panel should read as helpful detail, not the primary CTA.</p>
        </div>
      </div>
    </article>
    """


def build_preview_html() -> str:
    mockups = "".join(_mockup(direction) for direction in DIRECTIONS)
    labs = "".join(_state_board(direction) for direction in DIRECTIONS)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ScreenTranslator Button Style Preview</title>
  <style>
    :root {{
      color-scheme: dark;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Aptos", "Segoe UI", "Trebuchet MS", sans-serif;
      background:
        radial-gradient(circle at top, rgba(98, 128, 180, 0.24), transparent 32%),
        linear-gradient(180deg, #0b1018 0%, #101722 48%, #0a0f16 100%);
      color: #edf3ff;
    }}

    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px);
      background-size: 48px 48px;
      mask-image: linear-gradient(180deg, rgba(255,255,255,0.7), transparent 90%);
    }}

    .page {{
      position: relative;
      width: min(1440px, calc(100vw - 40px));
      margin: 0 auto;
      padding: 32px 0 48px;
    }}

    .hero {{
      display: grid;
      gap: 18px;
      padding: 24px 28px;
      border: 1px solid rgba(232, 240, 255, 0.12);
      border-radius: 24px;
      background: linear-gradient(135deg, rgba(16, 22, 32, 0.92), rgba(18, 28, 44, 0.7));
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
      backdrop-filter: blur(18px);
    }}

    .hero h1 {{
      margin: 0;
      font-size: clamp(32px, 5vw, 54px);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }}

    .hero p {{
      margin: 0;
      max-width: 76ch;
      color: #b7c6df;
      line-height: 1.6;
      font-size: 15px;
    }}

    .hero-grid {{
      display: grid;
      grid-template-columns: 1.5fr 1fr;
      gap: 18px;
      align-items: end;
    }}

    .summary-panel {{
      padding: 16px 18px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .summary-panel strong {{
      display: block;
      margin-bottom: 8px;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: #92a0be;
    }}

    .scene-switcher {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 8px;
    }}

    .scene-chip {{
      appearance: none;
      border: 1px solid rgba(255, 255, 255, 0.14);
      background: rgba(255, 255, 255, 0.06);
      color: #edf3ff;
      padding: 10px 14px;
      border-radius: 999px;
      cursor: pointer;
      transition: background 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
    }}

    .scene-chip:hover,
    .scene-chip.is-active {{
      background: rgba(80, 132, 236, 0.18);
      border-color: rgba(132, 176, 255, 0.5);
      box-shadow: 0 0 0 3px rgba(80, 132, 236, 0.14);
    }}

    .section {{
      margin-top: 28px;
    }}

    .section-heading {{
      margin-bottom: 18px;
    }}

    .section-heading h2,
    .section-heading h3,
    .preview-topline h2,
    .button-card h4 {{
      margin: 0;
    }}

    .section-heading p,
    .preview-topline p,
    .button-card p,
    .panel-heading + p {{
      margin: 0;
      color: var(--muted, #9db1c5);
      line-height: 1.6;
    }}

    .eyebrow {{
      display: inline-block;
      margin-bottom: 8px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: #8fa4c6;
    }}

    .compare-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}

    .preview-shell,
    .direction-lab {{
      border: 1px solid var(--line);
      border-radius: 24px;
      background: linear-gradient(160deg, var(--surface) 0%, var(--surface-strong) 100%);
      box-shadow: 0 18px 64px rgba(0, 0, 0, 0.28);
      overflow: hidden;
    }}

    .preview-shell {{
      padding: 22px;
    }}

    .preview-topline {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: end;
      margin-bottom: 16px;
    }}

    .preview-topline p {{
      max-width: 34ch;
      text-align: right;
    }}

    .toolbar-row,
    .action-row {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .toolbar-row {{
      align-items: center;
      padding: 12px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid rgba(255, 255, 255, 0.07);
    }}

    .toolbar-group,
    .action-left,
    .action-right {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }}

    .toolbar-group-right {{
      margin-left: auto;
    }}

    .toggle-pill {{
      display: inline-flex;
      padding: 3px;
      gap: 3px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.07);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .toggle-pill span {{
      padding: 6px 12px;
      border-radius: 999px;
      color: var(--muted);
      font-size: 12px;
    }}

    .toggle-pill .is-on {{
      background: var(--primary);
      color: white;
    }}

    .content-wrap {{
      margin-top: 14px;
      display: grid;
      gap: 12px;
    }}

    .translation-panel,
    .expand-panel {{
      padding: 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .translation-meta,
    .panel-heading {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }}

    .meta-pill,
    .panel-tag {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.06);
      color: var(--text);
      border: 1px solid rgba(255, 255, 255, 0.08);
      font-size: 12px;
    }}

    .meta-pill-soft {{
      color: var(--muted);
    }}

    .panel-tag-ai {{
      background: color-mix(in srgb, var(--ai) 24%, transparent);
    }}

    .translation-copy {{
      margin: 14px 0 18px;
    }}

    .translation-copy h3 {{
      margin: 0 0 10px;
      font-size: 22px;
      letter-spacing: -0.03em;
    }}

    .translation-copy p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
    }}

    .btn {{
      appearance: none;
      border: 1px solid transparent;
      border-radius: 12px;
      padding: 9px 14px;
      min-height: 40px;
      background: var(--neutral);
      color: var(--text);
      font: inherit;
      font-size: 13px;
      line-height: 1;
      cursor: pointer;
      transition: background 180ms ease, border-color 180ms ease, box-shadow 180ms ease, color 180ms ease, opacity 180ms ease;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
      white-space: nowrap;
    }}

    .btn.tone-primary {{
      background: color-mix(in srgb, var(--primary) 78%, var(--bg-alt));
      border-color: color-mix(in srgb, var(--primary-hover) 62%, transparent);
      color: white;
    }}

    .btn.tone-danger {{
      background: color-mix(in srgb, var(--danger) 82%, var(--bg-alt));
      border-color: color-mix(in srgb, var(--danger-hover) 62%, transparent);
      color: white;
    }}

    .btn.tone-mode {{
      background: color-mix(in srgb, var(--active) 84%, var(--bg-alt));
      border-color: color-mix(in srgb, var(--primary) 44%, transparent);
      color: white;
    }}

    .btn.tone-ai {{
      background: color-mix(in srgb, var(--ai) 80%, var(--bg-alt));
      border-color: color-mix(in srgb, var(--ai) 54%, white 4%);
      color: white;
    }}

    .btn.tone-neutral {{
      background: color-mix(in srgb, var(--neutral) 88%, var(--bg));
      border-color: var(--line);
      color: var(--text);
    }}

    .btn.tone-subtle {{
      background: color-mix(in srgb, var(--ghost) 80%, var(--bg));
      border-color: rgba(255, 255, 255, 0.08);
      color: var(--text);
    }}

    .btn.tone-ghost {{
      background: transparent;
      border-color: rgba(255, 255, 255, 0.08);
      color: var(--muted);
    }}

    .btn.tone-ghost-danger {{
      background: transparent;
      border-color: rgba(255, 255, 255, 0.08);
      color: var(--muted);
    }}

    .btn.tone-split {{
      background:
        linear-gradient(90deg, color-mix(in srgb, var(--ai) 22%, var(--neutral)) 0 78%, rgba(255,255,255,0.08) 78% 79%, color-mix(in srgb, var(--ai) 16%, var(--neutral)) 79% 100%);
      border-color: rgba(255, 255, 255, 0.1);
      color: var(--text);
      padding-right: 26px;
      position: relative;
    }}

    .btn.tone-split::after {{
      content: "▾";
      position: absolute;
      right: 10px;
      top: 50%;
      transform: translateY(-48%);
      color: var(--muted);
    }}

    .btn:hover,
    .btn.is-hover {{
      background: color-mix(in srgb, currentColor 0%, var(--neutral-hover) 100%);
      border-color: color-mix(in srgb, var(--primary) 28%, rgba(255, 255, 255, 0.18));
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--glow) 75%, transparent);
    }}

    .btn.tone-primary:hover,
    .btn.tone-primary.is-hover {{
      background: var(--primary-hover);
    }}

    .btn.tone-danger:hover,
    .btn.tone-danger.is-hover,
    .btn.tone-ghost-danger.is-hover,
    .btn.tone-ghost-danger:hover {{
      background: color-mix(in srgb, var(--danger) 22%, transparent);
      border-color: color-mix(in srgb, var(--danger-hover) 58%, transparent);
      color: white;
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--danger) 26%, transparent);
    }}

    .btn.is-pressed {{
      box-shadow: inset 0 2px 12px rgba(0, 0, 0, 0.35);
      filter: saturate(0.95);
    }}

    .btn.is-active {{
      border-color: color-mix(in srgb, var(--primary) 54%, rgba(255,255,255,0.18));
      background: color-mix(in srgb, var(--active) 88%, var(--bg-alt));
      color: white;
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--glow) 80%, transparent);
    }}

    .btn.is-disabled {{
      opacity: 0.45;
      cursor: default;
      box-shadow: none;
    }}

    body[data-scene="busy"] .preview-shell .toolbar-row .btn.tone-danger {{
      background: var(--danger-hover);
      border-color: color-mix(in srgb, var(--danger-hover) 58%, white 6%);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--danger) 24%, transparent);
    }}

    body[data-scene="idle"] .preview-shell .action-row .btn.tone-primary,
    body[data-scene="busy"] .preview-shell .action-row .btn.tone-primary {{
      opacity: 0.45;
      box-shadow: none;
    }}

    body[data-scene="source"] .preview-shell .action-row .btn.tone-primary,
    body[data-scene="explain"] .preview-shell .action-row .btn.tone-primary {{
      opacity: 1;
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--glow) 80%, transparent);
    }}

    body[data-scene="source"] .preview-shell .action-left .btn.tone-subtle:first-child,
    body[data-scene="explain"] .preview-shell .action-left .btn.tone-subtle:first-child {{
      border-color: color-mix(in srgb, var(--primary) 45%, transparent);
      background: color-mix(in srgb, var(--active) 78%, var(--bg-alt));
      color: white;
    }}

    body[data-scene="explain"] .preview-shell .action-right .btn.tone-split {{
      border-color: color-mix(in srgb, var(--ai) 58%, transparent);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--ai) 22%, transparent);
    }}

    .source-panel,
    .ai-panel {{
      display: none;
    }}

    body[data-scene="source"] .source-panel,
    body[data-scene="explain"] .source-panel {{
      display: block;
    }}

    body[data-scene="explain"] .ai-panel {{
      display: block;
    }}

    .labs {{
      display: grid;
      gap: 18px;
    }}

    .direction-lab {{
      padding: 22px;
    }}

    .lab-group + .lab-group {{
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid var(--line);
    }}

    .lab-group-heading {{
      margin-bottom: 14px;
    }}

    .button-card-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}

    .button-card {{
      padding: 14px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .button-card header {{
      margin-bottom: 12px;
    }}

    .state-grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
    }}

    .state-cell {{
      display: grid;
      gap: 8px;
    }}

    .state-label {{
      font-size: 11px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
    }}

    @media (max-width: 1100px) {{
      .hero-grid,
      .compare-grid,
      .button-card-grid,
      .state-grid {{
        grid-template-columns: 1fr;
      }}

      .preview-topline {{
        align-items: start;
        flex-direction: column;
      }}

      .preview-topline p {{
        text-align: left;
      }}
    }}
  </style>
</head>
<body data-scene="idle">
  <main class="page">
    <section class="hero">
      <div class="hero-grid">
        <div>
          <span class="eyebrow">ScreenTranslator Button Style Preview</span>
          <h1>两套按钮语言，同一套结果栏场景。</h1>
          <p>
            这个页面不是单纯的按钮板，而是把结果栏的工具栏、动作栏、原文面板和 AI 面板一起放进来，
            让你同时判断整体氛围和单个按钮的语义强弱。
          </p>
        </div>
        <div class="summary-panel">
          <strong>How to read this preview</strong>
          <p>上半部分看整体，上下文里比较 Calm Hierarchy 与 Functional Color。下半部分逐个看每一类按钮在 normal、hover、pressed、active、disabled 下的表现。</p>
        </div>
      </div>
      <div class="scene-switcher" aria-label="Preview scenes">
        <button class="scene-chip is-active" data-scene-target="idle" type="button">Idle</button>
        <button class="scene-chip" data-scene-target="busy" type="button">Busy</button>
        <button class="scene-chip" data-scene-target="source" type="button">Source Expanded</button>
        <button class="scene-chip" data-scene-target="explain" type="button">Explain Expanded</button>
      </div>
    </section>

    <section class="section">
      <div class="section-heading">
        <span class="eyebrow">Full Mockups</span>
        <h2>Result Bar Context</h2>
        <p>同一个结构，两种按钮语义。先看它们在真实布局里的压迫感、信息层级和功能识别速度。</p>
      </div>
      <div class="compare-grid">
        {mockups}
      </div>
    </section>

    <section class="section">
      <div class="section-heading">
        <span class="eyebrow">State Boards</span>
        <h2>Button Function Breakdown</h2>
        <p>这里把每一类功能按状态拆开，方便你检查哪些按钮太吵、哪些按钮不够明确。</p>
      </div>
      <div class="labs">
        {labs}
      </div>
    </section>
  </main>
  <script>
    const body = document.body;
    const chips = Array.from(document.querySelectorAll(".scene-chip"));
    for (const chip of chips) {{
      chip.addEventListener("click", () => {{
        body.dataset.scene = chip.dataset.sceneTarget;
        for (const other of chips) {{
          other.classList.toggle("is-active", other === chip);
        }}
      }});
    }}
  </script>
</body>
</html>
"""


def write_preview(output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_preview_html(), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    path = write_preview()
    print(path)
