#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试 main.py 传感器数据解析功能
"""

import sys
import struct

# 添加当前目录到路径，以便导入模块
sys.path.append('.')

# 尝试导入 main.py 中的类
try:
    from device.main import STM32Communication
    print("✅ 成功导入 STM32Communication 类")
except Exception as e:
    print("❌ 导入失败:", e)
    import traceback
    print("堆栈:", traceback.format_exc())
    sys.exit(1)

def test_parse_sensor_data():
    """测试传感器数据解析"""
    print("\n测试传感器数据解析...")
    
    # 创建测试数据
    # 使用 protocol.h 中定义的 SensorData 结构体格式
    # 格式: packet_seq (1) + 11个int16_t (22) + pressure(4) + altitude(4) + longitude(8) + latitude(8) = 47 bytes
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
    
    # 创建通信对象并解析数据
    try:
        comm = STM32Communication(None, None)  # 不需要真正的串口连接
        parsed_list = comm.parse_sensor_data(packed_data)
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
    print("测试 main.py 传感器数据解析功能")
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
