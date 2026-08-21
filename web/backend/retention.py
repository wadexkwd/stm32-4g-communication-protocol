#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - 数据保留策略服务
功能：
- 后台线程按 RETENTION_INTERVAL_SEC 周期执行清理：
  1) 统计早于保留窗口（RETENTION_DAYS 天）的记录
  2) 归档（可选）：流式导出为 CSV.gz 存入 ARCHIVE_DIR
  3) 删除已归档/过期记录
  4) VACUUM 回收文件空间
- RETENTION_DAYS = 0 表示永久保留，只统计不删除
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
        # 最近一次清理结果：{time, retention_days, archived_file, deleted_rows, error}
        self.last_result = {'time': None, 'retention_days': RETENTION_DAYS,
                            'archived_file': None, 'deleted_rows': 0, 'error': None}

    # ------------------------------------------------------------------ 运行控制
    def run(self):
        self._stop_event.wait(RETENTION_START_DELAY_SEC)
        while not self._stop_event.is_set():
            try:
                self.run_task()
            except Exception as e:
                self.last_result['error'] = f'{e}'
                traceback.print_exc()
            self._stop_event.wait(RETENTION_INTERVAL_SEC)

    def stop(self):
        self._stop_event.set()

    # ------------------------------------------------------------------ 清理任务
    def run_task(self):
        result = {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  'retention_days': RETENTION_DAYS,
                  'archived_file': None, 'deleted_rows': 0, 'error': None}

        if RETENTION_DAYS and RETENTION_DAYS > 0:
            cutoff = (datetime.now() - timedelta(days=RETENTION_DAYS)).strftime('%Y-%m-%d %H:%M:%S')
            expired = self.database.count_before(cutoff)
            if expired > 0:
                # 先归档再删除（归档失败则不删除，宁可占盘不可丢数）
                if ARCHIVE_ENABLED:
                    archive_path = self._archive(cutoff)
                    if archive_path:
                        result['archived_file'] = os.path.basename(archive_path)
                    else:
                        result['error'] = '归档失败，本次跳过删除'
                        self.last_result = result
                        return
                result['deleted_rows'] = self.database.delete_before(cutoff)
                self.database.vacuum()
        else:
            # 永久保留模式，仅做统计
            pass

        self.last_result = result

    def _archive(self, cutoff_time):
        """把过期数据流式导出为 CSV.gz，返回文件路径；失败返回 None"""
        try:
            os.makedirs(ARCHIVE_DIR, exist_ok=True)
            stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = os.path.join(ARCHIVE_DIR, f'sensor_data_{stamp}.csv.gz')

            with gzip.open(path, 'wt', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(DB_COLUMNS)
                count = 0
                for row in self.database.iter_rows_before(cutoff_time):
                    writer.writerow([row.get(col, '') for col in DB_COLUMNS])
                    count += 1
            if count == 0:
                # 并发下无数据可归档，删除空文件
                os.remove(path)
                return None
            print(f"[retention] 已归档 {count} 条过期数据 -> {path}")
            return path
        except Exception as e:
            print(f"[retention] 归档失败: {e}")
            traceback.print_exc()
            return None
