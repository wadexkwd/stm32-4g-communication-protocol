#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接从控制台运行的地图测试程序
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer

class MapWindow(QMainWindow):
    """地图测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("地图控制台测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 布局
        layout = QVBoxLayout(central_widget)
        
        # 地图视图
        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)
        
        # 连接信号
        self.map_view.loadFinished.connect(self.on_load_finished)
        self.map_view.titleChanged.connect(self.on_title_changed)
        self.map_view.urlChanged.connect(self.on_url_changed)
        
        # 加载地图
        self.load_map()
    
    def load_map(self):
        """加载地图"""
        print("正在加载地图...")
        
        # 使用本地 HTML 文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_map_simple.html")
        
        print(f"HTML 文件路径: {html_file}")
        
        if os.path.exists(html_file):
            print("HTML 文件存在")
            file_url = QUrl.fromLocalFile(html_file)
            print(f"加载 URL: {file_url.toString()}")
            
            self.map_view.load(file_url)
            print("地图加载命令已发送")
        else:
            print(f"错误: HTML 文件不存在: {html_file}")

    def on_load_finished(self, success):
        """加载完成回调"""
        print(f"加载完成: {success}")
        
        if success:
            print("地图页面加载成功")
        else:
            print("地图页面加载失败")

    def on_title_changed(self, title):
        """标题变化回调"""
        print(f"页面标题: {title}")

    def on_url_changed(self, url):
        """URL 变化回调"""
        print(f"URL: {url.toString()}")

def main():
    """主函数"""
    print("=== 地图组件测试程序 ===")
    
    # 创建应用程序
    app = QApplication(sys.argv)
    
    print("应用程序创建成功")
    
    try:
        # 创建并显示窗口
        window = MapWindow()
        window.show()
        print("窗口显示成功")
        
        # 设置定时器以定期打印状态
        timer = QTimer()
        timer.timeout.connect(lambda: print("程序仍在运行..."))
        timer.start(5000)
        
        print("定时器设置成功")
        
        # 运行事件循环
        print("运行事件循环...")
        result = app.exec()
        print(f"应用程序退出，返回码: {result}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        print(f"堆栈跟踪: {traceback.format_exc()}")
        result = 1
    
    print("\n=== 程序结束 ===")
    sys.exit(result)

if __name__ == "__main__":
    # 确保程序在运行时输出到控制台
    import sys
    sys.stdout.flush()
    main()