#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试网络请求到高德地图服务器
"""

import sys
import time
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


class NetworkTester:
    """网络测试类"""
    
    def __init__(self, app):
        self.app = app
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self.on_finished)
        
        self.start_tests()
        
    def start_tests(self):
        """开始所有测试"""
        print("=== Direct Network Requests Test ===")
        
        # 测试1: 测试基本连通性
        self.test_url("http://www.baidu.com", "Baidu Homepage")
        
        # 测试2: 测试高德地图API
        api_url = "https://webapi.amap.com/maps?v=2.0&key=431d3bb1fa78eef96736dc499113fca2"
        self.test_url(api_url, "AMap API Script")
        
        # 测试3: 测试其他高德地图服务
        self.test_url("https://webapi.amap.com", "AMap Base URL")
        
        # 超时
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.timeout_timer.start(20000)
        
    def test_url(self, url_str, description):
        """测试单个URL"""
        print(f"Testing: {description} ({url_str})")
        
        url = QUrl(url_str)
        request = QNetworkRequest(url)
        
        reply = self.manager.get(request)
        reply.url_str = url_str
        reply.description = description
        
        return reply
        
    def on_finished(self, reply):
        """请求完成处理"""
        description = getattr(reply, 'description', 'Unknown')
        url_str = getattr(reply, 'url_str', 'Unknown')
        
        print(f"\n=== {description} ===")
        
        if reply.error() == QNetworkReply.NoError:
            status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            print(f"Success - Status Code: {status_code}")
            
            content = reply.readAll()
            
            # 打印前200个字符
            content_str = content.data().decode('utf-8')
            if len(content_str) > 200:
                print(f"Content Preview: {content_str[:200]}...")
            else:
                print(f"Content: {content_str}")
                
        else:
            print(f"Error: {reply.error()}")
            print(f"Error String: {reply.errorString()}")
            
    def on_timeout(self):
        """超时处理"""
        print("\n=== Timeout ===")
        self.app.quit()
        


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    tester = NetworkTester(app)
    
    return app.exec()

if __name__ == "__main__":
    result = main()
    print(f"\n=== Test Completed ===")
    sys.exit(result)