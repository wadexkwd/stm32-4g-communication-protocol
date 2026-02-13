#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试版本的地图组件 - 优化高德地图API加载
"""

import sys
import os
import platform
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer, QCoreApplication
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile

class DebugWebEnginePage(QWebEnginePage):
    """捕获 JavaScript 控制台输出的自定义页面"""
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        level_str = str(level)
        print(f"[JS] {level_str} (line {line_number}): {message}")

class DebugMapWindow(QMainWindow):
    """调试版本的地图窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("地图组件 - 调试版")
        self.setGeometry(100, 100, 1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.map_view = QWebEngineView()
        self.page = DebugWebEnginePage()
        self.map_view.setPage(self.page)
        
        # 配置 WebEngine 设置
        self.setup_web_engine_settings()
        
        layout.addWidget(self.map_view)
        
        # 连接信号
        self.map_view.loadFinished.connect(self.on_load_finished)
        self.map_view.titleChanged.connect(self.on_title_changed)
        self.map_view.urlChanged.connect(self.on_url_changed)
        self.page.featurePermissionRequested.connect(self.on_feature_permission_requested)
        self.page.fullScreenRequested.connect(self.on_full_screen_requested)
        
        self.load_map()

    def setup_web_engine_settings(self):
        """配置 WebEngine 设置"""
        print("配置 WebEngine 设置...")
        
        profile = QWebEngineProfile.defaultProfile()
        
        # 启用网络缓存
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_cache")
        storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_storage")
        
        # 确保目录存在
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(storage_dir, exist_ok=True)
        
        profile.setCachePath(cache_dir)
        profile.setPersistentStoragePath(storage_dir)
        
        print(f"网络缓存路径: {profile.cachePath()}")
        print(f"持久存储路径: {profile.persistentStoragePath()}")
        
        # 打印设置信息
        print("WebEngine 设置:")
        print(f"HTTP缓存最大大小: {profile.httpCacheMaximumSize()}")
        
    def load_map(self):
        print("正在加载地图...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_map_amap_fixed.html")
        
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

    def on_feature_permission_requested(self, url, feature):
        print(f"权限请求: {feature} for {url}")
        self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)

    def on_full_screen_requested(self, request):
        print("全屏请求")
        request.accept()

    def check_map_content(self):
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
        
        # 获取页面内容
        self.map_view.page().runJavaScript(
            "document.documentElement.outerHTML", 
            lambda result: print("页面内容预览:\n" + result[:500])
        )
        
        # 检查状态信息
        self.map_view.page().runJavaScript(
            "document.getElementById('status')?.textContent || '未找到状态元素'",
            lambda text: print(f"状态信息: {text}")
        )
        
        # 检查 AMap 对象
        self.map_view.page().runJavaScript(
            "typeof AMap",
            lambda result: print(f"AMap类型: {result}")
        )
        
        # 检查 window.AMap
        self.map_view.page().runJavaScript(
            "Object.keys(window)",
            lambda result: print(f"Window对象属性数量: {len(result)}")
        )
        
        # 检查脚本加载错误
        self.map_view.page().runJavaScript(
            "document.querySelectorAll('script').length",
            lambda count: print(f"脚本标签数量: {count}")
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
        </body>
        </html>
        """
        self.map_view.setHtml(error_html)

def main():
    print("=== 地图组件调试程序 ===")
    
    app = QApplication(sys.argv)
    
    print(f"系统信息: {platform.system()} {platform.release()}")
    print(f"Python 版本: {sys.version}")
    print(f"应用程序创建成功")
    
    try:
        window = DebugMapWindow()
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