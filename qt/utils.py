#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - 工具模块
功能：
- 提供通用工具类和函数，包括日志重定向器、字符串处理、文件操作等
- 封装常用功能，提高代码复用性和可维护性
"""

import sys
from PySide6.QtCore import QObject, Signal

# 自定义日志重定向器
class StreamRedirector(QObject):
    """重定向标准输出和错误到Qt信号"""
    output_received = Signal(str)
    
    def __init__(self, stream):
        super().__init__()
        self.stream = stream
    
    def write(self, text):
        """重定向写入操作"""
        self.stream.write(text)
        self.output_received.emit(text)
    
    def flush(self):
        """刷新操作"""
        self.stream.flush()