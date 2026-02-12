#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - 日志窗口模块
功能：
- 提供独立的日志窗口显示功能
- 支持日志的添加、清除和窗口管理
"""

from datetime import datetime
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class LogWindow(QDialog):
    """日志窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("系统日志")
        self.setGeometry(200, 200, 800, 600)
        self.setModal(False)
        
        # 创建UI
        self.create_ui()
    
    def create_ui(self):
        """创建日志窗口界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 10))
        self.log_text.setStyleSheet("background-color: #f0f0f0;")
        
        # 清除按钮
        self.clear_btn = QPushButton("清除日志")
        self.clear_btn.clicked.connect(self.clear_log)
        
        # 关闭按钮
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        main_layout.addWidget(self.log_text)
        main_layout.addLayout(button_layout)
    
    def add_log(self, text):
        """添加日志内容"""
        if text.strip():
            # 添加时间戳
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            log_entry = f"[{timestamp}] {text.strip()}"
            self.log_text.append(log_entry)
            
            # 自动滚动到底部
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )
    
    def clear_log(self):
        """清除日志内容"""
        self.log_text.clear()
        print("日志已清除")