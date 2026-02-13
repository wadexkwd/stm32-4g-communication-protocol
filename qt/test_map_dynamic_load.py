#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试动态加载地图 API
"""

import sys
import os
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEnginePage

class DynamicWebEnginePage(QWebEnginePage):
    """捕获 JavaScript 控制台输出的自定义页面"""
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        level_str = str(level)
        print(f"[JS] {level_str} (line {line_number}): {message}")

class DynamicMapWindow(QMainWindow):
    """测试动态加载地图的窗口"""
    
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle("动态加载地图测试")
        self.setGeometry(100, 100, 800, 600)
        
        self.app = app
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.map_view = QWebEngineView()
        self.map_view.setPage(DynamicWebEnginePage())
        
        layout.addWidget(self.map_view)
        
        self.map_view.loadFinished.connect(self.on_load_finished)
        
        self.load_test_page()
        
        # 设置超时
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.timeout_timer.start(18000)

    def load_test_page(self):
        print("正在加载测试页面...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_map_dynamic_load.html")
        
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
        
        # 检查安全配置
        self.map_view.page().runJavaScript(
            "typeof window._AMapSecurityConfig",
            lambda result: print(f"安全配置类型: {result}")
        )
        
        # 检查脚本标签
        self.map_view.page().runJavaScript(
            "document.querySelectorAll('script[src*=\"amap\"]').length",
            lambda count: print(f"AMap脚本标签数量: {count}")
        )
        
        # 检查脚本状态
        self.map_view.page().runJavaScript(
            "document.getElementById('script-state').textContent",
            lambda text: print(f"脚本状态: {text.strip()}")
        )
        
        # 检查 AMap 类型
        self.map_view.page().runJavaScript(
            "typeof AMap",
            lambda type: print(f"AMap类型: {type}")
        )
        
        # 检查执行时间
        self.map_view.page().runJavaScript(
            "document.getElementById('load-time').textContent",
            lambda text: print(f"加载时间: {text}")
        )
        
        # 检查安全配置细节
        self.map_view.page().runJavaScript(
            "document.getElementById('security-config').textContent",
            lambda text: print(f"安全配置细节: {text}")
        )
        
        # 检查状态
        self.map_view.page().runJavaScript(
            "document.getElementById('status').textContent",
            lambda text: print(f"状态信息: {text.strip()}")
        )
        
        # 3秒后退出程序
        QTimer.singleShot(3000, self.app.quit)

    def on_timeout(self):
        """超时处理"""
        print("程序执行超时")
        self.app.quit()

def main():
    """主函数"""
    print("=== 动态加载地图 API 测试 ===")
    
    app = QApplication(sys.argv)
    
    try:
        window = DynamicMapWindow(app)
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