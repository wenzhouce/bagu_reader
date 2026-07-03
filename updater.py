import json
import os
import sys
import tempfile
import threading
from tkinter import messagebox, ttk
from tkinter import Toplevel, Label
from urllib import request
from urllib.error import URLError
import subprocess
import time
import shutil
from urllib.parse import urlparse, quote  # 在文件顶部添加

# ==================== 配置 ====================
# 远程版本信息 URL（请务必使用 raw 链接）
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/wenzhouce/bagu_reader/main/version.json"

# ==================== 版本号比较 ====================
def compare_version(v1, v2):
    """
    比较两个版本号字符串（如 "1.0.10" 和 "1.0.2"）。
    返回 1 表示 v1 > v2，-1 表示 v1 < v2，0 表示相等。
    """
    def split(v):
        return [int(x) for x in v.split('.')]
    v1_parts = split(v1)
    v2_parts = split(v2)
    # 补齐长度
    while len(v1_parts) < len(v2_parts):
        v1_parts.append(0)
    while len(v2_parts) < len(v1_parts):
        v2_parts.append(0)
    for a, b in zip(v1_parts, v2_parts):
        if a > b:
            return 1
        elif a < b:
            return -1
    return 0

# ==================== 更新主流程 ====================
def check_for_updates(parent_window):
    """
    在后台线程中检查更新。
    如果发现新版本，会在主线程中弹出对话框。
    """
    # 非打包环境（源码运行）跳过更新检查
    # 测试时可以注释掉下面两行，方便调试
    if not getattr(sys, 'frozen', False):
        print("源码模式，跳过自动更新")
        return

    def _check():
        try:
            with request.urlopen(REMOTE_VERSION_URL, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                remote_version = data.get("version", "")
                download_url = data.get("download_url", "")
                release_notes = data.get("release_notes", "无更新说明")
        except Exception as e:
            print(f"检查更新失败: {e}")
            return

        from config_path import VERSION
        if remote_version and compare_version(remote_version, VERSION) > 0:
            # 有新版本
            def show_update_dialog():
                ans = messagebox.askyesno(
                    "发现新版本",
                    f"当前版本 v{VERSION}\n最新版本 v{remote_version}\n\n更新内容：\n{release_notes}\n\n是否立即下载并更新？"
                )
                if ans:
                    start_download(parent_window, download_url)
            parent_window.after(0, show_update_dialog)
        else:
            # 已是最新，静默
            pass

    threading.Thread(target=_check, daemon=True).start()

# ==================== 下载与替换 ====================
def start_download(parent_window, url):
    """
    显示下载进度条，下载新 EXE 到临时目录，然后启动更新程序。
    """
    # 创建下载进度弹窗
    progress_win = Toplevel(parent_window)
    progress_win.title("正在更新")
    progress_win.geometry("400x120")
    progress_win.resizable(False, False)
    progress_win.transient(parent_window)
    progress_win.grab_set()

    Label(progress_win, text="下载新版本中...", font=("微软雅黑", 11)).pack(pady=10)
    progress = ttk.Progressbar(progress_win, orient="horizontal", length=360, mode="determinate")
    progress.pack(pady=5)
    status_label = Label(progress_win, text="准备下载...", font=("微软雅黑", 9))
    status_label.pack(pady=5)

    def download():
        try:
            # 对包含中文的 URL 进行编码
            parsed = urlparse(url)
            encoded_path = quote(parsed.path, safe='/')
            encoded_url = parsed._replace(path=encoded_path).geturl()
            print(f"编码后 URL: {encoded_url}")  # 调试用

            # 下载文件到临时目录
            temp_dir = tempfile.gettempdir()
            exe_name = os.path.basename(url)  # 这里保持原始文件名（含中文）
            if not exe_name:
                exe_name = "bagu_reader_new.exe"
            temp_exe_path = os.path.join(temp_dir, exe_name)

            # 使用编码后的 URL 下载
            req = request.urlopen(encoded_url)
            total_size = int(req.headers.get('Content-Length', 0))
            block_size = 8192
            downloaded = 0
            with open(temp_exe_path, 'wb') as f:
                while True:
                    chunk = req.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        progress['value'] = percent
                        status_label.config(text=f"已下载 {percent}%")
                    progress_win.update_idletasks()
            # 下载完成
            status_label.config(text="下载完成，准备更新...")
            progress_win.update_idletasks()
            time.sleep(0.5)

            # 获取当前 EXE 路径（即 sys.executable）
            current_exe = sys.executable

            # 创建更新脚本（批处理），等待主进程退出后替换
            script_content = f"""
@echo off
timeout /t 3 /nobreak >nul
move /Y "{temp_exe_path}" "{current_exe}"
if errorlevel 1 (
    echo 替换失败，请手动替换
    pause
) else (
    start "" "{current_exe}"
)
del "%~f0"
"""
            script_path = os.path.join(temp_dir, "update_temp.bat")
            with open(script_path, "w", encoding="gbk") as f:
                f.write(script_content)

            # 启动更新脚本（隐藏窗口）
            subprocess.Popen(
                script_path,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            # 关闭进度窗口
            progress_win.destroy()
            # 退出主程序
            parent_window.quit()
            # 强制结束进程（可选）
            # sys.exit(0)
        except Exception as e:
            progress_win.destroy()
            messagebox.showerror("更新失败", f"下载或替换过程中出错：\n{str(e)}")

    threading.Thread(target=download, daemon=True).start()