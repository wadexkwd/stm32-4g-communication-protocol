#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - Web后端数据库模块
功能：
- SQLite 初始化、批量插入、历史查询、设备列表
- 表结构与 qt/database_manager.py 保持一致（可读写同一份数据文件）
- 线程安全：MQTT线程写入 + API线程查询，使用锁 + 连接级操作
"""

import sqlite3
import threading
from datetime import datetime

from config import DATABASE_FILE, DB_COLUMNS


class Database:
    """数据库操作管理器（线程安全）"""

    def __init__(self, db_file=DATABASE_FILE):
        self.db_file = db_file
        self._lock = threading.Lock()
        self._init_database()

    def _connect(self):
        conn = sqlite3.connect(self.db_file, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """初始化数据库表结构"""
        with self._lock:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT, version TEXT, packet_order TEXT, event TEXT,
                    accel_x REAL, accel_y REAL, accel_z REAL,
                    gyro_x REAL, gyro_y REAL, gyro_z REAL,
                    angle_x REAL, angle_y REAL, angle_z REAL,
                    attitude1 REAL, attitude2 REAL,
                    pressure REAL, altitude REAL, longitude REAL, latitude REAL,
                    imei TEXT, received_time TEXT
                )
            ''')
            # 兼容已存在的旧表：补齐缺失列（与 qt 方案的 ALTER 逻辑一致）
            cursor.execute("PRAGMA table_info(sensor_data)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'event' not in columns:
                cursor.execute("ALTER TABLE sensor_data ADD COLUMN event TEXT")
            # 常用查询索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_data_imei_time
                ON sensor_data (imei, received_time)
            ''')
            conn.commit()
            conn.close()

    def save_data(self, data_list, imei):
        """批量保存数据（data_list 为解析后的 dict 列表）"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        placeholders = ', '.join(['?'] * len(DB_COLUMNS))
        columns_str = ', '.join(DB_COLUMNS)
        sql = f'INSERT INTO sensor_data ({columns_str}) VALUES ({placeholders})'

        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.cursor()
                for data in data_list:
                    row = [data.get(col, '') for col in DB_COLUMNS[:-2]] + [imei, now]
                    cursor.execute(sql, row)
                conn.commit()
            finally:
                conn.close()

    def query_data(self, imei=None, start_time=None, end_time=None,
                   event=None, limit=1000, offset=0):
        """查询数据，返回 dict 列表（含 id）"""
        conditions = []
        params = []
        if imei:
            conditions.append('imei = ?')
            params.append(imei)
        if start_time:
            conditions.append('received_time >= ?')
            params.append(start_time)
        if end_time:
            conditions.append('received_time <= ?')
            params.append(end_time)
        if event:
            conditions.append('event = ?')
            params.append(event)

        where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
        sql = f'SELECT * FROM sensor_data {where} ORDER BY received_time DESC, id DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(sql, params).fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()

    def count_data(self, imei=None, start_time=None, end_time=None, event=None):
        """统计符合条件的记录数"""
        conditions = []
        params = []
        if imei:
            conditions.append('imei = ?')
            params.append(imei)
        if start_time:
            conditions.append('received_time >= ?')
            params.append(start_time)
        if end_time:
            conditions.append('received_time <= ?')
            params.append(end_time)
        if event:
            conditions.append('event = ?')
            params.append(event)

        where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
        sql = f'SELECT COUNT(*) FROM sensor_data {where}'

        with self._lock:
            conn = self._connect()
            try:
                return conn.execute(sql, params).fetchone()[0]
            finally:
                conn.close()

    def get_devices(self):
        """获取出现过的设备列表（IMEI + 最近上报时间 + 记录数）"""
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute('''
                    SELECT imei, MAX(received_time) AS last_time, COUNT(*) AS count
                    FROM sensor_data
                    WHERE imei IS NOT NULL AND imei != ''
                    GROUP BY imei
                    ORDER BY last_time DESC
                ''').fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()

    def get_latest_by_device(self, imei, limit=1):
        """获取设备最近 N 条数据（用于前端进入页面时的初始展示）"""
        return self.query_data(imei=imei, limit=limit)
