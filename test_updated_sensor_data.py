#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试更新后的传感器数据打包和解包功能
"""

import struct
import random
from stm32_simulation_test import SensorDataGenerator


def test_sensor_data_generator():
    """测试传感器数据生成器"""
    print("测试传感器数据生成器:")
    print("=" * 50)
    
    generator = SensorDataGenerator()
    
    # 生成传感器数据
    sensor_data = generator.generate_sensor_data()
    print("生成的传感器数据:")
    for key, value in sensor_data.items():
        print(f"  {key}: {value}")
    
    print()
    
    # 测试数据打包
    data_bytes = generator.sensor_data_to_bytes(sensor_data)
    print(f"打包后的字节长度: {len(data_bytes)} bytes")
    print(f"打包后的字节内容: {data_bytes}")
    
    print()
    
    # 打印十六进制格式
    hex_str = ' '.join(f'{byte:02X}' for byte in data_bytes)
    print(f"十六进制格式: {hex_str}")
    
    print()
    
    # 测试解包
    try:
        unpacked_data = struct.unpack('<BhhhhhhhhhhhIfdd', data_bytes)
        print("解包成功:")
        print(f"  packet_order: {unpacked_data[0]}")
        print(f"  accel_x: {unpacked_data[1]}")
        print(f"  accel_y: {unpacked_data[2]}")
        print(f"  accel_z: {unpacked_data[3]}")
        print(f"  gyro_x: {unpacked_data[4]}")
        print(f"  gyro_y: {unpacked_data[5]}")
        print(f"  gyro_z: {unpacked_data[6]}")
        print(f"  angle_x: {unpacked_data[7]}")
        print(f"  angle_y: {unpacked_data[8]}")
        print(f"  angle_z: {unpacked_data[9]}")
        print(f"  attitude1: {unpacked_data[10]}")
        print(f"  attitude2: {unpacked_data[11]}")
        print(f"  pressure: {unpacked_data[12]}")
        print(f"  altitude: {unpacked_data[13]}")
        print(f"  longitude: {unpacked_data[14]}")
        print(f"  latitude: {unpacked_data[15]}")
    except Exception as e:
        print(f"解包失败: {e}")
    
    print()
    
    # 验证解包数据是否与原始数据匹配
    assert unpacked_data[0] == sensor_data['packet_order']
    assert unpacked_data[1] == sensor_data['accel_x']
    assert unpacked_data[2] == sensor_data['accel_y']
    assert unpacked_data[3] == sensor_data['accel_z']
    assert unpacked_data[4] == sensor_data['gyro_x']
    assert unpacked_data[5] == sensor_data['gyro_y']
    assert unpacked_data[6] == sensor_data['gyro_z']
    assert unpacked_data[7] == sensor_data['angle_x']
    assert unpacked_data[8] == sensor_data['angle_y']
    assert unpacked_data[9] == sensor_data['angle_z']
    assert unpacked_data[10] == sensor_data['attitude1']
    assert unpacked_data[11] == sensor_data['attitude2']
    assert unpacked_data[12] == sensor_data['pressure']
    assert abs(unpacked_data[13] - sensor_data['altitude']) < 0.0001
    assert abs(unpacked_data[14] - sensor_data['longitude']) < 0.000001
    assert abs(unpacked_data[15] - sensor_data['latitude']) < 0.000001
    
    print("✓ 解包数据与原始数据匹配")


def test_multiple_samples():
    """测试多个样本的打包功能"""
    print("\n测试多个样本的打包功能:")
    print("=" * 50)
    
    generator = SensorDataGenerator()
    
    # 生成5个传感器数据样本
    samples = generator.generate_multiple_samples(5)
    print(f"生成了 {len(samples)} 个传感器数据样本")
    
    # 打包多个样本
    data_bytes = generator.multiple_samples_to_bytes(samples)
    print(f"打包后的字节长度: {len(data_bytes)} bytes")
    
    # 验证总字节长度是否是单个样本长度的5倍
    single_length = len(generator.sensor_data_to_bytes(samples[0]))
    assert len(data_bytes) == single_length * 5
    
    print("✓ 多个样本打包成功")


def main():
    """主测试函数"""
    print("应急跌落事件监控系统 - 传感器数据格式测试")
    print("=" * 50)
    
    try:
        test_sensor_data_generator()
        test_multiple_samples()
        print("\n✅ 所有测试通过")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    main()
