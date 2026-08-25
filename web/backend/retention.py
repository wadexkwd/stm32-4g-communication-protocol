#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - 数据保留策略服务
功能：
- 后台线程按 RETENTION_INTERVAL_SEC 周期执行清理：
  1) 读取每台设备的保留天数（device_settings 表的设备级配置，未配置则用全局 RETENTION_DAYS）
  2) 逐台设备统计早于保留窗口的记录
  3) 归档（可选）：流式导出为 CSV.gz 存入 ARCHIVE_DIR
  4) 删除已归档/过期记录
  5) VACUUM 回收文件空间
- 保留天数为 0 表示永久保留，只统计不删除
- 前端修改设备保留配置后会调用 trigger()，数秒内按新配置执行一次清理
- 清理结果记录在 last_result，供 /api/dashboard 展示
"""

import csv
import gzip
import os
import threading
import traceback
from datetime import datetime, timedelta

from config import (RETENTION_DAYS, ARCHIVE_ENABLED, ARCHIVE_DIR,
                    RETENTION_INTERVAL_SEC, RETENTION_START_DELAY_SEC, DB_COLUMNS)


class RetentionService(threading.Thread):
    """数据保留策略服务（后台线程）"""

    def __init__(self, database):
        super().__init__(daemon=True, name='retention-service')
        self.database = database
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()   # 配置变更后提前唤醒清理循环
        # 最近一次清理结果：{time, retention_days, archived_file, deleted_rows, error, devices}
        self.last_result = {'time': None, 'retention_days': RETENTION_DAYS,
                            'archived_file': None, 'deleted_rows': 0, 'error': None,
                            'devices': []}

    # ------------------------------------------------------------------ 运行控制
    def run(self):
        self._stop_event.wait(RETENTION_START_DELAY_SEC)
        while not self._stop_event.is_set():
            try:
                self.run_task()
            except Exception as e:
                self.last_result['error'] = f'{e}'
                traceback.print_exc()
            # 等待下一周期，或被 trigger() 提前唤醒（配置变更立即生效）
            self._wake_event.wait(RETENTION_INTERVAL_SEC)
            self._wake_event.clear()

    def stop(self):
        self._stop_event.set()
        self._wake_event.set()

    def trigger(self):
        """提前唤醒清理循环（配置变更后调用，数秒内按新配置清理）"""
        self._wake_event.set()

    # ------------------------------------------------------------------ 清理任务
    def run_task(self):
        result = {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  'retention_days': RETENTION_DAYS,
                  'archived_file': None, 'deleted_rows': 0, 'error': None,
                  'devices': []}

        # 设备日志限量保留（与数据保留策略无关，始终执行，防止日志无限增长）
        self.database.prune_device_logs()

        # 每台设备的生效保留天数：设备级配置优先，否则用全局默认
        settings = self.database.get_device_retentions()
        devices = [d['imei'] for d in self.database.get_devices()]

        deleted_total = 0
        archived_names = []
        errors = []
        vacuum_needed = False

        for imei in devices:
            days = settings.get(imei, RETENTION_DAYS)
            if not days or days <= 0:
                continue    # 永久保留
            cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            expired = self.database.count_before(cutoff, imei=imei)
            if expired <= 0:
                continue

            device_result = {'imei': imei, 'days': days, 'deleted_rows': 0,
                             'archived_file': None, 'error': None}
            # 先归档再删除（归档失败则不删除，宁可占盘不可丢数）
            if ARCHIVE_ENABLED:
                archive_path = self._archive(cutoff, imei)
                if archive_path:
                    device_result['archived_file'] = os.path.basename(archive_path)
                    archived_names.append(device_result['archived_file'])
                else:
                    device_result['error'] = '归档失败，本次跳过删除'
                    errors.append(f'{imei}: 归档失败')
                    result['devices'].append(device_result)
                    continue

            device_result['deleted_rows'] = self.database.delete_before(cutoff, imei=imei)
            deleted_total += device_result['deleted_rows']
            vacuum_needed = True
            result['devices'].append(device_result)

        if vacuum_needed:
            self.database.vacuum()

        result['deleted_rows'] = deleted_total
        result['archived_file'] = ', '.join(archived_names) if archived_names else None
        result['error'] = '; '.join(errors) if errors else None
        self.last_result = result

    def _archive(self, cutoff_time, imei):
        """把指定设备的过期数据流式导出为 CSV.gz，返回文件路径；失败返回 None"""
        try:
            os.makedirs(ARCHIVE_DIR, exist_ok=True)
            stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = os.path.join(ARCHIVE_DIR, f'sensor_data_{imei}_{stamp}.csv.gz')

            with gzip.open(path, 'wt', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(DB_COLUMNS)
                count = 0
                for row in self.database.iter_rows_before(cutoff_time, imei=imei):
                    writer.writerow([row.get(col, '') for col in DB_COLUMNS])
                    count += 1
            if count == 0:
                # 并发下无数据可归档，删除空文件
                os.remove(path)
                return None
            print(f"[retention] 已归档 {imei} 过期数据 {count} 条 -> {path}")
            return path
        except Exception as e:
            print(f"[retention] 归档失败({imei}): {e}")
            traceback.print_exc()
            return None
