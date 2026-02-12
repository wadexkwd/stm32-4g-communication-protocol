#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - 配置参数模块
功能：
- 存放所有配置参数，包括MQTT服务器配置、传感器字段定义、事件类型映射等
- 提供统一的配置管理，便于修改和维护
"""

# =============================================================================
# 配置参数
# =============================================================================
MQTT_BROKER = "120.27.250.30"
MQTT_PORT = 1883
MQTT_USERNAME = ""
MQTT_PASSWORD = ""
DATABASE_FILE = "sensor_data.db"

# 传感器数据字段定义（按照协议顺序）
FIELD_ORDER = [
    'timestamp', 'version', 'packet_order', 'event',
    'accel_x', 'accel_y', 'accel_z',
    'gyro_x', 'gyro_y', 'gyro_z',
    'attitude1', 'attitude2', 'pressure',
    'altitude', 'longitude', 'latitude'
]

# 字段名映射（用于显示）
FIELD_NAMES = {
    'timestamp': '时间戳',
    'version': '版本',
    'packet_order': '包序',
    'event': '事件类型',
    'accel_x': '加速度X',
    'accel_y': '加速度Y',
    'accel_z': '加速度Z',
    'gyro_x': '角速度X',
    'gyro_y': '角速度Y',
    'gyro_z': '角速度Z',
    'angle_x': '角度X',
    'angle_y': '角度Y',
    'angle_z': '角度Z',
    'attitude1': '俯仰角',
    'attitude2': '翻滚角',
    'pressure': '气压',
    'altitude': '高度',
    'longitude': '经度',
    'latitude': '纬度'
}

# 事件类型映射
EVENT_TYPES = {
    'POWER_ON': '上电包',
    'SENSOR_DATA': '传感器数据包',
    'SENSOR_REPORT_TIMEOUT': '传感器数据超时事件包'
}

# 字段单位
FIELD_UNITS = {
    'accel_x': 'mg', 'accel_y': 'mg', 'accel_z': 'mg',
    'gyro_x': '°/s', 'gyro_y': '°/s', 'gyro_z': '°/s',
    'angle_x': '°', 'angle_y': '°', 'angle_z': '°',
    'attitude1': '°', 'attitude2': '°',
    'pressure': 'kPa', 'altitude': 'm',
    'longitude': '°', 'latitude': '°'
}

# 字段分类（用于分区展示）
FIELD_CATEGORIES = {
    '加速度': ['accel_x', 'accel_y', 'accel_z'],
    '角速度': ['gyro_x', 'gyro_y', 'gyro_z'],
    '姿态': ['attitude1', 'attitude2'],
    '环境': ['pressure', 'altitude'],
    '位置': ['longitude', 'latitude']
}
