#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网络连接测试程序 - 检查高德地图API访问
"""

import sys
import urllib.request
import urllib.error
import socket

def test_amap_api():
    print("=== 高德地图API访问测试 ===")
    
    # 测试连接
    test_urls = [
        ("高德地图API", "https://webapi.amap.com"),
        ("高德地图JS API", "https://webapi.amap.com/maps?v=2.0&key=431d3bb1fa78eef96736dc499113fca2"),
        ("简单测试页面", "https://www.baidu.com"),
        ("OpenStreetMap瓦片", "https://a.tile.openstreetmap.org/10/512/341.png")
    ]
    
    results = []
    
    for name, url in test_urls:
        print("\n测试: %s" % name)
        print("URL: %s" % url)
        
        try:
            # 配置超时时间
            timeout = 5
            socket.setdefaulttimeout(timeout)
            
            # 发送请求
            with urllib.request.urlopen(url, timeout=timeout) as response:
                status = response.getcode()
                content_length = response.getheader('Content-Length', 'Unknown')
                content_type = response.getheader('Content-Type', 'Unknown')
                
                print("成功")
                print("  状态码: %s" % status)
                print("  内容类型: %s" % content_type)
                print("  内容长度: %s" % content_length)
                
                results.append({
                    'name': name,
                    'success': True,
                    'status': status
                })
                
        except urllib.error.HTTPError as e:
            print("HTTP错误: %s - %s" % (e.code, e.reason))
            results.append({
                'name': name,
                'success': False,
                'error': "HTTP %s: %s" % (e.code, e.reason)
            })
            
        except urllib.error.URLError as e:
            print("URL错误: %s" % e.reason)
            results.append({
                'name': name,
                'success': False,
                'error': "URL错误: %s" % e.reason
            })
            
        except Exception as e:
            if "timed out" in str(e) or "timeout" in str(e):
                print("超时")
                results.append({
                    'name': name,
                    'success': False,
                    'error': "连接超时"
                })
            else:
                print("错误: %s" % str(e))
                import traceback
                print("  堆栈跟踪: %s" % traceback.format_exc())
                results.append({
                    'name': name,
                    'success': False,
                    'error': str(e)
                })
    
    # 测试本地网络接口
    print("\n=== 本地网络测试 ===")
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print("主机名: %s" % hostname)
        print("本地IP: %s" % local_ip)
    except Exception as e:
        print("获取本地网络信息失败: %s" % e)
    
    # 输出总结
    print("\n=== 测试总结 ===")
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print("成功: %d/%d" % (len(successful), len(test_urls)))
    print("失败: %d/%d" % (len(failed), len(test_urls)))
    
    if failed:
        print("\n失败列表:")
        for r in failed:
            print("  - %s: %s" % (r['name'], r['error']))
    
    if len(successful) >= 3:
        print("\n网络连接状态良好，可以正常访问高德地图API")
    else:
        print("\n网络连接可能存在问题")
    
    return len(successful) >= 3

if __name__ == "__main__":
    success = test_amap_api()
    sys.exit(0 if success else 1)