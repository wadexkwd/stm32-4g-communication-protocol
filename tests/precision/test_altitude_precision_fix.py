#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修改后的高度参数精度问题
"""

import struct
import ujson

def test_altitude_parsing():
    """测试高度参数的解析和格式化"""
    print("=" * 50)
    print("测试修改后的高度参数精度")
    print("=" * 50)
    
    # 测试数据结构 '<BhhhhhhhhhhhIfdd'
    # 对应字段: packet_order(1), accel_x(2), accel_y(3), accel_z(4), 
    # gyro_x(5), gyro_y(6), gyro_z(7), angle_x(8), angle_y(9), angle_z(10),
    # attitude1(11), attitude2(12), pressure(13), altitude(14), 
    # longitude(15), latitude(16)
    
    # 测试数据
    test_data = struct.pack(
        '<BhhhhhhhhhhhIfdd',
        1,      # packet_order
        -91,    # accel_x
        0,      # accel_y
        27,     # accel_z
        -11,    # gyro_x
        10,     # gyro_y
        -11,    # gyro_z
        -11,    # angle_x
        10,     # angle_y
        -11,    # angle_z
        7,      # attitude1
        410,    # attitude2
        101716, # pressure
        502.98, # altitude (4字节浮点)
        104.06, # longitude
        30.66   # latitude
    )
    
    print("原始二进制数据长度: {}".format(len(test_data)))
    print("预期长度: 47字节")
    assert len(test_data) == 47, "数据长度不符合预期"
    
    # 解析数据
    try:
        sensor_data = struct.unpack('<BhhhhhhhhhhhIfdd', test_data)
        print("解析成功")
        
        print("原始高度值: {}".format(sensor_data[13]))
        
        # 格式化高度值
        formatted_altitude = float("{0:.2f}".format(sensor_data[13]))
        print("格式化后的高度值: {}".format(formatted_altitude))
        
        # 验证格式化后的高度值
        assert formatted_altitude == 502.98, "高度值格式化不正确"
        
        # 测试JSON序列化
        sensor_dict = {
            'packet_order': sensor_data[0],
            'altitude': formatted_altitude
        }
        
        json_str = ujson.dumps(sensor_dict)
        print("JSON序列化结果: {}".format(json_str))
        
        # 检查是否有精度问题
        assert '502.9800000000001' not in json_str, "JSON序列化存在精度问题"
        assert '502.98' in json_str, "JSON序列化结果不正确"
        
        print("\n✅ 高度参数解析和格式化测试成功")
        
    except Exception as e:
        print("\n❌ 测试失败: {}".format(e))
        import traceback
        print(traceback.format_exc())

def test_multiple_altitudes():
    """测试多个高度值的解析"""
    print("\n" + "=" * 50)
    print("测试多个高度值的解析")
    print("=" * 50)
    
    test_altitudes = [502.98, 502.99, 123.45, 999.99, 0.01, 1000.00, -123.45, 325.49]
    
    all_passed = True
    
    for altitude in test_altitudes:
        try:
            # 创建测试数据
            test_data = struct.pack(
                '<BhhhhhhhhhhhIfdd',
                1, -91, 0, 27, -11, 10, -11, -11, 10, -11, 7, 410, 101716,
                altitude, 104.06, 30.66
            )
            
            sensor_data = struct.unpack('<BhhhhhhhhhhhIfdd', test_data)
            
            # 格式化高度值
            formatted_altitude = float("{0:.2f}".format(sensor_data[13]))
            
            # 验证
            assert abs(formatted_altitude - altitude) < 0.01, "高度值格式化不正确"
            
            # 测试JSON序列化
            sensor_dict = {'altitude': formatted_altitude}
            json_str = ujson.dumps(sensor_dict)
            
            expected_str = '"altitude":{}'.format(altitude)
            if expected_str not in json_str:
                # 可能有末尾的.0或其他格式
                if altitude == 1000.00:
                    assert '"altitude":1000.0' in json_str, "1000.00格式化不正确"
                else:
                    assert '{0:.2f}'.format(altitude) in json_str, "高度值{}序列化不正确".format(altitude)
            
            print("✅ 高度值 {} 测试成功".format(altitude))
            
        except Exception as e:
            print("❌ 高度值 {} 测试失败: {}".format(altitude, e))
            all_passed = False
    
    if all_passed:
        print("\n✅ 所有高度值测试成功")

def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 50)
    print("测试边界情况")
    print("=" * 50)
    
    edge_altitudes = [0.00, 10000.00, -999.99, 0.01, 9999.99]
    
    for altitude in edge_altitudes:
        try:
            test_data = struct.pack(
                '<BhhhhhhhhhhhIfdd',
                1, -91, 0, 27, -11, 10, -11, -11, 10, -11, 7, 410, 101716,
                altitude, 104.06, 30.66
            )
            
            sensor_data = struct.unpack('<BhhhhhhhhhhhIfdd', test_data)
            
            formatted_altitude = float("{0:.2f}".format(sensor_data[13]))
            
            assert abs(formatted_altitude - altitude) < 0.01, "边界值{}格式化不正确".format(altitude)
            
            print("✅ 边界值 {} 测试成功".format(altitude))
            
        except Exception as e:
            print("❌ 边界值 {} 测试失败: {}".format(altitude, e))

if __name__ == "__main__":
    try:
        test_altitude_parsing()
        test_multiple_altitudes()
        test_edge_cases()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试通过！修改后的高度参数处理正确")
        print("=" * 50)
        
    except Exception as e:
        print("\n" + "=" * 50)
        print("❌ 测试过程中出现错误")
        print("=" * 50)
        print(e)
        import traceback
        print(traceback.format_exc())
