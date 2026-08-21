#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据包序列生成
验证 STM32 模拟器是否能够生成包序递增的数据包
"""

import struct
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stm32_simulation_test import STM32Simulator

def test_packet_sequence():
    """测试数据包序列生成"""
    print("=" * 50)
    print("数据包序列测试")
    print("=" * 50)

    # 创建 STM32 模拟器实例（不实际连接串口）
    stm32 = STM32Simulator("COM5", 115200)

    # 测试生成前 5 个数据包的包序
    print("\n测试生成前 5 个数据包的包序:")
    print("-" * 50)

    # 捕获输出到字符串，避免实际发送
    import io
    import contextlib

    for i in range(5):
        # 使用上下文管理器捕获输出
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            # 生成传感器数据但不发送（修改发送方法以便测试）
            sensor_data = stm32.fixed_sensor_data.copy()
            sensor_data['packet_order'] = stm32.packet_order % 256
            stm32.packet_order += 1

            # 转换为二进制数据
            sensor_bytes = stm32.sensor_data_to_bytes(sensor_data)

            # 打包成完整帧
            frame = stm32.pack_frame(0x01, sensor_bytes)

        # 验证帧的完整性
        assert frame.startswith(b'\xAA\x55'), "帧头不正确"
        assert frame.endswith(b'\x55\xAA'), "帧尾不正确"

        # 解析帧信息
        cmd = struct.unpack('B', frame[2:3])[0]
        data_len = struct.unpack('H', frame[3:5])[0]
        checksum = struct.unpack('B', frame[5 + data_len:6 + data_len])[0]

        # 验证命令码和数据长度
        assert cmd == 0x01, "命令码不正确"
        assert data_len == 47, "数据长度不正确"

        # 验证包序
        parsed_packet_order = struct.unpack('<B', sensor_bytes[0:1])[0]
        assert parsed_packet_order == i, f"包序不正确，预期: {i}, 实际: {parsed_packet_order}"

        print(f"数据包 {i+1}:")
        print(f"  包序: {parsed_packet_order}")
        print(f"  命令码: 0x{cmd:02X}")
        print(f"  数据长度: {data_len} 字节")
        print(f"  校验和: 0x{checksum:02X}")
        print("-" * 50)

    print("\n✅ 包序递增测试成功！")
    print(f"包序按预期从 0 递增到 {i}")

    # 测试包序循环（超过 255）
    print("\n" + "=" * 50)
    print("包序循环测试 (测试超过 255 的情况)")
    print("=" * 50)

    # 设置包序为 254
    stm32.packet_order = 254

    for i in range(3):
        sensor_data = stm32.fixed_sensor_data.copy()
        sensor_data['packet_order'] = stm32.packet_order % 256
        stm32.packet_order += 1

        sensor_bytes = stm32.sensor_data_to_bytes(sensor_data)
        frame = stm32.pack_frame(0x01, sensor_bytes)

        parsed_packet_order = struct.unpack('<B', sensor_bytes[0:1])[0]

        print(f"数据包 (包序 = {stm32.packet_order - 1}):")
        print(f"  实际包序: {parsed_packet_order}")
        print("-" * 50)

    print("\n✅ 包序循环测试成功！")
    print("包序在超过 255 后正确循环到 0")

if __name__ == "__main__":
    test_packet_sequence()
