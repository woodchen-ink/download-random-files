import requests
import os
import time
import hashlib
from urllib.parse import urlparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from concurrent.futures import ThreadPoolExecutor

class FilesDownloader:
    def __init__(self, url, save_dir, request_interval=1, max_workers=5, log_callback=None):
        self.url = url
        self.save_dir = save_dir
        self.request_interval = request_interval
        self.max_workers = max_workers
        self.headers = {
            # 浏览器标识
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
            
            # 接受的内容类型
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            
            # 接受的编码方式
            'Accept-Encoding': 'gzip, deflate, br',
            
            # 接受的语言
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            
            # 连接类型
            'Connection': 'keep-alive',
            
            # 缓存控制
            'Cache-Control': 'max-age=0',
            
            # DNT (Do Not Track)
            'DNT': '1',
            
            # 升级不安全请求
            'Upgrade-Insecure-Requests': '1',
            
            # 来源页面
            'Referer': 'https://www.google.com/',
            
            # SEC 相关头部
            'sec-ch-ua': '"Not A(Brand";v="24", "Chromium";v="110"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1'
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

    def download_image(self):
        if not self.is_running:
            return False
        
        try:
            response = requests.get(self.url, headers=self.headers, allow_redirects=True)
            if response.status_code == 200:
                image_url = response.url
                image_content = response.content
                
                image_hash = hashlib.md5(image_content).hexdigest()
                parsed_url = urlparse(image_url)
                file_extension = os.path.splitext(parsed_url.path)[1]
                if not file_extension:
                    file_extension = '.unknown'
                
                filename = f"{image_hash}{file_extension}"
                filepath = os.path.join(self.save_dir, filename)
                
                with self.lock:
                    if not os.path.exists(filepath):
                        with open(filepath, 'wb') as f:
                            f.write(image_content)
                        self.log(f"已下载: {filename}")
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
                futures = [executor.submit(self.download_image) for _ in range(self.max_workers)]
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
        self.master.geometry("800x600")  # 增加初始窗口大小
        self.master.minsize(800, 600)    # 设置最小窗口大小
        self.master.configure(bg='#f0f0f0')
        self.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.create_widgets()
        self.downloader = None

    def create_widgets(self):
        style = ttk.Style()
        style.theme_use('clam')

        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 输入区域框架
        input_frame = ttk.LabelFrame(main_frame, text="下载设置", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        # URL输入
        ttk.Label(input_frame, text="URL:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.url_entry = ttk.Entry(input_frame, width=60)
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky="we", padx=5, pady=5)
        self.url_entry.insert(0, "")

        # 保存目录
        ttk.Label(input_frame, text="保存目录:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.dir_entry = ttk.Entry(input_frame, width=50)
        self.dir_entry.grid(row=1, column=1, sticky="we", padx=5, pady=5)
        self.dir_entry.insert(0, "downloaded")
        ttk.Button(input_frame, text="浏览", command=self.browse_directory).grid(row=1, column=2, padx=5, pady=5)

        # 设置区域
        settings_frame = ttk.Frame(input_frame)
        settings_frame.grid(row=2, column=0, columnspan=3, pady=5)

        ttk.Label(settings_frame, text="请求间隔（秒）:").pack(side=tk.LEFT, padx=5)
        self.interval_entry = ttk.Entry(settings_frame, width=10)
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        self.interval_entry.insert(0, "1")

        ttk.Label(settings_frame, text="并发下载:").pack(side=tk.LEFT, padx=5)
        self.concurrent_entry = ttk.Entry(settings_frame, width=10)
        self.concurrent_entry.pack(side=tk.LEFT, padx=5)
        self.concurrent_entry.insert(0, "5")

        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)

        self.start_button = ttk.Button(button_frame, text="开始", command=self.start_download, width=15)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_download, width=15, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.config(state=tk.DISABLED)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)

    def log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def start_download(self):
        url = self.url_entry.get()
        save_dir = self.dir_entry.get()
        try:
            interval = float(self.interval_entry.get())
            max_workers = int(self.concurrent_entry.get())
        except ValueError:
            messagebox.showerror("Error", "间隔或并发下载值无效。请输入数字。")
            return

        self.downloader = FilesDownloader(url, save_dir, interval, max_workers, self.log)
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
            self.downloader.stop()
            self.stop_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
