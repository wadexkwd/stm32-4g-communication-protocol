#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试使用本地 HTML 文件的地图组件
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView

class MapWindow(QMainWindow):
    """地图测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("本地 HTML 地图测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 布局
        layout = QVBoxLayout(central_widget)
        
        # 地图视图
        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)
        
        # 加载本地 HTML 文件
        self.load_local_html()
    
    def load_local_html(self):
        """加载本地 HTML 文件"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_map_simple.html")
        
        print(f"HTML 文件路径: {html_file}")
        
        if os.path.exists(html_file):
            print("HTML 文件存在")
            file_url = f"file:///{html_file.replace(os.sep, '/')}"
            print(f"加载 URL: {file_url}")
            
            self.map_view.load(file_url)
            print("加载命令已发送")
        else:
            print(f"错误: HTML 文件不存在: {html_file}")

def main():
    """主函数"""
    print("初始化 QApplication...")
    app = QApplication(sys.argv)
    
    print("QApplication 初始化成功")
    app.setStyle("Fusion")
    
    print("创建测试窗口...")
    window = MapWindow()
    
    print("显示窗口...")
    window.show()
    
    print("运行应用程序...")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()