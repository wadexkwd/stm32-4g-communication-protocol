#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的网络请求测试 - 无编码问题
"""

import sys
import os
import time
import urllib.request
import ssl
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

class SimpleRequestInterceptor(QWebEngineUrlRequestInterceptor):
    """拦截网络请求的简单类"""
    def __init__(self):
        super().__init__()
        
    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        method = info.requestMethod()
        
        print("Network request: {} {}".format(method, url))
        
        if 'amap' in url or 'webapi' in url:
            print("  AMap related request")

class SimpleNetworkWindow(QMainWindow):
    """简单网络测试窗口"""
    
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle("Simple Network Test")
        self.setGeometry(100, 100, 600, 500)
        
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
        
        interceptor = SimpleRequestInterceptor()
        profile.setUrlRequestInterceptor(interceptor)
        
        layout.addWidget(self.map_view)
        
        self.map_view.loadFinished.connect(self.on_load_finished)
        
        self.load_test_page()
        
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.timeout_timer.start(15000)

    def load_test_page(self):
        print("Loading test page...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_map_absolute_minimal.html")
        
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
        
        QTimer.singleShot(3000, self.app.quit)

    def on_timeout(self):
        print("Program timeout")
        self.app.quit()

def test_direct_access():
    """测试直接访问"""
    print("\n--- Direct HTTP Access Test ---")
    
    test_urls = [
        "https://webapi.amap.com/maps?v=2.0&key=431d3bb1fa78eef96736dc499113fca2",
        "https://httpbin.org/get"
    ]
    
    for url in test_urls:
        try:
            print("\nTesting {}".format(url))
            
            context = ssl._create_unverified_context()
            start_time = time.time()
            with urllib.request.urlopen(url, context=context, timeout=10) as response:
                content_type = response.getheader('Content-Type', 'unknown')
                
                print("  Status: {}".format(response.status))
                print("  Time: {:.2f} sec".format(time.time() - start_time))
                print("  Content-Type: {}".format(content_type))
                
                if 'amap' in url:
                    print("  Amap API access successful")
                
        except Exception as e:
            print("  Error: {}".format(e))

def main():
    """Main function"""
    print("=== Simple Network Details Test ===")
    print("Python version: {}".format(sys.version))
    print("Testing PySide6 WebEngine")
    
    test_direct_access()
    
    app = QApplication(sys.argv)
    
    try:
        window = SimpleNetworkWindow(app)
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