#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终的地图组件测试程序
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl

class FinalMapWindow(QMainWindow):
    """最终的地图窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("地图组件")
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
        
        # 使用本地简单地图 HTML
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_map_simple.html")
        
        print(f"HTML 文件路径: {html_file}")
        
        if os.path.exists(html_file):
            print("HTML 文件存在")
            file_url = QUrl.fromLocalFile(html_file)
            print(f"加载 URL: {file_url.toString()}")
            
            self.map_view.load(file_url)
            print("地图加载命令已发送")
        else:
            print(f"错误: HTML 文件不存在: {html_file}")
            self.show_error()

    def on_load_finished(self, success):
        """加载完成回调"""
        print(f"加载完成: {success}")
        
        if success:
            print("地图页面加载成功")
            # 页面加载成功后，检查地图内容
            self.check_map_content()
        else:
            print("地图页面加载失败")
            self.show_error()

    def on_title_changed(self, title):
        """标题变化回调"""
        print(f"页面标题: {title}")

    def on_url_changed(self, url):
        """URL 变化回调"""
        print(f"URL: {url.toString()}")

    def check_map_content(self):
        """检查地图内容"""
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
        
        # 检查页面内容
        self.map_view.page().runJavaScript(
            "document.documentElement.outerHTML", 
            lambda result: print("页面内容预览:\n" + result[:500])
        )
        
        # 检查是否有地图加载完成消息
        self.map_view.page().runJavaScript(
            "document.getElementById('status')?.textContent || '未找到状态元素'",
            lambda text: print(f"状态信息: {text}")
        )

    def show_error(self):
        """显示错误信息"""
        error_html = """
        <html>
        <body style="background-color: #ffcccc; padding: 20px;">
            <h1 style="color: red;">地图加载失败</h1>
            <p>无法加载地图页面。</p>
            <p>请检查：</p>
            <ul>
                <li>HTML 文件是否存在</li>
                <li>PySide6 WebEngine 是否正常工作</li>
                <li>网络连接是否正常</li>
            </ul>
        </body>
        </html>
        """
        self.map_view.setHtml(error_html)

def main():
    """主函数"""
    print("=== 地图组件测试程序 ===")
    
    # 创建应用程序
    app = QApplication(sys.argv)
    
    print("应用程序创建成功")
    
    try:
        # 创建并显示窗口
        window = FinalMapWindow()
        window.show()
        print("窗口显示成功")
        
        # 运行事件循环
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