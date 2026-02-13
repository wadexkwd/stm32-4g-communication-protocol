#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终的地图组件测试程序 - 修复高德地图API加载问题
"""

import sys
import os
import platform
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings


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
        
        layout.addWidget(self.map_view)
        
        self.map_view.loadFinished.connect(self.on_load_finished)
        self.map_view.titleChanged.connect(self.on_title_changed)
        self.map_view.urlChanged.connect(self.on_url_changed)
        
        self.load_map()
        
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.timeout_timer.start(20000)

    def load_map(self):
        print("正在加载地图...")
        
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>高德地图测试</title>
    <style>
        body { margin: 0; padding: 0; height: 100vh; background-color: #f0f0f0; }
        #map { 
            width: 100%; 
            height: 100%; 
            position: relative;
        }
        .status {
            position: absolute;
            top: 20px;
            left: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        .status.success { color: green; }
        .status.error { color: red; }
        .status.loading { color: orange; }
    </style>
    
    <script type="text/javascript">
        window._AMapSecurityConfig = {
            securityJsCode: "dd1127e11e1f2d5504a2f2ec9824eb78"
        };
    </script>
    
    <script type="text/javascript" src="https://webapi.amap.com/maps?v=2.0&key=431d3bb1fa78eef96736dc499113fca2"></script>
</head>
<body>
    <div id="map">
        <div class="status loading" id="status">
            <strong>地图加载中...</strong><br>
            <small>正在加载地图资源...</small>
        </div>
    </div>

    <script type="text/javascript">
        console.log('JavaScript 脚本开始执行');
        
        // 地图初始化变量
        let map;
        
        // 初始化地图
        function initMap() {
            console.log('开始初始化地图');
            
            try {
                // 初始化地图实例
                map = new AMap.Map('map', {
                    zoom: 13,
                    center: [116.397428, 39.90923],
                    viewMode: '2D',
                    mapStyle: 'amap://styles/normal'
                });
                
                console.log('地图初始化成功');
                
                // 更新状态信息
                document.getElementById('status').className = 'status success';
                document.getElementById('status').innerHTML = `
                    <strong>地图加载成功!</strong><br>
                    <small>高德地图API已准备好</small>
                `;
                
            } catch (error) {
                console.error('地图初始化失败:', error);
                document.getElementById('status').className = 'status error';
                document.getElementById('status').innerHTML = `
                    <strong>地图加载失败!</strong><br>
                    <small>错误: ${error.message}</small>
                `;
            }
        }
        
        // 页面加载完成后初始化
        window.addEventListener('DOMContentLoaded', () => {
            console.log('DOM加载完成');
            
            if (typeof AMap !== 'undefined') {
                console.log('高德地图API已加载');
                initMap();
            } else {
                console.error('高德地图API未加载');
                document.getElementById('status').className = 'status error';
                document.getElementById('status').innerHTML = `
                    <strong>初始化失败!</strong><br>
                    <small>API未加载</small>
                `;
            }
        });
        
        console.log('脚本执行完成');
    </script>
</body>
</html>
        """.strip()
        
        self.map_view.setHtml(html_content)
        print("地图内容已加载")

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
            "document.getElementById('map').getBoundingClientRect()", 
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
            lambda result: print(f"AMap类型: {result}")
        )
        
        QTimer.singleShot(5000, self.app_quit)

    def show_error(self):
        error_html = """
        <html>
        <body style="background-color: #ffcccc; padding: 20px;">
            <h1 style="color: red;">地图加载失败</h1>
            <p>无法加载地图页面。</p>
            <p>请检查：</p>
            <ul>
                <li>PySide6 WebEngine 是否正常工作</li>
                <li>网络连接是否正常</li>
            </ul>
        </body>
        </html>
        """
        self.map_view.setHtml(error_html)
        
        QTimer.singleShot(5000, self.app_quit)

    def app_quit(self):
        print("程序即将退出")
        QTimer.singleShot(500, QApplication.quit)
        
    def on_timeout(self):
        print("程序超时，即将退出")
        self.app_quit()


def main():
    print("=== 地图组件测试程序 ===")
    print(f"系统信息: {platform.system()} {platform.release()}")
    print(f"Python 版本: {sys.version}")
    
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
