#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试格式字符串字段计数
"""

import struct

def count_fields(format_str):
    """计算格式字符串的字段数量"""
    count = 0
    i = 0
    while i < len(format_str):
        char = format_str[i]
        
        if char in ['<', '>', '!', '@']:
            i += 1
            continue
            
        if char.isdigit():
            num = int(char)
            type_char = format_str[i+1]
            count += num
            i += 2
        else:
            count += 1
            i += 1
    return count

# 测试格式字符串
format_str1 = '<BhhhhhhhhhhIIdd'
print(f"格式字符串: {format_str1}")
print(f"字段数: {count_fields(format_str1)}")
print(f"calcsize: {struct.calcsize(format_str1)} bytes")

format_str2 = '<BhhhhhhhhhhIfdd'
print(f"\n格式字符串: {format_str2}")
print(f"字段数: {count_fields(format_str2)}")
print(f"calcsize: {struct.calcsize(format_str2)} bytes")

format_str3 = '<Bhhhhhhhhhhhfdd'
print(f"\n格式字符串: {format_str3}")
print(f"字段数: {count_fields(format_str3)}")
print(f"calcsize: {struct.calcsize(format_str3)} bytes")

# 测试创建数据
test_data = [
    1,
    2,3,4,5,6,7,8,9,10,11,12,13,  # 11个int16
    14,15,  # 2个uint32
    16.0,17.0  # 2个double
]
print(f"\n测试数据长度: {len(test_data)}")

# 测试打包
try:
    data = struct.pack(format_str1, *test_data)
    print(f"✅ 打包成功！字节数: {len(data)}")
    unpacked = struct.unpack(format_str1, data)
    print(f"✅ 解包成功！字段数: {len(unpacked)}")
    print(f"解包结果: {unpacked}")
    
except Exception as e:
    print(f"❌ 打包失败: {e}")
    import traceback
    print(f"堆栈: {traceback.format_exc()}")
