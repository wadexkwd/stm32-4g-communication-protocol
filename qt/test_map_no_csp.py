#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试无 CSP 限制的地图页面
"""

import sys
import os
import platform
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEnginePage

class DebugWebEnginePage(QWebEnginePage):
    """捕获 JavaScript 控制台输出的自定义页面"""
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        level_str = str(level)
        print(f"[JS] {level_str} (line {line_number}): {message}")

class NoCSPMapWindow(QMainWindow):
    """无 CSP 限制的地图窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("地图测试 - 无 CSP 限制")
        self.setGeometry(100, 100, 1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.map_view = QWebEngineView()
        self.page = DebugWebEnginePage()
        self.map_view.setPage(self.page)
        
        layout.addWidget(self.map_view)
        
        # 连接信号
        self.map_view.loadFinished.connect(self.on_load_finished)
        self.map_view.titleChanged.connect(self.on_title_changed)
        self.map_view.urlChanged.connect(self.on_url_changed)
        
        self.load_map()

    def load_map(self):
        """加载地图"""
        print("正在加载地图...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_map_amap_no_csp.html")
        
        print(f"HTML 文件路径: {html_file}")
        
        if os.path.exists(html_file):
            print("HTML 文件存在")
            file_url = QUrl.fromLocalFile(html_file)
            print(f"加载 URL: {file_url.toString()}")
            
            self.map_view.load(file_url)
            print("地图加载命令已发送")
        else:
            print(f"错误: HTML 文件不存在: {html_file}")
            self.show_error()

    def on_load_finished(self, success):
        """加载完成回调"""
        print(f"加载完成: {success}")
        
        if success:
            print("地图页面加载成功")
            self.check_map_content()
        else:
            print("地图页面加载失败")
            self.show_error()

    def on_title_changed(self, title):
        """标题变化回调"""
        print(f"页面标题: {title}")

    def on_url_changed(self, url):
        """URL 变化回调"""
        print(f"URL: {url.toString()}")

    def check_map_content(self):
        """检查页面内容"""
        self.map_view.page().runJavaScript(
            "typeof AMap",
            lambda result: print(f"AMap类型: {result}")
        )
        
        self.map_view.page().runJavaScript(
            "document.getElementById('status').textContent",
            lambda text: print(f"状态信息: {text.strip()}")
        )

    def show_error(self):
        """显示错误信息"""
        error_html = """
        <html>
        <body style="background-color: #ffcccc; padding: 20px;">
            <h1 style="color: red;">地图加载失败</h1>
            <p>无法加载地图页面。</p>
        </body>
        </html>
        """
        self.map_view.setHtml(error_html)

def main():
    """主函数"""
    print("=== 地图组件测试程序 ===")
    print(f"系统信息: {platform.system()} {platform.release()}")
    print(f"Python 版本: {sys.version}")
    
    app = QApplication(sys.argv)
    
    try:
        window = NoCSPMapWindow()
        window.show()
        print("窗口显示成功")
        
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
    main()