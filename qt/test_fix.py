#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试修复后的代码是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_window import DatabaseManager

def test_db_query_and_field_mapping():
    """测试数据库查询和字段映射"""
    try:
        # 初始化数据库管理器
        db_manager = DatabaseManager()
        
        # 获取已订阅的设备列表
        devices = db_manager.get_subscribed_devices()
        print(f"已订阅设备: {devices}")
        
        if devices:
            # 选择第一个设备进行测试
            test_imei = devices[0]
            
            from PySide6.QtCore import QDateTime
            # 查询最近5分钟的数据
            end_time = QDateTime.currentDateTime()
            start_time = end_time.addSecs(-300)
            
            results = db_manager.query_data(test_imei, start_time, end_time)
            
            if results:
                print(f"查询到 {len(results)} 条数据")
                
                # 打印第一条数据的详细信息
                first_data = results[0]
                print(f"\n第一条数据: {first_data}")
                
                # 数据库字段索引映射
                db_field_index = {
                    'timestamp': 1,
                    'version': 2,
                    'packet_order': 3,
                    'event': 21,
                    'accel_x': 4,
                    'accel_y': 5,
                    'accel_z': 6,
                    'gyro_x': 7,
                    'gyro_y': 8,
                    'gyro_z': 9,
                    'angle_x': 10,
                    'angle_y': 11,
                    'angle_z': 12,
                    'attitude1': 13,
                    'attitude2': 14,
                    'pressure': 15,
                    'altitude': 16,
                    'longitude': 17,
                    'latitude': 18  # 现在指向正确的位置
                }
                
                print("\n解析后的数据:")
                for field, index in db_field_index.items():
                    value = first_data[index]
                    print(f"{field}: {value}")
                
                # 特别检查经度和纬度
                print(f"\n经度: {first_data[db_field_index['longitude']]}")
                print(f"纬度: {first_data[db_field_index['latitude']]}")
                
                return True
            else:
                print("没有找到数据")
                return False
        else:
            print("没有已订阅的设备")
            return False
            
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        print(f"堆栈跟踪: {traceback.format_exc()}")
        return False

def test_field_order_consistency():
    """测试字段顺序一致性"""
    from main_window import FIELD_ORDER
    
    # 预期的字段顺序
    expected_order = [
        'timestamp', 'version', 'packet_order', 'event',
        'accel_x', 'accel_y', 'accel_z',
        'gyro_x', 'gyro_y', 'gyro_z',
        'angle_x', 'angle_y', 'angle_z',
        'attitude1', 'attitude2', 'pressure',
        'altitude', 'longitude', 'latitude'
    ]
    
    # 检查字段顺序是否一致
    if FIELD_ORDER == expected_order:
        print("字段顺序一致")
        return True
    else:
        print("字段顺序不一致")
        print(f"预期: {expected_order}")
        print(f"实际: {FIELD_ORDER}")
        return False

if __name__ == "__main__":
    print("开始测试Qt代码修复...")
    
    print("\n测试1: 字段顺序一致性")
    test1_result = test_field_order_consistency()
    
    print("\n测试2: 数据库查询和字段映射")
    test2_result = test_db_query_and_field_mapping()
    
    print("\n=== 测试结果 ===")
    if test1_result and test2_result:
        print("✅ 修复成功")
    else:
        print("❌ 修复失败")