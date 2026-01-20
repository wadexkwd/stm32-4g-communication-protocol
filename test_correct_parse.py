#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试正确的传感器数据解析
"""

import struct
import random

def test_correct_parse():
    """测试正确的传感器数据解析"""
    
    print("测试正确的传感器数据解析...")
    
    # protocol.h SensorData 结构体定义
    print("protocol.h SensorData 字段:")
    print("1. packet_seq (uint8_t)")
    print("2. acc_x (int16_t)")
    print("3. acc_y (int16_t)")
    print("4. acc_z (int16_t)")
    print("5. gyro_x (int16_t)")
    print("6. gyro_y (int16_t)")
    print("7. gyro_z (int16_t)")
    print("8. angle_x (int16_t)")
    print("9. angle_y (int16_t)")
    print("10. angle_z (int16_t)")
    print("11. attitude1 (int16_t)")
    print("12. attitude2 (int16_t)")
    print("13. pressure (uint32_t)")
    print("14. altitude (uint32_t)")
    print("15. longitude (double)")
    print("16. latitude (double)")
    
    print(f"\n总字段数: 16个")
    expected_size = 1 + (2*11) + 4 + 4 + 8 + 8
    print(f"预期字节数: {expected_size} bytes")
    
    # 创建测试数据
    test_data = [
        random.randint(0, 255),          # packet_seq (1)
        random.randint(-32768, 32767),  # acc_x (2)
        random.randint(-32768, 32767),  # acc_y (3)
        random.randint(-32768, 32767),  # acc_z (4)
        random.randint(-32768, 32767),  # gyro_x (5)
        random.randint(-32768, 32767),  # gyro_y (6)
        random.randint(-32768, 32767),  # gyro_z (7)
        random.randint(-32768, 32767),  # angle_x (8)
        random.randint(-32768, 32767),  # angle_y (9)
        random.randint(-32768, 32767),  # angle_z (10)
        random.randint(-32768, 32767),  # attitude1 (11)
        random.randint(-32768, 32767),  # attitude2 (12)
        random.randint(0, 4294967295),  # pressure (13)
        random.randint(0, 4294967295),  # altitude (14) - uint32_t
        random.uniform(-180, 180),      # longitude (15) - double
        random.uniform(-90, 90)         # latitude (16) - double
    ]
    
    print("\n测试数据:")
    print(f"  1. 包序: {test_data[0]}")
    print(f"  2. 加速度X: {test_data[1]}")
    print(f"  3. 加速度Y: {test_data[2]}")
    print(f"  4. 加速度Z: {test_data[3]}")
    print(f"  5. 角速度X: {test_data[4]}")
    print(f"  6. 角速度Y: {test_data[5]}")
    print(f"  7. 角速度Z: {test_data[6]}")
    print(f"  8. 角度X: {test_data[7]}")
    print(f"  9. 角度Y: {test_data[8]}")
    print(f" 10. 角度Z: {test_data[9]}")
    print(f" 11. 姿态角1: {test_data[10]}")
    print(f" 12. 姿态角2: {test_data[11]}")
    print(f" 13. 气压: {test_data[12]}")
    print(f" 14. 高度: {test_data[13]}")
    print(f" 15. 经度: {test_data[14]:.8f}")
    print(f" 16. 纬度: {test_data[15]:.8f}")
    
    # 正确的格式字符串 - 11个int16_t (h) + 2个uint32_t (I) + 2个double (d)
    format_str = '<BhhhhhhhhhhhIIdd'
    print(f"\n使用格式字符串: {format_str}")
    
    # 打包
    try:
        data_bytes = struct.pack(format_str, *test_data)
        print(f"打包成功，字节数: {len(data_bytes)} bytes (预期: {expected_size} bytes)")
        
        # 解包
        unpacked_data = struct.unpack(format_str, data_bytes)
        print(f"解包成功，字段数: {len(unpacked_data)}")
        
        print("\n解包后数据:")
        print(f"  1. 包序: {unpacked_data[0]}")
        print(f"  2. 加速度X: {unpacked_data[1]}")
        print(f"  3. 加速度Y: {unpacked_data[2]}")
        print(f"  4. 加速度Z: {unpacked_data[3]}")
        print(f"  5. 角速度X: {unpacked_data[4]}")
        print(f"  6. 角速度Y: {unpacked_data[5]}")
        print(f"  7. 角速度Z: {unpacked_data[6]}")
        print(f"  8. 角度X: {unpacked_data[7]}")
        print(f"  9. 角度Y: {unpacked_data[8]}")
        print(f" 10. 角度Z: {unpacked_data[9]}")
        print(f" 11. 姿态角1: {unpacked_data[10]}")
        print(f" 12. 姿态角2: {unpacked_data[11]}")
        print(f" 13. 气压: {unpacked_data[12]}")
        print(f" 14. 高度: {unpacked_data[13]}")
        print(f" 15. 经度: {unpacked_data[14]:.8f}")
        print(f" 16. 纬度: {unpacked_data[15]:.8f}")
        
        # 验证
        assert len(unpacked_data) == 16, "字段数量不匹配"
        assert len(data_bytes) == expected_size, f"字节数不匹配，预期 {expected_size}，实际 {len(data_bytes)}"
        
        # 检查所有字段
        all_match = True
        for i in range(len(test_data)):
            if i in (14, 15):  # 经度和纬度是浮点数，允许一定误差
                if abs(unpacked_data[i] - test_data[i]) > 0.00000001:
                    print(f"字段 {i+1} 不匹配: 预期 {test_data[i]:.8f}, 实际 {unpacked_data[i]:.8f}")
                    all_match = False
            else:  # 其他字段是整数，需要完全匹配
                if unpacked_data[i] != test_data[i]:
                    print(f"字段 {i+1} 不匹配: 预期 {test_data[i]}, 实际 {unpacked_data[i]}")
                    all_match = False
        
        if all_match:
            print("\n✅ 所有字段解析成功！")
            
            # 专门检查经度和纬度精度
            print(f"\n经度精度: {abs(unpacked_data[14] - test_data[14]):.10f}")
            print(f"纬度精度: {abs(unpacked_data[15] - test_data[15]):.10f}")
            
            if abs(unpacked_data[14] - test_data[14]) < 0.00000001:
                print("✅ 经度精度符合要求 (小于1e-8度)")
            if abs(unpacked_data[15] - test_data[15]) < 0.00000001:
                print("✅ 纬度精度符合要求 (小于1e-8度)")
                
        else:
            print("\n❌ 字段解析不匹配")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        print(f"堆栈: {traceback.format_exc()}")

test_correct_parse()
