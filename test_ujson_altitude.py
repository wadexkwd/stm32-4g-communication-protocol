#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试ujson库的浮点数精度问题
"""

import ujson
import random

def test_ujson_precision():
    """测试ujson的浮点数精度"""
    print("=" * 50)
    print("测试ujson库的浮点数精度")
    print("=" * 50)
    
    # 测试多个高度值
    test_altitudes = [
        502.98,
        123.45,
        999.99,
        0.01,
        1000.00,
        -123.45,
        325.49
    ]
    
    for altitude in test_altitudes:
        sensor_data = {
            'altitude': altitude
        }
        
        print(f"\n原始高度值: {altitude}")
        
        # 使用ujson序列化
        ujson_str = ujson.dumps(sensor_data)
        print(f"ujson序列化: {ujson_str}")
        
        # 检查是否有精度问题
        if '502.9800000000001' in ujson_str:
            print("发现精度问题!")
        
        # 测试格式化后的结果
        sensor_data_formatted = {
            'altitude': float("{0:.2f}".format(altitude))
        }
        ujson_formatted_str = ujson.dumps(sensor_data_formatted)
        print(f"格式化后ujson序列化: {ujson_formatted_str}")

def test_random_altitudes_with_ujson():
    """测试随机高度值的精度问题"""
    print("\n" + "=" * 50)
    print("测试随机高度值的精度")
    print("=" * 50)
    
    precision_issues = 0
    
    for i in range(1000):
        altitude = round(random.uniform(-1000, 10000), 2)
        sensor_data = {
            'altitude': altitude
        }
        
        ujson_str = ujson.dumps(sensor_data)
        
        # 检查是否有精度问题
        if len(str(altitude)) < len(ujson_str.split(':')[1].split('}')[0]):
            precision_issues += 1
            print(f"\n高度值: {altitude}")
            print(f"ujson序列化: {ujson_str}")
            
    print(f"\n总测试次数: 1000")
    print(f"出现精度问题的次数: {precision_issues}")

if __name__ == "__main__":
    try:
        import ujson
        print("成功导入ujson库")
        
        test_ujson_precision()
        test_random_altitudes_with_ujson()
        
    except ImportError:
        print("错误: 未找到ujson库，请先安装")
        print("安装命令: pip install ujson")
