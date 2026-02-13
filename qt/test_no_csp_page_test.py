#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试无CSP页面
"""

import sys
import os
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

class NoCSPTestWindow(QMainWindow):
    """无CSP测试窗口"""
    
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle("无CSP页面测试")
        self.setGeometry(100, 100, 800, 600)
        
        self.app = app
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.map_view = QWebEngineView()
        
        # 配置 WebEngine
        profile = QWebEngineProfile.defaultProfile()
        
        settings = self.map_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        
        # 设置拦截器
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
        self.map_view.page().profile().downloadRequested.connect(
            lambda d: print("Download requested: {}".format(d.url().toString()))
        )
        
        self.load_test_page()
        
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.timeout_timer.start(20000)

    def load_test_page(self):
        print("Loading test page...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_no_csp_page.html")
        
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
        
        self.map_view.page().runJavaScript(
            "navigator.onLine",
            lambda online: print("Online status: {}".format(online))
        )
        
        self.map_view.page().runJavaScript(
            "document.readyState",
            lambda state: print("Document state: {}".format(state))
        )
        
        self.map_view.page().runJavaScript(
            "typeof AMap",
            lambda type: print("AMap type: {}".format(type))
        )
        
        self.map_view.page().runJavaScript(
            "document.getElementById('status').textContent",
            lambda text: print("Status text: {}".format(text.strip()))
        )
        
        self.map_view.page().runJavaScript(
            "document.getElementById('status').className",
            lambda cls: print("Status class: {}".format(cls))
        )
        
        QTimer.singleShot(5000, self.app.quit)

    def on_timeout(self):
        print("Program timeout")
        self.app.quit()

def main():
    """Main function"""
    print("=== 无CSP页面测试 ===")
    print("Python version: {}".format(sys.version))
    
    app = QApplication(sys.argv)
    
    try:
        window = NoCSPTestWindow(app)
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