#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试高度值解析
验证protocol.h中的altitude字段定义
"""

import struct

def test_altitude_parse():
    """测试高度值解析"""
    
    print("protocol.h中SensorData结构体定义:")
    print("""
typedef struct __attribute__((packed)) {
    uint8_t packet_seq;       // 包序 (1字节)
    int16_t acc_x;            // 加速度X (2字节)
    int16_t acc_y;            // 加速度Y (2字节)
    int16_t acc_z;            // 加速度Z (2字节)
    int16_t gyro_x;           // 角速度X (2字节)
    int16_t gyro_y;           // 角速度Y (2字节)
    int16_t gyro_z;           // 角速度Z (2字节)
    int16_t angle_x;          // 角度X (2字节)
    int16_t angle_y;          // 角度Y (2字节)
    int16_t angle_z;          // 角度Z (2字节)
    int16_t attitude1;        // 姿态角1 (2字节)
    int16_t attitude2;        // 姿态角2 (2字节)
    uint32_t pressure;        // 气压 (4字节)
    uint32_t altitude;        // 高度 (4字节)  或 float altitude;
    double longitude;         // 经度 (8字节)
    double latitude;          // 纬度 (8字节)
} SensorData;
    """)
    
    print("\n结构体大小计算:")
    print(f"packet_seq: 1")
    print(f"acc_x: 2")
    print(f"acc_y: 2")
    print(f"acc_z: 2")
    print(f"gyro_x: 2")
    print(f"gyro_y: 2")
    print(f"gyro_z: 2")
    print(f"angle_x: 2")
    print(f"angle_y: 2")
    print(f"angle_z: 2")
    print(f"attitude1: 2")
    print(f"attitude2: 2")
    print(f"pressure: 4")
    print(f"altitude (uint32_t): 4")
    print(f"longitude: 8")
    print(f"latitude: 8")
    
    total_size_uint32 = 1 + 2*11 + 4 + 4 + 8 + 8
    total_size_float = 1 + 2*11 + 4 + 4 + 8 + 8  # float也是4字节
    
    print(f"\n结构体总大小 (altitude为uint32_t): {total_size_uint32} bytes")
    print(f"结构体总大小 (altitude为float): {total_size_float} bytes")
    
    print(f"\n两者大小相同，说明字节长度一致")
    
    # 测试解析
    print("\n" + "-"*50)
    print("测试解析:")
    
    # 创建测试数据
    test_data = {
        'packet_seq': 1,
        'acc_x': 100,
        'acc_y': 200,
        'acc_z': 300,
        'gyro_x': 400,
        'gyro_y': 500,
        'gyro_z': 600,
        'angle_x': 700,
        'angle_y': 800,
        'angle_z': 900,
        'attitude1': 1000,
        'attitude2': 1100,
        'pressure': 101325,
        'altitude_float': 123.45,  # 浮点数高度
        'altitude_uint32': 12345,  # 整数高度
        'longitude': 116.3974,
        'latitude': 39.9086
    }
    
    # 打包数据为字节
    # 使用 float 类型打包 altitude
    packed_float = struct.pack(
        '<Bhhhhhhhhhhhfdd',
        test_data['packet_seq'],
        test_data['acc_x'],
        test_data['acc_y'],
        test_data['acc_z'],
        test_data['gyro_x'],
        test_data['gyro_y'],
        test_data['gyro_z'],
        test_data['angle_x'],
        test_data['angle_y'],
        test_data['angle_z'],
        test_data['attitude1'],
        test_data['attitude2'],
        test_data['pressure'],
        test_data['altitude_float'],
        test_data['longitude'],
        test_data['latitude']
    )
    
    # 使用 uint32_t 类型打包 altitude
    packed_uint32 = struct.pack(
        '<Bhhhhhhhhhhhidd',
        test_data['packet_seq'],
        test_data['acc_x'],
        test_data['acc_y'],
        test_data['acc_z'],
        test_data['gyro_x'],
        test_data['gyro_y'],
        test_data['gyro_z'],
        test_data['angle_x'],
        test_data['angle_y'],
        test_data['angle_z'],
        test_data['attitude1'],
        test_data['attitude2'],
        test_data['pressure'],
        test_data['altitude_uint32'],
        test_data['longitude'],
        test_data['latitude']
    )
    
    print(f"\n打包数据字节长度:")
    print(f"altitude为float: {len(packed_float)} bytes")
    print(f"altitude为uint32_t: {len(packed_uint32)} bytes")
    
    # 解包
    unpacked_float = struct.unpack('<Bhhhhhhhhhhhfdd', packed_float)
    unpacked_uint32 = struct.unpack('<Bhhhhhhhhhhhidd', packed_uint32)
    
    print(f"\n解包结果:")
    print(f"altitude (float): {unpacked_float[13]:.2f}")
    print(f"altitude (uint32_t): {unpacked_uint32[13]}")
    
    print("\n" + "-"*50)
    print("结论:")
    print("1. 无论altitude是float还是uint32_t，字节长度都是4字节")
    print("2. 使用f格式解析时，会将4字节数据解释为浮点数")
    print("3. 使用i格式解析时，会将4字节数据解释为整数")
    print("4. 选择使用f格式解析符合用户要求的'按浮点解析'")

test_altitude_parse()
