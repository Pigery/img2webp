"""
UI组件模块 - 提供可复用的界面组件
"""

from PyQt6.QtWidgets import (
    QFrame, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, 
    QGroupBox, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt

class DragDropFrame(QFrame):
    """
    拖拽区域组件 - 支持文件拖放操作
    
    功能：
    - 提供可视化的拖放区域
    - 支持自定义拖拽进入和放下事件处理
    - 显示图标和提示文本
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setAcceptDrops(True)
        self.setup_ui()
    
    def setup_ui(self):
        """初始化拖拽区域UI布局"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        self.icon_label = QLabel("📁")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 48px;")
        
        self.text_label = QLabel("拖拽文件或文件夹到此处\n或点击下方按钮选择")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("font-size: 14px;")
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
    
    def dragEnterEvent(self, event):
        """拖拽进入事件 - 接受文件URL"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """拖拽放下事件 - 默认空实现，通过set_drop_handler设置"""
        pass
    
    def set_drag_enter_handler(self, handler):
        """设置自定义拖拽进入事件处理器"""
        self.dragEnterEvent = handler
    
    def set_drop_handler(self, handler):
        """设置自定义拖拽放下事件处理器"""
        self.dropEvent = handler


class TitleLabel(QLabel):
    """
    标题标签组件 - 用于显示页面或区域标题
    
    功能：
    - 居中显示标题文本
    - 统一的标题样式
    """
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class OutputSettings(QGroupBox):
    """
    输出设置组件 - 用于配置输出目录和质量参数
    
    功能：
    - 选择输出目录
    - 设置WebP图片质量
    - 提供质量预设选项
    """
    
    def __init__(self, parent=None):
        super().__init__("输出设置", parent)
        self.setup_ui()
    
    def setup_ui(self):
        """初始化输出设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)
        
        path_layout.addWidget(QLabel("输出目录:"), 0)
        
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择转换后图片保存的位置...")
        self.path_edit.setReadOnly(True)
        path_layout.addWidget(self.path_edit, 1)
        
        self.btn_browse = QPushButton("浏览")
        path_layout.addWidget(self.btn_browse, 0)
        
        layout.addLayout(path_layout)
        
        quality_layout = QHBoxLayout()
        quality_layout.setSpacing(10)
        
        quality_layout.addWidget(QLabel("WebP质量:"), 0)
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["高质量 (95)", "较高质量 (85)", "中等质量 (75)", "低质量 (60)"])
        self.quality_combo.setCurrentIndex(1)
        quality_layout.addWidget(self.quality_combo, 0)
        quality_layout.addStretch(1)
        
        layout.addLayout(quality_layout)
    
    def get_quality(self):
        """获取当前选择的WebP质量值"""
        quality_map = {0: 95, 1: 85, 2: 75, 3: 60}
        return quality_map[self.quality_combo.currentIndex()]
    
    def get_output_path(self):
        """获取当前选择的输出目录路径"""
        return self.path_edit.text()


class VideoCompressionSettings(QGroupBox):
    """
    视频压缩设置组件 - 用于配置视频压缩参数
    
    功能：
    - 选择输出目录
    - 设置压缩质量
    - 显示FFmpeg状态
    """
    
    def __init__(self, parent=None):
        super().__init__("视频压缩设置", parent)
        self.setup_ui()
    
    def setup_ui(self):
        """初始化视频压缩设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)
        
        path_layout.addWidget(QLabel("输出目录:"), 0)
        
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择压缩后视频保存的位置...")
        self.path_edit.setReadOnly(True)
        path_layout.addWidget(self.path_edit, 1)
        
        self.btn_browse = QPushButton("浏览")
        path_layout.addWidget(self.btn_browse, 0)
        
        layout.addLayout(path_layout)
        
        quality_layout = QHBoxLayout()
        quality_layout.setSpacing(10)
        
        quality_layout.addWidget(QLabel("压缩质量:"), 0)
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["高质量", "中等质量", "低质量"])
        self.quality_combo.setCurrentIndex(1)
        quality_layout.addWidget(self.quality_combo, 0)
        quality_layout.addStretch(1)
        
        layout.addLayout(quality_layout)
        
        self.ffmpeg_warning = QLabel("✓ FFmpeg 已自动捆绑")
        self.ffmpeg_warning.setStyleSheet("color: #27ae60; font-size: 12px;")
        layout.addWidget(self.ffmpeg_warning)
    
    def get_quality(self):
        """获取当前选择的压缩质量级别"""
        quality_map = {0: "high", 1: "medium", 2: "low"}
        return quality_map[self.quality_combo.currentIndex()]
    
    def get_output_path(self):
        """获取当前选择的输出目录路径"""
        return self.path_edit.text()
    
    def set_ffmpeg_status(self, installed, message=None):
        """
        设置FFmpeg状态显示
        
        Args:
            installed: FFmpeg是否已安装
            message: 可选的状态消息
        """
        if installed:
            self.ffmpeg_warning.setText("✓ FFmpeg 已就绪")
            self.ffmpeg_warning.setStyleSheet("color: #27ae60; font-size: 12px;")
        else:
            self.ffmpeg_warning.setText(f"⚠️ {message or 'FFmpeg 未安装'}")
            self.ffmpeg_warning.setStyleSheet("color: #e74c3c; font-size: 12px;")
