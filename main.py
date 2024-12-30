import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon
#从其他代码中引入
from ui import BilibiliDownloaderUI
from download import DownloadWorker
from process import merge_video_audio, get_video_quality
from bilibili_api import BilibiliAPI
from bili_login import BiliLogin, format_cookie_string

def resource_path(relative_path):
    """ 获取资源的绝对路径 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class BilibiliDownloader(BilibiliDownloaderUI):
    def __init__(self):
        super(BilibiliDownloader, self).__init__()
        self.video_meta = None
        self.video_downloaded = False
        self.audio_downloaded = False
        self.api = BilibiliAPI()
        self.setWindowIcon(QIcon(resource_path('app.ico')))
        self.setup_connections()
        self.load_cookies()

    def setup_connections(self):
        """设置信号连接"""
        self.query_btn.clicked.connect(self.query_video)
        self.download_btn.clicked.connect(self.start_download)
        self.select_path_btn.clicked.connect(self.select_download_path)
        self.login_btn.clicked.connect(self.show_login_dialog)

    def show_login_dialog(self):
        """显示登录对话框"""
        self.login_dialog = BiliLogin()
        self.login_dialog.login_success.connect(self.handle_login_success)
        self.login_dialog.show()

    def handle_login_success(self, cookie_dict):
        """处理登录成功"""
        # 更新API中的cookie
        self.api.headers['Cookie'] = format_cookie_string(cookie_dict)
        self.status_text.append("登录成功！Cookie已更新")

    def load_cookies(self):
        """加载保存的cookie"""
        cookies = BiliLogin.load_cookies()
        if cookies:
            self.api.headers['Cookie'] = format_cookie_string(cookies)
            self.status_text.append("已加载保存的登录信息")

    def select_download_path(self):
        """选择下载路径"""
        path = QFileDialog.getExistingDirectory(
            self,
            "选择下载路径",
            os.path.expanduser('~'),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if path:
            self.path_input.setText(path)

    def query_video(self):
        """查询视频信息"""
        bv_number = self.bv_input.text().strip()
        if not bv_number:
            QMessageBox.warning(self, '警告', '请输入BV号')
            return

        video_info, error = self.api.get_video_info(bv_number)
        if error:
            QMessageBox.warning(self, '错误', error)
            return

        self.video_meta = video_info
        self.update_video_info()
        self.update_part_combo()
        self.update_quality_combo()

    def update_video_info(self):
        """更新视频信息显示"""
        if self.video_meta:
            info_text = f"标题: {self.video_meta['title']}\n"
            info_text += f"UP主: {self.video_meta['owner']['name']}\n"
            info_text += f"视频简介: {self.video_meta['desc']}\n"
            self.video_info.setText(info_text)

    def update_part_combo(self):
        """更新分P下拉框"""
        self.part_combo.clear()
        if self.video_meta:
            pages = self.video_meta['pages']
            for page in pages:
                self.part_combo.addItem(f"P{page['page']}: {page['part']}", page['cid'])

    def update_quality_combo(self):
        """更新质量选择下拉框"""
        self.quality_combo.clear()
        qualities = get_video_quality()
        for qn, desc in qualities.items():
            self.quality_combo.addItem(desc, qn)

    def start_download(self):
        """开始下载"""
        if not self.video_meta:
            QMessageBox.warning(self, '警告', '请先查询视频信息')
            return

        download_path = self.path_input.text()
        if not download_path:
            QMessageBox.warning(self, '警告', '请选择下载路径')
            return

        try:
            # 获取下载参数
            aid = self.video_meta['aid']
            cid = self.part_combo.currentData()
            quality = self.quality_combo.currentData()
            title = self.video_meta['title'].replace(" ", "_")

            # 获取下载链接
            urls, error = self.api.get_download_urls(aid, cid, quality)
            if error:
                QMessageBox.warning(self, '错误', error)
                return

            # 准备下载路径
            paths, error = self.api.prepare_download_paths(download_path, title)
            if error:
                QMessageBox.warning(self, '错误', error)
                return

            # 创建下载工作线程
            self.video_worker = DownloadWorker(urls['video_url'], paths['video_path'], "视频流")
            self.audio_worker = DownloadWorker(urls['audio_url'], paths['audio_path'], "音频流")

            # 连接信号
            self.video_worker.progress_updated.connect(self.update_progress)
            self.audio_worker.progress_updated.connect(self.update_progress)
            self.video_worker.status_updated.connect(self.update_status)
            self.audio_worker.status_updated.connect(self.update_status)
            self.video_worker.download_completed.connect(
                lambda success, desc: self.handle_download_completed(
                    success, desc, paths['video_path'], paths['audio_path'], paths['output_path']
                )
            )
            self.audio_worker.download_completed.connect(
                lambda success, desc: self.handle_download_completed(
                    success, desc, paths['video_path'], paths['audio_path'], paths['output_path']
                )
            )

            # 启动下载
            self.video_worker.start()
            self.audio_worker.start()

            self.download_btn.setEnabled(False)
            self.status_text.append(f"开始下载到: {download_path}")

        except Exception as e:
            QMessageBox.warning(self, '错误', f"下载过程出错: {str(e)}")
            self.status_text.append(f"错误详情: {str(e)}")

    def update_progress(self, progress, desc):
        """更新进度条"""
        if desc == "视频流":
            self.video_progress.setValue(progress)
        else:
            self.audio_progress.setValue(progress)

    def update_status(self, message):
        """更新状态信息"""
        self.status_text.append(message)

    def handle_download_completed(self, success, desc, video_path, audio_path, output_path):
        """处理下载完成事件"""
        if desc == "视频流":
            self.video_downloaded = success
        else:
            self.audio_downloaded = success

        if self.video_downloaded and self.audio_downloaded:
            success, message = merge_video_audio(video_path, audio_path, output_path)
            self.update_status(message)

            # 清理临时文件
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                self.update_status("临时文件清理完成")
            except Exception as e:
                self.update_status(f"清理临时文件失败: {str(e)}")

            self.download_btn.setEnabled(True)
            self.video_downloaded = False
            self.audio_downloaded = False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 设置应用程序图标
    app.setWindowIcon(QIcon(resource_path('app.ico')))
    # 创建并显示主窗口
    window = BilibiliDownloader()
    window.show()
    sys.exit(app.exec_())