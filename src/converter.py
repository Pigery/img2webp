"""
图片/视频转换模块 - 负责图片和视频格式转换的核心逻辑

功能：
- 图片转WebP格式转换
- 视频压缩处理
- 多线程异步转换
- 进度报告和错误处理
"""

import os
import subprocess
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal
import imageio_ffmpeg


class VideoCompressionWorker(QThread):
    """
    视频压缩工作线程 - 在后台线程中执行视频压缩任务
    
    功能：
    - 使用FFmpeg进行视频压缩
    - 支持多种质量级别（高、中、低）
    - 实时报告压缩进度
    - 统计压缩结果和失败信息
    
    信号：
    - progress_updated(int, str): 压缩进度更新，参数为进度百分比和状态消息
    - compression_complete(dict): 压缩完成，参数为结果字典
    - error_occurred(str): 发生错误，参数为错误消息
    """
    
    progress_updated = pyqtSignal(int, str)
    compression_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, files_to_compress, output_dir, quality="medium"):
        """
        初始化视频压缩工作线程
        
        Args:
            files_to_compress: 待压缩文件列表，每个元素为包含path和output_path的字典
            output_dir: 输出目录路径
            quality: 压缩质量级别，可选值: "high", "medium", "low"
        """
        super().__init__()
        self.files_to_compress = files_to_compress
        self.output_dir = output_dir
        self.quality = quality
        self.total_files = len(files_to_compress)
        self.compressed_count = 0
        self.failed_count = 0
        self.results = {}
        
        self.quality_settings = {
            "high": {"crf": 18, "preset": "slow"},
            "medium": {"crf": 23, "preset": "medium"},
            "low": {"crf": 28, "preset": "fast"}
        }
    
    def run(self):
        """执行视频压缩任务的主循环"""
        for index, file_info in enumerate(self.files_to_compress):
            try:
                input_path = file_info['path']
                output_path = file_info['output_path']
                
                progress = int((index + 1) / self.total_files * 100)
                self.progress_updated.emit(progress, f"正在压缩: {os.path.basename(input_path)}")
                
                result = self.compress_video(input_path, output_path)
                
                if result['success']:
                    self.compressed_count += 1
                    self.results[input_path] = result
                else:
                    self.failed_count += 1
                    self.results[input_path] = result
                    self.error_occurred.emit(result.get('error', '未知错误'))
                
            except Exception as e:
                self.failed_count += 1
                self.results[input_path] = {'success': False, 'error': str(e)}
                self.error_occurred.emit(f"压缩失败 {os.path.basename(input_path)}: {str(e)}")
        
        self.compression_complete.emit(self.results)
    
    def compress_video(self, input_path, output_path):
        """
        使用FFmpeg压缩视频
        
        Args:
            input_path: 输入视频文件路径
            output_path: 输出视频文件路径
            
        Returns:
            dict: 包含压缩结果的字典，包括success、output、input_size、output_size、compression_ratio等字段
        """
        settings = self.quality_settings.get(self.quality, self.quality_settings["medium"])
        crf = settings["crf"]
        preset = settings["preset"]
        
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        
        cmd = [
            ffmpeg_path, '-y',
            '-i', input_path,
            '-c:v', 'libx264',
            '-crf', str(crf),
            '-preset', preset,
            '-c:a', 'aac',
            '-b:a', '128k',
            output_path
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            _, stderr = process.communicate()
            
            if process.returncode == 0:
                input_size = os.path.getsize(input_path)
                output_size = os.path.getsize(output_path)
                ratio = (1 - output_size / input_size) * 100
                
                return {
                    'success': True,
                    'output': output_path,
                    'input_size': input_size,
                    'output_size': output_size,
                    'compression_ratio': round(ratio, 2)
                }
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                return {'success': False, 'error': f"FFmpeg错误: {error_msg[:200]}"}
                
        except FileNotFoundError:
            return {'success': False, 'error': '未找到FFmpeg，请确保已安装并添加到系统PATH'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class ImageConversionWorker(QThread):
    """
    图片转换工作线程 - 在后台线程中执行图片转WebP任务
    
    功能：
    - 将多种格式图片转换为WebP格式
    - 支持透明度处理
    - 实时报告转换进度
    - 统计转换结果和失败信息
    
    信号：
    - progress_updated(int, str): 转换进度更新，参数为进度百分比和状态消息
    - conversion_complete(dict): 转换完成，参数为结果字典
    - error_occurred(str): 发生错误，参数为错误消息
    """
    
    progress_updated = pyqtSignal(int, str)
    conversion_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, files_to_convert, output_dir, quality=85):
        """
        初始化图片转换工作线程
        
        Args:
            files_to_convert: 待转换文件列表，每个元素为包含path和output_name的字典
            output_dir: 输出目录路径
            quality: WebP质量值，范围1-100，默认85
        """
        super().__init__()
        self.files_to_convert = files_to_convert
        self.output_dir = output_dir
        self.quality = quality
        self.total_files = len(files_to_convert)
        self.converted_count = 0
        self.failed_count = 0
        self.results = {}
    
    def run(self):
        """执行图片转换任务的主循环"""
        for index, file_info in enumerate(self.files_to_convert):
            try:
                input_path = file_info['path']
                output_filename = file_info['output_name']
                output_path = os.path.join(self.output_dir, output_filename)
                
                progress = int((index + 1) / self.total_files * 100)
                self.progress_updated.emit(progress, f"正在转换: {os.path.basename(input_path)}")
                
                with Image.open(input_path) as img:
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        img = img.convert('RGBA')
                    
                    img.save(output_path, 'WEBP', quality=self.quality, lossless=False)
                
                self.converted_count += 1
                self.results[input_path] = {'success': True, 'output': output_path}
                
            except Exception as e:
                self.failed_count += 1
                self.results[input_path] = {'success': False, 'error': str(e)}
                self.error_occurred.emit(f"转换失败 {os.path.basename(input_path)}: {str(e)}")
        
        self.conversion_complete.emit(self.results)


def get_default_icon():
    """
    获取默认图标路径
    
    Returns:
        str: 图标文件路径，如果不存在则返回空字符串
    """
    return "icon.png" if os.path.exists("icon.png") else ""


def is_image_file(file_path, image_extensions):
    """
    检查文件是否为支持的图片格式
    
    Args:
        file_path: 文件路径
        image_extensions: 支持的图片扩展名列表
        
    Returns:
        bool: 如果是支持的图片格式返回True，否则返回False
    """
    ext = os.path.splitext(file_path)[1].lower()
    return ext in image_extensions


def generate_output_name(filename, existing_names):
    """
    生成唯一的输出文件名
    
    Args:
        filename: 原始文件名
        existing_names: 已存在的文件名集合
        
    Returns:
        str: 唯一的输出文件名（.webp格式）
    """
    base_name = os.path.splitext(filename)[0]
    output_name = base_name + '.webp'
    counter = 1
    
    while output_name in existing_names:
        output_name = f"{base_name}_{counter}.webp"
        counter += 1
    
    return output_name


def is_video_file(file_path):
    """
    检查文件是否为支持的视频格式
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 如果是支持的视频格式返回True，否则返回False
    """
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.mpeg', '.mpg']
    ext = os.path.splitext(file_path)[1].lower()
    return ext in video_extensions


def generate_video_output_name(filename, existing_names):
    """
    生成唯一的输出视频文件名
    
    Args:
        filename: 原始文件名
        existing_names: 已存在的文件名集合
        
    Returns:
        str: 唯一的输出视频文件名（_compressed.mp4格式）
    """
    base_name = os.path.splitext(filename)[0]
    output_name = base_name + '_compressed.mp4'
    counter = 1
    
    while output_name in existing_names:
        output_name = f"{base_name}_{counter}_compressed.mp4"
        counter += 1
    
    return output_name


def check_ffmpeg():
    """
    检查FFmpeg是否已安装（通过 imageio-ffmpeg）
    
    Returns:
        tuple: (bool, str) 第一个元素表示是否可用，第二个元素为状态消息或错误信息
    """
    try:
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(ffmpeg_path):
            return True, None
        else:
            return False, "FFmpeg二进制文件未找到"
    except Exception as e:
        return False, f"获取FFmpeg失败: {str(e)}"
