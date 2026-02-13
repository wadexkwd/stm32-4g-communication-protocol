#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接在代码中创建HTML页面
"""

import sys
import os
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineCore import QWebEnginePage


class InlineHTMLTestWindow(QMainWindow):
    """直接创建HTML页面的测试窗口"""
    
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle("Inline HTML Test")
        self.setGeometry(100, 100, 1200, 800)
        
        self.app = app
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.map_view = QWebEngineView()
        
        profile = QWebEngineProfile.defaultProfile()
        
        settings = self.map_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        
        # 输出页面加载信息
        page = self.map_view.page()
        
        class DebugPage(QWebEnginePage):
            def javaScriptConsoleMessage(self, level, message, line_number, source_id):
                print(f"JS {level}: {message}")
                
        self.map_view.setPage(DebugPage())
        
        layout.addWidget(self.map_view)
        
        self.map_view.loadFinished.connect(self.on_load_finished)
        
        self.load_inline_html()
        
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.timeout_timer.start(30000)

    def load_inline_html(self):
        """直接加载HTML字符串"""
        print("Loading inline HTML...")
        
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inline AMap Test</title>
    <style>
        #status {
            padding: 10px;
            margin: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            white-space: pre-wrap;
            font-family: monospace;
        }
        #map-container {
            width: 800px;
            height: 400px;
            margin: 20px;
            border: 1px solid #ddd;
        }
    </style>
    
    <script type="text/javascript">
        window._AMapSecurityConfig = {
            securityJsCode: "dd1127e11e1f2d5504a2f2ec9824eb78"
        };
    </script>
    <script type="text/javascript" src="https://webapi.amap.com/maps?v=2.0&key=431d3bb1fa78eef96736dc499113fca2"></script>
</head>
<body>
    <h1>Direct HTML Test</h1>
    
    <div id="status"></div>
    
    <div id="map-container"></div>
    
    <script type="text/javascript">
        function log(msg, isError) {
            const statusDiv = document.getElementById('status');
            const color = isError ? 'red' : 'green';
            statusDiv.innerHTML += `[${new Date().toLocaleTimeString()}] <span style="color:${color}">${msg}</span>\\n`;
            console.log(msg);
        }
        
        log('Inline HTML script executed');
        
        // 检查AMap
        if (typeof AMap !== 'undefined') {
            log('✅ AMap API loaded');
            
            try {
                const map = new AMap.Map('map-container', {
                    center: [116.397428, 39.90923],
                    zoom: 10
                });
                log('✅ Map created');
            } catch (e) {
                log(`❌ Error: ${e.message}`, true);
            }
        } else {
            log('❌ AMap API NOT loaded', true);
        }
        
        log('Script execution complete');
    </script>
</body>
</html>
        """.strip()
        
        self.map_view.setHtml(html_content)
        print("HTML content loaded")

    def on_load_finished(self, success):
        print("Load finished: {}".format(success))
        
        if success:
            print("Page loaded successfully")
            self.check_page_content()
        else:
            print("Page load failed")
            self.app.quit()

    def check_page_content(self):
        print("Checking page content...")
        
        self.map_view.page().runJavaScript(
            "typeof AMap",
            lambda type: print("AMap type: {}".format(type))
        )
        
        self.map_view.page().runJavaScript(
            "document.getElementById('status').textContent",
            lambda text: print("Status text length: {}".format(len(text.strip())))
        )
        
        self.map_view.page().runJavaScript(
            "document.getElementById('status').textContent",
            lambda text: print("Status content: {}".format(text.strip()[:300]))
        )
        
        QTimer.singleShot(10000, self.app.quit)

    def on_timeout(self):
        print("Program timeout")
        self.app.quit()


def main():
    print("=== Inline HTML Test ===")
    print("Python version: {}".format(sys.version))
    
    app = QApplication(sys.argv)
    
    try:
        window = InlineHTMLTestWindow(app)
        window.show()
        
        start_time = time.time()
        result = app.exec()
        elapsed = time.time() - start_time
        print("Application runtime: {:.1f} sec".format(elapsed))
        
    except Exception as e:
        print("\nError: {}".format(e))
        import traceback
        print("Stack trace: {}".format(traceback.format_exc()))
        result = 1
    
    print("\n=== Test Finished ===")
    sys.exit(result)

if __name__ == "__main__":
    main()