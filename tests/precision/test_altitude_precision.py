#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试高度参数在JSON中的浮点数精度问题
"""

import json
import struct
import random

def test_altitude_precision():
    """测试高度参数的JSON序列化精度"""
    print("=" * 50)
    print("测试高度参数JSON序列化精度")
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
        # 创建测试数据
        sensor_data = {
            'packet_order': 0,
            'accel_x': -91,
            'accel_y': 0,
            'accel_z': 27,
            'gyro_x': -11,
            'gyro_y': 10,
            'gyro_z': -11,
            'angle_x': -11,
            'angle_y': 10,
            'angle_z': -11,
            'attitude1': 7,
            'attitude2': 410,
            'pressure': 101716,
            'altitude': altitude,
            'longitude': 104.06,
            'latitude': 30.66,
            'timestamp': '2024-01-01 00:00:00'
        }
        
        # 测试不同的格式化方法
        print(f"\n原始高度值: {altitude}")
        
        # 方法1: 直接序列化
        json_str1 = json.dumps(sensor_data)
        print(f"直接序列化: {json_str1}")
        
        # 方法2: 使用字符串格式化
        sensor_data_formatted = sensor_data.copy()
        sensor_data_formatted['altitude'] = float("{0:.2f}".format(altitude))
        json_str2 = json.dumps(sensor_data_formatted)
        print(f"格式化到2位小数: {json_str2}")
        
        # 方法3: 使用round函数
        sensor_data_rounded = sensor_data.copy()
        sensor_data_rounded['altitude'] = round(altitude, 2)
        json_str3 = json.dumps(sensor_data_rounded)
        print(f"四舍五入到2位小数: {json_str3}")
        
        # 方法4: 转换为Decimal类型（如果可用）
        try:
            from decimal import Decimal
            sensor_data_decimal = sensor_data.copy()
            sensor_data_decimal['altitude'] = Decimal("{0:.2f}".format(altitude))
            json_str4 = json.dumps(sensor_data_decimal)
            print(f"使用Decimal类型: {json_str4}")
        except ImportError:
            print(f"Decimal类型不可用")

def test_random_altitudes():
    """测试随机高度值的精度问题"""
    print("\n" + "=" * 50)
    print("测试随机高度值")
    print("=" * 50)
    
    for i in range(5):
        altitude = round(random.uniform(-1000, 10000), 2)
        sensor_data = {
            'altitude': altitude
        }
        
        print(f"\n原始高度值: {altitude}")
        
        # 直接序列化
        json_str = json.dumps(sensor_data)
        print(f"JSON序列化结果: {json_str}")
        
        # 检查是否有精度问题
        if len(str(altitude)) != len(json_str.split(':')[1].split('}')[0]):
            print("警告: 可能存在浮点数精度问题")

if __name__ == "__main__":
    # 测试已知高度值
    test_altitude_precision()
    
    # 测试随机高度值
    test_random_altitudes()
