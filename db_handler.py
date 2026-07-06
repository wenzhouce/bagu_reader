import json
import os
from tkinter import messagebox
from config_path import DB_FILE

def init_db():
    db_path = DB_FILE()
    if not os.path.exists(db_path):
        init_data = [
            {
                "category": "基础分类",
                "items": [
                    {
                        "title": "示例题目",
                        "md_content": "# 示例内容\n在这里编写你的笔记"
                    }
                ]
            }
        ]
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(init_data, f, ensure_ascii=False, indent=2)

def load_db():
    init_db()
    db_path = DB_FILE()
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("数据库损坏", f"题库文件损坏，已重置空白题库！\n错误：{str(e)}")
        init_db()
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)

def save_db(data):
    db_path = DB_FILE()
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, ensure_ascii=False, fp=f, indent=2)