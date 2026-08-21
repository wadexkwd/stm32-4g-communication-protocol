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
from datetime import datetime, timedelta

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

    def get_latest_rows_by_device(self):
        """每个设备最新一条数据（含位置/事件/版本），用于数据看板"""
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute('''
                    SELECT s.* FROM sensor_data s
                    JOIN (SELECT imei, MAX(id) AS mid FROM sensor_data GROUP BY imei) t
                      ON s.id = t.mid
                    ORDER BY s.received_time DESC
                ''').fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()

    def get_recent_event_counts(self, hours=24):
        """近 N 小时各设备异常事件计数：{imei: {'POWER_ON': n, 'SENSOR_REPORT_TIMEOUT': m}}"""
        since = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute('''
                    SELECT imei, event, COUNT(*) AS cnt FROM sensor_data
                    WHERE event IN ('POWER_ON', 'SENSOR_REPORT_TIMEOUT')
                      AND received_time >= ?
                    GROUP BY imei, event
                ''', (since,)).fetchall()
                result = {}
                for row in rows:
                    result.setdefault(row['imei'], {})[row['event']] = row['cnt']
                return result
            finally:
                conn.close()

    def get_recent_volume(self, hours=24):
        """近 N 小时各设备上报记录数：{imei: count}"""
        since = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute('''
                    SELECT imei, COUNT(*) AS cnt FROM sensor_data
                    WHERE received_time >= ?
                    GROUP BY imei
                ''', (since,)).fetchall()
                return {row['imei']: row['cnt'] for row in rows}
            finally:
                conn.close()

    def get_recent_events_hourly(self, hours=24):
        """近 N 小时异常事件按小时计数：{ 'YYYY-MM-DD HH:00': {'SENSOR_REPORT_TIMEOUT': n, 'POWER_ON': m} }"""
        since = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute('''
                    SELECT strftime('%Y-%m-%d %H:00', received_time) AS hour, event, COUNT(*) AS cnt
                    FROM sensor_data
                    WHERE event IN ('POWER_ON', 'SENSOR_REPORT_TIMEOUT') AND received_time >= ?
                    GROUP BY hour, event
                    ORDER BY hour
                ''', (since,)).fetchall()
                result = {}
                for row in rows:
                    result.setdefault(row['hour'], {})[row['event']] = row['cnt']
                return result
            finally:
                conn.close()

    # ------------------------------------------------------------------ 保留策略支撑
    def count_before(self, cutoff_time):
        """统计早于指定时间（含）的记录数"""
        with self._lock:
            conn = self._connect()
            try:
                return conn.execute(
                    'SELECT COUNT(*) FROM sensor_data WHERE received_time < ?',
                    (cutoff_time,)).fetchone()[0]
            finally:
                conn.close()

    def iter_rows_before(self, cutoff_time):
        """流式迭代早于指定时间的记录（逐批 yield，避免大结果集占内存）"""
        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.execute(
                    'SELECT * FROM sensor_data WHERE received_time < ? ORDER BY id',
                    (cutoff_time,))
                while True:
                    batch = cursor.fetchmany(5000)
                    if not batch:
                        break
                    for row in batch:
                        yield dict(row)
            finally:
                conn.close()

    def delete_before(self, cutoff_time):
        """删除早于指定时间的记录，返回删除行数"""
        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.execute(
                    'DELETE FROM sensor_data WHERE received_time < ?',
                    (cutoff_time,))
                conn.commit()
                return cursor.rowcount
            finally:
                conn.close()

    def vacuum(self):
        """回收已删除数据的空间（VACUUM 会短暂阻塞写入，在清理任务里低频调用）"""
        with self._lock:
            conn = self._connect()
            try:
                conn.execute('VACUUM')
            finally:
                conn.close()

    def get_storage_stats(self):
        """存储统计：总行数/最早记录/文件大小"""
        import os
        with self._lock:
            conn = self._connect()
            try:
                total, oldest = conn.execute(
                    'SELECT COUNT(*), MIN(received_time) FROM sensor_data').fetchone()
            finally:
                conn.close()
        try:
            size_mb = round(os.path.getsize(self.db_file) / 1024 / 1024, 2)
        except OSError:
            size_mb = None
        return {'total_rows': total, 'oldest_time': oldest, 'db_size_mb': size_mb}
