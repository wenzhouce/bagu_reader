import os
import sys
import json
import shutil
from pathlib import Path

# ========== 当前版本号 ==========
VERSION = "1.0.1"
# 默认库文件名
DEFAULT_LIB_NAME = "bagu_db.json"
# 行测库默认名称
XINGCE_LIB_NAME = "xingce_db.json"
# 所有可选题库列表
LIB_LIST = [
    ("八股知识库", DEFAULT_LIB_NAME),
    ("行测题库", XINGCE_LIB_NAME)
]

# ========== 打包路径适配函数 ==========
def get_app_dir():
    """获取程序所在目录（用于源码运行）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(".")

def get_default_user_data_dir():
    """原始默认用户数据目录 bagu_knowledge"""
    home = Path.home()
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if not base:
            base = home / "AppData" / "Roaming"
        return Path(base) / "bagu_knowledge"
    elif sys.platform == "darwin":
        return home / "Library" / "Application Support" / "bagu_knowledge"
    else:
        return home / ".config" / "bagu_knowledge"

# ========== 全局运行时变量 ==========
DATA_ROOT: Path = None
CURR_LIB_FILE: str = DEFAULT_LIB_NAME

# ========== 动态获取路径函数（替代property） ==========
def get_db_file() -> Path:
    return DATA_ROOT / CURR_LIB_FILE

def get_asset_dir() -> Path:
    return DATA_ROOT / "assets"

def get_config_file() -> Path:
    return DATA_ROOT / "config.json"

# ========== 目录迁移工具函数 ==========
def migrate_all_data(old_root: Path, new_root: Path):
    """完整迁移旧目录全部数据到新目录"""
    if not old_root.exists():
        return True
    new_root.mkdir(parents=True, exist_ok=True)
    for item in old_root.iterdir():
        dst = new_root / item.name
        if item.is_dir():
            shutil.copytree(item, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dst)
    return True

# ========== 全局默认配置模板 ==========
DEFAULT_GLOBAL_CFG = {
    "custom_data_root": "",
    "current_lib": DEFAULT_LIB_NAME,
    "tree_font_size": 16,
    "ui_font_size": 12,
    "preview_title_size": 32,
    "preview_font_size": 23,
    "editor_font_size": 14,
    "preview_line_height": 1.9,
    "preview_padding_y": 24
}

def load_global_config():
    """加载全局配置，初始化DATA_ROOT、CURR_LIB_FILE"""
    global DATA_ROOT, CURR_LIB_FILE
    default_dir = get_default_user_data_dir()
    cfg_path = default_dir / "config.json"
    cfg = DEFAULT_GLOBAL_CFG.copy()

    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                cfg.update(loaded)
        except Exception:
            pass

    # 初始化存储根目录
    custom_path_str = cfg.get("custom_data_root", "").strip()
    if custom_path_str and Path(custom_path_str).exists():
        DATA_ROOT = Path(custom_path_str)
    else:
        DATA_ROOT = default_dir

    # 初始化当前库
    CURR_LIB_FILE = cfg.get("current_lib", DEFAULT_LIB_NAME)

    # 创建目录（这里调用函数获取真实Path对象）
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    asset_dir = get_asset_dir()
    asset_dir.mkdir(parents=True, exist_ok=True)
    return cfg

def save_global_config(cfg):
    """保存全局配置到config.json"""
    cfg_path = get_config_file()
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, ensure_ascii=False, fp=f, indent=2)

# 新增：修改当前选中库的全局方法
def set_current_lib(file_name: str):
    global CURR_LIB_FILE
    CURR_LIB_FILE = file_name

# 初始化全局路径配置（程序启动第一时间执行）
global_config = load_global_config()

# 对外导出路径获取方法，替换原来的DB_FILE/ASSET_DIR/CONFIG_FILE
DB_FILE = get_db_file
ASSET_DIR = get_asset_dir
CONFIG_FILE = get_config_file
