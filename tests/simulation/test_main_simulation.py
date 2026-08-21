#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 main.py 解析功能
"""

import struct
import json

def test_parse_sensor_data():
    """测试传感器数据解析"""
    
    print("测试 main.py 传感器数据解析...")
    
    # 使用与 main.py 相同的格式字符串
    format_str = '<BhhhhhhhhhhhIIdd'
    
    # 创建测试数据
    from random import randint, uniform
    
    test_data = [
        randint(0, 255),          # packet_seq
        randint(-32768, 32767),  # acc_x
        randint(-32768, 32767),  # acc_y
        randint(-32768, 32767),  # acc_z
        randint(-32768, 32767),  # gyro_x
        randint(-32768, 32767),  # gyro_y
        randint(-32768, 32767),  # gyro_z
        randint(-32768, 32767),  # angle_x
        randint(-32768, 32767),  # angle_y
        randint(-32768, 32767),  # angle_z
        randint(-32768, 32767),  # attitude1
        randint(-32768, 32767),  # attitude2
        randint(0, 4294967295),  # pressure
        randint(0, 4294967295),  # altitude
        uniform(-180, 180),      # longitude (高精度)
        uniform(-90, 90)         # latitude (高精度)
    ]
    
    print(f"原始经度: {test_data[14]:.10f}")
    print(f"原始纬度: {test_data[15]:.10f}")
    
    # 打包
    data_bytes = struct.pack(format_str, *test_data)
    
    # 解析（模拟 main.py 中的 parse_sensor_data 方法）
    try:
        sensor_data = struct.unpack(format_str, data_bytes)
        
        parsed_data = {
            'packet_order': sensor_data[0],
            'accel_x': sensor_data[1],
            'accel_y': sensor_data[2],
            'accel_z': sensor_data[3],
            'gyro_x': sensor_data[4],
            'gyro_y': sensor_data[5],
            'gyro_z': sensor_data[6],
            'angle_x': sensor_data[7],
            'angle_y': sensor_data[8],
            'angle_z': sensor_data[9],
            'attitude1': sensor_data[10],
            'attitude2': sensor_data[11],
            'pressure': sensor_data[12],
            'altitude': sensor_data[13],
            'longitude': float("{0:.8f}".format(sensor_data[14])),
            'latitude': float("{0:.8f}".format(sensor_data[15])),
            'timestamp': "2026-01-16 09:00:00"
        }
        
        print(f"\n解析后的经度: {parsed_data['longitude']:.10f}")
        print(f"解析后的纬度: {parsed_data['latitude']:.10f}")
        
        # 序列化到 JSON
        json_str = json.dumps(parsed_data)
        print(f"\nJSON 序列化: {json_str}")
        
        # 检查精度
        lon_diff = abs(parsed_data['longitude'] - test_data[14])
        lat_diff = abs(parsed_data['latitude'] - test_data[15])
        
        print(f"\n精度差异:")
        print(f"  经度: {lon_diff:.12f}")
        print(f"  纬度: {lat_diff:.12f}")
        
        if lon_diff < 0.00000001 and lat_diff < 0.00000001:
            print("\n✅ 解析和序列化精度符合要求 (小于1e-8度)")
        else:
            print("\n❌ 精度不符合要求")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        print(f"堆栈: {traceback.format_exc()}")

test_parse_sensor_data()
