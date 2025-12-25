"""
图片格式转换器 - 将各种图片格式转换为WebP格式
支持文件/文件夹上传、拖拽上传、多格式同时转换
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui import ImageConverterApp


def main():
    """主函数 - 创建并运行应用程序"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = ImageConverterApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
