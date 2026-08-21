#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
conn = sqlite3.connect('sensor_data.db')
cursor = conn.cursor()

# 检查表结构
cursor.execute('PRAGMA table_info(sensor_data)')
print('=== 表结构 ===')
for col in cursor.fetchall():
    print(f'{col[0]}: {col[1]} ({col[2]})')

# 查询前几行数据
cursor.execute('SELECT * FROM sensor_data LIMIT 5')
print('\n=== 前5行数据 ===')
for row in cursor.fetchall():
    print(row)

conn.close()