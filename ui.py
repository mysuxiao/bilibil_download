from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox,
                             QProgressBar, QTextEdit, QFrame)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QFont, QColor, QPalette


class StyleSheet:
    """统一的样式定义"""
    MAIN_STYLE = """
        QMainWindow {
            background-color: #f5f6fa;
        }
        QLabel {
            font-size: 14px;
            color: #2c3e50;
        }
        QLineEdit {
            padding: 8px;
            border: 2px solid #dcdde1;
            border-radius: 4px;
            background-color: white;
            font-size: 14px;
        }
        QPushButton {
            padding: 8px 16px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:pressed {
            background-color: #2475a7;
        }
        QComboBox {
            padding: 8px;
            border: 2px solid #dcdde1;
            border-radius: 4px;
            background-color: white;
            font-size: 14px;
        }
        QProgressBar {
            border: 2px solid #dcdde1;
            border-radius: 4px;
            text-align: center;
            background-color: white;
        }
        QProgressBar::chunk {
            background-color: #3498db;
            border-radius: 2px;
        }
        QTextEdit {
            border: 2px solid #dcdde1;
            border-radius: 4px;
            background-color: white;
            padding: 8px;
            font-size: 14px;
        }
    """


class CustomFrame(QFrame):
    """自定义分组框"""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            CustomFrame {
                background-color: white;
                border: 1px solid #dcdde1;
                border-radius: 8px;
                margin: 8px;
                padding: 16px;
            }
        """)
        self.layout = QVBoxLayout(self)
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 8px;
                }
            """)
            self.layout.addWidget(title_label)


class BilibiliDownloaderUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Bilibili Video Downloader')
        self.setGeometry(100, 100, 800, 700)
        self.setStyleSheet(StyleSheet.MAIN_STYLE)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 输入区域
        input_frame = CustomFrame("视频信息")
        main_layout.addWidget(input_frame)

        # BV号输入
        bv_layout = QHBoxLayout()
        bv_label = QLabel('BV号:')
        self.bv_input = QLineEdit()
        self.bv_input.setPlaceholderText("请输入BV号")
        self.query_btn = QPushButton('查询')
        self.login_btn = QPushButton('扫码登录')
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)

        bv_layout.addWidget(bv_label)
        bv_layout.addWidget(self.bv_input)
        bv_layout.addWidget(self.query_btn)
        bv_layout.addWidget(self.login_btn)
        input_frame.layout.addLayout(bv_layout)

        # 视频信息显示
        self.video_info = QTextEdit()
        self.video_info.setReadOnly(True)
        self.video_info.setMaximumHeight(100)
        input_frame.layout.addWidget(self.video_info)

        # 选项区域
        options_frame = CustomFrame("下载选项")
        main_layout.addWidget(options_frame)

        options_layout = QHBoxLayout()

        # 分P选择
        part_layout = QVBoxLayout()
        part_label = QLabel('选择分P:')
        self.part_combo = QComboBox()
        part_layout.addWidget(part_label)
        part_layout.addWidget(self.part_combo)
        options_layout.addLayout(part_layout)

        # 画质选择
        quality_layout = QVBoxLayout()
        quality_label = QLabel('选择画质:')
        self.quality_combo = QComboBox()
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        options_layout.addLayout(quality_layout)

        options_frame.layout.addLayout(options_layout)

        # 下载路径
        path_layout = QHBoxLayout()
        path_label = QLabel('下载路径:')
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.select_path_btn = QPushButton('选择路径')
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.select_path_btn)
        options_frame.layout.addLayout(path_layout)

        # 下载按钮
        self.download_btn = QPushButton('开始下载')
        self.download_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 24px;
                font-size: 16px;
                background-color: #e74c3c;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        options_frame.layout.addWidget(self.download_btn, alignment=Qt.AlignCenter)

        # 进度显示区域
        progress_frame = CustomFrame("下载进度")
        main_layout.addWidget(progress_frame)

        # 进度条
        self.video_progress = QProgressBar()
        self.audio_progress = QProgressBar()
        progress_frame.layout.addWidget(QLabel('视频下载进度:'))
        progress_frame.layout.addWidget(self.video_progress)
        progress_frame.layout.addWidget(QLabel('音频下载进度:'))
        progress_frame.layout.addWidget(self.audio_progress)

        # 状态显示
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        progress_frame.layout.addWidget(self.status_text)


class LoginDialog(QWidget):
    login_success = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.initUI()
        self.qr_key = None
        self.check_timer = None

    def initUI(self):
        self.setWindowTitle('哔哩哔哩扫码登录')
        self.setFixedSize(380, 500)
        self.setStyleSheet(StyleSheet.MAIN_STYLE)

        # 使用 QVBoxLayout 作为主布局
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignCenter)  # 设置整体布局居中对齐

        # 标题
        title_label = QLabel('扫码登录')
        title_label.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 创建一个容器用于包装二维码
        qr_container = QWidget()
        qr_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #dcdde1;
                border-radius: 10px;
            }
        """)

        # 二维码容器使用 QVBoxLayout
        qr_layout = QVBoxLayout(qr_container)
        qr_layout.setContentsMargins(20, 20, 20, 20)
        qr_layout.setAlignment(Qt.AlignCenter)  # 设置二维码容器内部居中对齐

        # 二维码标签
        self.qr_label = QLabel()
        self.qr_label.setFixedSize(280, 280)
        self.qr_label.setAlignment(Qt.AlignCenter)
        qr_layout.addWidget(self.qr_label)

        # 将二维码容器添加到主布局
        layout.addWidget(qr_container, alignment=Qt.AlignCenter)

        # 状态标签
        self.status_label = QLabel('请使用哔哩哔哩App扫描二维码登录')
        self.status_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # 刷新按钮
        self.refresh_btn = QPushButton('刷新二维码')
        self.refresh_btn.setFixedWidth(240)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.refresh_btn, alignment=Qt.AlignCenter)

        # 设置主布局
        self.setLayout(layout)