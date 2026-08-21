#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - Web后端配置模块
功能：
- 存放MQTT服务器、数据库等配置参数
- 字段定义/事件类型映射与 qt/config.py 保持一致
"""

import os

# =============================================================================
# 配置参数
# =============================================================================
MQTT_BROKER = "120.27.250.30"
MQTT_PORT = 1883
MQTT_USERNAME = ""
MQTT_PASSWORD = ""
MQTT_TOPIC_UP_PREFIX = "up/"          # 上行数据主题前缀，订阅 up/+ 通配所有设备
MQTT_CLIENT_ID = "web_backend_listener"

# 数据库文件（默认 web/backend/sensor_data.db，可改为指向 qt 方案的 sensor_data.db 共用数据）
_DATABASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(_DATABASE_DIR, "sensor_data.db")

# Web服务配置
WEB_HOST = "0.0.0.0"
WEB_PORT = 8000

# 前端静态文件目录
FRONTEND_DIR = os.path.normpath(os.path.join(_DATABASE_DIR, "..", "frontend"))

# 传感器数据字段定义（按照协议顺序）
FIELD_ORDER = [
    'timestamp', 'version', 'packet_order', 'event',
    'accel_x', 'accel_y', 'accel_z',
    'gyro_x', 'gyro_y', 'gyro_z',
    'angle_x', 'angle_y', 'angle_z',
    'attitude1', 'attitude2',
    'pressure', 'altitude', 'longitude', 'latitude'
]

# 数据库列（FIELD_ORDER + 设备号 + 接收时间）
DB_COLUMNS = FIELD_ORDER + ['imei', 'received_time']

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

# 图表曲线定义（key -> 标题, y轴单位, 字段列表）
CHARTS = {
    'accel': {
        'title': '加速度随时间变化曲线',
        'unit': 'mg',
        'fields': ['accel_x', 'accel_y', 'accel_z'],
    },
    'gyro': {
        'title': '角速度随时间变化曲线',
        'unit': '°/s',
        'fields': ['gyro_x', 'gyro_y', 'gyro_z'],
    },
    'pitch': {
        'title': '俯仰角随时间变化曲线',
        'unit': '°',
        'fields': ['attitude1'],
    },
    'roll': {
        'title': '翻滚角随时间变化曲线',
        'unit': '°',
        'fields': ['attitude2'],
    },
    'env': {
        'title': '气压/高度变化曲线',
        'unit': '',
        'fields': ['pressure', 'altitude'],
    },
}
