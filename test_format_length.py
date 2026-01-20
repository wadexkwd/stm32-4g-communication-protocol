#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试格式字符串长度
"""

import struct

# 测试格式字符串长度
format_str = '<Bhhhhhhhhhhhfdd'
print(f"格式字符串: {format_str}")

# 计算字段数量
count = 0
i = 1  # 跳过 '<'
while i < len(format_str):
    char = format_str[i]
    if char.isdigit():
        # 数字后面紧跟类型
        num = int(char)
        type_char = format_str[i+1]
        count += num
        i += 2
    else:
        count += 1
        i += 1

print(f"字段数量: {count}")

# 计算预期大小
size = struct.calcsize(format_str)
print(f"计算大小: {size} bytes")

# 测试打包
try:
    # 根据格式字符串确定字段数
    data = struct.pack(format_str,
        1,       # B
        2,3,4,5,6,7,8,9,10,11,12,13,  # h (12个)
        14.5,    # f
        15.6,16.7 # d (2个)
    )
    print(f"打包成功，字节数: {len(data)}")
    print(f"字节: {list(data)}")
    
    # 解包
    unpacked = struct.unpack(format_str, data)
    print(f"解包成功，字段数: {len(unpacked)}")
    print(f"解包结果: {unpacked}")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    print(f"堆栈: {traceback.format_exc()}")
