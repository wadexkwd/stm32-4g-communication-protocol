#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查 PySide6-WebEngine 是否可用
"""

import sys

def check_webengine_import():
    """检查 PySide6-WebEngine 是否可以正常导入"""
    print("检查 PySide6-WebEngine 导入...")
    
    try:
        from PySide6 import QtWebEngineWidgets
        print("PySide6.QtWebEngineWidgets 导入成功")
    except ImportError as e:
        print(f"PySide6.QtWebEngineWidgets 导入失败: {e}")
    
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
        print("QWebEngineView 导入成功")
        return True
    except ImportError as e:
        print(f"QWebEngineView 导入失败: {e}")
        return False

def check_pyside6_version():
    """检查 PySide6 版本"""
    try:
        import PySide6
        print(f"PySide6 版本: {PySide6.__version__}")
    except Exception as e:
        print(f"无法获取 PySide6 版本: {e}")

def check_shiboken():
    """检查 shiboken6 是否可用"""
    try:
        import shiboken6
        print(f"shiboken6 版本: {shiboken6.__version__}")
    except Exception as e:
        print(f"shiboken6 不可用: {e}")

if __name__ == "__main__":
    print("开始检查 PySide6-WebEngine...")
    print("-" * 50)
    
    # 检查 Python 版本
    print(f"Python 版本: {sys.version}")
    print(f"版本信息: {sys.version_info}")
    
    print("-" * 50)
    
    check_pyside6_version()
    
    print("-" * 50)
    
    check_shiboken()
    
    print("-" * 50)
    
    if check_webengine_import():
        print("-" * 50)
        print("PySide6-WebEngine 组件可用")
    else:
        print("-" * 50)
        print("PySide6-WebEngine 组件不可用")
    
    print("\n检查完成")