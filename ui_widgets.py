import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import ttkbootstrap as bs
from ttkbootstrap.constants import *
from tkinterweb import HtmlFrame
import shutil
from config_path import load_config, save_config, ASSET_DIR
from db_handler import load_db, save_db
from utils import safe_asset_name, render_md_to_html
import os
from config_path import VERSION
class BaguApp(bs.Window):
    def __init__(self):
        super().__init__(themename="cosmo")
        self.title(f"我的八股知识库 v{VERSION} | 本地离线MD文档工具（无自动拖拽误触）")
        self.geometry("1660x920")
        self.place_window_center()
        self.dark_mode = False  # 初始为浅色
        # 加载全部样式配置
        self.font_cfg = load_config()
        self.tree_font_size = self.font_cfg["tree_font_size"]
        self.ui_font_size = self.font_cfg["ui_font_size"]
        self.preview_title_size = self.font_cfg["preview_title_size"]
        self.preview_font_size = self.font_cfg["preview_font_size"]
        self.editor_font_size = self.font_cfg["editor_font_size"]
        self.preview_line_height = self.font_cfg["preview_line_height"]
        self.preview_padding_y = self.font_cfg["preview_padding_y"]

        self.db_data = load_db()
        self.current_category_idx = None
        self.current_item_idx = None
        self.edit_win = None
        # 记录选中状态，刷新后恢复
        self.last_sel_cat = None
        self.last_sel_item = None

        # 全局统一UI控件字体大小
        self.style.configure(".", font=("微软雅黑", self.ui_font_size))
        # 树形行高样式
        self.update_tree_style()
        self.create_widgets()
        self.refresh_tree()
        self.restore_selection()

    # 更新树形字体+行高样式
    def update_tree_style(self):
        tree_font = ("微软雅黑", self.tree_font_size)
        row_h = int(self.tree_font_size * 2.3)
        self.style.configure("CustomTree.Treeview", font=tree_font, rowheight=row_h)
        self.style.map("CustomTree.Treeview", background=[("selected", "#4080d0")])

    def create_widgets(self):
        # 顶部总栏
        top_container = ttk.Frame(self)
        top_container.pack(fill=X, padx=12, pady=6)

        btn_frame = ttk.Frame(top_container)
        btn_frame.pack(side=LEFT)
        btn_frame = ttk.Frame(top_container)
        btn_frame.pack(side=LEFT)

        # 第一组：基础增删改
        ttk.Button(btn_frame, text="新增分类", command=self.add_category, bootstyle=SUCCESS, width=10).pack(side=LEFT,
                                                                                                            padx=2)
        ttk.Button(btn_frame, text="新增题目", command=self.add_item, bootstyle=PRIMARY, width=10).pack(side=LEFT,
                                                                                                        padx=2)
        ttk.Button(btn_frame, text="编辑内容", command=self.edit_item, bootstyle=INFO, width=10).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="删除选中", command=self.delete_selected, bootstyle=DANGER, width=10).pack(side=LEFT,
                                                                                                              padx=2)

        # 分隔线
        ttk.Separator(btn_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=6)

        # 第二组：导出、排序、重命名、移动
        ttk.Button(btn_frame, text="导出MD", command=self.export_md, bootstyle=SECONDARY, width=10).pack(side=LEFT,
                                                                                                         padx=2)
        ttk.Button(btn_frame, text="调整顺序", command=self.open_sort_window, bootstyle=WARNING, width=10).pack(
            side=LEFT, padx=2)
        ttk.Button(btn_frame, text="重命名分类", command=self.rename_category, bootstyle=INFO, width=10).pack(side=LEFT,
                                                                                                              padx=2)
        ttk.Button(btn_frame, text="移动题目", command=self.move_item, bootstyle=WARNING, width=10).pack(side=LEFT,
                                                                                                         padx=2)
        # 右侧搜索、主题、字体设置
        right_top_frame = ttk.Frame(top_container)
        right_top_frame.pack(side=RIGHT)
        ttk.Label(right_top_frame, text="搜索：").pack(side=LEFT, padx=3)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(right_top_frame, textvariable=self.search_var, width=28)
        search_entry.pack(side=LEFT, padx=3)
        search_entry.bind("<Return>", self.do_search)
        ttk.Button(right_top_frame, text="查找", command=self.do_search, bootstyle=OUTLINE, width=6).pack(side=LEFT, padx=3)
        ttk.Button(right_top_frame, text="切换深色/浅色", command=self.toggle_theme, bootstyle=LIGHT, width=14).pack(side=LEFT, padx=6)
        ttk.Button(right_top_frame, text="全局样式设置", command=self.open_font_setting, bootstyle=PRIMARY, width=12).pack(side=LEFT, padx=4)

        # 主分栏
        main_paned = ttk.PanedWindow(self, orient=HORIZONTAL)
        main_paned.pack(fill=BOTH, expand=True, padx=12, pady=6)

        # 左侧树形（加宽380，自定义样式）
        left_wrap = ttk.Frame(main_paned, width=380)
        main_paned.add(left_wrap, weight=1)
        ttk.Label(left_wrap, text="📚 八股分类目录（点击【调整顺序】手动移位）", font=("微软雅黑", 14, "bold")).pack(anchor=W, pady=3)
        self.tree = ttk.Treeview(left_wrap, show="tree", style="CustomTree.Treeview")
        self.tree.pack(fill=BOTH, expand=True, pady=4)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # 右侧预览
        right_wrap = ttk.Frame(main_paned)
        main_paned.add(right_wrap, weight=3)
        ttk.Label(right_wrap, text="📖 Markdown 实时预览", font=("微软雅黑", 14, "bold")).pack(anchor=W, pady=3)
        self.html_view = HtmlFrame(right_wrap, messages_enabled=False)
        self.html_view.pack(fill=BOTH, expand=True, pady=4)

    # 切换深浅主题
    def toggle_theme(self):
        current = self.style.theme_use()
        if current in ["cosmo", "minty"]:
            self.style.theme_use("darkly")
            self.dark_mode = True
        else:
            self.style.theme_use("cosmo")
            self.dark_mode = False

        # 重新应用 UI 字体（覆盖主题默认）
        self.style.configure(".", font=("微软雅黑", self.ui_font_size))
        # 更新树形样式
        self.update_tree_style()
        # 刷新预览
        self.on_tree_select(None)

    # 刷新目录树（修复父ID报错）
    def refresh_tree(self, keyword=""):
        self.tree.delete(*self.tree.get_children())
        kw = keyword.lower().strip()
        self.cat_id_map = {}
        if not kw:
            for cat_idx, cat in enumerate(self.db_data):
                cid = self.tree.insert("", END, text=f"📁 {cat['category']}", open=True, values=[str(cat_idx), "cat"])
                self.cat_id_map[cat_idx] = cid
                for item_idx, item in enumerate(cat["items"]):
                    self.tree.insert(cid, END, text=f"📝 {item['title']}", values=[str(cat_idx), "item", str(item_idx)])
            return
        for cat_idx, cat in enumerate(self.db_data):
            match_items = []
            for item_idx, item in enumerate(cat["items"]):
                title = item["title"].lower()
                content = item["md_content"].lower()
                if kw in title or kw in content:
                    match_items.append((item_idx, item["title"]))
            if match_items:
                cid = self.tree.insert("", END, text=f"📁 {cat['category']}", open=True, values=[str(cat_idx), "cat"])
                self.cat_id_map[cat_idx] = cid
                for item_idx, title in match_items:
                    self.tree.insert(cid, END, text=f"📝 {title}", values=[str(cat_idx), "item", str(item_idx)])

    # 刷新后恢复上次选中条目
    def restore_selection(self):
        if self.last_sel_cat is None:
            return
        cat_id = self.cat_id_map.get(self.last_sel_cat)
        if cat_id is None:
            return
        if self.last_sel_item is None:
            self.tree.selection_set(cat_id)
            self.tree.focus(cat_id)
            self.tree.see(cat_id)
            self.on_tree_select(None)
        else:
            children = self.tree.get_children(cat_id)
            for child in children:
                vals = self.tree.item(child, "values")
                if int(vals[2]) == self.last_sel_item:
                    self.tree.selection_set(child)
                    self.tree.focus(child)
                    self.tree.see(child)
                    self.on_tree_select(None)
                    break

    # 搜索
    def do_search(self, event=None):
        self.refresh_tree(self.search_var.get().strip())
        self.restore_selection()

    # 选中条目加载预览，记录当前选中
    def on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel:
            self.last_sel_cat = None
            self.last_sel_item = None
            tip_html = f"<h3 style='padding:{self.preview_padding_y}px;font-size:{self.preview_font_size}px;'>请点击下方【📝】题目查看详细八股内容</h3>"
            self.html_view.load_html(tip_html)
            return
        item = self.tree.item(sel[0])
        vals = item["values"]
        if vals[1] == "cat":
            self.last_sel_cat = int(vals[0])
            self.last_sel_item = None
            self.current_category_idx = self.last_sel_cat
            self.current_item_idx = None
            tip_html = f"<h3 style='padding:{self.preview_padding_y}px;font-size:{self.preview_font_size}px;'>请点击下方【📝】题目查看详细八股内容</h3>"
            self.html_view.load_html(tip_html)
        else:
            self.last_sel_cat = int(vals[0])
            self.last_sel_item = int(vals[2])
            self.current_category_idx = self.last_sel_cat
            self.current_item_idx = self.last_sel_item
            cat = self.db_data[self.current_category_idx]
            md_text = cat["items"][self.current_item_idx]["md_content"]
            html_str = render_md_to_html(md_text, self.font_cfg)
            self.html_view.load_html(html_str)

    # 新增分类
    def add_category(self):
        name = simpledialog.askstring("新增八股分类", prompt="输入分类名称（如Redis面试题、Java并发）")
        if not name:
            return
        self.db_data.append({"category": name, "items": []})
        save_db(self.db_data)
        self.last_sel_cat = len(self.db_data)-1
        self.last_sel_item = None
        self.refresh_tree()
        self.restore_selection()

    # 新增题目
    def add_item(self):
        if self.current_category_idx is None:
            messagebox.showwarning("提示", "请先在左侧选中一个分类文件夹！")
            return
        cat = self.db_data[self.current_category_idx]
        title = simpledialog.askstring("新增八股题目", prompt="输入面试题标题")
        if not title:
            return
        cat["items"].append({
            "title": title,
            "md_content": "# 在这里编写你的八股答案\n## 基础写法\n- 列表1\n- 列表2\n## 插入图片（自动缩放）\n![](./assets/xxx.jpg)\n## 自定义图片宽度\n<img src='./assets/xxx.jpg' width='600' />"
        })
        save_db(self.db_data)
        self.last_sel_item = len(cat["items"])-1
        self.refresh_tree()
        self.restore_selection()

    # 导出MD
    def export_md(self):
        if self.current_item_idx is None:
            messagebox.showwarning("提示", "请选中一条八股题目！")
            return
        cat = self.db_data[self.current_category_idx]
        item = cat["items"][self.current_item_idx]
        save_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown文件", "*.md")],
            initialfile=f"{item['title']}.md"
        )
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(f"# {item['title']}\n\n")
                f.write(item["md_content"])
            messagebox.showinfo("导出成功", f"文件已保存至：{save_path}")

    # 全局样式设置弹窗
    def open_font_setting(self):
        win = bs.Toplevel(self)
        win.title("全局样式设置（立即生效）")
        win.geometry("620x480")
        win.place_window_center()

        container = ttk.Frame(win)
        container.pack(padx=24, pady=16, fill=BOTH, expand=True)

        # 1. 顶部UI控件字体（搜索框、按钮）
        ttk.Label(container, text="1. 顶部按钮/搜索框UI字体大小：", font=("微软雅黑", 11)).pack(anchor=W, pady=6)
        ui_var = tk.IntVar(value=self.ui_font_size)
        ttk.Scale(container, from_=9, to=16, variable=ui_var, orient=HORIZONTAL).pack(fill=X, pady=2)

        # 2. 左侧目录树字体
        ttk.Label(container, text="2. 左侧分类目录字体大小：", font=("微软雅黑", 11)).pack(anchor=W, pady=6)
        tree_var = tk.IntVar(value=self.tree_font_size)
        ttk.Scale(container, from_=8, to=16, variable=tree_var, orient=HORIZONTAL).pack(fill=X, pady=2)

        # 3. 预览大标题字号
        ttk.Label(container, text="3. Markdown预览标题字号（一级标题）：", font=("微软雅黑", 11)).pack(anchor=W, pady=6)
        title_var = tk.IntVar(value=self.preview_title_size)
        ttk.Scale(container, from_=16, to=32, variable=title_var, orient=HORIZONTAL).pack(fill=X, pady=2)

        # 4. 预览正文字体
        ttk.Label(container, text="4. 右侧预览正文文字大小：", font=("微软雅黑", 11)).pack(anchor=W, pady=6)
        prev_var = tk.IntVar(value=self.preview_font_size)
        ttk.Scale(container, from_=12, to=26, variable=prev_var, orient=HORIZONTAL).pack(fill=X, pady=2)

        # 5. 预览行间距
        ttk.Label(container, text="5. 预览正文行间距（1.0紧凑~2.2宽松）：", font=("微软雅黑", 11)).pack(anchor=W, pady=6)
        line_var = tk.DoubleVar(value=self.preview_line_height)
        s_line = ttk.Scale(container, from_=1.0, to=2.2, variable=line_var, orient=HORIZONTAL)
        s_line.pack(fill=X, pady=2)

        # 6. 预览上下空白边距
        ttk.Label(container, text="6. 预览区域上下空白边距：", font=("微软雅黑", 11)).pack(anchor=W, pady=6)
        pad_var = tk.IntVar(value=self.preview_padding_y)
        ttk.Scale(container, from_=8, to=60, variable=pad_var, orient=HORIZONTAL).pack(fill=X, pady=2)

        # 7. 编辑弹窗Markdown输入框字体
        ttk.Label(container, text="7. 编辑弹窗Markdown输入框字体：", font=("微软雅黑", 11)).pack(anchor=W, pady=6)
        edit_var = tk.IntVar(value=self.editor_font_size)
        s_edit = ttk.Scale(container, from_=9, to=18, variable=edit_var, orient=HORIZONTAL)
        s_edit.pack(fill=X, pady=2)

        def save_all_style():
            self.ui_font_size = ui_var.get()
            self.tree_font_size = tree_var.get()
            self.preview_title_size = title_var.get()
            self.preview_font_size = prev_var.get()
            self.preview_line_height = round(line_var.get(), 1)
            self.preview_padding_y = pad_var.get()
            self.editor_font_size = edit_var.get()

            self.font_cfg.update({
                "ui_font_size": self.ui_font_size,
                "tree_font_size": self.tree_font_size,
                "preview_title_size": self.preview_title_size,
                "preview_font_size": self.preview_font_size,
                "preview_line_height": self.preview_line_height,
                "preview_padding_y": self.preview_padding_y,
                "editor_font_size": self.editor_font_size
            })
            save_config(self.font_cfg)
            self.update_tree_style()
            self.on_tree_select(None)
            messagebox.showinfo("保存成功", "全部样式已永久保存，新打开编辑窗口自动生效！")
            win.destroy()

        ttk.Button(win, text="保存并立即应用", bootstyle=SUCCESS, width=18, command=save_all_style).pack(pady=12)

    # 打开编辑窗口
    def edit_item(self):
        if self.current_item_idx is None:
            messagebox.showwarning("提示", "请选中一条八股题目！")
            return
        cat = self.db_data[self.current_category_idx]
        item = cat["items"][self.current_item_idx]
        self.open_editor(item, self.current_category_idx, self.current_item_idx)

    def open_editor(self, item, cat_idx, item_idx):
        if self.edit_win is not None:
            self.edit_win.destroy()
        self.edit_win = bs.Toplevel(self)
        self.edit_win.title(f"编辑八股：{item['title']} Markdown编辑器（Ctrl+Z撤销 Ctrl+Y重做）")
        self.edit_win.geometry("1150x780")
        self.edit_win.place_window_center()

        ttk.Label(self.edit_win, text="📌 题目标题", font=("微软雅黑",12,"bold")).pack(anchor=W, padx=14, pady=4)
        title_entry = ttk.Entry(self.edit_win, font=("微软雅黑", 12))
        title_entry.insert(0, item["title"])
        title_entry.pack(fill=X, padx=14, pady=2)

        ttk.Label(self.edit_win, text="✏️ Markdown 编辑区（Ctrl+Z撤销 / Ctrl+Y重做）", font=("微软雅黑",12,"bold")).pack(anchor=W, padx=14, pady=3)
        hint_frame = ttk.Frame(self.edit_win)
        hint_frame.pack(fill=X, padx=14, pady=2)
        ttk.Label(hint_frame,
                  text="⚠️ 多个空格会被折叠，请用 &nbsp; 或代码块保留空格（示例：`&nbsp;&nbsp;` 表示两个空格）",
                  font=("微软雅黑", 10), foreground="red").pack(anchor=W)
        md_text = bs.Text(self.edit_win, font=("Consolas", self.editor_font_size), undo=True)

        # def debug(event):
        #     print(
        #         "widget =", event.widget,
        #         "keysym =", event.keysym,
        #         "keycode =", event.keycode,
        #         "keysym_num =", event.keysym_num,
        #         "state =", event.state,
        #         "char =", repr(event.char)
        #     )
        #
        # md_text.bind("<KeyPress>", debug)
        md_text.insert(END, item["md_content"])
        md_text.pack(fill=BOTH, expand=True, padx=14, pady=4)

        bottom_bar = ttk.Frame(self.edit_win)
        bottom_bar.pack(fill=X, padx=14, pady=8)

        def insert_img():
            path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.webp")])
            if not path:
                return
            old_name = os.path.basename(path)
            new_name = safe_asset_name(old_name)
            target_path = os.path.join(ASSET_DIR, new_name)
            shutil.copy(path, target_path)
            snippet = f'\n<img src="./assets/{new_name}" width="700" />\n'
            md_text.insert(END, snippet)

        def insert_small_img():
            path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
            if not path:
                return
            old_name = os.path.basename(path)
            new_name = safe_asset_name(old_name)
            target_path = os.path.join(ASSET_DIR, new_name)
            shutil.copy(path, target_path)
            snippet = f'\n<img src="./assets/{new_name}" width="450" />\n'
            md_text.insert(END, snippet)

        def save_action():
            new_title = title_entry.get().strip()
            new_md = md_text.get("1.0", END).strip()
            if not new_title:
                messagebox.showerror("错误", "题目标题不能为空！")
                return
            self.db_data[cat_idx]["items"][item_idx]["title"] = new_title
            self.db_data[cat_idx]["items"][item_idx]["md_content"] = new_md
            save_db(self.db_data)
            self.refresh_tree()
            self.restore_selection()
            html_str = render_md_to_html(new_md, self.font_cfg)
            self.html_view.load_html(html_str)
            self.edit_win.destroy()
            messagebox.showinfo("保存成功", "八股内容已写入本地数据库！")

        ttk.Button(bottom_bar, text="保存全部修改", bootstyle=SUCCESS, width=16, command=save_action).pack(side=RIGHT, padx=6)
        ttk.Button(bottom_bar, text="插入大图(width700)", command=insert_img, bootstyle=INFO).pack(side=LEFT, padx=4)
        ttk.Button(bottom_bar, text="插入小图(width450)", command=insert_small_img, bootstyle=INFO).pack(side=LEFT, padx=4)

        def insert_nbsp():
            # 在光标位置插入 &nbsp;
            md_text.insert(INSERT, "&nbsp;")

        ttk.Button(bottom_bar, text="插入 &nbsp;", command=insert_nbsp, bootstyle=INFO).pack(side=LEFT, padx=4)
    # 删除分类/题目
    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        tree_item = self.tree.item(sel[0])
        vals = tree_item["values"]
        if vals[1] == "cat":
            cat_idx = int(vals[0])
            cat_name = self.db_data[cat_idx]["category"]
            if messagebox.askyesno("危险确认", f"确定删除分类「{cat_name}」？分类内所有八股题目将全部清除！"):
                del self.db_data[cat_idx]
        else:
            c_idx = int(vals[0])
            i_idx = int(vals[2])
            title = self.db_data[c_idx]["items"][i_idx]["title"]
            if messagebox.askyesno("确认删除", f"确定删除题目「{title}」？"):
                del self.db_data[c_idx]["items"][i_idx]
        save_db(self.db_data)
        self.refresh_tree()
        self.restore_selection()
        tip_html = f"<h3 style='padding:{self.preview_padding_y}px;font-size:{self.preview_font_size}px;'>请选择左侧八股题目查看内容</h3>"
        self.html_view.load_html(tip_html)

    # 手动调整顺序弹窗
    def open_sort_window(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选中需要移位的分类/题目！")
            return
        vals = self.tree.item(sel[0], "values")
        sort_win = bs.Toplevel(self)
        sort_win.title("手动调整条目顺序（上移/下移）")
        sort_win.geometry("420x160")
        sort_win.place_window_center()

        ttk.Label(sort_win, text="当前选中：" + self.tree.item(sel[0], "text"), font=("微软雅黑", 11)).pack(pady=12)
        btn_box = ttk.Frame(sort_win)
        btn_box.pack()

        def move_up():
            if vals[1] == "cat":
                idx = int(vals[0])
                if idx <= 0:
                    messagebox.showinfo("提示", "已经是第一条，无法上移")
                    return
                obj = self.db_data.pop(idx)
                self.db_data.insert(idx-1, obj)
                self.last_sel_cat = idx -1
            else:
                cid = int(vals[0])
                iid = int(vals[2])
                if iid <=0:
                    messagebox.showinfo("提示", "该分类第一条，无法上移")
                    return
                obj = self.db_data[cid]["items"].pop(iid)
                self.db_data[cid]["items"].insert(iid-1, obj)
                self.last_sel_cat = cid
                self.last_sel_item = iid -1
            save_db(self.db_data)
            self.refresh_tree()
            self.restore_selection()
            messagebox.showinfo("完成", "已向上移动一位")

        def move_down():
            if vals[1] == "cat":
                idx = int(vals[0])
                if idx >= len(self.db_data)-1:
                    messagebox.showinfo("提示", "最后一个分类，无法下移")
                    return
                obj = self.db_data.pop(idx)
                self.db_data.insert(idx+1, obj)
                self.last_sel_cat = idx +1
            else:
                cid = int(vals[0])
                iid = int(vals[2])
                item_list = self.db_data[cid]["items"]
                if iid >= len(item_list)-1:
                    messagebox.showinfo("提示", "该分类最后一题，无法下移")
                    return
                obj = item_list.pop(iid)
                item_list.insert(iid+1, obj)
                self.last_sel_cat = cid
                self.last_sel_item = iid +1
            save_db(self.db_data)
            self.refresh_tree()
            self.restore_selection()
            messagebox.showinfo("完成", "已向下移动一位")

        ttk.Button(btn_box, text="⬆ 上移", command=move_up, bootstyle=PRIMARY, width=10).pack(side=LEFT, padx=8)
        ttk.Button(btn_box, text="⬇ 下移", command=move_down, bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=8)
        ttk.Button(sort_win, text="关闭窗口", command=sort_win.destroy, bootstyle=SECONDARY).pack(pady=12)

    def rename_category(self):
        # 检查是否选中了一个分类（而不是题目）
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选中一个分类文件夹！")
            return
        item = self.tree.item(sel[0])
        vals = item["values"]
        if vals[1] != "cat":
            messagebox.showwarning("提示", "请选中一个分类，而不是题目！")
            return
        cat_idx = int(vals[0])
        old_name = self.db_data[cat_idx]["category"]
        new_name = simpledialog.askstring("重命名分类", f"将「{old_name}」更名为：", initialvalue=old_name)
        if not new_name or new_name == old_name:
            return
        self.db_data[cat_idx]["category"] = new_name
        save_db(self.db_data)
        self.refresh_tree()
        self.restore_selection()

    def move_item(self):
        # 检查是否选中了一个题目
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选中一个题目！")
            return
        item = self.tree.item(sel[0])
        vals = item["values"]
        if vals[1] != "item":
            messagebox.showwarning("提示", "请选中一个题目，而不是分类！")
            return
        src_cat_idx = int(vals[0])
        src_item_idx = int(vals[2])
        title = self.db_data[src_cat_idx]["items"][src_item_idx]["title"]

        # 列出所有可用的分类（排除当前分类？或允许移到同一分类，但无意义，可排除）
        cat_names = [f"{i + 1}. {cat['category']}" for i, cat in enumerate(self.db_data)]
        # 用下拉菜单让用户选择目标分类
        import tkinter.simpledialog as sd
        choice = sd.askstring("移动题目",
                              f"将「{title}」移动到哪个分类？\n\n请输入分类序号（1~{len(cat_names)}）：\n" + "\n".join(
                                  cat_names))
        if not choice:
            return
        try:
            target_idx = int(choice) - 1
            if target_idx < 0 or target_idx >= len(self.db_data):
                raise ValueError
        except:
            messagebox.showerror("错误", "请输入有效的序号！")
            return

        if target_idx == src_cat_idx:
            messagebox.showinfo("提示", "目标分类与当前相同，无需移动。")
            return

        # 执行移动：从源分类删除，插入到目标分类的末尾（或指定位置）
        item_obj = self.db_data[src_cat_idx]["items"].pop(src_item_idx)
        self.db_data[target_idx]["items"].append(item_obj)
        save_db(self.db_data)

        # 刷新并选中目标分类（可选）
        self.last_sel_cat = target_idx
        self.last_sel_item = len(self.db_data[target_idx]["items"]) - 1
        self.refresh_tree()
        self.restore_selection()
        messagebox.showinfo("完成", f"「{title}」已移动到「{self.db_data[target_idx]['category']}」")