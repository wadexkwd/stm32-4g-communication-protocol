#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
详细的网络请求测试
"""

import sys
import os
import time
import urllib.request
import ssl
import socket
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    """拦截和记录网络请求"""
    def __init__(self):
        super().__init__()
        
    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        method = info.requestMethod()
        first_party_url = info.firstPartyUrl().toString()
        
        print(f"[网络请求] {method} {url}")
        print(f"  来源页面: {first_party_url}")
        print(f"  请求类型: {info.resourceType()}")
        
        # 打印请求头
        req = info.requestHeaders()
        for name, value in req.items():
            print(f"  {name}: {value}")
        
        if 'amap' in url or 'webapi' in url:
            print("  🚨 高德地图相关请求")

class NetworkDetailsWindow(QMainWindow):
    """详细网络测试窗口"""
    
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle("网络详情测试")
        self.setGeometry(100, 100, 600, 500)
        
        self.app = app
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.map_view = QWebEngineView()
        
        # 配置 WebEngine
        profile = QWebEngineProfile.defaultProfile()
        
        # 允许所有内容和属性
        settings = self.map_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        
        # 设置拦截器
        interceptor = RequestInterceptor()
        profile.setUrlRequestInterceptor(interceptor)
        
        # 启用网络日志
        profile.setCachePath(os.path.join(os.getcwd(), 'qt', 'webengine_cache'))
        profile.setPersistentStoragePath(os.path.join(os.getcwd(), 'qt', 'webengine_storage'))
        
        print("WebEngine配置完成")
        
        layout.addWidget(self.map_view)
        
        self.map_view.loadFinished.connect(self.on_load_finished)
        self.map_view.urlChanged.connect(lambda url: print(f"URL变化: {url.toString()}"))
        
        self.load_test_page()
        
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.timeout_timer.start(15000)

    def load_test_page(self):
        print("正在加载网络测试页面...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_map_absolute_minimal.html")
        
        if os.path.exists(html_file):
            file_url = QUrl.fromLocalFile(html_file)
            self.map_view.load(file_url)
            print(f"加载 URL: {file_url.toString()}")
        else:
            print(f"错误: HTML 文件不存在: {html_file}")
            self.app.quit()

    def on_load_finished(self, success):
        print(f"\n加载完成: {success}")
        
        if success:
            print("页面加载成功")
            self.check_request_status()
        else:
            print("页面加载失败")
            self.app.quit()

    def check_request_status(self):
        print("\n=== 检查页面状态 ===")
        
        # 检查网络状态
        self.map_view.page().runJavaScript(
            "navigator.onLine",
            lambda online: print(f"在线状态: {online}")
        )
        
        # 检查资源加载
        self.map_view.page().runJavaScript(
            "document.readyState",
            lambda state: print(f"文档状态: {state}")
        )
        
        # 检查脚本是否加载成功
        self.map_view.page().runJavaScript(
            "document.querySelectorAll('script[src]').length",
            lambda count: print(f"外部脚本数量: {count}")
        )
        
        QTimer.singleShot(3000, self.app.quit)

    def on_timeout(self):
        print("\n⚠️ 程序执行超时")
        self.app.quit()

def test_direct_http_access():
    """测试直接HTTP访问"""
    print("\n=== 直接HTTP访问测试 ===")
    
    test_urls = [
        "https://webapi.amap.com/maps?v=2.0&key=431d3bb1fa78eef96736dc499113fca2",
        "https://httpbin.org/get",
        "https://www.baidu.com"
    ]
    
    for url in test_urls:
        try:
            print(f"\n测试 {url}")
            
            context = ssl._create_unverified_context()
            start_time = time.time()
            with urllib.request.urlopen(url, context=context, timeout=10) as response:
                content_type = response.getheader('Content-Type', 'unknown')
                content_length = response.getheader('Content-Length', 'unknown')
                
                print(f"  ✅ 响应状态: {response.status}")
                print(f"  响应时间: {time.time() - start_time:.2f}秒")
                print(f"  Content-Type: {content_type}")
                print(f"  Content-Length: {content_length}")
                
                if 'amap' in url:
                    print(f"  🎉 高德地图API访问成功")
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")

def main():
    """主函数"""
    print("=== 网络详情测试 ===")
    print(f"Python 版本: {sys.version}")
    print(f"PySide6 WebEngine测试")
    
    test_direct_http_access()
    
    app = QApplication(sys.argv)
    
    try:
        window = NetworkDetailsWindow(app)
        window.show()
        
        start_time = time.time()
        result = app.exec()
        elapsed = time.time() - start_time
        print(f"\n应用程序运行时间: {elapsed:.1f}秒")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        print(f"堆栈跟踪: {traceback.format_exc()}")
        result = 1
    
    print("\n=== 测试结束 ===")
    sys.exit(result)

if __name__ == "__main__":
    main()