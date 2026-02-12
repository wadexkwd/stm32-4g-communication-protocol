#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查 PySide6 WebEngine 版本和详细信息
"""

import sys
import os

def check_pyside6_info():
    """检查 PySide6 详细信息"""
    print("=== PySide6 信息 ===")
    
    # 基本导入检查
    try:
        import PySide6
        print(f"PySide6 版本: {PySide6.__version__}")
        print(f"PySide6 路径: {PySide6.__file__}")
    except Exception as e:
        print(f"PySide6 导入失败: {e}")
        return False
    
    try:
        from PySide6 import QtCore
        print(f"\nQtCore 版本: {QtCore.__version__}")
        print(f"QtCore 路径: {QtCore.__file__}")
    except Exception as e:
        print(f"QtCore 导入失败: {e}")
    
    try:
        from PySide6 import QtWidgets
        print(f"\nQtWidgets 版本: {QtWidgets.__version__}")
        print(f"QtWidgets 路径: {QtWidgets.__file__}")
    except Exception as e:
        print(f"QtWidgets 导入失败: {e}")
    
    try:
        from PySide6 import QtWebEngineWidgets
        print(f"\nQtWebEngineWidgets 版本: {QtWebEngineWidgets.__version__}")
        print(f"QtWebEngineWidgets 路径: {QtWebEngineWidgets.__file__}")
    except Exception as e:
        print(f"QtWebEngineWidgets 导入失败: {e}")
        return False
    
    try:
        from PySide6 import QtWebEngineCore
        print(f"\nQtWebEngineCore 版本: {QtWebEngineCore.__version__}")
        print(f"QtWebEngineCore 路径: {QtWebEngineCore.__file__}")
    except Exception as e:
        print(f"QtWebEngineCore 导入失败: {e}")
    
    # 检查 Qt WebEngine 运行时信息
    try:
        from PySide6.QtWebEngineCore import QWebEngineProfile
        profile = QWebEngineProfile.defaultProfile()
        print(f"\nWebEngine 缓存路径: {profile.cachePath()}")
        print(f"WebEngine 持久存储路径: {profile.persistentStoragePath()}")
        
        # 检查是否有可用的存储路径
        if os.path.exists(profile.cachePath()):
            print(f"缓存路径存在: {profile.cachePath()}")
        if os.path.exists(profile.persistentStoragePath()):
            print(f"持久存储路径存在: {profile.persistentStoragePath()}")
            
    except Exception as e:
        print(f"WebEngineProfile 检查失败: {e}")
    
    return True

def check_system_info():
    """检查系统信息"""
    print("\n=== 系统信息 ===")
    print(f"操作系统: {sys.platform}")
    print(f"系统: {os.name}")
    print(f"Python 版本: {sys.version}")
    print(f"版本信息: {sys.version_info}")
    print(f"用户: {os.getenv('USERNAME')}")
    print(f"临时目录: {os.getenv('TEMP')}")

def check_modules():
    """检查已安装的模块"""
    print("\n=== 已安装的模块 ===")
    try:
        import subprocess
        output = subprocess.check_output([sys.executable, "-m", "pip", "list"], 
                                       universal_newlines=True, shell=True)
        
        # 筛选 PySide6 相关模块
        print("PySide6 相关模块:")
        for line in output.split('\n'):
            if 'PySide6' in line:
                print(line.strip())
                
    except Exception as e:
        print(f"模块检查失败: {e}")

def main():
    """主函数"""
    print("开始检查 PySide6 WebEngine...")
    print("-" * 50)
    
    # 检查系统信息
    check_system_info()
    
    print("-" * 50)
    
    # 检查模块信息
    check_modules()
    
    print("-" * 50)
    
    # 检查 PySide6 信息
    success = check_pyside6_info()
    
    if success:
        print("\n" + "-" * 50)
        print("✅ Qt WebEngine 配置检查通过")
    else:
        print("\n" + "-" * 50)
        print("❌ Qt WebEngine 配置检查失败")
    
    print("\n检查完成")

if __name__ == "__main__":
    main()