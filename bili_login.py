import json
import qrcode
import requests
from io import BytesIO
from PyQt5.QtCore import QTimer
from ui import LoginDialog
from PyQt5.QtGui import QPixmap

class BiliLogin(LoginDialog):
    def __init__(self):
        super().__init__()
        # 连接刷新按钮的信号
        self.refresh_btn.clicked.connect(self.get_qr_code)
        # 初始获取二维码
        self.get_qr_code()

    def get_qr_code(self):
        """获取二维码"""
        try:
            # 停止现有的检查定时器
            if self.check_timer:
                self.check_timer.stop()

            # 获取二维码密钥
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            # 使用 tv 端的 API，可能更稳定
            response = requests.get(
                'https://passport.bilibili.com/x/passport-login/web/qrcode/generate',
                headers=headers
            )

            data = response.json()

            if data['code'] == 0:
                self.qr_key = data['data']['qrcode_key']
                qr_url = data['data']['url']

                # 生成二维码图片
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=2,
                )
                qr.add_data(qr_url)
                qr.make(fit=True)

                # 将二维码转换为PyQt可显示的格式
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                qr_pixmap = QPixmap()
                qr_pixmap.loadFromData(buffer.getvalue())
                self.qr_label.setPixmap(qr_pixmap.scaled(240, 240))

                # 开始检查扫码状态
                self.check_timer = QTimer()
                self.check_timer.timeout.connect(self.check_scan_status)
                self.check_timer.start(2000)  # 每2秒检查一次
                self.status_label.setText('请使用哔哩哔哩App扫描二维码登录')
            else:
                self.status_label.setText(f'获取二维码失败：{data.get("message", "未知错误")}')

        except Exception as e:
            self.status_label.setText(f'发生错误: {str(e)}')

    def check_scan_status(self):
        """检查扫码状态"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(
                f'https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={self.qr_key}',
                headers=headers
            )

            data = response.json()

            if data['code'] == 0:
                status = data['data'].get('code')
                if status == 0:
                    # 登录成功
                    self.check_timer.stop()
                    self.status_label.setText('登录成功！正在获取用户信息...')

                    if 'data' in data and 'url' in data['data']:
                        # 解析url中的参数获取cookies
                        from urllib.parse import parse_qs, urlparse
                        parsed_url = urlparse(data['data']['url'])
                        params = parse_qs(parsed_url.query)

                        cookies = {}
                        if 'SESSDATA' in params:
                            cookies['SESSDATA'] = params['SESSDATA'][0]
                        if 'bili_jct' in params:
                            cookies['bili_jct'] = params['bili_jct'][0]
                        if 'DedeUserID' in params:
                            cookies['DedeUserID'] = params['DedeUserID'][0]
                        if 'DedeUserID__ckMd5' in params:
                            cookies['DedeUserID__ckMd5'] = params['DedeUserID__ckMd5'][0]

                        self.get_user_cookies(cookies)
                    else:
                        self.status_label.setText('获取登录信息失败，请重试')

                elif status == 86038:
                    # 二维码已过期
                    self.check_timer.stop()
                    self.status_label.setText('二维码已过期，请点击刷新重试')
                elif status == 86090:
                    # 等待扫码
                    self.status_label.setText('请使用哔哩哔哩App扫描二维码登录')
                elif status == 86101:
                    # 已扫码，等待确认
                    self.status_label.setText('已扫描，请在手机上确认登录')
                else:
                    self.status_label.setText(f'未知状态({status})，请刷新重试')
            else:
                self.status_label.setText(f'检查状态失败：{data.get("message", "未知错误")}')

        except Exception as e:
            self.status_label.setText(f'检查状态时发生错误: {str(e)}')
            print(f"详细错误信息: {str(e)}")  # 添加详细错误信息打印

    def get_user_cookies(self, cookies):
        """获取用户Cookie信息"""
        try:
            # 检查必要的cookie是否都存在
            required_cookies = ['SESSDATA', 'bili_jct', 'DedeUserID']
            if not all(key in cookies for key in required_cookies):
                self.status_label.setText('获取Cookie失败，缺少必要信息')
                return

            # 保存cookie到文件
            with open('bili_cookies.json', 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            # 发送登录成功信号
            self.login_success.emit(cookies)
            self.status_label.setText('登录信息已保存！请关闭此窗口')
            self.refresh_btn.setEnabled(False)

        except Exception as e:
            self.status_label.setText(f'保存Cookie时发生错误: {str(e)}')
            print(f"详细错误信息: {str(e)}")  # 添加详细错误信息打印

    @staticmethod
    def load_cookies():
        """加载保存的Cookie"""
        try:
            with open('bili_cookies.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None


def format_cookie_string(cookie_dict):
    """将Cookie字典格式化为字符串"""
    return '; '.join([f'{k}={v}' for k, v in cookie_dict.items()])