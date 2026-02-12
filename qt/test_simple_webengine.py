#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 WebEngineView 基本功能
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView

class SimpleWebEngineWindow(QMainWindow):
    """简单的 WebEngineView 测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebEngineView 基本功能测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 布局
        layout = QVBoxLayout(central_widget)
        
        # 简单的 Web 视图
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
        # 测试简单的 HTML 显示
        self.test_simple_html()
        
        # 测试加载外部网页
        # self.test_external_url()
    
    def test_simple_html(self):
        """测试显示简单的 HTML"""
        simple_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>简单测试页面</title>
            <style>
                body {
                    background-color: #f0f0f0;
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    margin: 0;
                    height: 100%;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                }
                .status {
                    color: green;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>WebEngineView 测试页面</h1>
                <p class="status">✓ 页面加载成功！</p>
                <p>这是一个简单的 HTML 页面，用于测试 WebEngineView 的基本显示功能。</p>
                <ul>
                    <li>如果您能看到这个页面，说明 WebEngineView 工作正常</li>
                    <li>检查页面是否有样式（背景色、阴影等）</li>
                    <li>验证中文显示是否正常</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        print("正在加载简单 HTML 页面...")
        self.web_view.setHtml(simple_html)
        print("HTML 页面加载完成")
    
    def test_external_url(self):
        """测试加载外部网页"""
        print("正在加载外部网页...")
        self.web_view.load("https://www.baidu.com")
        print("外部网页加载命令已发送")

def main():
    """主函数"""
    print("初始化 QApplication...")
    app = QApplication(sys.argv)
    
    print("QApplication 初始化成功")
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建测试窗口
    window = SimpleWebEngineWindow()
    window.show()
    print("窗口已显示")
    
    # 运行应用程序
    print("运行应用程序...")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()