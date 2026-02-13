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
from PySide6.QtGui import QFont, QPalette

class LogWindow(QDialog):
    """日志窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("系统日志")
        self.setGeometry(200, 200, 800, 600)
        self.setModal(False)
        
        # 创建UI
        self.create_ui()
        
        # 自动适应系统主题
        self.adjust_theme()
    
    def create_ui(self):
        """创建日志窗口界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 10))
        
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
    
    def adjust_theme(self):
        """根据系统主题调整背景和字体颜色"""
        # 获取当前调色板
        palette = self.log_text.palette()
        
        # 获取背景颜色（跟随主界面或系统）
        bg_color = palette.color(QPalette.Base)
        
        # 计算对比度，自动确定字体颜色（取反）
        # 使用相对亮度算法计算对比度
        r, g, b = bg_color.red(), bg_color.green(), bg_color.blue()
        relative_luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # 如果背景较暗，使用白色字体；如果背景较亮，使用黑色字体
        if relative_luminance < 0.5:
            fg_color = palette.color(QPalette.Light)  # 白色
        else:
            fg_color = palette.color(QPalette.Dark)   # 黑色
        
        # 设置样式
        self.log_text.setStyleSheet(
            f"background-color: rgb({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}); "
            f"color: rgb({fg_color.red()}, {fg_color.green()}, {fg_color.blue()});"
        )
    
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
