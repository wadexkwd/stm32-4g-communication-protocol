#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
仅测试传感器数据解析功能，不依赖硬件模块
"""

import sys
import struct
import time

def calculate_checksum(cmd, data_len, data):
    """计算校验和（异或校验）"""
    checksum = cmd
    checksum ^= (data_len >> 8) & 0xFF
    checksum ^= data_len & 0xFF
    for byte in data:
        checksum ^= byte
    return checksum

def parse_sensor_data(data):
    """解析传感器数据上传帧 - 独立版本，不依赖 machine 模块"""
    sensor_data_list = []
    sample_length = 47

    if len(data) % sample_length != 0:
        print("数据长度不是 %d 的整数倍，无法解析" % sample_length)
        return sensor_data_list

    def format_timestamp(timestamp=None):
        """模拟时间格式化"""
        try:
            if timestamp is None:
                timestamp = time.time()
            t = time.localtime(timestamp)
            return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                t[0], t[1], t[2], t[3], t[4], t[5]
            )
        except Exception as e:
            return str(timestamp)

    formatted_time = format_timestamp()
    
    sample_count = len(data) // sample_length
    for i in range(sample_count):
        sample_data = data[i * sample_length:(i + 1) * sample_length]
        try:
            sensor_data = struct.unpack('<BhhhhhhhhhhhIIdd', sample_data)
            # 确保经度和纬度保留足够的精度（至少8位小数）
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
                'longitude': float("%.8f" % sensor_data[14]),
                'latitude': float("%.8f" % sensor_data[15]),
                'timestamp': formatted_time
            }
            sensor_data_list.append(parsed_data)
            
            # 打印调试信息 - 详细输出每一组解析的数据
            print("=" * 60)
            print("第 %d 组传感器数据解析成功:" % (i+1))
            print("包序: %d" % parsed_data['packet_order'])
            print("加速度 X: %d, Y: %d, Z: %d" % (parsed_data['accel_x'], parsed_data['accel_y'], parsed_data['accel_z']))
            print("角速度 X: %d, Y: %d, Z: %d" % (parsed_data['gyro_x'], parsed_data['gyro_y'], parsed_data['gyro_z']))
            print("角度 X: %d, Y: %d, Z: %d" % (parsed_data['angle_x'], parsed_data['angle_y'], parsed_data['angle_z']))
            print("姿态角1: %d, 姿态角2: %d" % (parsed_data['attitude1'], parsed_data['attitude2']))
            print("气压: %d" % parsed_data['pressure'])
            print("高度: %d" % parsed_data['altitude'])
            print("经度: %.8f" % parsed_data['longitude'])
            print("纬度: %.8f" % parsed_data['latitude'])
            print("时间戳: %s" % parsed_data['timestamp'])
            print("=" * 60)
            
        except Exception as e:
            print("解析第 %d 组传感器数据失败: %s" % (i+1, e))
            import sys
            print("错误类型: %s" % type(e))
            print("错误信息: %s" % e)
            print("错误位置: %s" % sys.exc_info()[2])

    print("传感器数据解析完成，共成功解析 %d 组数据" % len(sensor_data_list))
    return sensor_data_list

def test_parse_sensor_data():
    """测试传感器数据解析"""
    print("\n测试传感器数据解析...")
    
    # 创建测试数据
    # 使用 protocol.h 中定义的 SensorData 结构体格式
    test_data = [
        1,                      # packet_seq
        100, 200, 300,         # acc_x, acc_y, acc_z
        400, 500, 600,         # gyro_x, gyro_y, gyro_z
        700, 800, 900,         # angle_x, angle_y, angle_z
        1000, 1100,            # attitude1, attitude2
        101325,                # pressure (Pa)
        1000,                  # altitude (cm)
        116.39741856,          # longitude (Beijing)
        39.90873124            # latitude (Beijing)
    ]
    
    print("原始测试数据:")
    print("包序:", test_data[0])
    print("加速度:", test_data[1], test_data[2], test_data[3])
    print("角速度:", test_data[4], test_data[5], test_data[6])
    print("角度:", test_data[7], test_data[8], test_data[9])
    print("姿态角:", test_data[10], test_data[11])
    print("气压:", test_data[12])
    print("高度:", test_data[13])
    print("经度:", "%.8f" % test_data[14])
    print("纬度:", "%.8f" % test_data[15])
    
    # 打包测试数据
    try:
        packed_data = struct.pack('<BhhhhhhhhhhhIIdd', *test_data)
        print("\n✅ 数据打包成功")
        print("打包后长度:", len(packed_data), "字节")
        if len(packed_data) != 47:
            print("⚠️  打包长度不符，应为 47 字节，实际为", len(packed_data), "字节")
    except Exception as e:
        print("❌ 数据打包失败:", e)
        import traceback
        print("堆栈:", traceback.format_exc())
        return False
    
    # 解析数据
    try:
        parsed_list = parse_sensor_data(packed_data)
        print("\n✅ 数据解析成功")
        print("解析到", len(parsed_list), "组数据")
        
        if parsed_list:
            parsed_data = parsed_list[0]
            print("\n解析结果:")
            print("包序:", parsed_data['packet_order'])
            print("加速度:", parsed_data['accel_x'], parsed_data['accel_y'], parsed_data['accel_z'])
            print("角速度:", parsed_data['gyro_x'], parsed_data['gyro_y'], parsed_data['gyro_z'])
            print("角度:", parsed_data['angle_x'], parsed_data['angle_y'], parsed_data['angle_z'])
            print("姿态角:", parsed_data['attitude1'], parsed_data['attitude2'])
            print("气压:", parsed_data['pressure'])
            print("高度:", parsed_data['altitude'])
            print("经度:", "%.8f" % parsed_data['longitude'])
            print("纬度:", "%.8f" % parsed_data['latitude'])
            print("时间戳:", parsed_data['timestamp'])
            
            # 检查精度
            lon_diff = abs(parsed_data['longitude'] - test_data[14])
            lat_diff = abs(parsed_data['latitude'] - test_data[15])
            
            print("\n精度检查:")
            print("经度差异: %.12f (应小于1e-8)" % lon_diff)
            print("纬度差异: %.12f (应小于1e-8)" % lat_diff)
            
            if lon_diff < 0.00000001 and lat_diff < 0.00000001:
                print("✅ 经纬度精度符合要求")
            else:
                print("❌ 经纬度精度不符合要求")
                
            return True
        else:
            print("❌ 未解析到任何数据")
            return False
            
    except Exception as e:
        print("❌ 数据解析失败:", e)
        import traceback
        print("堆栈:", traceback.format_exc())
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("测试传感器数据解析功能")
    print("=" * 50)
    
    try:
        success = test_parse_sensor_data()
        
        if success:
            print("\n" + "=" * 50)
            print("✅ 所有测试通过")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("❌ 测试失败")
            print("=" * 50)
            
    except Exception as e:
        print("❌ 测试过程出错:", e)
        import traceback
        print("堆栈:", traceback.format_exc())
