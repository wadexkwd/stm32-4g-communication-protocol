#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - 数据库操作模块
功能：
- 提供数据库初始化、数据保存、查询和设备列表获取功能
- 封装SQLite数据库操作，确保数据持久化存储
"""

import sqlite3
from datetime import datetime
from PySide6.QtCore import QDateTime
from config import DATABASE_FILE

class DatabaseManager:
    """数据库操作管理器"""
    
    def __init__(self, db_file=DATABASE_FILE):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 检查事件类型字段是否存在
        cursor.execute("PRAGMA table_info(sensor_data)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'event' not in columns:
            # 添加事件类型字段
            cursor.execute("ALTER TABLE sensor_data ADD COLUMN event TEXT")
        
        conn.commit()
        conn.close()
    
    def save_data(self, data_list, imei):
        """保存数据到数据库"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        for data in data_list:
            # 准备数据
            row_data = [
                data.get('timestamp', ''),
                data.get('version', ''),
                data.get('packet_order', ''),
                data.get('event', ''),
                data.get('accel_x', ''),
                data.get('accel_y', ''),
                data.get('accel_z', ''),
                data.get('gyro_x', ''),
                data.get('gyro_y', ''),
                data.get('gyro_z', ''),
                data.get('angle_x', ''),
                data.get('angle_y', ''),
                data.get('angle_z', ''),
                data.get('attitude1', ''),
                data.get('attitude2', ''),
                data.get('pressure', ''),
                data.get('altitude', ''),
                data.get('longitude', ''),
                data.get('latitude', ''),
                imei,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            ]
            
            # 插入数据
            cursor.execute('''
                INSERT INTO sensor_data (
                    timestamp, version, packet_order, event, accel_x, accel_y, accel_z,
                    gyro_x, gyro_y, gyro_z, angle_x, angle_y, angle_z,
                    attitude1, attitude2, pressure, altitude, longitude, latitude,
                    imei, received_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', row_data)
        
        conn.commit()
        conn.close()
    
    def query_data(self, imei, start_time, end_time):
        """查询指定IMEI和时间段的数据"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 格式化时间查询
        start_str = start_time.toString('yyyy-MM-dd HH:mm:ss')
        end_str = end_time.toString('yyyy-MM-dd HH:mm:ss')
        
        cursor.execute('''
            SELECT * FROM sensor_data 
            WHERE imei = ? AND received_time BETWEEN ? AND ?
            ORDER BY received_time ASC
        ''', (imei, start_str, end_str))
        
        results = cursor.fetchall()
        conn.close()
        
        return results

    def get_subscribed_devices(self):
        """获取已订阅的设备列表"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT imei FROM sensor_data
            ORDER BY imei
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in results if row[0]]