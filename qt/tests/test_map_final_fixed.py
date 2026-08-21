#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终的地图组件测试程序 - 修复后的版本
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings

class TestWebEnginePage(QWebEnginePage):
    """捕获 JavaScript 控制台输出的自定义页面"""
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        level_str = str(level)
        print(f"[JS] {level_str} (line {line_number}): {message}")

class FinalMapWindow(QMainWindow):
    """最终的地图窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("地图组件")
        self.setGeometry(100, 100, 1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.map_view = QWebEngineView()
        self.map_view.setPage(TestWebEnginePage())
        
        # 关键的修复设置
        settings = self.map_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.XSSAuditingEnabled, False)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.SpatialNavigationEnabled, True)
        settings.setAttribute(QWebEngineSettings.LinksIncludedInFocusChain, True)
        
        print("WebEngine 设置:")
        print(f"JavaScript 启用: {settings.testAttribute(QWebEngineSettings.JavascriptEnabled)}")
        print(f"本地访问远程URL: {settings.testAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls)}")
        
        layout.addWidget(self.map_view)
        
        self.map_view.loadFinished.connect(self.on_load_finished)
        self.map_view.titleChanged.connect(self.on_title_changed)
        self.map_view.urlChanged.connect(self.on_url_changed)
        
        self.load_map()

    def load_map(self):
        print("正在加载地图...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 尝试使用多个可用的HTML文件
        html_files = [
            os.path.join(current_dir, "test_map_amap_fixed.html"),
            os.path.join(current_dir, "test_map_amap.html"),
    
        ]
        
        html_file = None
        for f in html_files:
            if os.path.exists(f):
                html_file = f
                print(f"使用HTML文件: {html_file}")
                break
        
        if html_file:
            file_url = QUrl.fromLocalFile(html_file)
            print(f"加载 URL: {file_url.toString()}")
            
            self.map_view.load(file_url)
            print("地图加载命令已发送")
        else:
            print("错误: 未找到任何地图HTML文件")
            self.show_error()

    def on_load_finished(self, success):
        print(f"加载完成: {success}")
        
        if success:
            print("地图页面加载成功")
            self.check_map_content()
        else:
            print("地图页面加载失败")
            self.show_error()

    def on_title_changed(self, title):
        print(f"页面标题: {title}")

    def on_url_changed(self, url):
        print(f"URL: {url.toString()}")

    def check_map_content(self):
        self.map_view.page().runJavaScript(
            "document.hidden", 
            lambda hidden: print(f"页面是否隐藏: {hidden}")
        )
        
        self.map_view.page().runJavaScript(
            "document.getElementById('map')?.getBoundingClientRect() || '无地图容器'", 
            lambda rect: print(f"地图容器尺寸: {rect}")
        )
        
        self.map_view.page().runJavaScript(
            "document.documentElement.outerHTML", 
            lambda result: print("页面内容预览:\n" + result[:500])
        )
        
        self.map_view.page().runJavaScript(
            "document.getElementById('status')?.textContent || '未找到状态元素'",
            lambda text: print(f"状态信息: {text}")
        )
        
        self.map_view.page().runJavaScript(
            "typeof AMap",
            lambda amap_type: print(f"AMap类型: {amap_type}")
        )

    def show_error(self):
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
            <p><strong>调试信息:</strong></p>
            <p>Python版本: {}</p>
        </body>
        </html>
        """.format(sys.version)
        self.map_view.setHtml(error_html)

def main():
    print("=== 地图组件测试程序 ===")
    
    app = QApplication(sys.argv)
    
    print("应用程序创建成功")
    
    try:
        window = FinalMapWindow()
        window.show()
        print("窗口显示成功")
        
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