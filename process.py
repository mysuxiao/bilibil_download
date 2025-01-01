import os
from imageio_ffmpeg import get_ffmpeg_exe


def merge_video_audio(video_path, audio_path, output_path):
    """合并视频和音频"""
    try:
        ffmpeg_path = get_ffmpeg_exe()  # 自动获取ffmpeg路径
        import subprocess

        cmd = [
            ffmpeg_path,
            '-i', video_path,
            '-i', audio_path,
            '-c', 'copy',
            '-y',  # 自动覆盖输出文件
            output_path
        ]

        # 创建 startupinfo 对象（Windows下隐藏控制台窗口）
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            text=False  # 使用二进制模式
        )

        # 获取输出并正确处理编码
        stdout, stderr = process.communicate()

        # 尝试不同的编码方式解码输出
        try:
            stderr = stderr.decode('utf-8') if stderr else ''
        except UnicodeDecodeError:
            try:
                stderr = stderr.decode('gbk') if stderr else ''
            except UnicodeDecodeError:
                stderr = str(stderr) if stderr else ''

        if process.returncode == 0:
            # 删除临时文件
            try:
                os.remove(video_path)
                os.remove(audio_path)
            except Exception as e:
                print(f"删除临时文件失败: {str(e)}")  # 仅打印错误，不影响主流程
            return True, '视频合并完成'
        else:
            return False, f'合并失败: {stderr}'

    except Exception as e:
        return False, f'合并过程出错: {str(e)}'
def get_video_quality():
    return {
        116: '高清 1080P60',
        80: '高清 1080P',
        64: '高清 720P',
        32: '清晰 480P',
        16: '流畅 360P'
    }

