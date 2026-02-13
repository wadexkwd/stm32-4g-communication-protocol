#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
极简版本的地图组件测试程序
"""

import sys
import os
import platform
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEnginePage

class MinimalWebEnginePage(QWebEnginePage):
    """捕获 JavaScript 控制台输出的自定义页面"""
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        level_str = str(level)
        print(f"[JS] {level_str} (line {line_number}): {message}")

class MinimalMapWindow(QMainWindow):
    """极简版本的地图窗口"""
    
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle("地图组件 - 极简版")
        self.setGeometry(100, 100, 800, 600)
        
        self.app = app
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.map_view = QWebEngineView()
        self.map_view.setPage(MinimalWebEnginePage())
        
        layout.addWidget(self.map_view)
        
        self.map_view.loadFinished.connect(self.on_load_finished)
        
        self.load_map()
        
        # 设置超时
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.timeout_timer.start(15000)

    def load_map(self):
        print("正在加载地图...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_map_amap_no_csp.html")
        
        print(f"HTML 文件路径: {html_file}")
        
        if os.path.exists(html_file):
            file_url = QUrl.fromLocalFile(html_file)
            self.map_view.load(file_url)
            print(f"加载 URL: {file_url.toString()}")
        else:
            print(f"错误: HTML 文件不存在: {html_file}")
            self.show_error()

    def on_load_finished(self, success):
        print(f"加载完成: {success}")
        
        if success:
            print("页面加载成功")
            # 检查页面内容
            self.check_map_content()
        else:
            print("页面加载失败")
            self.show_error()

    def check_map_content(self):
        """检查地图内容"""
        print("检查页面内容...")
        
        self.map_view.page().runJavaScript(
            "typeof AMap",
            lambda result: print(f"AMap类型: {result}")
        )
        
        self.map_view.page().runJavaScript(
            "document.getElementById('status').textContent",
            lambda text: print(f"状态信息: {text.strip()}")
        )
        
        # 3秒后退出程序
        QTimer.singleShot(3000, self.app.quit)

    def show_error(self):
        """显示错误信息"""
        self.app.quit()

    def on_timeout(self):
        """超时处理"""
        print("程序执行超时")
        self.app.quit()

def main():
    """主函数"""
    print("=== 地图组件测试程序 ===")
    print(f"系统信息: {platform.system()} {platform.release()}")
    print(f"Python 版本: {sys.version}")
    
    app = QApplication(sys.argv)
    
    try:
        window = MinimalMapWindow(app)
        window.show()
        print("窗口显示成功")
        
        start_time = time.time()
        result = app.exec()
        elapsed = time.time() - start_time
        print(f"应用程序运行时间: {elapsed:.1f}秒")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        print(f"堆栈跟踪: {traceback.format_exc()}")
        result = 1
    
    print("\n=== 程序结束 ===")
    sys.exit(result)

if __name__ == "__main__":
    main()