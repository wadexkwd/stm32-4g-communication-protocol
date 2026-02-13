#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化后的地图组件测试程序
"""

import sys
import os
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl

class MapWindow(QMainWindow):
    """地图测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("优化后的地图组件测试")
        self.setGeometry(100, 100, 1000, 700)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 布局
        layout = QVBoxLayout(central_widget)
        
        # 地图视图
        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)
        
        # 连接信号
        self.map_view.loadFinished.connect(self.on_load_finished)
        self.map_view.titleChanged.connect(self.on_title_changed)
        self.map_view.urlChanged.connect(self.on_url_changed)
        
        # 加载地图
        self.load_map()
    
    def load_map(self):
        """加载地图"""
        print("正在加载地图...")
        
        # 使用本地 HTML 文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_map_amap.html")
        
        print(f"HTML 文件路径: {html_file}")
        
        if os.path.exists(html_file):
            print("HTML 文件存在")
            file_url = QUrl.fromLocalFile(html_file)
            print(f"加载 URL: {file_url.toString()}")
            
            self.map_view.load(file_url)
            print("地图加载命令已发送")
        else:
            print(f"错误: HTML 文件不存在: {html_file}")
            # 显示错误信息
            error_html = """
            <html>
            <body style="background-color: #ffcccc; padding: 20px;">
                <h1 style="color: red;">错误</h1>
                <p>无法找到地图 HTML 文件</p>
                <p>路径: {}</p>
            </body>
            </html>
            """.format(html_file)
            self.map_view.setHtml(error_html)
    
    def on_load_finished(self, success):
        """加载完成回调"""
        print(f"加载完成: {success}")
        
        if success:
            # 页面加载成功
            print("地图页面加载成功")
            
            # 检查页面内容
            self.map_view.page().runJavaScript(
                "document.documentElement.outerHTML", 
                self.on_js_result
            )
            
            # 检查页面可见性
            self.map_view.page().runJavaScript(
                "document.hidden", 
                lambda hidden: print(f"页面是否隐藏: {hidden}")
            )
            
            # 检查地图容器尺寸
            self.map_view.page().runJavaScript(
                "document.getElementById('map').getBoundingClientRect()", 
                lambda rect: print(f"地图容器尺寸: {rect}")
            )
            
        else:
            print("地图页面加载失败")
    
    def on_title_changed(self, title):
        """标题变化回调"""
        print(f"页面标题: {title}")
    
    def on_url_changed(self, url):
        """URL 变化回调"""
        print(f"URL: {url.toString()}")
    
    def on_js_result(self, result):
        """JavaScript 结果回调"""
        if result:
            print("页面内容预览:")
            print(result[:500])
        else:
            print("页面内容获取失败")

def main():
    """主函数"""
    print("=== 地图组件测试程序 ===")
    
    # 初始化应用
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("地图组件测试")
    app.setApplicationVersion("1.0")
    app.setStyle("Fusion")
    
    print("应用程序初始化成功")
    
    try:
        # 创建窗口
        window = MapWindow()
        
        # 显示窗口
        window.show()
        print("窗口已显示")
        
        # 运行应用程序
        print("运行应用程序...")
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