#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
获取status text的具体内容
"""

import sys
import os
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineCore import QWebEnginePage

class DebugPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        print(f"JS {level}: {message}")

class GetStatusWindow(QMainWindow):
    """获取status text的窗口"""
    
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle("Get Status")
        self.setGeometry(100, 100, 800, 600)
        
        self.app = app
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.map_view = QWebEngineView()
        self.map_view.setPage(DebugPage())
        
        settings = self.map_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        
        layout.addWidget(self.map_view)
        
        self.map_view.loadFinished.connect(self.on_load_finished)
        
        self.load_test_page()
        
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.timeout_timer.start(20000)

    def load_test_page(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_script_loading.html")
        
        if os.path.exists(html_file):
            file_url = QUrl.fromLocalFile(html_file)
            self.map_view.load(file_url)
        else:
            print("Error: HTML file not found")
            self.app.quit()

    def on_load_finished(self, success):
        if success:
            self.get_status_text()
        else:
            print("Page load failed")
            self.app.quit()

    def get_status_text(self):
        print("Getting status text...")
        
        self.map_view.page().runJavaScript(
            "document.getElementById('status').textContent",
            self.print_status
        )

    def print_status(self, text):
        print("\n=== Status Text ===\n")
        print(text)
        print("\n=== End Status ===\n")
        
        QTimer.singleShot(1000, self.app.quit)

    def on_timeout(self):
        print("Timeout")
        self.app.quit()

def main():
    app = QApplication(sys.argv)
    
    try:
        window = GetStatusWindow(app)
        window.show()
        result = app.exec()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())
        result = 1
    
    sys.exit(result)

if __name__ == "__main__":
    main()