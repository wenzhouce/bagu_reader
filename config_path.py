import os
import sys
import json
from pathlib import Path

# ========== 当前版本号 ==========
VERSION = "1.0.0"

# ========== 打包路径适配函数 ==========
def get_app_dir():
    """获取程序所在目录（用于源码运行）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(".")

def get_user_data_dir():
    """
    获取适合当前平台的用户数据目录（用于打包后的 EXE）。
    目录名固定为 'bagu_knowledge'，可自定义。
    """
    home = Path.home()
    if sys.platform == "win32":
        # Windows: %APPDATA%\bagu_knowledge
        base = os.environ.get("APPDATA")
        if not base:
            base = home / "AppData" / "Roaming"
        return Path(base) / "bagu_knowledge"
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/bagu_knowledge
        return home / "Library" / "Application Support" / "bagu_knowledge"
    else:
        # Linux/Unix: ~/.config/bagu_knowledge
        return home / ".config" / "bagu_knowledge"

# ========== 动态决定数据根目录 ==========
if getattr(sys, 'frozen', False):
    # 打包成 EXE 时，数据存到用户目录
    DATA_ROOT = get_user_data_dir()
else:
    # 源码运行时，数据存到程序所在目录
    DATA_ROOT = Path(get_app_dir())

# 确保数据目录存在
DATA_ROOT.mkdir(parents=True, exist_ok=True)

# 全局路径定义（基于 DATA_ROOT）
DB_FILE = DATA_ROOT / "bagu_db.json"
ASSET_DIR = DATA_ROOT / "assets"
CONFIG_FILE = DATA_ROOT / "config.json"

# 创建 assets 目录
ASSET_DIR.mkdir(parents=True, exist_ok=True)

# ========== 以下配置加载逻辑不变 ==========
DEFAULT_FONT_CFG = {
    "tree_font_size": 16,
    "ui_font_size": 12,
    "preview_title_size": 32,
    "preview_font_size": 23,
    "editor_font_size": 14,
    "preview_line_height": 1.9,
    "preview_padding_y": 24
}

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                for k, v in DEFAULT_FONT_CFG.items():
                    if k not in cfg:
                        cfg[k] = v
                return cfg
        except Exception:
            return DEFAULT_FONT_CFG.copy()
    return DEFAULT_FONT_CFG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, ensure_ascii=False, fp=f, indent=2)