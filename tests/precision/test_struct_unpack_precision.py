#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试struct解包时的浮点数精度问题
"""

import ujson
import struct
import random

def test_struct_unpack_altitude_precision():
    """测试struct解包时的高度参数精度问题"""
    print("=" * 50)
    print("测试struct解包时的高度参数精度")
    print("=" * 50)
    
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
        print(f"\n原始高度值: {altitude}")
        
        # 将高度值打包为4字节浮点数
        binary_data = struct.pack('<f', altitude)
        
        # 解包
        unpacked_altitude = struct.unpack('<f', binary_data)[0]
        print(f"解包后的高度值: {unpacked_altitude}")
        
        # 格式化到2位小数
        formatted_altitude = float("{0:.2f}".format(unpacked_altitude))
        print(f"格式化到2位小数: {formatted_altitude}")
        
        # 使用ujson序列化
        json_str = ujson.dumps({'altitude': formatted_altitude})
        print(f"ujson序列化结果: {json_str}")
        
        # 检查是否有精度问题
        if '502.9800000000001' in json_str:
            print("警告: 发现精度问题")

def test_random_struct_unpack():
    """测试随机高度值的struct解包精度问题"""
    print("\n" + "=" * 50)
    print("测试随机高度值的struct解包精度")
    print("=" * 50)
    
    precision_issues = 0
    
    for i in range(1000):
        altitude = round(random.uniform(-1000, 10000), 2)
        
        # 打包和解包
        binary_data = struct.pack('<f', altitude)
        unpacked_altitude = struct.unpack('<f', binary_data)[0]
        
        # 格式化
        formatted_altitude = float("{0:.2f}".format(unpacked_altitude))
        
        # 序列化
        json_str = ujson.dumps({'altitude': formatted_altitude})
        
        # 检查是否有精度问题
        if len(str(altitude)) < len(json_str.split(':')[1].split('}')[0]):
            precision_issues += 1
            print(f"\n高度值: {altitude}")
            print(f"解包后: {unpacked_altitude}")
            print(f"格式化后: {formatted_altitude}")
            print(f"JSON序列化: {json_str}")
            
    print(f"\n总测试次数: 1000")
    print(f"出现精度问题的次数: {precision_issues}")

if __name__ == "__main__":
    test_struct_unpack_altitude_precision()
    test_random_struct_unpack()
