#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的网络连接测试程序
"""

import sys
import platform
import urllib.request
import ssl

def test_network_connection():
    """测试网络连接"""
    print("=== 网络连接测试 ===")
    print(f"系统信息: {platform.system()} {platform.release()}")
    print(f"Python 版本: {sys.version}")
    
    test_urls = [
        ("百度", "https://www.baidu.com"),
        ("高德地图", "https://ditu.amap.com"),
        ("高德API", "https://webapi.amap.com/maps?v=2.0&key=431d3bb1fa78eef96736dc499113fca2")
    ]
    
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    for name, url in test_urls:
        print(f"\n测试 {name} ({url})")
        
        try:
            req = urllib.request.Request(url, method='HEAD')
            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                print(f"成功: {response.status} {response.reason}")
                
        except Exception as e:
            print(f"失败: {e}")

if __name__ == "__main__":
    test_network_connection()
    print("\n=== 测试完成 ===")