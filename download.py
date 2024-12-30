import os
import json
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time


class DownloadWorker(QThread):
    progress_updated = pyqtSignal(int, str)
    status_updated = pyqtSignal(str)
    download_completed = pyqtSignal(bool, str)

    def __init__(self, url, save_path, desc):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.desc = desc
        self.headers = {
            'referer': 'https://www.bilibili.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = self.create_session()
        self.load_cookies()
        self.is_running = True

    def create_session(self):
        """创建带有重试机制的会话"""
        session = requests.Session()
        retry_strategy = Retry(
            total=5,  # 总重试次数
            backoff_factor=1,  # 重试间隔
            status_forcelist=[500, 502, 503, 504, 429]  # 需要重试的状态码
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def load_cookies(self):
        """加载保存的cookie"""
        try:
            if os.path.exists('bili_cookies.json'):
                with open('bili_cookies.json', 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    cookie_string = '; '.join([f'{k}={v}' for k, v in cookies.items()])
                    self.headers['Cookie'] = cookie_string
                return True
            return False
        except Exception as e:
            self.status_updated.emit(f"加载cookie失败: {str(e)}")
            return False

    def format_size(self, size_bytes):
        """格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f}TB"

    def run(self):
        temp_path = f"{self.save_path}.tmp"
        first_byte = 0

        # 检查断点续传
        if os.path.exists(temp_path):
            first_byte = os.path.getsize(temp_path)
            if first_byte > 0:
                self.headers['Range'] = f'bytes={first_byte}-'

        try:
            # 创建保存目录
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)

            # 获取响应
            response = self.get_response(self.url)

            # 检查响应状态
            if response.status_code == 403:
                self.status_updated.emit("下载失败：cookie已过期，请重新登录")
                self.download_completed.emit(False, self.desc)
                return
            elif response.status_code not in [200, 206]:  # 206是断点续传的状态码
                self.status_updated.emit(f"下载失败：HTTP {response.status_code}")
                self.download_completed.emit(False, self.desc)
                return

            # 获取文件大小
            file_size = int(response.headers.get('content-length', 0))
            if first_byte > 0:
                file_size += first_byte
            formatted_size = self.format_size(file_size)

            mode = 'ab' if first_byte > 0 else 'wb'
            downloaded_size = first_byte
            chunk_size = 1024 * 1024  # 1MB chunks
            start_time = time.time()

            with open(temp_path, mode) as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if not self.is_running:
                        break

                    if chunk:
                        size = file.write(chunk)
                        downloaded_size += size
                        progress = int((downloaded_size / file_size) * 100) if file_size > 0 else 0

                        # 计算下载速度
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            speed = downloaded_size / (1024 * 1024 * elapsed_time)  # MB/s
                            downloaded_formatted = self.format_size(downloaded_size)
                            self.status_updated.emit(
                                f"正在下载{self.desc}: {downloaded_formatted}/{formatted_size} ({progress}%) - {speed:.2f}MB/s"
                            )

                        self.progress_updated.emit(progress, self.desc)

            if self.is_running:
                # 下载完成，将临时文件重命名为最终文件
                os.replace(temp_path, self.save_path)
                self.status_updated.emit(f"{self.desc}下载完成，保存至: {self.save_path}")
                self.download_completed.emit(True, self.desc)
            else:
                self.status_updated.emit(f"{self.desc}下载已取消")
                self.download_completed.emit(False, self.desc)

        except requests.exceptions.RequestException as e:
            self.status_updated.emit(f"网络错误：{str(e)}")
            self.download_completed.emit(False, self.desc)
        except IOError as e:
            self.status_updated.emit(f"文件写入错误：{str(e)}")
            self.download_completed.emit(False, self.desc)
        except Exception as e:
            self.status_updated.emit(f"下载{self.desc}出错: {str(e)}")
            self.download_completed.emit(False, self.desc)

    def get_response(self, url):
        """获取响应"""
        try:
            response = self.session.get(
                url=url,
                headers=self.headers,
                stream=True,
                timeout=30
            )
            return response
        except requests.exceptions.Timeout:
            raise Exception("请求超时，请检查网络连接")
        except requests.exceptions.RequestException as e:
            raise Exception(f"请求失败：{str(e)}")

    def stop(self):
        """停止下载"""
        self.is_running = False

