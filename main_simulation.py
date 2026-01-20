#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - 模拟版本
用于在标准 Python 环境中测试程序功能
功能：
- 模拟串口通信与STM32交互
- 解析传感器数据帧
- 模拟MQTT通信上传数据到云端
- 心跳包处理
- 配置管理
- 看门狗功能，增强程序鲁棒性
"""

import struct
import time
import json
import threading
import random

# =============================================================================
# 配置参数
# =============================================================================
SERIAL_PORT = "COM5"  # 串口设备，使用标准串口
BAUD_RATE = 115200  # 波特率
MQTT_BROKER = "120.27.250.30"  # MQTT服务器地址，与dc_main一致
MQTT_PORT = 1883  # MQTT端口，与dc_main一致
MQTT_USERNAME = ""  # MQTT用户名，与dc_main一致（不需要认证）
MQTT_PASSWORD = ""  # MQTT密码，与dc_main一致（不需要认证）
HEARTBEAT_INTERVAL = 60  # 心跳间隔（秒）
WATCHDOG_INTERVAL = 30  # 看门狗喂狗间隔（秒）
STM32_TIMEOUT_INTERVAL = 20  # STM32数据超时检测间隔（秒）
APP_VERSION = 1001  # 应用程序版本号，从1001开始编码

# 设备IMEI号，用于确保MQTT客户端唯一性
IMEI = "default_imei_123456789012345"  # 模拟值

# =============================================================================
# 命令码定义（明确区分上行和下行）
# =============================================================================
# 上行命令（STM32 → 4G → 云端）
CMD_UP_DATA_UPLOAD = 0x01      # 传感器数据上传
CMD_UP_CONFIG_REPLY = 0x03     # 配置参数回复
CMD_UP_HEARTBEAT = 0x04        # 心跳包
CMD_UP_RESET_REPLY = 0x07      # 复位命令回复

# 下行命令（云端 → 4G → STM32）
CMD_DOWN_CONFIG_SET = 0x02     # 配置参数设置
CMD_DOWN_HEARTBEAT_REPLY = 0x05  # 心跳包回复
CMD_DOWN_RESET = 0x06          # 复位命令

# =============================================================================
# 帧格式常量
# =============================================================================
FRAME_HEADER = b'\xAA\x55'
FRAME_TAIL = b'\x55\xAA'


# =============================================================================
# STM32串口通信类
# 负责与STM32主控的串口通信，包括帧的打包、解包、校验和计算等
# =============================================================================
class STM32Communication:
    """STM32串口通信类 - 模拟版本"""
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.is_connected = False
        self.simulate_data = True

    def connect(self):
        """连接串口"""
        try:
            # 模拟串口连接
            self.is_connected = True
            print("串口连接成功")
            return True
        except Exception as e:
            print(f"串口连接失败: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """断开串口连接"""
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

    def unpack_frame(self, frame):
        """解包数据帧"""
        try:
            # 验证帧头和帧尾
            if frame[:2] != FRAME_HEADER or frame[-2:] != FRAME_TAIL:
                return None, None, None

            # 解析命令码和数据长度
            cmd = struct.unpack('B', frame[2:3])[0]
            data_len = struct.unpack('H', frame[3:5])[0]

            # 验证数据长度
            if data_len != len(frame[5:-3]):
                return None, None, None

            # 验证校验和
            checksum = struct.unpack('B', frame[5 + data_len:6 + data_len])[0]
            calculated_checksum = self.calculate_checksum(cmd, data_len, frame[5:-3])
            if checksum != calculated_checksum:
                return None, None, None

            # 返回命令码和数据域
            return cmd, data_len, frame[5:-3]
        except Exception as e:
            print(f"帧解析失败: {e}")
            return None, None, None

    def read_frame(self):
        """读取完整数据帧"""
        if not self.is_connected:
            return None, None, None

        # 模拟读取帧
        if self.simulate_data and random.random() < 0.3:
            # 随机返回不同类型的帧
            cmd_type = random.randint(0, 3)
            if cmd_type == 0:
                return self._simulate_sensor_data_frame()
            elif cmd_type == 1:
                return self._simulate_heartbeat_frame()
            elif cmd_type == 2:
                return self._simulate_config_reply_frame()
            elif cmd_type == 3:
                return self._simulate_reset_reply_frame()

        return None, None, None

    def _simulate_sensor_data_frame(self):
        """模拟传感器数据帧"""
        cmd = CMD_UP_DATA_UPLOAD
        # 根据协议文档创建一个43字节的模拟数据
        data = bytearray(43)
        # 填充一些随机值
        for i in range(43):
            data[i] = random.randint(0, 255)
        data = bytes(data)
        return cmd, len(data), data

    def _simulate_heartbeat_frame(self):
        """模拟心跳帧"""
        cmd = CMD_UP_HEARTBEAT
        data = struct.pack('B', 0x00)
        return cmd, len(data), data

    def _simulate_config_reply_frame(self):
        """模拟配置回复帧"""
        cmd = CMD_UP_CONFIG_REPLY
        data = struct.pack('HHB', 100, 200, 1)
        return cmd, len(data), data

    def _simulate_reset_reply_frame(self):
        """模拟复位回复帧"""
        cmd = CMD_UP_RESET_REPLY
        data = struct.pack('B', 0x01)
        return cmd, len(data), data

    def send_frame(self, cmd, data=b''):
        """发送数据帧"""
        if not self.is_connected:
            return False

        # 模拟发送帧
        print(f"模拟发送帧: 命令码={cmd}, 数据长度={len(data)}")
        return True

    def parse_sensor_data(self, data):
        """解析传感器数据上传帧"""
        sensor_data_list = []
        sample_length = 43  # 每个样本固定长度

        if len(data) % sample_length != 0:
            print("传感器数据长度不正确")
            return sensor_data_list

        # 获取当前时间戳（同一包数据使用相同的时间戳）
        timestamp = time.time()
        
        sample_count = len(data) // sample_length
        for i in range(sample_count):
            sample_data = data[i * sample_length:(i + 1) * sample_length]
            try:
                sensor_data = {
                    'packet_order': struct.unpack('B', sample_data[0:1])[0],
                    'accel_x': struct.unpack('h', sample_data[1:3])[0],
                    'accel_y': struct.unpack('h', sample_data[3:5])[0],
                    'accel_z': struct.unpack('h', sample_data[5:7])[0],
                    'gyro_x': struct.unpack('h', sample_data[7:9])[0],
                    'gyro_y': struct.unpack('h', sample_data[9:11])[0],
                    'gyro_z': struct.unpack('h', sample_data[11:13])[0],
                    'angle_x': struct.unpack('h', sample_data[13:15])[0],
                    'angle_y': struct.unpack('h', sample_data[15:17])[0],
                    'angle_z': struct.unpack('h', sample_data[17:19])[0],
                    'pressure': struct.unpack('I', sample_data[19:23])[0],
                    'longitude': struct.unpack('d', sample_data[23:31])[0],
                    'latitude': struct.unpack('d', sample_data[31:39])[0],
                    'timestamp': timestamp  # 添加时间戳字段
                }
                sensor_data_list.append(sensor_data)
            except Exception as e:
                print(f"解析传感器数据失败: {e}")

        return sensor_data_list

    def parse_config_data(self, data):
        """解析配置参数数据"""
        try:
            config = {
                'sample_interval': struct.unpack('H', data[0:2])[0],
                'upload_interval': struct.unpack('H', data[2:4])[0],
                'data_format': struct.unpack('B', data[4:5])[0]
            }
            return config
        except Exception as e:
            print(f"解析配置参数失败: {e}")
            return None

    def parse_heartbeat_data(self, data):
        """解析心跳包数据"""
        try:
            status = struct.unpack('B', data[0:1])[0]
            return status
        except Exception as e:
            print(f"解析心跳包失败: {e}")
            return None

    def parse_reset_data(self, data):
        """解析复位命令数据"""
        try:
            reset_type = struct.unpack('B', data[0:1])[0]
            return reset_type
        except Exception as e:
            print(f"解析复位命令失败: {e}")
            return None


# =============================================================================
# MQTT客户端类
# 负责与云端MQTT服务器的连接、数据发布和订阅功能
# =============================================================================
class MQTTClient:
    """MQTT客户端类 - 模拟版本"""
    def __init__(self, broker, port, username, password, imei):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.imei = imei
        self.topic_up = "up/{}".format(imei)  # 上行数据主题，包含IMEI
        self.topic_down = "down/{}".format(imei)  # 下行控制主题，包含IMEI
        self.is_connected = False

    def connect(self):
        """连接MQTT服务器"""
        try:
            # 模拟MQTT连接
            self.is_connected = True
            print("MQTT连接成功")
            return True
        except Exception as e:
            print(f"MQTT连接失败: {e}")
            self.is_connected = False
            return False

    def on_message(self, topic, msg):
        """下行消息接收回调"""
        print(f"收到下行控制消息: {topic.decode('utf-8')} -> {msg.decode('utf-8')}")

    def publish_up_sensor_data(self, sensor_data_list):
        """发布上行传感器数据到云端"""
        if not self.is_connected:
            return False

        try:
            # 为每个传感器数据添加版本字段
            data_with_version = []
            for sensor_data in sensor_data_list:
                sensor_data['version'] = APP_VERSION
                data_with_version.append(sensor_data)
                
            payload = json.dumps(data_with_version)
            print(f"已发布上行传感器数据，共 {len(data_with_version)} 个样本，主题: {self.topic_up}")
            print(f"数据内容: {payload}")
            return True
        except Exception as e:
            print(f"发布上行传感器数据失败: {e}")
            return False

    def publish_up_heartbeat(self, status):
        """发布上行心跳包到云端"""
        if not self.is_connected:
            return False

        try:
            payload = json.dumps({'status': status, 'version': APP_VERSION})
            print(f"已发布上行心跳包，状态: {status}，主题: {self.topic_up}")
            print(f"数据内容: {payload}")
            return True
        except Exception as e:
            print(f"发布上行心跳包失败: {e}")
            return False

    def publish_up_config_reply(self, config):
        """发布上行配置参数回复到云端"""
        if not self.is_connected:
            return False

        try:
            config_with_version = config.copy()
            config_with_version['version'] = APP_VERSION
            payload = json.dumps(config_with_version)
            print(f"已发布上行配置参数回复，配置: {config_with_version}，主题: {self.topic_up}")
            print(f"数据内容: {payload}")
            return True
        except Exception as e:
            print(f"发布上行配置参数回复失败: {e}")
            return False

    def publish_up_reset_reply(self, reset_status):
        """发布上行复位命令回复到云端"""
        if not self.is_connected:
            return False

        try:
            payload = json.dumps({'reset_status': reset_status, 'version': APP_VERSION})
            print(f"已发布上行复位命令回复，状态: {reset_status}，主题: {self.topic_up}")
            print(f"数据内容: {payload}")
            return True
        except Exception as e:
            print(f"发布上行复位命令回复失败: {e}")
            return False
            
    def publish_up_exception_event(self, event_type, description):
        """发布上行异常事件到云端"""
        if not self.is_connected:
            return False

        try:
            payload = json.dumps({
                'event_type': event_type,
                'description': description,
                'timestamp': time.time(),
                'version': APP_VERSION
            })
            print(f"已发布上行异常事件，类型: {event_type}，描述: {description}，主题: {self.topic_up}")
            print(f"数据内容: {payload}")
            return True
        except Exception as e:
            print(f"发布上行异常事件失败: {e}")
            return False
 
    def disconnect(self):
        """断开MQTT连接"""
        self.is_connected = False
        print("MQTT连接已断开")


# =============================================================================
# 看门狗类
# 负责监控程序运行状态，在规定时间内未喂狗则重启程序
# =============================================================================
class Watchdog:
    """程序看门狗类 - 模拟版本"""
    def __init__(self, timeout, callback):
        self.timeout = timeout
        self.callback = callback
        self.timer = None
        self.is_alive = False

    def start(self):
        """启动看门狗"""
        self.is_alive = True
        self._schedule_timer()
        print("看门狗已启动")

    def stop(self):
        """停止看门狗"""
        self.is_alive = False
        if self.timer:
            self.timer.cancel()
            self.timer = None
        print("看门狗已停止")

    def feed(self):
        """喂狗"""
        if self.is_alive:
            self._schedule_timer()
            print("看门狗已喂狗")

    def _schedule_timer(self):
        """调度定时器"""
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.timeout, self._on_timeout)
        self.timer.start()

    def _on_timeout(self):
        """超时回调"""
        print("看门狗超时，程序将重启")
        self.callback()


# =============================================================================
# 主函数
# 程序入口，负责初始化各种组件并启动主循环
# =============================================================================
def main():
    """主函数 - 模拟版本"""
    # 记录程序启动时间
    start_time = time.time()
    # 记录最后一次收到STM32数据的时间
    last_stm32_data_time = time.time()
    # 标记是否已上报过超时异常
    timeout_event_reported = False

    def restart_program():
        """重启程序"""
        print("正在重启程序...")
        # 模拟重启
        time.sleep(2)
        print("程序已重启")

    # 初始化看门狗
    watchdog = Watchdog(WATCHDOG_INTERVAL, restart_program)
    watchdog.start()

    # 初始化STM32通信
    stm32 = STM32Communication(SERIAL_PORT, BAUD_RATE)
    if not stm32.connect():
        print("无法连接到STM32，程序退出")
        watchdog.stop()
        return

    # 初始化MQTT客户端
    mqtt_client = MQTTClient(
        MQTT_BROKER,
        MQTT_PORT,
        MQTT_USERNAME,
        MQTT_PASSWORD,
        IMEI
    )
    if not mqtt_client.connect():
        print("无法连接到MQTT服务器，程序退出")
        stm32.disconnect()
        watchdog.stop()
        return

    # 心跳定时器
    heartbeat_timer = None

    def heartbeat_task():
        """心跳任务"""
        while True:
            if stm32.is_connected:
                # 发送心跳包（下行）
                stm32.send_frame(CMD_DOWN_HEARTBEAT_REPLY, b'\x00')
                print("已发送心跳包回复（下行）")
            time.sleep(HEARTBEAT_INTERVAL)

    # 启动心跳任务
    threading.Thread(target=heartbeat_task, daemon=True).start()

    try:
        while True:
            # 读取STM32发送的数据帧（上行）
            cmd, data_len, data = stm32.read_frame()

            if cmd is not None:
                print("收到命令码: 0x{:02X}, 数据长度: {}".format(cmd, data_len))
                # 更新最后一次收到STM32数据的时间
                last_stm32_data_time = time.time()
                # 重置超时事件上报标记
                timeout_event_reported = False

                # 根据命令码处理数据
                if cmd == CMD_UP_DATA_UPLOAD:
                    # 解析STM32上传的传感器数据（上行）
                    sensor_data_list = stm32.parse_sensor_data(data)
                    if sensor_data_list:
                        # 发送到MQTT服务器（上行）
                        mqtt_client.publish_up_sensor_data(sensor_data_list)
                    # 喂狗
                    watchdog.feed()
                elif cmd == CMD_UP_CONFIG_REPLY:
                    # 解析STM32回复的配置参数（上行）
                    config = stm32.parse_config_data(data)
                    if config:
                        print("收到STM32配置参数回复: {}".format(config))
                        mqtt_client.publish_up_config_reply(config)
                    # 喂狗
                    watchdog.feed()
                elif cmd == CMD_UP_HEARTBEAT:
                    # 解析STM32发送的心跳包（上行）并回复（下行）
                    status = stm32.parse_heartbeat_data(data)
                    if status is not None:
                        print("收到STM32心跳包，状态: {}".format(status))
                        stm32.send_frame(CMD_DOWN_HEARTBEAT_REPLY, struct.pack('B', status))
                        mqtt_client.publish_up_heartbeat(status)
                    # 喂狗
                    watchdog.feed()
                elif cmd == CMD_UP_RESET_REPLY:
                    # 解析STM32回复的复位命令（上行）
                    reset_status = stm32.parse_reset_data(data)
                    if reset_status is not None:
                        print("收到STM32复位命令回复，状态: {}".format(reset_status))
                        mqtt_client.publish_up_reset_reply(reset_status)
                    # 喂狗
                    watchdog.feed()
                else:
                    print("未知命令码: 0x{:02X}".format(cmd))
                    # 喂狗
                    watchdog.feed()

            # 检测STM32数据超时
            if time.time() - last_stm32_data_time > STM32_TIMEOUT_INTERVAL:
                if not timeout_event_reported:
                    print("STM32数据超时，上报异常事件")
                    mqtt_client.publish_up_exception_event(
                        event_type="STM32_COMMUNICATION_TIMEOUT",
                        description="超过{}秒未收到STM32数据".format(STM32_TIMEOUT_INTERVAL)
                    )
                    timeout_event_reported = True
                # 即使超时也要喂狗，防止程序重启
                watchdog.feed()

            # 定期喂狗（防止长时间没有数据导致超时）
            if time.time() - start_time > WATCHDOG_INTERVAL / 2:
                watchdog.feed()
                start_time = time.time()

            # 短暂休眠，避免CPU占用过高
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("程序被用户中断")
    except Exception as e:
        print("程序异常: {}".format(e))
    finally:
        # 清理资源
        stm32.disconnect()
        mqtt_client.disconnect()
        watchdog.stop()
        print("程序已退出")


if __name__ == "__main__":
    main()
