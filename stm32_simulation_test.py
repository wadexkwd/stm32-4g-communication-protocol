#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - STM32模拟器测试程序
功能：
- 电脑串口连接4G模块，模拟STM32发送传感器数据
- 生成10组模拟传感器数据并轮询发送
- 支持配置串口参数（COM5，115200波特率）
"""

import serial
import struct
import time
import random

# =============================================================================
# 配置参数
# =============================================================================
SERIAL_PORT = "COM5"  # 串口设备
BAUD_RATE = 115200  # 波特率
DATA_SEND_INTERVAL = 0.1  # 数据发送间隔（秒）
TEST_DATA_COUNT = 10  # 测试数据组数

# =============================================================================
# 命令码定义
# =============================================================================
CMD_DATA_UPLOAD = 0x01
CMD_CONFIG_SET = 0x02
CMD_CONFIG_REPLY = 0x03
CMD_HEARTBEAT = 0x04
CMD_HEARTBEAT_REPLY = 0x05
CMD_RESET = 0x06
CMD_RESET_REPLY = 0x07

# =============================================================================
# 帧格式常量
# =============================================================================
FRAME_HEADER = b'\xAA\x55'
FRAME_TAIL = b'\x55\xAA'


# =============================================================================
# STM32模拟器类
# 负责模拟STM32的行为，包括数据生成和发送
# =============================================================================
class STM32Simulator:
    """STM32模拟器类"""
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.is_connected = False
        self.packet_order = 0  # 包序计数器
        # 固定的传感器数据（除了包序）
        self.fixed_sensor_data = {
            'accel_x': -91,
            'accel_y': 0,
            'accel_z': 27,
            'gyro_x': -11,
            'gyro_y': 10,
            'gyro_z': -11,
            'angle_x': -11,
            'angle_y': 10,
            'angle_z': -11,
            'attitude1': 7,
            'attitude2': 410,
            'pressure': 101716,
            'altitude': 325.49,
            'longitude': 104.06,
            'latitude': 30.66
        }

    def connect(self):
        """连接串口"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.is_connected = True
            print("串口连接成功")
            return True
        except Exception as e:
            print(f"串口连接失败: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """断开串口连接"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.is_connected = False
            print("串口已断开")

    def calculate_checksum(self, cmd, data_len, data):
        """计算校验和（异或校验）"""
        checksum = cmd
        checksum ^= (data_len >> 8) & 0xFF
        checksum ^= data_len & 0xFF
        for byte in data:
            checksum ^= byte
        return checksum

    def pack_frame(self, cmd, data=b''):
        """打包数据帧"""
        data_len = len(data)
        checksum = self.calculate_checksum(cmd, data_len, data)
        frame = (
            FRAME_HEADER +
            struct.pack('B', cmd) +
            struct.pack('H', data_len) +
            data +
            struct.pack('B', checksum) +
            FRAME_TAIL
        )
        return frame

    def sensor_data_to_bytes(self, sensor_data):
        """将传感器数据转换为二进制格式"""
        # 按照协议格式打包数据，使用小端无对齐方式，字节长度为47字节 (<BhhhhhhhhhhhIfdd: 1+2*12+4+4+8+8=47字节)
        data = struct.pack(
            '<BhhhhhhhhhhhIfdd',
            sensor_data['packet_order'],
            sensor_data['accel_x'],
            sensor_data['accel_y'],
            sensor_data['accel_z'],
            sensor_data['gyro_x'],
            sensor_data['gyro_y'],
            sensor_data['gyro_z'],
            sensor_data['angle_x'],
            sensor_data['angle_y'],
            sensor_data['angle_z'],
            sensor_data['attitude1'],
            sensor_data['attitude2'],
            sensor_data['pressure'],
            sensor_data['altitude'],
            sensor_data['longitude'],
            sensor_data['latitude']
        )
        return data

    def send_frame(self):
        """发送数据帧，包序自增"""
        if not self.is_connected or not self.ser:
            return False

        try:
            # 生成当前包序的传感器数据
            sensor_data = self.fixed_sensor_data.copy()
            sensor_data['packet_order'] = self.packet_order % 256
            self.packet_order += 1

            # 转换为二进制数据
            sensor_bytes = self.sensor_data_to_bytes(sensor_data)

            # 打包成完整帧
            frame = self.pack_frame(CMD_DATA_UPLOAD, sensor_bytes)

            # 发送数据
            self.ser.write(frame)

            # 打印发送的字节内容（十六进制格式）
            hex_str = ' '.join(f'{byte:02X}' for byte in frame)
            print(f"发送字节: [{hex_str}]")

            # 打印传感器数据信息
            print(f"  包序: {sensor_data['packet_order']}")
            print(f"  加速度: X={sensor_data['accel_x']}mg, Y={sensor_data['accel_y']}mg, Z={sensor_data['accel_z']}mg")
            print(f"  角速度: X={sensor_data['gyro_x']}°/s, Y={sensor_data['gyro_y']}°/s, Z={sensor_data['gyro_z']}°/s")
            print(f"  角度: X={sensor_data['angle_x']}°, Y={sensor_data['angle_y']}°, Z={sensor_data['angle_z']}°")
            print(f"  姿态角: A1={sensor_data['attitude1']}°, A2={sensor_data['attitude2']}°")
            print(f"  气压: {sensor_data['pressure']} Pa")
            print(f"  高度: {sensor_data['altitude']} cm")
            print(f"  经纬度: {sensor_data['longitude']:.6f}, {sensor_data['latitude']:.6f}")

            return True
        except Exception as e:
            print(f"发送帧失败: {e}")
            return False
# =============================================================================
# 传感器数据生成器类
# 负责生成模拟的传感器数据
# =============================================================================
class SensorDataGenerator:
    """传感器数据生成器类"""
    def __init__(self):
        self.packet_order = 0

    def generate_sensor_data(self):
        """生成传感器数据样本"""
        # 包序
        packet_order = self.packet_order % 256
        self.packet_order += 1

        # 加速度数据（mg） - 范围-32768~32767
        accel_x = random.randint(-32768, 32767)
        accel_y = random.randint(-32768, 32767)
        accel_z = random.randint(-32768, 32767)  # 重力加速度

        # 角速度数据（°/s） - 范围-32768~32767
        gyro_x = random.randint(-32768, 32767)
        gyro_y = random.randint(-32768, 32767)
        gyro_z = random.randint(-32768, 32767)

        # 角度数据（°） - 范围-32768~32767
        angle_x = random.randint(-32768, 32767)
        angle_y = random.randint(-32768, 32767)
        angle_z = random.randint(-32768, 32767)

        # 姿态数据（°） - 范围-32768~32767
        attitude1 = random.randint(-32768, 32767)
        attitude2 = random.randint(-32768, 32767)

        # 气压数据（Pa） - 范围0~4294967295
        pressure = random.randint(0, 4294967295)

        # 海拔数据（米） - 范围-1000~10000米，精度0.01米
        altitude = random.uniform(-1000, 10000)

        # 经度和纬度数据
        longitude = random.uniform(-180, 180)
        latitude = random.uniform(-90, 90)

        return {
            'packet_order': packet_order,
            'accel_x': accel_x,
            'accel_y': accel_y,
            'accel_z': accel_z,
            'gyro_x': gyro_x,
            'gyro_y': gyro_y,
            'gyro_z': gyro_z,
            'angle_x': angle_x,
            'angle_y': angle_y,
            'angle_z': angle_z,
            'attitude1': attitude1,
            'attitude2': attitude2,
            'pressure': pressure,
            'altitude': altitude,
            'longitude': longitude,
            'latitude': latitude
        }

    def generate_multiple_samples(self, count):
        """生成多个传感器数据样本"""
        samples = []
        for _ in range(count):
            samples.append(self.generate_sensor_data())
        return samples

    def sensor_data_to_bytes(self, sensor_data):
        """将传感器数据转换为二进制格式"""
        # 按照协议格式打包数据，使用小端无对齐方式，字节长度为47字节 (<BhhhhhhhhhhhIfdd: 1+2*12+4+4+8+8=47字节)
        data = struct.pack(
            '<BhhhhhhhhhhhIfdd',
            sensor_data['packet_order'],
            sensor_data['accel_x'],
            sensor_data['accel_y'],
            sensor_data['accel_z'],
            sensor_data['gyro_x'],
            sensor_data['gyro_y'],
            sensor_data['gyro_z'],
            sensor_data['angle_x'],
            sensor_data['angle_y'],
            sensor_data['angle_z'],
            sensor_data['attitude1'],
            sensor_data['attitude2'],
            sensor_data['pressure'],
            sensor_data['altitude'],
            sensor_data['longitude'],
            sensor_data['latitude']
        )
        print(f"打包后的字节长度: {len(data)} 字节")
        hex_str = ' '.join(f'{byte:02X}' for byte in data)
        print(f"打包后的字节内容: [{hex_str}]")
        return data

    def multiple_samples_to_bytes(self, sensor_data_list):
        """将多个传感器数据样本转换为二进制格式"""
        data = b''
        for sensor_data in sensor_data_list:
            data += self.sensor_data_to_bytes(sensor_data)
        return data


# =============================================================================
# 主函数
# 程序入口，负责初始化各种组件并启动主循环
# =============================================================================
def main():
    """主函数"""
    print("=" * 50)
    print("STM32模拟器测试程序")
    print("=" * 50)
    print(f"串口配置: {SERIAL_PORT} @ {BAUD_RATE} bps")
    print(f"发送间隔: {DATA_SEND_INTERVAL} 秒")
    print("发送固定数据包")
    print("=" * 50)

    # 初始化STM32模拟器
    stm32 = STM32Simulator(SERIAL_PORT, BAUD_RATE)
    if not stm32.connect():
        print("无法连接到串口，程序退出")
        return

    try:
        # 轮询发送固定数据
        print(f"\n开始轮询发送固定数据包（按 Ctrl+C 停止）:")
        print("-" * 50)

        index = 0
        while True:
            group_index = index + 1

            print(f"发送数据包 {group_index}:")

            if stm32.send_frame():
                print(f"✓ 发送成功")
            else:
                print(f"✗ 发送失败")

            print("-" * 50)

            # 等待发送间隔
            time.sleep(DATA_SEND_INTERVAL)

            index += 1
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序异常: {e}")
    finally:
        # 清理资源
        stm32.disconnect()
        print("\n程序已退出")


if __name__ == "__main__":
    main()
