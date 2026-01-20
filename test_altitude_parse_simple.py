#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试高度值解析
"""

import struct

# 测试高度值解析
def test_altitude_parsing():
    """测试高度值解析"""
    
    # 测试浮点数
    altitude_float = 123.45
    packed_float = struct.pack('<f', altitude_float)
    unpacked_float = struct.unpack('<f', packed_float)[0]
    
    # 测试整数
    altitude_uint32 = 12345
    packed_uint32 = struct.pack('<I', altitude_uint32)
    unpacked_uint32 = struct.unpack('<I', packed_uint32)[0]
    
    print("浮点数高度测试:")
    print(f"原始值: {altitude_float}")
    print(f"打包后字节: {list(packed_float)}")
    print(f"解包后值: {unpacked_float:.2f}")
    
    print("\n整数高度测试:")
    print(f"原始值: {altitude_uint32}")
    print(f"打包后字节: {list(packed_uint32)}")
    print(f"解包后值: {unpacked_uint32}")
    
    print("\n字节长度:")
    print(f"浮点数: {len(packed_float)} bytes")
    print(f"整数: {len(packed_uint32)} bytes")

test_altitude_parsing()
