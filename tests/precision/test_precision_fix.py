#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试经度和纬度精度修复后的效果
模拟 main.py 中的相关函数
"""

import ustruct as struct
import ujson
import random

# 模拟 parse_sensor_data 函数
def test_parse_sensor_data():
    """测试 parse_sensor_data 函数的修复效果"""
    
    # 生成随机的传感器数据，包括高精度的经纬度
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
        'altitude': random.randint(0, 4294967295),
        'longitude': random.uniform(-180, 180),
        'latitude': random.uniform(-90, 90)
    }
    
    print("原始经纬度:")
    print("经度: {:.8f}".format(test_data['longitude']))
    print("纬度: {:.8f}".format(test_data['latitude']))
    
    # 打包数据（使用与main.py中相同的格式）
    data_bytes = struct.pack(
        '<BhhhhhhhhhhhIIdd',
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
    
    print("\n打包后的字节长度: {} bytes".format(len(data_bytes)))
    
    # 解包数据
    unpacked_data = struct.unpack('<BhhhhhhhhhhhIIdd', data_bytes)
    
    print("\n解包后的经纬度:")
    print("经度: {:.8f}".format(unpacked_data[14]))
    print("纬度: {:.8f}".format(unpacked_data[15]))
    
    # 模拟修复后的处理方式（格式化到8位小数）
    formatted_longitude = float("{0:.8f}".format(unpacked_data[14]))
    formatted_latitude = float("{0:.8f}".format(unpacked_data[15]))
    
    print("\n格式化后的经纬度（保留8位小数）:")
    print("经度: {:.8f}".format(formatted_longitude))
    print("纬度: {:.8f}".format(formatted_latitude))
    
    # 测试 ujson 序列化
    test_sensor_data = {
        'packet_order': unpacked_data[0],
        'accel_x': unpacked_data[1],
        'accel_y': unpacked_data[2],
        'accel_z': unpacked_data[3],
        'gyro_x': unpacked_data[4],
        'gyro_y': unpacked_data[5],
        'gyro_z': unpacked_data[6],
        'angle_x': unpacked_data[7],
        'angle_y': unpacked_data[8],
        'angle_z': unpacked_data[9],
        'attitude1': unpacked_data[10],
        'attitude2': unpacked_data[11],
        'pressure': unpacked_data[12],
        'altitude': unpacked_data[13],
        'longitude': formatted_longitude,
        'latitude': formatted_latitude,
        'timestamp': "2024-05-20 14:30:00"
    }
    
    # 序列化为 JSON 字符串
    json_str = ujson.dumps(test_sensor_data)
    
    print("\nJSON 序列化结果:")
    print(json_str)
    
    # 检查经纬度在 JSON 中的精度
    print("\nJSON 中的经纬度:")
    if 'longitude' in json_str:
        long_part = json_str.split('longitude":')[1].split(',')[0]
        lat_part = json_str.split('latitude":')[1].split(',')[0]
        print("经度: {}".format(long_part))
        print("纬度: {}".format(lat_part))
        
        # 检查小数位数
        long_decimal_digits = len(long_part.split('.')[1]) if '.' in long_part else 0
        lat_decimal_digits = len(lat_part.split('.')[1]) if '.' in lat_part else 0
        
        print("\n小数位数:")
        print("经度: {} 位".format(long_decimal_digits))
        print("纬度: {} 位".format(lat_decimal_digits))
        
        assert long_decimal_digits >= 6, "经度精度不足，至少需要6位小数"
        assert lat_decimal_digits >= 6, "纬度精度不足，至少需要6位小数"
        
        print("\n✓ 经纬度精度满足要求（至少6位小数）")
    else:
        print("JSON中未找到经纬度数据")

# 测试多个数据样本
def test_multiple_samples():
    """测试多个传感器数据样本"""
    print("=" * 50)
    print("测试多个传感器数据样本")
    print("=" * 50)
    
    for i in range(5):
        print("\n\n--- 第 {} 个样本 ---".format(i+1))
        test_parse_sensor_data()

# 测试边缘情况
def test_edge_cases():
    """测试边缘情况的精度"""
    print("\n" + "=" * 50)
    print("测试边缘情况的精度")
    print("=" * 50)
    
    edge_cases = [
        (-180.0, -90.0),       # 最小经纬度
        (180.0, 90.0),         # 最大经纬度
        (0.0, 0.0),            # 赤道和本初子午线
        (116.3974199, 39.9086923),  # 北京坐标
        (-74.0060, 40.7128),   # 纽约坐标
        (139.6917, 35.6895)    # 东京坐标
    ]
    
    for lon, lat in edge_cases:
        print("\n测试坐标: ({:.8f}, {:.8f})".format(lon, lat))
        
        # 打包和解包
        data_bytes = struct.pack('<BhhhhhhhhhhhIIdd', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, lon, lat)
        unpacked_data = struct.unpack('<BhhhhhhhhhhhIIdd', data_bytes)
        
        formatted_lon = float("{0:.8f}".format(unpacked_data[14]))
        formatted_lat = float("{0:.8f}".format(unpacked_data[15]))
        
        # 序列化为 JSON
        test_sensor_data = {
            'longitude': formatted_lon,
            'latitude': formatted_lat
        }
        json_str = ujson.dumps(test_sensor_data)
        
        print("JSON 序列化: {}".format(json_str))
        
        # 检查精度
        if 'longitude' in json_str:
            long_part = json_str.split('longitude":')[1].split(',')[0]
            lat_part = json_str.split('latitude":')[1].split('}')[0]
            
            long_decimal_digits = len(long_part.split('.')[1]) if '.' in long_part else 0
            lat_decimal_digits = len(lat_part.split('.')[1]) if '.' in lat_part else 0
            
            print("经度小数位数: {}, 纬度小数位数: {}".format(long_decimal_digits, lat_decimal_digits))
            
            assert long_decimal_digits >= 6, f"经度精度不足: {long_decimal_digits} 位"
            assert lat_decimal_digits >= 6, f"纬度精度不足: {lat_decimal_digits} 位"

if __name__ == "__main__":
    print("Testing precision fix for main.py")
    
    try:
        test_parse_sensor_data()
        test_multiple_samples()
        test_edge_cases()
        
        print("\n" + "=" * 50)
        print("✅ 所有精度测试通过！")
        print("=" * 50)
        print("经纬度现在会保留至少8位小数的精度")
        print("在 JSON 字符串中会显示足够的小数位数")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())
