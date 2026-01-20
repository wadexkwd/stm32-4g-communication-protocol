#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试真实场景中的浮点数精度问题
"""

import ujson
import struct
import random

def test_actual_struct_unpack_precision():
    """测试实际struct解包时的精度问题"""
    print("=" * 50)
    print("测试真实场景中的浮点数精度问题")
    print("=" * 50)
    
    precision_issues = 0
    test_count = 10000
    
    for i in range(test_count):
        # 生成一个随机的两位小数高度值
        altitude = round(random.uniform(-1000, 10000), 2)
        
        # 打包成4字节浮点数
        binary_data = struct.pack('<f', altitude)
        
        # 解包
        unpacked_altitude = struct.unpack('<f', binary_data)[0]
        
        # 尝试格式化到2位小数
        formatted_altitude = float("{0:.2f}".format(unpacked_altitude))
        
        # 使用ujson序列化
        json_str = ujson.dumps({'altitude': formatted_altitude})
        
        # 检查是否有精度问题
        if '502.9800000000001' in json_str or '502.9900000000001' in json_str or len(str(formatted_altitude)) < len(json_str.split(':')[1].split('}')[0]):
            precision_issues += 1
            print(f"\n高度值: {altitude}")
            print(f"解包后: {unpacked_altitude}")
            print(f"格式化后: {formatted_altitude}")
            print(f"JSON序列化: {json_str}")
            
    print(f"\n总测试次数: {test_count}")
    print(f"出现精度问题的次数: {precision_issues}")
    print(f"精度问题比例: {precision_issues/test_count*100:.2f}%")

def test_specific_case():
    """测试用户提到的特定情况"""
    print("\n" + "=" * 50)
    print("测试用户提到的特定情况")
    print("=" * 50)
    
    # 测试用户提到的情况
    test_altitudes = [502.98, 502.99]
    
    for altitude in test_altitudes:
        print(f"\n原始高度值: {altitude}")
        
        # 打包成4字节浮点数
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
        
        # 使用标准json库序列化
        import json
        json_str_std = json.dumps({'altitude': formatted_altitude})
        print(f"标准json库序列化: {json_str_std}")
        
        # 检查是否有精度问题
        if len(str(formatted_altitude)) < len(json_str.split(':')[1].split('}')[0]):
            print("警告: 发现精度问题")

def test_string_formatting_solution():
    """测试使用字符串格式化的解决方案"""
    print("\n" + "=" * 50)
    print("测试使用字符串格式化的解决方案")
    print("=" * 50)
    
    test_altitudes = [502.98, 502.99]
    
    for altitude in test_altitudes:
        print(f"\n原始高度值: {altitude}")
        
        binary_data = struct.pack('<f', altitude)
        unpacked_altitude = struct.unpack('<f', binary_data)[0]
        
        # 使用字符串格式化保持精度
        formatted_str = "{0:.2f}".format(unpacked_altitude)
        print(f"字符串格式化: {formatted_str}")
        
        # 直接序列化为字符串
        json_str = ujson.dumps({'altitude': formatted_str})
        print(f"字符串序列化结果: {json_str}")
        
        # 或者使用Decimal类型（如果可用）
        try:
            from decimal import Decimal
            decimal_value = Decimal(formatted_str)
            # 自定义序列化函数
            def decimal_default(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                raise TypeError
            
            json_str_dec = ujson.dumps({'altitude': decimal_value}, default=decimal_default)
            print(f"Decimal类型序列化: {json_str_dec}")
        except ImportError:
            print("Decimal类型不可用")

if __name__ == "__main__":
    test_specific_case()
    test_string_formatting_solution()
    test_actual_struct_unpack_precision()
