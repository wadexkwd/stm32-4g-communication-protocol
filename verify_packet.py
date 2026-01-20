#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct

# 从 stm32_simulation_test.py 中提取的常量和函数
CMD_DATA_UPLOAD = 0x01
FRAME_HEADER = b'\xAA\x55'
FRAME_TAIL = b'\x55\xAA'

def calculate_checksum(cmd, data_len, data):
    """计算校验和（异或校验）"""
    checksum = cmd
    checksum ^= (data_len >> 8) & 0xFF
    checksum ^= data_len & 0xFF
    for byte in data:
        checksum ^= byte
    return checksum

def pack_frame(cmd, data=b''):
    """打包数据帧"""
    data_len = len(data)
    checksum = calculate_checksum(cmd, data_len, data)
    frame = (
        FRAME_HEADER +
        struct.pack('<B', cmd) +
        struct.pack('<H', data_len) +
        data +
        struct.pack('<B', checksum) +
        FRAME_TAIL
    )
    return frame

def verify_packet(packet_hex):
    """验证数据包是否符合组包逻辑"""
    # 将十六进制字符串转换为字节数组
    packet_bytes = bytes.fromhex(packet_hex.replace(' ', ''))
    print(f"数据包字节数: {len(packet_bytes)}")
    
    # 检查帧头
    if packet_bytes[:2] != FRAME_HEADER:
        print("❌ 帧头错误")
        return False
    print("✅ 帧头正确")
    
    # 检查帧尾
    if packet_bytes[-2:] != FRAME_TAIL:
        print("❌ 帧尾错误")
        return False
    print("✅ 帧尾正确")
    
    # 解析命令码
    cmd = packet_bytes[2]
    print(f"命令码: 0x{cmd:02X}")
    
    # 解析数据长度
    data_len = struct.unpack('<H', packet_bytes[3:5])[0]
    print(f"数据长度: {data_len} 字节")
    
    # 解析数据内容
    data = packet_bytes[5:5+data_len]
    print(f"数据内容字节数: {len(data)}")
    
    # 解析校验和
    checksum = packet_bytes[5+data_len]
    print(f"校验和: 0x{checksum:02X}")
    
    # 计算校验和
    calculated_checksum = calculate_checksum(cmd, data_len, data)
    print(f"计算的校验和: 0x{calculated_checksum:02X}")
    
    # 验证校验和
    if checksum != calculated_checksum:
        print("❌ 校验和错误")
        return False
    print("✅ 校验和正确")
    
    # 验证数据长度
    if len(data) != data_len:
        print("❌ 数据长度不匹配")
        return False
    
    # 验证命令码是否为数据上传命令
    if cmd != CMD_DATA_UPLOAD:
        print(f"⚠️ 命令码不是数据上传命令 (0x01)，而是 0x{cmd:02X}")
    
    return True

def parse_sensor_data(data):
    """解析传感器数据"""
    if len(data) != 47:
        print(f"数据长度错误，应为 47 字节，实际为 {len(data)} 字节")
        return None
    
    try:
        sensor_data = struct.unpack('<BhhhhhhhhhhhIIdd', data)
        return {
            'packet_order': sensor_data[0],
            'accel_x': sensor_data[1],
            'accel_y': sensor_data[2],
            'accel_z': sensor_data[3],
            'gyro_x': sensor_data[4],
            'gyro_y': sensor_data[5],
            'gyro_z': sensor_data[6],
            'angle_x': sensor_data[7],
            'angle_y': sensor_data[8],
            'angle_z': sensor_data[9],
            'attitude1': sensor_data[10],
            'attitude2': sensor_data[11],
            'pressure': sensor_data[12],
            'altitude': sensor_data[13],
            'longitude': sensor_data[14],
            'latitude': sensor_data[15]
        }
    except Exception as e:
        print(f"解析传感器数据失败: {e}")
        return None

if __name__ == "__main__":
    # 用户提供的数据包
    user_packet = "AA 55 01 2F 00 0E A5 FF 00 00 1B 00 F5 FF 0A 00 F5 FF F5 FF 0A 00 F5 FF 07 00 9A 01 54 8D 01 00 BC 06 02 C2 A4 70 3D 0A D7 03 5A 40 29 5C 8F C2 F5 A8 3E 40 69 55 AA"
    
    print("=" * 50)
    print("数据包验证")
    print("=" * 50)
    
    # 验证数据包
    if verify_packet(user_packet):
        print("\n✅ 数据包符合组包逻辑")
        
        # 解析并打印传感器数据
        packet_bytes = bytes.fromhex(user_packet.replace(' ', ''))
        data_len = struct.unpack('<H', packet_bytes[3:5])[0]
        data = packet_bytes[5:5+data_len]
        sensor_data = parse_sensor_data(data)
        
        if sensor_data:
            print("\n传感器数据:")
            print(f"  包序: {sensor_data['packet_order']}")
            print(f"  加速度: X={sensor_data['accel_x']}mg, Y={sensor_data['accel_y']}mg, Z={sensor_data['accel_z']}mg")
            print(f"  角速度: X={sensor_data['gyro_x']}°/s, Y={sensor_data['gyro_y']}°/s, Z={sensor_data['gyro_z']}°/s")
            print(f"  角度: X={sensor_data['angle_x']}°, Y={sensor_data['angle_y']}°, Z={sensor_data['angle_z']}°")
            print(f"  姿态角: A1={sensor_data['attitude1']}°, A2={sensor_data['attitude2']}°")
            print(f"  气压: {sensor_data['pressure']} Pa")
            print(f"  高度: {sensor_data['altitude']} cm")
            print(f"  经纬度: {sensor_data['longitude']:.6f}, {sensor_data['latitude']:.6f}")
    else:
        print("\n❌ 数据包不符合组包逻辑")
