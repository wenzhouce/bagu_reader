from db_handler import init_db
from ui_widgets import BaguApp
from updater import check_for_updates

if __name__ == "__main__":
    init_db()
    app = BaguApp()
    check_for_updates(app)   # 在 app.mainloop() 之前调用
    app.mainloop()
"""
bagu_know/
├── main.py                # 程序入口，启动窗口
├── config_path.py         # 路径、默认配置、文件读写工具函数
├── db_handler.py          # 数据库初始化/加载/保存
├── ui_widgets.py          # 主窗口类、所有界面渲染、交互逻辑
├── utils.py               # 通用工具（图片复制、文件名处理、MD渲染）
"""