#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试用户提供的数据包是否符合 main.py 中的解析代码
"""

import struct

# 用户提供的数据包
PACKET_STR = "AA55012700000100F7FFFEFF010000000000FEFFFCFF00005B3A0100000000000000F03F0000000000000040C255AA"

# 帧格式常量
FRAME_HEADER = b'\xAA\x55'
FRAME_TAIL = b'\x55\xAA'

def hex_str_to_bytes(hex_str):
    """将十六进制字符串转换为字节数组"""
    if len(hex_str) % 2 != 0:
        raise ValueError("十六进制字符串长度必须是偶数")
    
    bytes_data = bytearray()
    for i in range(0, len(hex_str), 2):
        byte_str = hex_str[i:i+2]
        bytes_data.append(int(byte_str, 16))
    
    return bytes(bytes_data)

def calculate_checksum(cmd, data_len, data):
    """计算校验和（异或校验）"""
    checksum = cmd
    checksum ^= (data_len >> 8) & 0xFF
    checksum ^= data_len & 0xFF
    for byte in data:
        checksum ^= byte
    return checksum

def parse_sensor_data(data):
    """解析传感器数据上传帧（复制自 main.py）"""
    sensor_data_list = []
    sample_length = 47  # 每个样本固定长度，<BhhhhhhhhhhIIdd 格式对应的字节数：1+22+4+4+16=47

    if len(data) % sample_length != 0:
        print("传感器数据长度不正确")
        return sensor_data_list

    # 获取当前时间戳（同一包数据使用相同的时间戳）
    timestamp = 1234567890
    
    sample_count = len(data) // sample_length
    for i in range(sample_count):
        sample_data = data[i * sample_length:(i + 1) * sample_length]
        try:
            sensor_data = {
                'packet_order': struct.unpack('<B', sample_data[0:1])[0],
                'accel_x': struct.unpack('<h', sample_data[1:3])[0],
                'accel_y': struct.unpack('<h', sample_data[3:5])[0],
                'accel_z': struct.unpack('<h', sample_data[5:7])[0],
                'gyro_x': struct.unpack('<h', sample_data[7:9])[0],
                'gyro_y': struct.unpack('<h', sample_data[9:11])[0],
                'gyro_z': struct.unpack('<h', sample_data[11:13])[0],
                'angle_x': struct.unpack('<h', sample_data[13:15])[0],
                'angle_y': struct.unpack('<h', sample_data[15:17])[0],
                'angle_z': struct.unpack('<h', sample_data[17:19])[0],
                'attitude1': struct.unpack('<h', sample_data[19:21])[0],
                'attitude2': struct.unpack('<h', sample_data[21:23])[0],
                'pressure': struct.unpack('<I', sample_data[23:27])[0],
                'altitude': struct.unpack('<I', sample_data[27:31])[0],
                'longitude': struct.unpack('<d', sample_data[31:39])[0],
                'latitude': struct.unpack('<d', sample_data[39:47])[0],
                'timestamp': timestamp  # 添加时间戳字段
            }
            sensor_data_list.append(sensor_data)
        except Exception as e:
            print(f"解析传感器数据失败: {e}")

    return sensor_data_list

def main():
    """主函数"""
    print("=" * 50)
    print("数据包测试程序")
    print("=" * 50)

    try:
        # 将十六进制字符串转换为字节数组
        packet_bytes = hex_str_to_bytes(PACKET_STR)
        print(f"数据包长度: {len(packet_bytes)} 字节")
        print(f"数据包内容: {PACKET_STR}")
        print("-" * 50)

        # 验证帧头和帧尾
        if packet_bytes[:2] != FRAME_HEADER or packet_bytes[-2:] != FRAME_TAIL:
            print("❌ 帧头或帧尾不正确")
            return

        print("✓ 帧头和帧尾验证通过")

        # 解析命令码和数据长度
        cmd = struct.unpack('B', packet_bytes[2:3])[0]
        data_len = struct.unpack('H', packet_bytes[3:5])[0]

        print(f"命令码: 0x{cmd:02X}")
        print(f"数据长度: {data_len} 字节")

        # 验证数据长度
        if data_len != len(packet_bytes[5:-3]):
            print("❌ 数据长度不正确")
            return

        print("✓ 数据长度验证通过")

        # 验证校验和
        checksum = struct.unpack('B', packet_bytes[5 + data_len:6 + data_len])[0]
        calculated_checksum = calculate_checksum(cmd, data_len, packet_bytes[5:-3])
        if checksum != calculated_checksum:
            print(f"❌ 校验和不正确 - 实际值: 0x{checksum:02X}, 计算值: 0x{calculated_checksum:02X}")
            return

        print("✓ 校验和验证通过")
        print("-" * 50)

        # 根据命令码处理数据
        if cmd == 0x01:  # CMD_DATA_UPLOAD
            print("正在解析传感器数据...")
            sensor_data_list = parse_sensor_data(packet_bytes[5:-3])
            if sensor_data_list:
                print(f"解析到 {len(sensor_data_list)} 个传感器数据样本")
                print("-" * 50)
                # 打印传感器数据
                for i, sensor_data in enumerate(sensor_data_list):
                    print(f"样本 {i+1}:")
                    print(f"  包序: {sensor_data['packet_order']}")
                    print(f"  加速度: X={sensor_data['accel_x']}, Y={sensor_data['accel_y']}, Z={sensor_data['accel_z']}")
                    print(f"  角速度: X={sensor_data['gyro_x']}, Y={sensor_data['gyro_y']}, Z={sensor_data['gyro_z']}")
                    print(f"  角度: X={sensor_data['angle_x']}, Y={sensor_data['angle_y']}, Z={sensor_data['angle_z']}")
                    print(f"  气压: {sensor_data['pressure']}")
                    print(f"  经度: {sensor_data['longitude']:.6f}")
                    print(f"  纬度: {sensor_data['latitude']:.6f}")
                    print()
            else:
                print("❌ 未解析到传感器数据")
        else:
            print(f"命令码 0x{cmd:02X} 不是数据上传命令")

        print("=" * 50)
        print("数据包测试完成")

    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()
