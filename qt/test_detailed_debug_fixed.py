#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
详细调试程序 - 修复版本
"""

import sys
import os
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineUrlRequestInterceptor

class DetailedDebugPage(QWebEnginePage):
    """捕获JavaScript控制台输出的页面类"""
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        level_str = "Unknown"
        if level == QWebEnginePage.InfoMessageLevel:
            level_str = "Info"
        elif level == QWebEnginePage.WarningMessageLevel:
            level_str = "Warning"
        elif level == QWebEnginePage.ErrorMessageLevel:
            level_str = "Error"
            
        print("JS {} ({}:{}): {}".format(level_str, source_id, line_number, message))

class DetailedDebugWindow(QMainWindow):
    """详细调试窗口"""
    
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle("详细调试")
        self.setGeometry(100, 100, 1000, 700)
        
        self.app = app
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.map_view = QWebEngineView()
        self.map_view.setPage(DetailedDebugPage())
        
        # 配置 WebEngine
        profile = QWebEngineProfile.defaultProfile()
        
        settings = self.map_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        
        # 网络拦截器
        class Interceptor(QWebEngineUrlRequestInterceptor):
            def interceptRequest(self, info):
                url = info.requestUrl().toString()
                method = info.requestMethod()
                
                print("Network request: {} {}".format(method, url))
                
                if 'amap' in url or 'webapi' in url:
                    print("  AMap related request")
        
        profile.setUrlRequestInterceptor(Interceptor())
        
        layout.addWidget(self.map_view)
        
        self.map_view.loadFinished.connect(self.on_load_finished)
        
        self.load_test_page()
        
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.timeout_timer.start(20000)

    def load_test_page(self):
        print("Loading detailed test page...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_simple_script.html")
        
        if os.path.exists(html_file):
            file_url = QUrl.fromLocalFile(html_file)
            self.map_view.load(file_url)
            print("Loading URL: {}".format(file_url.toString()))
        else:
            print("Error: HTML file not found: {}".format(html_file))
            self.app.quit()

    def on_load_finished(self, success):
        print("Load finished: {}".format(success))
        
        if success:
            print("Page loaded successfully")
            self.check_page_content()
        else:
            print("Page load failed")
            self.app.quit()

    def check_page_content(self):
        print("Checking page content...")
        
        # 检查AMap对象
        self.map_view.page().runJavaScript(
            "typeof AMap",
            lambda type: print("AMap type: {}".format(type))
        )
        
        # 检查status内容
        self.map_view.page().runJavaScript(
            "document.getElementById('status').innerHTML",
            lambda html: print("Status HTML: {}".format(html))
        )
        
        # 检查document.readyState
        self.map_view.page().runJavaScript(
            "document.readyState",
            lambda state: print("Document state: {}".format(state))
        )
        
        # 检查所有script标签
        self.map_view.page().runJavaScript(
            "Array.from(document.querySelectorAll('script')).map(s => "
            "{src: s.src, id: s.id, loaded: s.src ? 'external' : 'inline'})",
            lambda scripts: print("Scripts: {}".format(len(scripts)))
        )
        
        # 检查是否有网络请求错误
        self.map_view.page().runJavaScript(
            "performance.getEntriesByType('resource')"
            ".filter(entry => entry.entryType === 'resource' && entry.responseStatus !== 200)",
            lambda errors: print("Resource errors: {}".format(len(errors)))
        )
        
        QTimer.singleShot(5000, self.app.quit)

    def on_timeout(self):
        print("Program timeout")
        self.app.quit()

def main():
    """Main function"""
    print("=== 详细调试程序 ===")
    print("Python version: {}".format(sys.version))
    
    app = QApplication(sys.argv)
    
    try:
        window = DetailedDebugWindow(app)
        window.show()
        
        start_time = time.time()
        result = app.exec()
        elapsed = time.time() - start_time
        print("Application runtime: {:.1f} sec".format(elapsed))
        
    except Exception as e:
        print("\nError: {}".format(e))
        import traceback
        print("Stack trace: {}".format(traceback.format_exc()))
        result = 1
    
    print("\n=== Test Finished ===")
    sys.exit(result)

if __name__ == "__main__":
    main()