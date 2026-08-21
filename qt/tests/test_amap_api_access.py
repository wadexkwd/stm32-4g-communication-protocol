#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的高德地图API访问测试程序
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEnginePage

class SimpleTestPage(QWebEnginePage):
    """捕获 JavaScript 控制台输出的自定义页面"""
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        level_str = str(level)
        print(f"[JS] {level_str} (line {line_number}): {message}")

def main():
    print("=== 简单的高德地图API访问测试 ===")
    
    app = QApplication(sys.argv)
    
    # 创建 WebEngine 视图
    web_view = QWebEngineView()
    web_view.setPage(SimpleTestPage())
    
    def on_load_finished(success):
        print(f"加载完成: {success}")
        
        if success:
            print("HTML页面加载成功")
            
            # 检查页面内容
            web_view.page().runJavaScript("document.documentElement.innerHTML", 
                                        lambda html: print(f"页面内容长度: {len(html)}"))
            
            web_view.page().runJavaScript("document.title", 
                                        lambda title: print(f"页面标题: {title}"))
            
            # 检查状态信息
            web_view.page().runJavaScript(
                "document.getElementById('status')?.textContent || '未找到状态元素'",
                lambda status: print(f"状态信息: {status}")
            )
            
            # 检查调试信息
            web_view.page().runJavaScript(
                "document.getElementById('debug-info')?.innerHTML || '未找到调试信息'",
                lambda debug: print(f"调试信息:\n{debug}")
            )
            
            # 检查 AMap 对象是否已加载
            web_view.page().runJavaScript("typeof AMap", 
                                        lambda amap_type: print(f"AMap类型: {amap_type}"))
        else:
            print("HTML页面加载失败")
        
        # 5秒后退出
        QTimer.singleShot(5000, app.quit)
    
    # 连接加载完成信号
    web_view.loadFinished.connect(on_load_finished)
    
    # 加载地图页面
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_file = os.path.join(current_dir, "test_map_amap_fixed.html")
    
    if os.path.exists(html_file):
        print(f"HTML文件存在: {html_file}")
        file_url = QUrl.fromLocalFile(html_file)
        print(f"加载URL: {file_url.toString()}")
        web_view.load(file_url)
        
        print("地图加载命令已发送")
    else:
        print(f"HTML文件不存在: {html_file}")
        return 1
    
    # 显示窗口（可选，但可能有助于调试）
    web_view.show()
    web_view.setWindowTitle("高德地图API简单测试")
    
    # 运行应用程序
    print("运行应用程序...")
    try:
        result = app.exec()
        print(f"应用程序退出，返回码: {result}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        print(f"堆栈跟踪: {traceback.format_exc()}")
        result = 1
    
    print("=== 测试完成 ===")
    return result

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)