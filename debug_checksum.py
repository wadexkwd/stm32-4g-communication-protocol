#!/usr/bin/env python
# -*- coding: utf-8 -*-

from stm32_simulation_test import SensorDataGenerator, STM32Simulator, CMD_DATA_UPLOAD

# 创建测试数据
data_generator = SensorDataGenerator()
test_data = data_generator.generate_sensor_data()
data_bytes = data_generator.sensor_data_to_bytes(test_data)

# 创建模拟器实例
simulator = STM32Simulator('COM5', 115200)

# 计算校验和
checksum1 = simulator.calculate_checksum(CMD_DATA_UPLOAD, len(data_bytes), data_bytes)

print("调试校验和计算:")
print("=" * 50)
print(f"命令码: 0x{CMD_DATA_UPLOAD:02X}")
print(f"数据长度: 0x{len(data_bytes):04X} ({len(data_bytes)}字节)")
print(f"数据域字节数: {len(data_bytes)}")
print(f"数据域 (十六进制): {' '.join(f'{b:02X}' for b in data_bytes)}")
print(f"\n计算的校验和: 0x{checksum1:02X}")

# 手动计算校验和以验证
checksum2 = CMD_DATA_UPLOAD
checksum2 ^= (len(data_bytes) >> 8) & 0xFF
checksum2 ^= len(data_bytes) & 0xFF
for byte in data_bytes:
    checksum2 ^= byte
    print(f"  添加字节 0x{byte:02X}，校验和变为 0x{checksum2:02X}")

print(f"\n手动计算的校验和: 0x{checksum2:02X}")

# 验证两个计算结果是否一致
if checksum1 == checksum2:
    print("\n✓ 校验和计算一致")
else:
    print("\n✗ 校验和计算不一致")

# 打包成帧并检查校验和
frame = simulator.pack_frame(CMD_DATA_UPLOAD, data_bytes)
print(f"\n打包后的帧长度: {len(frame)}字节")
print(f"帧内容 (十六进制): {' '.join(f'{b:02X}' for b in frame)}")

# 从帧中提取校验和
frame_checksum = frame[3 + len(data_bytes)]  # 2字节帧头 + 1字节命令 + 2字节长度 + 数据长度
print(f"帧中的校验和: 0x{frame_checksum:02X}")

# 验证打包后的校验和是否正确
if frame_checksum == checksum1:
    print("\n✓ 帧中的校验和正确")
else:
    print("\n✗ 帧中的校验和不正确")
    print(f"  预期校验和: 0x{checksum1:02X}")
    print(f"  实际校验和: 0x{frame_checksum:02X}")
