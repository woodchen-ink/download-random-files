import requests
import os
import time
import hashlib
import json
from urllib.parse import urlparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from concurrent.futures import ThreadPoolExecutor


class FilesDownloader:
    def __init__(
        self,
        url,
        save_dir,
        request_interval=1,
        max_workers=5,
        log_callback=None,
        is_json_mode=False,
        json_path="data",
    ):
        self.url = url
        self.save_dir = save_dir
        self.request_interval = request_interval
        self.max_workers = max_workers
        self.is_json_mode = is_json_mode
        self.json_path = json_path
        self.headers = {
            # 浏览器标识
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
            # 接受的内容类型
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            # 接受的编码方式
            "Accept-Encoding": "gzip, deflate, br",
            # 接受的语言
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            # 连接类型
            "Connection": "keep-alive",
            # 缓存控制
            "Cache-Control": "max-age=0",
            # DNT (Do Not Track)
            "DNT": "1",
            # 升级不安全请求
            "Upgrade-Insecure-Requests": "1",
            # 来源页面
            "Referer": "https://www.google.com/",
            # SEC 相关头部
            "sec-ch-ua": '"Not A(Brand";v="24", "Chromium";v="110"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
        }
        self.consecutive_duplicates = 0
        self.is_running = False
        self.log_callback = log_callback
        self.download_count = 0
        self.lock = threading.Lock()

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def get_image_url_from_json(self, response):
        try:
            json_data = response.json()
            path_parts = self.json_path.split(".")
            value = json_data
            for part in path_parts:
                value = value[part]
            if isinstance(value, str):
                return value
            else:
                self.log(f"JSON 路径 '{self.json_path}' 不是字符串值")
                return None
        except (json.JSONDecodeError, KeyError) as e:
            self.log(f"解析 JSON 错误: {str(e)}")
            return None

    def download_image(self):
        if not self.is_running:
            return False

        try:
            response = requests.get(
                self.url, headers=self.headers, allow_redirects=True
            )
            if response.status_code == 200:
                if self.is_json_mode:
                    image_url = self.get_image_url_from_json(response)
                    if not image_url:
                        return True  # 继续尝试下载

                    # 获取真实图片内容
                    image_response = requests.get(image_url, headers=self.headers)
                    if image_response.status_code != 200:
                        self.log(
                            f"下载图片失败，URL: {image_url}，状态码: {image_response.status_code}"
                        )
                        return True

                    image_content = image_response.content
                    parsed_url = urlparse(image_url)
                else:
                    image_url = response.url
                    image_content = response.content
                    parsed_url = urlparse(image_url)

                image_hash = hashlib.md5(image_content).hexdigest()
                file_extension = os.path.splitext(parsed_url.path)[1]
                if not file_extension:
                    file_extension = ".unknown"

                filename = f"{image_hash}{file_extension}"
                filepath = os.path.join(self.save_dir, filename)

                with self.lock:
                    if not os.path.exists(filepath):
                        with open(filepath, "wb") as f:
                            f.write(image_content)
                        self.log(f"已下载: {filename} ({image_url})")
                        self.consecutive_duplicates = 0
                        self.download_count += 1
                    else:
                        self.log(f"已跳过: {filename} (已经存在)")
                        self.consecutive_duplicates += 1
            else:
                self.log(f"下载文件失败。状态码: {response.status_code}")
        except Exception as e:
            self.log(f"发生错误: {str(e)}")

        return self.consecutive_duplicates < 20

    def run(self):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        self.is_running = True
        self.consecutive_duplicates = 0
        self.download_count = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while self.is_running:
                futures = [
                    executor.submit(self.download_image)
                    for _ in range(self.max_workers)
                ]
                if not all(future.result() for future in futures):
                    self.is_running = False
                    self.log("检测到 20 个连续重复项。停止下载过程。")
                    break
                time.sleep(self.request_interval)

        self.log(f"下载过程完成。总下载量: {self.download_count}")

    def stop(self):
        self.is_running = False


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("302文件下载器")
        self.master.geometry("800x700")  # 增加窗口高度以适应更多内容
        self.master.minsize(800, 700)
        self.master.configure(bg="#f5f5f5")  # 更改背景色为浅灰色
        self.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.create_widgets()
        self.downloader = None

    def create_widgets(self):
        # 配置样式
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TLabelframe", background="#f5f5f5")
        style.configure(
            "TLabelframe.Label", font=("微软雅黑", 10, "bold"), background="#f5f5f5"
        )
        style.configure("TButton", font=("微软雅黑", 10), background="#e1e1e1")
        style.configure("TLabel", font=("微软雅黑", 10), background="#f5f5f5")
        style.configure("TCheckbutton", background="#f5f5f5")
        style.configure("Info.TLabelframe", background="#e8f4f8", padding=10)
        style.configure(
            "Info.TLabelframe.Label",
            font=("微软雅黑", 10, "bold"),
            background="#e8f4f8",
        )
        style.configure(
            "Primary.TButton", font=("微软雅黑", 10, "bold"), background="#4a86e8"
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#3a76d8"), ("pressed", "#2a66c8")],
            foreground=[("active", "white"), ("pressed", "white")],
        )

        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        title_label = ttk.Label(
            title_frame, text="302文件下载器", font=("微软雅黑", 16, "bold")
        )
        title_label.pack(pady=10)
        subtitle_label = ttk.Label(
            title_frame,
            text="支持直接或通过JSON响应获取的文件下载",
            font=("微软雅黑", 10),
        )
        subtitle_label.pack()

        # 输入区域框架
        input_frame = ttk.LabelFrame(main_frame, text="下载设置", padding=15)
        input_frame.pack(fill=tk.X, padx=5, pady=10)

        # URL输入
        ttk.Label(input_frame, text="URL:").grid(
            row=0, column=0, sticky="e", padx=5, pady=8
        )
        self.url_entry = ttk.Entry(input_frame, width=60, font=("微软雅黑", 10))
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky="we", padx=5, pady=8)
        self.url_entry.insert(0, "")

        # 保存目录
        ttk.Label(input_frame, text="保存目录:").grid(
            row=1, column=0, sticky="e", padx=5, pady=8
        )
        self.dir_entry = ttk.Entry(input_frame, width=50, font=("微软雅黑", 10))
        self.dir_entry.grid(row=1, column=1, sticky="we", padx=5, pady=8)
        self.dir_entry.insert(0, "downloaded")
        browse_btn = ttk.Button(input_frame, text="浏览", command=self.browse_directory)
        browse_btn.grid(row=1, column=2, padx=5, pady=8)

        # JSON模式选择
        self.is_json_mode = tk.BooleanVar(value=False)
        json_check_frame = ttk.Frame(input_frame)
        json_check_frame.grid(row=2, column=0, sticky="w", padx=5, pady=8)

        # 使用标准tk.Checkbutton而不是ttk.Checkbutton，解决样式问题
        self.json_check = tk.Checkbutton(
            json_check_frame,
            text="JSON响应模式",
            variable=self.is_json_mode,
            command=self.toggle_json_mode,
            font=("微软雅黑", 10),
            bg="#f5f5f5",
            activebackground="#f5f5f5",
        )
        self.json_check.pack(side=tk.LEFT)

        # 添加问号图标和悬停提示
        help_icon = ttk.Label(
            json_check_frame, text="?", cursor="hand2", font=("微软雅黑", 9, "bold")
        )
        help_icon.pack(side=tk.LEFT, padx=5)
        help_icon.bind("<Enter>", self.show_json_help)
        help_icon.bind("<Leave>", self.hide_json_help)

        # JSON路径设置
        json_path_frame = ttk.Frame(input_frame)
        json_path_frame.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=8)

        ttk.Label(json_path_frame, text="JSON 字段路径:").pack(side=tk.LEFT, padx=5)
        self.json_path_entry = ttk.Entry(
            json_path_frame, width=20, font=("微软雅黑", 10)
        )
        self.json_path_entry.pack(side=tk.LEFT, padx=5)
        self.json_path_entry.insert(0, "data")
        self.json_path_entry.config(state=tk.DISABLED)  # 初始禁用

        # JSON帮助信息框
        self.json_help_frame = ttk.LabelFrame(
            input_frame, text="JSON模式说明", style="Info.TLabelframe"
        )
        self.json_help_text = tk.Text(
            self.json_help_frame,
            height=4,
            width=70,
            wrap=tk.WORD,
            font=("微软雅黑", 9),
            bg="#e8f4f8",
            relief=tk.FLAT,
        )
        self.json_help_text.pack(fill=tk.BOTH, padx=5, pady=5)
        self.json_help_text.insert(
            tk.END,
            "JSON响应模式用于处理返回JSON数据的API，而不是直接返回文件的URL。\n"
            "• 字段路径：指定JSON中图片URL所在的字段路径，如 'data' 或 'data.url'\n"
            '• 示例JSON: {"code": 200, "data": "https://example.com/image.jpg"}\n'
            "• 支持多级路径：使用点号分隔，如 'result.data.url'",
        )
        self.json_help_text.configure(state=tk.DISABLED)
        self.json_help_frame.grid(
            row=3, column=0, columnspan=3, sticky="we", padx=5, pady=5
        )
        self.json_help_frame.grid_remove()  # 默认隐藏

        # 设置区域
        settings_frame = ttk.Frame(input_frame)
        settings_frame.grid(row=4, column=0, columnspan=3, pady=10)

        ttk.Label(settings_frame, text="请求间隔（秒）:").pack(side=tk.LEFT, padx=5)
        self.interval_entry = ttk.Entry(settings_frame, width=10, font=("微软雅黑", 10))
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        self.interval_entry.insert(0, "1")

        ttk.Label(settings_frame, text="并发下载:").pack(side=tk.LEFT, padx=20)
        self.concurrent_entry = ttk.Entry(
            settings_frame, width=10, font=("微软雅黑", 10)
        )
        self.concurrent_entry.pack(side=tk.LEFT, padx=5)
        self.concurrent_entry.insert(0, "5")

        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=15)

        self.start_button = ttk.Button(
            button_frame,
            text="开始下载",
            command=self.start_download,
            width=15,
            style="Primary.TButton",
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="停止下载",
            command=self.stop_download,
            width=15,
            state=tk.DISABLED,
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="下载日志", padding=15)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=10)

        # 日志头部信息
        log_header = ttk.Frame(log_frame)
        log_header.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(
            log_header, text="状态信息和下载记录将显示在下方：", font=("微软雅黑", 9)
        ).pack(anchor=tk.W)

        # 日志文本区
        self.log_area = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=12, font=("微软雅黑", 9)
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.config(state=tk.DISABLED)

        # 底部状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=5)
        ttk.Label(status_frame, text="302文件下载器 v1.1", font=("微软雅黑", 8)).pack(
            side=tk.RIGHT
        )

    def show_json_help(self, event):
        self.json_help_frame.grid()

    def hide_json_help(self, event):
        self.json_help_frame.grid_remove()

    def toggle_json_mode(self):
        if self.is_json_mode.get():
            self.json_path_entry.config(state=tk.NORMAL)
        else:
            self.json_path_entry.config(state=tk.DISABLED)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)

    def log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def start_download(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("错误", "请输入有效的URL")
            return

        save_dir = self.dir_entry.get()
        is_json_mode = self.is_json_mode.get()
        json_path = self.json_path_entry.get()

        if is_json_mode and not json_path:
            messagebox.showerror("错误", "JSON模式下必须指定字段路径")
            return

        try:
            interval = float(self.interval_entry.get())
            max_workers = int(self.concurrent_entry.get())

            if interval <= 0:
                raise ValueError("间隔必须大于0")
            if max_workers <= 0:
                raise ValueError("并发数必须大于0")

        except ValueError as e:
            messagebox.showerror("错误", f"输入值无效: {str(e)}")
            return

        self.log(f"开始下载{'JSON模式' if is_json_mode else '直接模式'} - URL: {url}")
        if is_json_mode:
            self.log(f"JSON路径设置为: {json_path}")

        self.downloader = FilesDownloader(
            url=url,
            save_dir=save_dir,
            request_interval=interval,
            max_workers=max_workers,
            log_callback=self.log,
            is_json_mode=is_json_mode,
            json_path=json_path,
        )

        self.download_thread = threading.Thread(target=self.downloader.run)
        self.download_thread.daemon = True  # 设置为守护线程
        self.download_thread.start()

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_download)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def monitor_download(self):
        while self.download_thread.is_alive():
            time.sleep(0.5)
        # 下载结束后自动恢复按钮状态
        self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)

    def stop_download(self):
        if self.downloader:
            self.log("正在停止下载过程...")
            self.downloader.stop()
            self.stop_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
