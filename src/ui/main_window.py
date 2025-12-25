"""
主窗口模块 - 程序主界面
包含图片转换和视频压缩两个标签页
"""

import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, 
                             QPushButton, QGroupBox, QMessageBox, QTabWidget,
                             QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QProgressBar, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QBrush, QColor

from ui.components import (DragDropFrame, TitleLabel,  OutputSettings, 
                           VideoCompressionSettings)
from converter import (ImageConversionWorker, VideoCompressionWorker, 
                       get_default_icon, is_image_file, is_video_file, 
                       generate_output_name, generate_video_output_name, 
                       check_ffmpeg)


class ImageConversionTab(QWidget):
    """图片转换标签页 - 提供图片选择、转换和进度显示功能"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        """初始化UI布局"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        self.drag_frame = DragDropFrame()
        layout.addWidget(self.drag_frame)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.btn_select_files = QPushButton(" 选择图片")
        self.btn_select_folder = QPushButton(" 选择文件夹")
        self.btn_clear = QPushButton(" 清空列表")
        
        button_layout.addWidget(self.btn_select_files)
        button_layout.addWidget(self.btn_select_folder)
        button_layout.addWidget(self.btn_clear)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        files_group = QGroupBox("待转换文件列表")
        files_layout = QVBoxLayout(files_group)
        
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(["文件路径", "文件名", "格式", "状态"])
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.files_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.files_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.files_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.files_table.setColumnWidth(1, 150)
        self.files_table.setColumnWidth(2, 80)
        self.files_table.setColumnWidth(3, 100)
        self.files_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.files_table.setAlternatingRowColors(True)
        files_layout.addWidget(self.files_table)
        
        self.files_info_label = QLabel("已选择 0 个文件")
        self.files_info_label.setStyleSheet("font-size: 12px;")
        files_layout.addWidget(self.files_info_label)
        
        layout.addWidget(files_group)
        
        self.output_settings = OutputSettings()
        layout.addWidget(self.output_settings)
        
        self.progress_section = QVBoxLayout()
        self.progress_section.setSpacing(8)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.progress_label = QLabel("准备就绪")
        self.progress_label.setStyleSheet("font-size: 12px;")
        
        self.progress_section.addWidget(self.progress_bar)
        self.progress_section.addWidget(self.progress_label)
        
        layout.addLayout(self.progress_section)
        
        self.btn_convert = QPushButton("开始转换")
        self.btn_convert.setEnabled(False)
        layout.addWidget(self.btn_convert)
        
        self.setup_connections()
    
    def setup_connections(self):
        """连接信号和槽"""
        self.btn_select_files.clicked.connect(self.select_files)
        self.btn_select_folder.clicked.connect(self.select_folder)
        self.btn_clear.clicked.connect(self.clear_files)
        self.output_settings.btn_browse.clicked.connect(self.select_output_directory)
        self.btn_convert.clicked.connect(self.start_conversion)
        
        self.drag_frame.set_drag_enter_handler(self.dragEnterEvent)
        self.drag_frame.set_drop_handler(self.dropEvent)
    
    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """处理拖拽放下事件 - 添加文件到列表"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                if is_image_file(file_path, self.parent.image_extensions):
                    files.append(file_path)
            elif os.path.isdir(file_path):
                for root, dirs, filenames in os.walk(file_path):
                    for filename in filenames:
                        full_path = os.path.join(root, filename)
                        if is_image_file(full_path, self.parent.image_extensions):
                            files.append(full_path)
        
        if files:
            self.add_files_to_list(files)
    
    def select_files(self):
        """打开文件选择对话框"""
        file_filter = "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.tif);;所有文件 (*)"
        files, _ = QFileDialog.getOpenFileNames(self, "选择图片文件", "", file_filter)
        if files:
            self.add_files_to_list(files)
    
    def select_folder(self):
        """打开文件夹选择对话框并扫描图片"""
        folder = QFileDialog.getExistingDirectory(self, "选择包含图片的文件夹", "")
        if folder:
            files = []
            for root, dirs, filenames in os.walk(folder):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if is_image_file(file_path, self.parent.image_extensions):
                        files.append(file_path)
            
            if files:
                self.add_files_to_list(files)
                QMessageBox.information(self, "文件夹扫描完成", f"找到 {len(files)} 个图片文件")
            else:
                QMessageBox.warning(self, "未找到图片", "所选文件夹中没有找到支持的图片格式文件")
    
    def add_files_to_list(self, files):
        """添加文件到转换列表"""
        existing_names = [item['output_name'] for item in self.parent.files_to_convert]
        
        for file_path in files:
            if file_path not in [item['path'] for item in self.parent.files_to_convert]:
                ext = os.path.splitext(file_path)[1].upper()
                filename = os.path.basename(file_path)
                output_name = generate_output_name(filename, existing_names)
                existing_names.append(output_name)
                
                self.parent.files_to_convert.append({
                    'path': file_path,
                    'filename': filename,
                    'format': ext,
                    'output_name': output_name,
                    'status': '等待转换',
                    'type': 'image'
                })
        
        self.update_files_table()
        self.update_files_info()
        self.update_convert_button()
    
    def update_files_table(self):
        """更新文件列表表格显示"""
        image_files = [f for f in self.parent.files_to_convert if f.get('type') == 'image']
        self.files_table.setRowCount(len(image_files))
        
        for row, file_info in enumerate(image_files):
            path_item = QTableWidgetItem(file_info['path'])
            path_item.setToolTip(file_info['path'])
            filename_item = QTableWidgetItem(file_info['filename'])
            format_item = QTableWidgetItem(file_info['format'])
            status_item = QTableWidgetItem(file_info['status'])
            
            colors = {'转换成功': '#27ae60', '转换失败': '#e74c3c', '转换中': '#3498db', '等待转换': '#7f8c8d'}
            color = colors.get(file_info['status'], '#000000')
            status_item.setForeground(QBrush(QColor(color)))
            
            self.files_table.setItem(row, 0, path_item)
            self.files_table.setItem(row, 1, filename_item)
            self.files_table.setItem(row, 2, format_item)
            self.files_table.setItem(row, 3, status_item)
    
    def update_files_info(self):
        """更新文件信息标签"""
        count = len([f for f in self.parent.files_to_convert if f.get('type') == 'image'])
        self.files_info_label.setText(f"已选择 {count} 个图片文件")
    
    def update_convert_button(self):
        """根据文件和输出目录状态启用/禁用转换按钮"""
        has_images = any(f.get('type') == 'image' for f in self.parent.files_to_convert)
        has_output = bool(self.output_settings.get_output_path())
        self.btn_convert.setEnabled(has_images and has_output)
    
    def clear_files(self):
        """清空文件列表"""
        self.parent.files_to_convert = [f for f in self.parent.files_to_convert if f.get('type') != 'image']
        self.update_files_table()
        self.update_files_info()
        self.update_convert_button()
    
    def select_output_directory(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录", "")
        if directory:
            self.parent.output_directory = directory
            self.output_settings.path_edit.setText(directory)
            self.update_convert_button()
    
    def start_conversion(self):
        """开始图片转换任务"""
        if not self.parent.files_to_convert:
            QMessageBox.warning(self, "警告", "请先选择要转换的文件")
            return
        
        if not self.parent.output_directory:
            QMessageBox.warning(self, "警告", "请选择输出目录")
            return
        
        quality = self.output_settings.get_quality()
        
        self.btn_convert.setEnabled(False)
        self.btn_select_files.setEnabled(False)
        self.btn_select_folder.setEnabled(False)
        
        image_files = [f for f in self.parent.files_to_convert if f.get('type') == 'image']
        for file_info in image_files:
            file_info['status'] = '等待转换'
        self.update_files_table()
        
        self.worker = ImageConversionWorker(image_files, self.parent.output_directory, quality)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.conversion_complete.connect(self.on_conversion_complete)
        self.worker.error_occurred.connect(self.on_error_occurred)
        self.worker.start()
    
    def on_progress_updated(self, progress, message):
        """更新转换进度"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
    
    def on_conversion_complete(self, results):
        """处理转换完成事件"""
        success_count = 0
        failed_count = 0
        
        for file_info in self.parent.files_to_convert:
            if file_info.get('type') == 'image':
                input_path = file_info['path']
                if input_path in results:
                    if results[input_path]['success']:
                        file_info['status'] = '转换成功'
                        success_count += 1
                    else:
                        file_info['status'] = '转换失败'
                        failed_count += 1
        
        self.update_files_table()
        
        self.btn_convert.setEnabled(True)
        self.btn_select_files.setEnabled(True)
        self.btn_select_folder.setEnabled(True)
        
        self.progress_bar.setValue(100)
        self.progress_label.setText(f"转换完成！成功: {success_count}, 失败: {failed_count}")
        
        if success_count > 0:
            reply = QMessageBox.question(
                self, "转换完成", 
                f"成功转换 {success_count} 个文件\n失败: {failed_count} 个\n\n是否打开输出文件夹？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                os.startfile(self.parent.output_directory)
    
    def on_error_occurred(self, error_message):
        """处理转换错误"""
        print(f"错误: {error_message}")


class VideoCompressionTab(QWidget):
    """视频压缩标签页 - 提供视频选择、压缩和进度显示功能"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """初始化UI布局"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        self.drag_frame = DragDropFrame()
        self.drag_frame.icon_label.setText("🎬")
        self.drag_frame.text_label.setText("拖拽视频文件到此处\n支持 MP4, AVI, MKV, MOV 等格式")
        layout.addWidget(self.drag_frame)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.btn_select_files = QPushButton(" 选择视频")
        self.btn_clear = QPushButton(" 清空列表")
        
        button_layout.addWidget(self.btn_select_files)
        button_layout.addWidget(self.btn_clear)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        files_group = QGroupBox("待压缩视频列表")
        files_layout = QVBoxLayout(files_group)
        
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(["文件路径", "文件名", "原始大小", "状态"])
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.files_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.files_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.files_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.files_table.setColumnWidth(1, 150)
        self.files_table.setColumnWidth(2, 100)
        self.files_table.setColumnWidth(3, 100)
        self.files_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.files_table.setAlternatingRowColors(True)
        files_layout.addWidget(self.files_table)
        
        self.files_info_label = QLabel("已选择 0 个视频")
        self.files_info_label.setStyleSheet("font-size: 12px;")
        files_layout.addWidget(self.files_info_label)
        
        layout.addWidget(files_group)
        
        self.video_settings = VideoCompressionSettings()
        layout.addWidget(self.video_settings)
        
        self.progress_section = QVBoxLayout()
        self.progress_section.setSpacing(8)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.progress_label = QLabel("准备就绪")
        self.progress_label.setStyleSheet("font-size: 12px;")
        
        self.progress_section.addWidget(self.progress_bar)
        self.progress_section.addWidget(self.progress_label)
        
        layout.addLayout(self.progress_section)
        
        self.btn_compress = QPushButton("开始压缩")
        self.btn_compress.setEnabled(False)
        layout.addWidget(self.btn_compress)
    
    def setup_connections(self):
        """连接信号和槽"""
        self.btn_select_files.clicked.connect(self.select_files)
        self.btn_clear.clicked.connect(self.clear_files)
        self.video_settings.btn_browse.clicked.connect(self.select_output_directory)
        self.btn_compress.clicked.connect(self.start_compression)
        
        self.drag_frame.set_drag_enter_handler(self.dragEnterEvent)
        self.drag_frame.set_drop_handler(self.dropEvent)
    
    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """处理拖拽放下事件 - 添加视频文件到列表"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path) and is_video_file(file_path):
                files.append(file_path)
        
        if files:
            self.add_files_to_list(files)
    
    def select_files(self):
        """打开文件选择对话框"""
        file_filter = "视频文件 (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.mpeg *.mpg);;所有文件 (*)"
        files, _ = QFileDialog.getOpenFileNames(self, "选择视频文件", "", file_filter)
        if files:
            self.add_files_to_list(files)
    
    def add_files_to_list(self, files):
        """添加视频文件到压缩列表"""
        existing_paths = [item['path'] for item in self.parent.video_files]
        existing_output_names = [item['output_name'] for item in self.parent.video_files]
        
        for file_path in files:
            if file_path not in existing_paths:
                filename = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                output_name = generate_video_output_name(filename, existing_output_names)
                existing_output_names.append(output_name)
                existing_paths.append(file_path)
                
                self.parent.video_files.append({
                    'path': file_path,
                    'filename': filename,
                    'size': file_size,
                    'output_name': output_name,
                    'status': '等待压缩'
                })
        
        self.update_files_table()
        self.update_files_info()
        self.update_compress_button()
    
    def update_files_table(self):
        """更新视频列表表格显示"""
        self.files_table.setRowCount(len(self.parent.video_files))
        
        for row, file_info in enumerate(self.parent.video_files):
            path_item = QTableWidgetItem(file_info['path'])
            path_item.setToolTip(file_info['path'])
            
            filename_item = QTableWidgetItem(file_info['filename'])
            
            size_str = self.format_size(file_info['size'])
            size_item = QTableWidgetItem(size_str)
            
            status_item = QTableWidgetItem(file_info['status'])
            colors = {'压缩成功': '#27ae60', '压缩失败': '#e74c3c', '压缩中': '#3498db', '等待压缩': '#7f8c8d'}
            color = colors.get(file_info['status'], '#000000')
            status_item.setForeground(QBrush(QColor(color)))
            
            self.files_table.setItem(row, 0, path_item)
            self.files_table.setItem(row, 1, filename_item)
            self.files_table.setItem(row, 2, size_item)
            self.files_table.setItem(row, 3, status_item)
    
    def format_size(self, size):
        """格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    
    def update_files_info(self):
        """更新视频信息标签"""
        self.files_info_label.setText(f"已选择 {len(self.parent.video_files)} 个视频")
    
    def update_compress_button(self):
        """根据视频和输出目录状态启用/禁用压缩按钮"""
        has_videos = len(self.parent.video_files) > 0
        has_output = bool(self.video_settings.get_output_path())
        self.btn_compress.setEnabled(has_videos and has_output)
    
    def clear_files(self):
        """清空视频列表"""
        self.parent.video_files = []
        self.update_files_table()
        self.update_files_info()
        self.update_compress_button()
    
    def select_output_directory(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录", "")
        if directory:
            self.parent.video_output_directory = directory
            self.video_settings.path_edit.setText(directory)
            self.update_compress_button()
    
    def start_compression(self):
        """开始视频压缩任务"""
        if not self.parent.video_files:
            QMessageBox.warning(self, "警告", "请先选择要压缩的视频")
            return
        
        if not self.parent.video_output_directory:
            QMessageBox.warning(self, "警告", "请选择输出目录")
            return
        
        quality = self.video_settings.get_quality()
        
        self.btn_compress.setEnabled(False)
        self.btn_select_files.setEnabled(False)
        self.btn_clear.setEnabled(False)
        
        for file_info in self.parent.video_files:
            file_info['status'] = '等待压缩'
        self.update_files_table()
        
        files_to_compress = []
        for file_info in self.parent.video_files:
            output_path = os.path.join(self.parent.video_output_directory, file_info['output_name'])
            files_to_compress.append({
                'path': file_info['path'],
                'output_path': output_path
            })
        
        self.worker = VideoCompressionWorker(files_to_compress, self.parent.video_output_directory, quality)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.compression_complete.connect(self.on_compression_complete)
        self.worker.error_occurred.connect(self.on_error_occurred)
        self.worker.start()
    
    def on_progress_updated(self, progress, message):
        """更新压缩进度"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
    
    def on_compression_complete(self, results):
        """处理压缩完成事件"""
        success_count = 0
        failed_count = 0
        
        for file_info in self.parent.video_files:
            input_path = file_info['path']
            if input_path in results:
                if results[input_path]['success']:
                    file_info['status'] = '压缩成功'
                    success_count += 1
                else:
                    file_info['status'] = '压缩失败'
                    failed_count += 1
        
        self.update_files_table()
        
        self.btn_compress.setEnabled(True)
        self.btn_select_files.setEnabled(True)
        self.btn_clear.setEnabled(True)
        
        self.progress_bar.setValue(100)
        self.progress_label.setText(f"压缩完成！成功: {success_count}, 失败: {failed_count}")
        
        if success_count > 0:
            reply = QMessageBox.question(
                self, "压缩完成", 
                f"成功压缩 {success_count} 个视频\n失败: {failed_count} 个\n\n是否打开输出文件夹？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                os.startfile(self.parent.video_output_directory)
    
    def on_error_occurred(self, error_message):
        """处理压缩错误"""
        print(f"错误: {error_message}")


class ImageConverterApp(QMainWindow):
    """主应用窗口 - 图片转换与视频压缩工具"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Img2WebP - 图片转换与视频压缩工具")
        self.setWindowIcon(QIcon(get_default_icon()))
        self.resize(900, 700)
        
        self.image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif']
        self.files_to_convert = []
        self.output_directory = ""
        
        self.video_files = []
        self.video_output_directory = ""
        
        self.setup_ui()
        self.check_ffmpeg()
    
    def check_ffmpeg(self):
        """检查FFmpeg是否安装"""
        installed, message = check_ffmpeg()
        self.video_tab.video_settings.set_ffmpeg_status(installed, message)
    
    def setup_ui(self):
        """初始化UI布局"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        main_layout.addWidget(TitleLabel("Img2WebP - 图片转换与视频压缩工具"))
        
        self.tabs = QTabWidget()
        
        self.image_tab = ImageConversionTab(self)
        self.tabs.addTab(self.image_tab, "🖼️ 图片转WebP")
        
        self.video_tab = VideoCompressionTab(self)
        self.tabs.addTab(self.video_tab, "🎬 视频压缩")
        
        main_layout.addWidget(self.tabs)
