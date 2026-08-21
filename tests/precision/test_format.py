#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 mqtt_listener.py 中的格式化输出函数
"""

import sys
import os

# 将当前目录添加到系统路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入 mqtt_listener 模块
import mqtt_listener

# 模拟测试数据（传感器数据列表）
test_data = [
    {
        'timestamp': '2026-01-16 08:16:11',
        'version': '1001',
        'packet_order': '36',
        'accel_x': '0',
        'accel_y': '0',
        'accel_z': '0',
        'gyro_x': '0',
        'gyro_y': '0',
        'gyro_z': '0',
        'angle_x': '0',
        'angle_y': '0',
        'angle_z': '0',
        'attitude1': '2',
        'attitude2': '1',
        'pressure': '95325',
        'altitude': '1140847598',
        'longitude': '104.06',
        'latitude': '30.66'
    }
]

print("测试格式化输出函数:")
print("-" * 80)

# 调用格式化函数
mqtt_listener.format_sensor_data(test_data)

print("\n" + "-" * 80)
print("测试完成！")
