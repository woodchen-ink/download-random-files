import requests
import os
import time
import hashlib
from urllib.parse import urlparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading

class ImageDownloader:
    def __init__(self, url, save_dir, request_interval=1, log_callback=None):
        self.url = url
        self.save_dir = save_dir
        self.request_interval = request_interval
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0'
        }
        self.consecutive_duplicates = 0
        self.is_running = False
        self.log_callback = log_callback
        
    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def download_image(self):
        try:
            response = requests.get(self.url, headers=self.headers, allow_redirects=True)
            if response.status_code == 200:
                image_url = response.url
                image_content = response.content
                
                image_hash = hashlib.md5(image_content).hexdigest()
                
                parsed_url = urlparse(image_url)
                file_extension = os.path.splitext(parsed_url.path)[1]
                
                filename = f"{image_hash}{file_extension}"
                filepath = os.path.join(self.save_dir, filename)
                
                if not os.path.exists(filepath):
                    with open(filepath, 'wb') as f:
                        f.write(image_content)
                    self.log(f"Downloaded: {filename}")
                    self.consecutive_duplicates = 0
                else:
                    self.log(f"Skipped: {filename} (already exists)")
                    self.consecutive_duplicates += 1
            else:
                self.log(f"Failed to download image. Status code: {response.status_code}")
        except Exception as e:
            self.log(f"An error occurred: {str(e)}")
    
    def run(self):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        self.is_running = True
        i = 0
        while self.is_running:
            self.download_image()
            if self.consecutive_duplicates >= 10:
                self.log("Detected 10 consecutive duplicates. Stopping the download process.")
                break
            time.sleep(self.request_interval)
            i += 1
        
        self.log(f"Download process completed. Total attempts: {i}")

    def stop(self):
        self.is_running = False

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("Image Downloader")
        self.master.geometry("600x500")
        self.master.configure(bg='#f0f0f0')
        self.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.create_widgets()
        self.downloader = None

    def create_widgets(self):
        style = ttk.Style()
        style.theme_use('clam')

        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(frame, text="URL:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.url_entry = ttk.Entry(frame, width=50)
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky="we", padx=5, pady=5)
        self.url_entry.insert(0, "https://t.alcy.cc/ycy/")

        ttk.Label(frame, text="Save Directory:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.dir_entry = ttk.Entry(frame, width=40)
        self.dir_entry.grid(row=1, column=1, sticky="we", padx=5, pady=5)
        self.dir_entry.insert(0, "downloaded_images")
        ttk.Button(frame, text="Browse", command=self.browse_directory).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(frame, text="Request Interval (seconds):").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.interval_entry = ttk.Entry(frame, width=10)
        self.interval_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.interval_entry.insert(0, "1")

        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=10)

        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_download)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_download, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=70, height=15)
        self.log_area.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
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
        except ValueError:
            messagebox.showerror("Error", "Invalid interval. Please enter a number.")
            return

        self.downloader = ImageDownloader(url, save_dir, interval, self.log)
        self.download_thread = threading.Thread(target=self.downloader.run)
        self.download_thread.start()

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

    def stop_download(self):
        if self.downloader:
            self.downloader.stop()
            self.download_thread.join()
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

root = tk.Tk()
app = Application(master=root)
app.mainloop()
