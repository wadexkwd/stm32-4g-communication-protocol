#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 Qt WebEngine 错误信息
"""

import sys
import traceback
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile

def main():
    """主函数"""
    print("=== Qt WebEngine 测试 ===")
    print(f"Python 版本: {sys.version}")
    
    try:
        print("\n1. 初始化 QApplication...")
        app = QApplication(sys.argv)
        print("QApplication 初始化成功")
        
        # 检查 WebEngineProfile
        print("\n2. 检查 WebEngineProfile...")
        default_profile = QWebEngineProfile.defaultProfile()
        print("WebEngineProfile 获取成功")
        
        print(f"Cache path: {default_profile.cachePath()}")
        print(f"Persistent storage path: {default_profile.persistentStoragePath()}")
        
        print("\n3. 创建窗口...")
        window = QMainWindow()
        window.setWindowTitle("WebEngine 测试")
        window.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        print("\n4. 创建 WebEngineView...")
        web_view = QWebEngineView()
        
        print("\n5. 显示窗口...")
        window.show()
        
        print("\n6. 加载简单页面...")
        simple_html = """
        <html>
        <body style="background-color: #f0f0f0; padding: 20px;">
            <h1>测试成功!</h1>
            <p style="color: green;">WebEngineView 已正常工作</p>
            <p>Python 版本: %s</p>
        </body>
        </html>
        """ % sys.version
        
        web_view.setHtml(simple_html)
        
        print("\n7. 添加到布局...")
        layout.addWidget(web_view)
        
        print("\n8. 运行应用程序...")
        result = app.exec()
        print(f"应用程序退出代码: {result}")
        
        return result
        
    except Exception as e:
        print(f"\n错误: {e}")
        print(f"\n堆栈跟踪:")
        print(traceback.format_exc())
        return 1
    except SystemExit as e:
        print(f"\n系统退出: {e}")
        return e.code

if __name__ == "__main__":
    result = main()
    print(f"\n程序结束，返回码: {result}")
    sys.exit(result)