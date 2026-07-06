import os
import uuid
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from pathlib import Path
from config_path import ASSET_DIR
import re

def safe_asset_name(origin_name):
    suffix = origin_name.split(".")[-1]
    new_name = f"{uuid.uuid4().hex}.{suffix}"
    return new_name

# Markdown转HTML渲染函数
def render_md_to_html(md_text, font_cfg, dark_mode=False):
    extensions = ["fenced_code", "tables", "nl2br", CodeHiliteExtension(linenums=False, css_class="codehilite")]
    raw_html = markdown.markdown(md_text, extensions=extensions)
    # 去掉 CodeHilite 自动生成的空 span（修复顶部空行）
    raw_html = raw_html.replace("<span></span>", "")
    # 去除代码块末尾多余换行
    raw_html = re.sub(
        r'(<code[^>]*>)([\s\S]*?)\n(</code>)',
        lambda m: m.group(1) + m.group(2).rstrip("\n") + m.group(3),
        raw_html,
        flags=re.S
    )
    # ========== 修复点：加括号调用ASSET_DIR() ==========
    asset_path = ASSET_DIR()
    asset_uri = asset_path.as_uri() + "/"
    raw_html = raw_html.replace('src="./assets/', f'src="{asset_uri}')

    # 专为 tkinterweb 优化的语法高亮 CSS（模拟 VSCode 浅色主题）
    pygments_css = """
    /* 代码块容器 */
    .codehilite {
        background: #f5f7fa;
        border-radius: 6px;
        padding: 0;
        margin: 8px 0;
        overflow-x: auto;
    }
    .codehilite pre {
        margin: 0;
        padding: 12px;
        background: #f5f7fa;
        border: none;
        font-family: Consolas, "Courier New", monospace;
        font-size: 15px;
        white-space: pre;
        overflow-x: auto;
    }
    .codehilite code {
        font-family: Consolas, "Courier New", monospace;
        font-size: inherit;
    }
    /* 关键字 */
    .k { color: #0000FF; font-weight: bold; }
    .kc { color: #0000FF; font-weight: bold; }
    .kd { color: #0000FF; font-weight: bold; }
    .kn { color: #0000FF; font-weight: bold; }
    .kp { color: #0000FF; font-weight: bold; }
    .kr { color: #0000FF; font-weight: bold; }
    .kt { color: #2B91AF; }
    /* 字符串 */
    .s { color: #A31515; }
    .s1 { color: #A31515; }
    .s2 { color: #A31515; }
    .sb { color: #A31515; }
    .sc { color: #A31515; }
    .sd { color: #A31515; }
    .se { color: #A31515; }
    .sh { color: #A31515; }
    .si { color: #A31515; }
    .sr { color: #A31515; }
    .ss { color: #A31515; }
    /* 注释 */
    .c { color: #008000; font-style: italic; }
    .c1 { color: #008000; font-style: italic; }
    .cm { color: #008000; font-style: italic; }
    .cp { color: #008000; font-style: italic; }
    .cs { color: #008000; font-style: italic; }
    /* 函数/方法 */
    .nf { color: #795E26; }
    .nb { color: #267F99; }
    .na { color: #795E26; }
    .nc { color: #2B91AF; }
    .no { color: #795E26; }
    /* 操作符、标点 */
    .o { color: #000000; }
    .p { color: #000000; }
    /* 数字 */
    .m { color: #098658; }
    .mf { color: #098658; }
    .mh { color: #098658; }
    .mi { color: #098658; }
    .mo { color: #098658; }
    .il { color: #098658; }
    /* 变量 */
    .n { color: #000000; }
    .v { color: #001080; }
    .vm { color: #001080; }
    .vc { color: #001080; }
    .vg { color: #001080; }
    .vi { color: #001080; }
    /* 特殊 */
    .err { color: #FF0000; }
    .w { color: #888888; }
    """

    full_html = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        /* 插入手写的 Pygments 兼容样式 */
        {pygments_css}

        /* 通用样式 */
        body {{
            font-family: "微软雅黑", SimHei;
            font-size: {font_cfg["preview_font_size"]}px;
            line-height: {font_cfg["preview_line_height"]};
            padding: {font_cfg["preview_padding_y"]}px;
            margin: 0;
        }}
        h1 {{ font-size: {font_cfg["preview_title_size"]}px; }}
        h2 {{ font-size: {max(font_cfg["preview_title_size"] - 4, font_cfg["preview_font_size"] + 2)}px; }}
        h3 {{ font-size: {max(font_cfg["preview_title_size"] - 8, font_cfg["preview_font_size"])}px; }}
        p {{ margin:8px 0; }}
        ul, ol {{ padding-left:24px; }}
        .codehilite {{
            background: #f5f7fa;
            border-radius: 6px;
            padding: 0;
            margin: 8px 0;
            overflow-x: auto;
        }}
        .codehilite pre {{
            margin: 0;
            padding: 12px;
            background: #f5f7fa;
            border: none;
            font-family: Consolas, "Courier New", monospace;
            font-size: {font_cfg["preview_font_size"]}px;
            white-space: pre;
            overflow-x: auto;
        }}
        .codehilite code {{
            font-family: Consolas, "Courier New", monospace;
            font-size: inherit;
        }}
        pre {{ margin: 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
        td, th {{ border: 1px solid #ddd; padding: 8px 12px; }}
        img {{ max-width: 100%; border-radius: 8px; margin: 8px 0; }}
    </style>
    </head>
    <body>{raw_html}</body>
    </html>
    """
    return full_html