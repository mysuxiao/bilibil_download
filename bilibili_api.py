import os
import time
import json
import requests

class BilibiliAPI:
    def __init__(self):
        self.headers = {
            'referer': 'https://www.bilibili.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        # 初始化时加载cookie
        self.load_cookies()

    def load_cookies(self):
        """加载保存的cookie"""
        try:
            if os.path.exists('bili_cookies.json'):
                with open('bili_cookies.json', 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    # 将cookie字典转换为字符串格式
                    cookie_string = '; '.join([f'{k}={v}' for k, v in cookies.items()])
                    self.headers['Cookie'] = cookie_string
                return True
            else:
                print("Cookie文件不存在")
                return False
        except Exception as e:
            print(f"加载cookie失败: {str(e)}")
            return False

    def update_cookies(self, cookie_dict):
        """更新cookie"""
        try:
            cookie_string = '; '.join([f'{k}={v}' for k, v in cookie_dict.items()])
            self.headers['Cookie'] = cookie_string
            return True
        except Exception as e:
            print(f"更新cookie失败: {str(e)}")
            return False

    def get_video_info(self, bv_number):
        """获取视频信息"""
        try:
            meta_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_number}"
            response = requests.get(meta_url, headers=self.headers)

            if response.status_code != 200:
                return None, f"请求失败，状态码: {response.status_code}"

            if not response.text:
                return None, "服务器返回空响应"

            try:
                meta_data = response.json()
            except ValueError as e:
                return None, f"JSON解析失败: {response.text[:100]}"

            if meta_data['code'] == 0:
                return meta_data['data'], None
            elif meta_data['code'] == -403:
                return None, "Cookie已过期，请重新登录"
            else:
                error_message = meta_data.get('message', '未知错误')
                return None, f"获取视频信息失败: {error_message}"

        except requests.exceptions.RequestException as e:
            return None, f"网络请求失败: {str(e)}"
        except Exception as e:
            return None, f"程序出错: {str(e)}"

    def get_download_urls(self, aid, cid, quality):
        """获取下载链接"""
        try:
            download_url = f"https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&qn={quality}&fnver=0&fnval=80&fourk=1"
            response = requests.get(download_url, headers=self.headers)

            if response.status_code != 200:
                return None, f'获取下载链接失败，状态码：{response.status_code}'

            try:
                download_data = response.json()
            except ValueError as e:
                return None, f'解析下载信息失败：{str(e)}'

            if download_data.get('code') == -403:
                return None, "Cookie已过期，请重新登录"
            elif download_data.get('code') != 0:
                error_msg = download_data.get('message', '未知错误')
                return None, f'获取下载链接失败：{error_msg}'

            if 'dash' not in download_data.get('data', {}):
                return None, '视频格式不支持'

            video_url = download_data['data']['dash']['video'][0]['baseUrl']
            audio_url = download_data['data']['dash']['audio'][0]['baseUrl']

            return {'video_url': video_url, 'audio_url': audio_url}, None

        except Exception as e:
            return None, f"获取下载链接出错: {str(e)}"

    def prepare_download_paths(self, download_path, title):
        """准备下载路径"""
        try:
            if not os.path.exists(download_path):
                os.makedirs(download_path)

            if not os.access(download_path, os.W_OK):
                return None, '下载路径没有写入权限'

            current_time = time.strftime("%Y%m%d_%H%M%S")
            # 过滤文件名中的非法字符
            safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).rstrip()

            temp_video_path = os.path.join(download_path, f'{safe_title}_{current_time}_temp_video.m4s')
            temp_audio_path = os.path.join(download_path, f'{safe_title}_{current_time}_temp_audio.m4s')
            output_path = os.path.join(download_path, f'{safe_title}_{current_time}.mp4')

            return {
                       'video_path': temp_video_path,
                       'audio_path': temp_audio_path,
                       'output_path': output_path
                   }, None

        except Exception as e:
            return None, f'准备下载路径失败: {str(e)}'

    def check_cookie_status(self):
        """检查cookie状态"""
        try:
            # 尝试访问需要登录的API接口
            test_url = "https://api.bilibili.com/x/web-interface/nav"
            response = requests.get(test_url, headers=self.headers)
            data = response.json()

            if data['code'] == 0:
                return True, "Cookie有效"
            else:
                return False, "Cookie已过期或无效"
        except Exception as e:
            return False, f"检查Cookie状态失败: {str(e)}"