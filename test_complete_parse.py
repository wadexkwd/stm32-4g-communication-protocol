#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试完整传感器数据解析
"""

import struct
import random

def test_complete_parse():
    """测试完整传感器数据解析"""
    
    print("测试完整传感器数据解析...")
    
    # 创建测试数据
    test_data = {
        'packet_order': random.randint(0, 255),
        'accel_x': random.randint(-32768, 32767),
        'accel_y': random.randint(-32768, 32767),
        'accel_z': random.randint(-32768, 32767),
        'gyro_x': random.randint(-32768, 32767),
        'gyro_y': random.randint(-32768, 32767),
        'gyro_z': random.randint(-32768, 32767),
        'angle_x': random.randint(-32768, 32767),
        'angle_y': random.randint(-32768, 32767),
        'angle_z': random.randint(-32768, 32767),
        'attitude1': random.randint(-32768, 32767),
        'attitude2': random.randint(-32768, 32767),
        'pressure': random.randint(0, 4294967295),
        'altitude': random.uniform(-1000, 10000),
        'longitude': random.uniform(-180, 180),
        'latitude': random.uniform(-90, 90)
    }
    
    print("测试数据:")
    print(f"  包序: {test_data['packet_order']}")
    print(f"  加速度X: {test_data['accel_x']}")
    print(f"  加速度Y: {test_data['accel_y']}")
    print(f"  加速度Z: {test_data['accel_z']}")
    print(f"  角速度X: {test_data['gyro_x']}")
    print(f"  角速度Y: {test_data['gyro_y']}")
    print(f"  角速度Z: {test_data['gyro_z']}")
    print(f"  角度X: {test_data['angle_x']}")
    print(f"  角度Y: {test_data['angle_y']}")
    print(f"  角度Z: {test_data['angle_z']}")
    print(f"  姿态角1: {test_data['attitude1']}")
    print(f"  姿态角2: {test_data['attitude2']}")
    print(f"  气压: {test_data['pressure']}")
    print(f"  高度: {test_data['altitude']:.2f}")
    print(f"  经度: {test_data['longitude']:.8f}")
    print(f"  纬度: {test_data['latitude']:.8f}")
    
    # 使用 float 格式打包 altitude
    data_bytes = struct.pack(
        '<Bhhhhhhhhhhhfdd',
        test_data['packet_order'],
        test_data['accel_x'],
        test_data['accel_y'],
        test_data['accel_z'],
        test_data['gyro_x'],
        test_data['gyro_y'],
        test_data['gyro_z'],
        test_data['angle_x'],
        test_data['angle_y'],
        test_data['angle_z'],
        test_data['attitude1'],
        test_data['attitude2'],
        test_data['pressure'],
        test_data['altitude'],
        test_data['longitude'],
        test_data['latitude']
    )
    
    print(f"\n打包后字节长度: {len(data_bytes)} bytes (预期47字节)")
    
    # 解包数据
    unpacked_data = struct.unpack('<Bhhhhhhhhhhhfdd', data_bytes)
    
    print("\n解包后数据:")
    print(f"  包序: {unpacked_data[0]}")
    print(f"  加速度X: {unpacked_data[1]}")
    print(f"  加速度Y: {unpacked_data[2]}")
    print(f"  加速度Z: {unpacked_data[3]}")
    print(f"  角速度X: {unpacked_data[4]}")
    print(f"  角速度Y: {unpacked_data[5]}")
    print(f"  角速度Z: {unpacked_data[6]}")
    print(f"  角度X: {unpacked_data[7]}")
    print(f"  角度Y: {unpacked_data[8]}")
    print(f"  角度Z: {unpacked_data[9]}")
    print(f"  姿态角1: {unpacked_data[10]}")
    print(f"  姿态角2: {unpacked_data[11]}")
    print(f"  气压: {unpacked_data[12]}")
    print(f"  高度: {unpacked_data[13]:.2f}")
    print(f"  经度: {unpacked_data[14]:.8f}")
    print(f"  纬度: {unpacked_data[15]:.8f}")
    
    # 验证解析结果
    print("\n验证解析结果:")
    assert unpacked_data[0] == test_data['packet_order'], "包序解析错误"
    assert unpacked_data[1] == test_data['accel_x'], "加速度X解析错误"
    assert unpacked_data[2] == test_data['accel_y'], "加速度Y解析错误"
    assert unpacked_data[3] == test_data['accel_z'], "加速度Z解析错误"
    assert unpacked_data[4] == test_data['gyro_x'], "角速度X解析错误"
    assert unpacked_data[5] == test_data['gyro_y'], "角速度Y解析错误"
    assert unpacked_data[6] == test_data['gyro_z'], "角速度Z解析错误"
    assert unpacked_data[7] == test_data['angle_x'], "角度X解析错误"
    assert unpacked_data[8] == test_data['angle_y'], "角度Y解析错误"
    assert unpacked_data[9] == test_data['angle_z'], "角度Z解析错误"
    assert unpacked_data[10] == test_data['attitude1'], "姿态角1解析错误"
    assert unpacked_data[11] == test_data['attitude2'], "姿态角2解析错误"
    assert unpacked_data[12] == test_data['pressure'], "气压解析错误"
    assert abs(unpacked_data[13] - test_data['altitude']) < 0.01, "高度解析错误"
    assert abs(unpacked_data[14] - test_data['longitude']) < 0.00000001, "经度解析错误"
    assert abs(unpacked_data[15] - test_data['latitude']) < 0.00000001, "纬度解析错误"
    
    print("\n✅ 所有字段解析成功！")
    print("高度值已正确解析为浮点数")

test_complete_parse()
