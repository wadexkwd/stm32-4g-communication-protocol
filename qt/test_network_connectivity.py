#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试网络连接
"""

import sys
import os
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEnginePage

class NetworkWebEnginePage(QWebEnginePage):
    """捕获 JavaScript 控制台输出的自定义页面"""
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        level_str = str(level)
        print(f"[JS] {level_str} (line {line_number}): {message}")

class NetworkTestWindow(QMainWindow):
    """测试网络连接的窗口"""
    
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle("网络连接测试")
        self.setGeometry(100, 100, 800, 600)
        
        self.app = app
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.map_view = QWebEngineView()
        self.map_view.setPage(NetworkWebEnginePage())
        
        layout.addWidget(self.map_view)
        
        self.map_view.loadFinished.connect(self.on_load_finished)
        
        self.load_test_page()
        
        # 设置超时
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.timeout_timer.start(20000)

    def load_test_page(self):
        print("正在加载网络测试页面...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_network_connectivity.html")
        
        print(f"HTML 文件路径: {html_file}")
        
        if os.path.exists(html_file):
            file_url = QUrl.fromLocalFile(html_file)
            self.map_view.load(file_url)
            print(f"加载 URL: {file_url.toString()}")
        else:
            print(f"错误: HTML 文件不存在: {html_file}")
            self.app.quit()

    def on_load_finished(self, success):
        print(f"加载完成: {success}")
        
        if success:
            print("页面加载成功")
            self.check_page_content()
        else:
            print("页面加载失败")
            self.app.quit()

    def check_page_content(self):
        """检查页面内容"""
        print("检查页面内容...")
        
        # 检查在线状态
        self.map_view.page().runJavaScript(
            "document.getElementById('online-status').textContent",
            lambda text: print(f"在线状态: {text.strip()}")
        )
        
        # 检查网络类型
        self.map_view.page().runJavaScript(
            "document.getElementById('network-type').textContent",
            lambda text: print(f"网络类型: {text.strip()}")
        )
        
        # 检查 Google CDN 测试
        self.map_view.page().runJavaScript(
            "document.querySelector('#google-cdn').textContent",
            lambda text: print(f"Google CDN: {text.strip()}")
        )
        
        # 检查高德地图测试
        self.map_view.page().runJavaScript(
            "document.querySelector('#amap-api').textContent",
            lambda text: print(f"高德地图API: {text.strip()}")
        )
        
        # 检查 HTTP 测试
        self.map_view.page().runJavaScript(
            "document.querySelector('#http-test').textContent",
            lambda text: print(f"HTTP测试: {text.strip()}")
        )
        
        # 检查所有测试结果
        self.map_view.page().runJavaScript(
            "Array.from(document.querySelectorAll('.test')).map(el => el.className)",
            lambda results: print(f"测试结果: {results}")
        )
        
        # 3秒后退出程序
        QTimer.singleShot(3000, self.app.quit)

    def on_timeout(self):
        """超时处理"""
        print("程序执行超时")
        self.app.quit()

def main():
    """主函数"""
    print("=== 网络连接测试 ===")
    
    app = QApplication(sys.argv)
    
    try:
        window = NetworkTestWindow(app)
        window.show()
        
        start_time = time.time()
        result = app.exec()
        elapsed = time.time() - start_time
        print(f"应用程序运行时间: {elapsed:.1f}秒")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        print(f"堆栈跟踪: {traceback.format_exc()}")
        result = 1
    
    print("\n=== 测试结束 ===")
    sys.exit(result)

if __name__ == "__main__":
    main()