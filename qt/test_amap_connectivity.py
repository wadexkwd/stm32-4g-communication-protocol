#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试高德地图 API 连通性
"""

import requests
import time
import sys

def test_amap_api():
    """测试高德地图 API 连通性"""
    print("=== 高德地图 API 连通性测试 ===")
    
    api_key = "431d3bb1fa78eef96736dc499113fca2"
    base_url = "https://webapi.amap.com"
    
    test_cases = [
        {
            "name": "地图 API",
            "url": f"{base_url}/maps?v=2.0&key={api_key}",
            "method": "GET"
        },
        {
            "name": "IP 定位",
            "url": f"{base_url}/location/ip?key={api_key}",
            "method": "GET"
        },
        {
            "name": "坐标转换",
            "url": f"{base_url}/v3/assistant/coordinate/convert?locations=116.403874,39.915168&coordsys=gps&key={api_key}",
            "method": "GET"
        },
        {
            "name": "静态地图",
            "url": f"{base_url}/v3/staticmap?location=116.403874,39.915168&zoom=10&size=400*400&markers=large,0xFF0000:A:116.403874,39.915168&key={api_key}",
            "method": "GET",
            "check_content": False
        },
        {
            "name": "简单访问测试",
            "url": "https://httpbin.org/get",
            "method": "GET"
        }
    ]
    
    all_success = True
    
    for test in test_cases:
        print(f"\n--- 测试: {test['name']} ---")
        print(f"URL: {test['url']}")
        
        try:
            start_time = time.time()
            
            if test["method"] == "GET":
                response = requests.get(test["url"], timeout=10)
            else:
                response = requests.post(test["url"], timeout=10)
            
            elapsed = time.time() - start_time
            
            print(f"状态码: {response.status_code}")
            print(f"响应时间: {elapsed:.2f}秒")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                if test.get("check_content", True):
                    print(f"响应长度: {len(response.text)} 字符")
                    print(f"响应前50字符: {repr(response.text[:50])}")
                else:
                    print("响应内容: 二进制数据")
                
                if test["name"] == "地图 API":
                    print("API 响应类型: JavaScript 文件")
                    if "AMap" in response.text:
                        print("✅ 响应中包含 AMap 关键字")
                    else:
                        print("⚠️ 响应中未找到 AMap 关键字")
                
                print("✅ 测试通过")
            else:
                print(f"❌ 状态码错误: {response.status_code}")
                all_success = False
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
            all_success = False
        except requests.exceptions.ConnectionError:
            print("❌ 连接错误")
            all_success = False
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            print(f"堆栈跟踪: {traceback.format_exc()}")
            all_success = False
    
    return all_success

def main():
    """主函数"""
    print("=== 测试系统信息 ===")
    print(f"Python 版本: {sys.version}")
    print(f"请求库: {requests.__version__}")
    print()
    
    success = test_amap_api()
    
    print("\n=== 测试结果 ===")
    if success:
        print("✅ 所有测试通过")
        return 0
    else:
        print("❌ 部分或所有测试失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)