#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# 尝试设置环境变量以解决Qt显示问题
os.environ['QT_QPA_PLATFORM'] = 'windows'
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''

from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

def main():
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("Qt测试")
    window.setGeometry(100, 100, 300, 200)
    
    layout = QVBoxLayout()
    
    label = QLabel("PySide6测试程序")
    label.setAlignment(Qt.AlignCenter)
    label.setFont(QFont("Arial", 14, QFont.Bold))
    
    layout.addWidget(label)
    window.setLayout(layout)
    
    window.show()
    print("窗口已显示")
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    print("PySide6测试程序启动")
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")