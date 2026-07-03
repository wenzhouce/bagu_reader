import json
from tkinter import messagebox
from config_path import DB_FILE
import os
# 初始化题库数据库
def init_db():
    if not os.path.exists(DB_FILE):
        init_data = [
            {
                "category": "Java基础面试题",
                "items": [
                    {
                        "title": "String为什么设计成final不可变的?",
                        "md_content": "# String为什么是不可变\n## 1. 字符串常量池复用\n如果可变，池内字符串会互相污染，引发逻辑bug\n## 2. 线程安全\n不可变对象天然线程安全，无需同步锁\n## 3. 哈希缓存\nString重写hashCode，创建时缓存哈希值，作为HashMap键性能更好\n## 4. 安全参数\n网络请求、文件路径等参数不会被篡改"
                    }
                ]
            }
        ]
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(init_data, f, ensure_ascii=False, indent=2)

def load_db():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        messagebox.showerror("数据库损坏", "题库文件损坏，已重置为空白题库！")
        init_db()
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, ensure_ascii=False, fp=f, indent=2)