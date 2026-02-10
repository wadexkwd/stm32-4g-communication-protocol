#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - 4G模块QPython实现
基于移远EC800M-CN模块，使用QPython开发
功能：
- 串口通信与STM32交互
- 解析传感器数据帧
- MQTT通信上传数据到云端 
- 心跳包处理
- 配置管理
- 看门狗功能，增强程序鲁棒性
"""

from machine import UART, RTC
import ustruct as struct
import utime
from umqtt import MQTTClient
import ujson
import _thread
import modem
import net
import checkNet
import pm
import log
import sim
import dataCall

# 初始化 RTC
rtc = RTC()

# =============================================================================
# 配置参数
# =============================================================================
SERIAL_PORT = UART.UART2  # 串口设备，使用Quectel专用UART2
BAUD_RATE = 115200  # 波特率
MQTT_BROKER = "120.27.250.30"  # MQTT服务器地址，与dc_main一致
MQTT_PORT = 1883  # MQTT端口，与dc_main一致
MQTT_USERNAME = ""  # MQTT用户名，与dc_main一致（不需要认证）
MQTT_PASSWORD = ""  # MQTT密码，与dc_main一致（不需要认证）
HEARTBEAT_INTERVAL = 60  # 心跳间隔（秒）
WATCHDOG_INTERVAL = 30  # 看门狗喂狗间隔（秒）
STM32_TIMEOUT_INTERVAL = 600  # STM32数据超时检测间隔（秒）
APP_VERSION = 1001  # 应用程序版本号，从1001开始编码
UPLOAD_INTERVAL = 1  # 数据上传间隔（秒）

# 设备IMEI号，用于确保MQTT客户端唯一性
import modem
try:
    IMEI = modem.getDevImei()  # 获取设备IMEI号
except Exception as e:
    print("获取IMEI失败: %s" % e)
    IMEI = "123456789012345"  # 默认值

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
    """STM32串口通信类 - Quectel专用"""
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.is_connected = False

    def connect(self):
        """连接串口"""
        try:
            self.ser = UART(self.port, self.baudrate, 8, 0, 1, 0)
            self.is_connected = True
            print("串口连接成功")
            return True
        except Exception as e:
            print("串口连接失败: %s" % e)
            self.is_connected = False
            return False

    def disconnect(self):
        """断开串口连接"""
        if self.ser:
            self.ser = None
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
            print("帧解析失败: %s" % e)
            return None, None, None

    def read_frame(self):
        """读取完整数据帧 - 轻量级版本，降低资源消耗"""
        if not self.is_connected or not self.ser:
            return []

        try:
            if self.ser.any() == 0:
                return []
                
            # 读取少量数据，避免内存消耗过大
            raw_data = self.ser.read(128)  # 限制读取字节数
            
            frames = []
            buffer = raw_data
            while True:
                header_pos = buffer.find(FRAME_HEADER)
                if header_pos == -1:
                    break

                buffer = buffer[header_pos:]

                if len(buffer) < 8:
                    break

                data_len = struct.unpack('H', buffer[3:5])[0]
                total_frame_length = 2 + 1 + 2 + data_len + 1 + 2

                if len(buffer) < total_frame_length:
                    break

                if buffer[total_frame_length - 2:total_frame_length] == FRAME_TAIL:
                    frame = buffer[:total_frame_length]
                    cmd, data_len, data = self.unpack_frame(frame)
                    frames.append((cmd, data_len, data))
                    buffer = buffer[total_frame_length:]
                else:
                    buffer = buffer[1:]
                    
            return frames
                
        except Exception as e:
            return []

    def send_frame(self, cmd, data=b''):
        """发送数据帧"""
        if not self.is_connected or not self.ser:
            return False

        frame = self.pack_frame(cmd, data)
        try:
            self.ser.write(frame)
            return True
        except Exception as e:
            print("发送帧失败: %s" % e)
            return False

    def format_timestamp(self, timestamp=None):
        """将时间戳格式化为 yyyy-mm-dd hh:mm:ss 格式的字符串"""
        try:
            # 直接从 RTC 读取当前时间（更准确）
            rtc_time = rtc.datetime()
            return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                rtc_time[0], rtc_time[1], rtc_time[2], 
                rtc_time[4], rtc_time[5], rtc_time[6]
            )
        except Exception as e:
            print("时间格式化失败: %s" % e)
            return str(timestamp)

    def parse_sensor_data(self, data):
        """解析传感器数据上传帧 - 轻量级版本"""
        sensor_data_list = []
        sample_length = 47

        if len(data) % sample_length != 0:
            return sensor_data_list

        formatted_time = self.format_timestamp()
        
        sample_count = len(data) // sample_length
        for i in range(sample_count):
            sample_data = data[i * sample_length:(i + 1) * sample_length]
            try:
                sensor_data = struct.unpack('<BhhhhhhhhhhhIfdd', sample_data)
                # 确保经度和纬度保留足够的精度（至少8位小数）
                # 处理高度参数的精度问题
                altitude = sensor_data[13]
                # 确保高度值精确到2位小数
                formatted_altitude = float("{0:.2f}".format(altitude))
                
                parsed_data = {
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
                    'altitude': formatted_altitude,
                    'longitude': float("%.8f" % sensor_data[14]),
                    'latitude': float("%.8f" % sensor_data[15]),
                    'timestamp': formatted_time
                }
                sensor_data_list.append(parsed_data)
                
                # 打印调试信息 - 详细输出每一组解析的数据
                
                # print("=" * 60)
                # print("第 %d 组传感器数据解析成功:" % (i+1))
                # print("包序: %d" % parsed_data['packet_order'])
                # print("加速度 X: %d, Y: %d, Z: %d" % (parsed_data['accel_x'], parsed_data['accel_y'], parsed_data['accel_z']))
                # print("角速度 X: %d, Y: %d, Z: %d" % (parsed_data['gyro_x'], parsed_data['gyro_y'], parsed_data['gyro_z']))
                # print("角度 X: %d, Y: %d, Z: %d" % (parsed_data['angle_x'], parsed_data['angle_y'], parsed_data['angle_z']))
                # print("姿态角1: %d, 姿态角2: %d" % (parsed_data['attitude1'], parsed_data['attitude2']))
                # print("气压: %d" % parsed_data['pressure'])
                # print("高度: %.2f" % parsed_data['altitude'])
                # print("经度: %.8f" % parsed_data['longitude'])
                # print("纬度: %.8f" % parsed_data['latitude'])
                # print("时间戳: %s" % parsed_data['timestamp'])
                # print("=" * 60)
                
            except Exception as e:
                print("解析第 %d 组传感器数据失败: %s" % (i+1, e))
                import sys
                print("错误类型: %s" % type(e))
                print("错误信息: %s" % e)
                print("错误位置: %s" % sys.exc_info()[2])

        print("传感器数据解析完成，共成功解析 %d 组数据" % len(sensor_data_list))
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
            print("解析配置参数失败: %s" % e)
            return None

    def parse_heartbeat_data(self, data):
        """解析心跳包数据"""
        try:
            status = struct.unpack('B', data[0:1])[0]
            return status
        except Exception as e:
            print("解析心跳包失败: %s" % e)
            return None

    def parse_reset_data(self, data):
        """解析复位命令数据"""
        try:
            reset_type = struct.unpack('B', data[0:1])[0]
            return reset_type
        except Exception as e:
            print("解析复位命令失败: %s" % e)
            return None


# =============================================================================
# MQTT客户端类
# 负责与云端MQTT服务器的连接、数据发布和订阅功能
# =============================================================================
class MyMQTTClient:
    """MQTT客户端类 - Quectel专用（基于dc_main.py的稳定实现）"""
    def __init__(self, broker, port, username, password, imei):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.imei = imei
        self.topic_up = "up/{}".format(imei)  # 上行数据主题，包含IMEI
        self.topic_down = "down/{}".format(imei)  # 下行控制主题，包含IMEI
        self.client = None
        self.is_connected = False
        self.reconnect_interval = 5  # 重连间隔（秒）
        self.max_reconnect_attempts = 0  # 0表示无限重试
        self.reconnect_attempts = 0
        self.last_connection_check = utime.time()
        self.connection_check_interval = 30  # 连接状态检查间隔（秒）
        self.__nw_flag = True  # 网络状态标志
        self.mp_lock = _thread.allocate_lock()  # 创建互斥锁

    def _cleanup_connection(self):
        """清理旧的MQTT连接"""
        if self.client:
            try:
                self.client.close()  # 使用close释放socket资源，而不是disconnect
            except Exception as e:
                print("清理旧连接时出错: %s" % e)
            finally:
                self.client = None
                self.is_connected = False

    def connect(self):
        """连接MQTT服务器"""
        # 先清理旧连接
        self._cleanup_connection()
        
        try:
            # 禁用umqtt内部重连机制，使用自定义重连逻辑
            self.client = MQTTClient(self.imei, self.broker, self.port, self.username, self.password,keepalive=0, reconn=False)
            self.client.connect(clean_session=True)
            self.client.set_callback(self.on_message)
            self.client.subscribe(self.topic_down.encode('utf-8'))
            print("MQTT连接成功")
            self.is_connected = True
            self.reconnect_attempts = 0  # 重置重连次数
            self.last_connection_check = utime.time()
            # 注册网络状态回调
            dataCall.setCallback(self.nw_cb)
            return True
        except Exception as e:
            print("MQTT连接失败: %s" % e)
            self._cleanup_connection()
            return False

    def nw_cb(self, args):
        """网络状态回调"""
        nw_sta = args[1]
        if nw_sta == 1:
            # 网络连接
            print("*** 网络连接成功！ ***")
            self.__nw_flag = True
        else:
            # 网络断线
            print("*** 网络连接断开！ ***")
            self.__nw_flag = False
            self.is_connected = False

    def _attempt_reconnect(self):
        """尝试重连MQTT服务器"""
        print("正在尝试重新连接MQTT服务器...")
        
        # 检查锁是否已经被获取
        if self.mp_lock.locked():
            return False
            
        self.mp_lock.acquire()
        
        # 重新连接前关闭之前的连接，释放资源
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                print("关闭旧连接失败: %s" % e)
        
        # 重置连接状态
        self.client = None
        self.is_connected = False
        
        # 等待一段时间再尝试重连
        utime.sleep(3)
        
        # 检查网络状态
        net_sta = net.getState()
        if net_sta != -1 and net_sta[1][0] == 1:
            call_state = dataCall.getInfo(1, 0)
            if (call_state != -1) and (call_state[2][0] == 1):
                try:
                    # 网络正常，重新连接mqtt
                    if self.connect():
                        # 重新连接成功，订阅主题
                        if self.topic_down is not None:
                            self.client.subscribe(self.topic_down.encode('utf-8'), qos=0)
                        self.mp_lock.release()
                        return True
                    else:
                        self.mp_lock.release()
                        utime.sleep(5)
                        return False
                except Exception as e:
                    print("重连MQTT失败: %s" % e)
                    self.mp_lock.release()
                    utime.sleep(5)
                    return False
            else:
                # 网络未恢复，等待恢复
                print("网络拨号未激活，等待恢复...")
                self.mp_lock.release()
                utime.sleep(10)
                return False
        else:
            # 网络未注册，等待恢复
            print("网络未注册，等待恢复...")
            self.mp_lock.release()
            utime.sleep(10)
            return False

    def check_connection(self):
        """检查MQTT连接状态"""
        current_time = utime.time()
        if current_time - self.last_connection_check >= self.connection_check_interval:
            self.last_connection_check = current_time
            
            # 尝试发送一个ping来检查连接
            if self.is_connected and self.client:
                try:
                    self.client.ping()
                    return True
                except Exception as e:
                    print("MQTT连接检查失败: %s" % e)
                    self.is_connected = False
                    return False
            else:
                return False

    def ensure_connected(self):
        """确保MQTT连接处于活动状态"""
        if not self.is_connected or not self.client:
            print("MQTT未连接，尝试重连...")
            return self._attempt_reconnect()
        else:
            return True

    def on_message(self, topic, msg):
        """下行消息接收回调"""
        print("收到下行控制消息: %s -> %s" % (topic.decode('utf-8'), msg.decode('utf-8')))
        # 这里可以添加对下行命令的处理逻辑
        try:
            payload = ujson.loads(msg.decode('utf-8'))
            # 根据消息内容处理不同的下行命令
            if 'config' in payload:
                print("收到配置参数设置命令")
            elif 'reset' in payload:
                print("收到复位命令")
        except Exception as e:
            print("解析下行消息失败: %s" % e)

    def publish_up_sensor_data(self, sensor_data_list):
        """发布上行传感器数据到云端"""
        if not self.ensure_connected():
            return False

        try:
            # 为每个传感器数据添加版本字段
            data_with_version = []
            for sensor_data in sensor_data_list:
                sensor_data['version'] = APP_VERSION
                data_with_version.append(sensor_data)
                
            payload = ujson.dumps({
                'event': 'SENSOR_DATA',
                'data': data_with_version,
                'version': APP_VERSION
            })
            self.client.publish(self.topic_up.encode('utf-8'), payload.encode('utf-8'), qos=0)
            print("已发布上行传感器数据，共 %d 个样本，主题: %s" % (len(data_with_version), self.topic_up))
            return True
        except Exception as e:
            print("发布上行传感器数据失败: %s" % e)
            self.is_connected = False
            # 尝试重连
            if self._attempt_reconnect():
                # 重连成功后再次尝试发布
                try:
                    payload = ujson.dumps({
                        'event': 'SENSOR_DATA',
                        'data': data_with_version,
                        'version': APP_VERSION
                    })
                    self.client.publish(self.topic_up.encode('utf-8'), payload.encode('utf-8'), qos=0)
                    print("重连后发布成功，共 %d 个样本，主题: %s" % (len(data_with_version), self.topic_up))
                    return True
                except Exception as e2:
                    print("重连后发布仍失败: %s" % e2)
                    self.is_connected = False
            return False

    def publish_up_heartbeat(self, status):
        """发布上行心跳包到云端"""
        if not self.ensure_connected():
            return False

        try:
            payload = ujson.dumps({'status': status, 'version': APP_VERSION, 'event': 'HEARTBEAT'})
            self.client.publish(self.topic_up.encode('utf-8'), payload.encode('utf-8'), qos=0)
            print("已发布上行心跳包，状态: %d，主题: %s" % (status, self.topic_up))
            return True
        except Exception as e:
            print("发布上行心跳包失败: %s" % e)
            self.is_connected = False
            # 尝试重连
            if self._attempt_reconnect():
                # 重连成功后再次尝试发布
                try:
                    payload = ujson.dumps({'status': status, 'version': APP_VERSION, 'event': 'HEARTBEAT'})
                    self.client.publish(self.topic_up.encode('utf-8'), payload.encode('utf-8'), qos=0)
                    print("重连后发布成功，状态: %d，主题: %s" % (status, self.topic_up))
                    return True
                except Exception as e2:
                    print("重连后发布仍失败: %s" % e2)
                    self.is_connected = False
            return False

    def publish_up_config_reply(self, config):
        """发布上行配置参数回复到云端"""
        if not self.ensure_connected():
            return False

        try:
            config_with_version = config.copy()
            config_with_version['version'] = APP_VERSION
            config_with_version['event'] = 'CONFIG_REPLY'
            payload = ujson.dumps(config_with_version)
            self.client.publish(self.topic_up.encode('utf-8'), payload.encode('utf-8'), qos=0)
            print("已发布上行配置参数回复，配置: %s，主题: %s" % (str(config_with_version), self.topic_up))
            return True
        except Exception as e:
            print("发布上行配置参数回复失败: %s" % e)
            self.is_connected = False
            # 尝试重连
            if self._attempt_reconnect():
                # 重连成功后再次尝试发布
                try:
                    config_with_version = config.copy()
                    config_with_version['version'] = APP_VERSION
                    config_with_version['event'] = 'CONFIG_REPLY'
                    payload = ujson.dumps(config_with_version)
                    self.client.publish(self.topic_up.encode('utf-8'), payload.encode('utf-8'), qos=0)
                    print("重连后发布成功，配置: %s，主题: %s" % (str(config_with_version), self.topic_up))
                    return True
                except Exception as e2:
                    print("重连后发布仍失败: %s" % e2)
                    self.is_connected = False
            return False

    def publish_up_reset_reply(self, reset_status):
        """发布上行复位命令回复到云端"""
        if not self.ensure_connected():
            return False

        try:
            payload = ujson.dumps({'reset_status': reset_status, 'version': APP_VERSION, 'event': 'RESET_REPLY'})
            self.client.publish(self.topic_up.encode('utf-8'), payload.encode('utf-8'), qos=0)
            print("已发布上行复位命令回复，状态: %d，主题: %s" % (reset_status, self.topic_up))
            return True
        except Exception as e:
            print("发布上行复位命令回复失败: %s" % e)
            self.is_connected = False
            # 尝试重连
            if self._attempt_reconnect():
                # 重连成功后再次尝试发布
                try:
                    payload = ujson.dumps({'reset_status': reset_status, 'version': APP_VERSION, 'event': 'RESET_REPLY'})
                    self.client.publish(self.topic_up.encode('utf-8'), payload.encode('utf-8'), qos=0)
                    print("重连后发布成功，状态: %d，主题: %s" % (reset_status, self.topic_up))
                    return True
                except Exception as e2:
                    print("重连后发布仍失败: %s" % e2)
                    self.is_connected = False
            return False
            
    def format_timestamp(self, timestamp=None):
        """将时间戳格式化为 yyyy-mm-dd hh:mm:ss 格式的字符串"""
        try:
            # 直接从 RTC 读取当前时间（更准确）
            rtc_time = rtc.datetime()
            return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                rtc_time[0], rtc_time[1], rtc_time[2], 
                rtc_time[4], rtc_time[5], rtc_time[6]
            )
        except Exception as e:
            print("时间格式化失败: %s" % e)
            return str(timestamp)

    def publish_up_exception_event(self, event_type, description):
        """发布上行异常事件到云端"""
        if not self.ensure_connected():
            return False

        try:
            payload = ujson.dumps({
                'event': event_type,
                'description': description,
                'timestamp': self.format_timestamp(utime.time()),
                'version': APP_VERSION
            })
            self.client.publish(self.topic_up.encode('utf-8'), payload.encode('utf-8'), qos=0)
            print("已发布上行异常事件，类型: %s，描述: %s，主题: %s" % (event_type, description, self.topic_up))
            return True
        except Exception as e:
            print("发布上行异常事件失败: %s" % e)
            self.is_connected = False
            # 尝试重连
            if self._attempt_reconnect():
                # 重连成功后再次尝试发布
                try:
                    payload = ujson.dumps({
                        'event': event_type,
                        'description': description,
                        'timestamp': self.format_timestamp(utime.time()),
                        'version': APP_VERSION
                    })
                    self.client.publish(self.topic_up.encode('utf-8'), payload.encode('utf-8'), qos=0)
                    print("重连后发布成功，类型: %s，描述: %s，主题: %s" % (event_type, description, self.topic_up))
                    return True
                except Exception as e2:
                    print("重连后发布仍失败: %s" % e2)
                    self.is_connected = False
            return False
            
    def publish_up_power_on_event(self):
        """发布上电事件到云端"""
        if not self.ensure_connected():
            return False

        try:
            payload = ujson.dumps({
                'event': 'POWER_ON',
                'timestamp': self.format_timestamp(utime.time()),
                'version': APP_VERSION,
                'imei': self.imei
            })
            self.client.publish(self.topic_up.encode('utf-8'), payload.encode('utf-8'), qos=0)
            print("已发布上电事件，主题: %s" % self.topic_up)
            return True
        except Exception as e:
            print("发布上电事件失败: %s" % e)
            self.is_connected = False
            # 尝试重连
            if self._attempt_reconnect():
                # 重连成功后再次尝试发布
                try:
                    payload = ujson.dumps({
                        'event': 'POWER_ON',
                        'timestamp': self.format_timestamp(utime.time()),
                        'version': APP_VERSION,
                        'imei': self.imei
                    })
                    self.client.publish(self.topic_up.encode('utf-8'), payload.encode('utf-8'), qos=0)
                    print("重连后发布成功，主题: %s" % self.topic_up)
                    return True
                except Exception as e2:
                    print("重连后发布仍失败: %s" % e2)
                    self.is_connected = False
            return False
 
    def disconnect(self):
        """断开MQTT连接"""
        self._cleanup_connection()
        print("MQTT连接已断开")

    def loop_forever(self):
        """启动MQTT消息监听线程"""
        def __listen():
            while True:
                try:
                    if not self.is_connected or self.client is None:
                        utime.sleep(1)
                        continue
                    self.client.wait_msg()
                except OSError as e:
                    print("MQTT监听异常: %s" % e)
                    # 任何OSError都直接触发重连
                    self._attempt_reconnect()
                    utime.sleep(1)
                except Exception as e:
                    print("MQTT监听线程异常: %s" % e)
                    self.is_connected = False
                    utime.sleep(1)

        _thread.start_new_thread(__listen, ())

    def check_connection(self):
        """检查MQTT连接状态"""
        current_time = utime.time()
        if current_time - self.last_connection_check >= self.connection_check_interval:
            self.last_connection_check = current_time
            
            # 尝试发送一个ping来检查连接
            if self.is_connected and self.client:
                try:
                    self.client.ping()
                    return True
                except Exception as e:
                    print("MQTT连接检查失败: %s" % e)
                    self.is_connected = False
                    return False
            else:
                return False
        return True


# =============================================================================
# 看门狗类
# 负责监控程序运行状态，在规定时间内未喂狗则重启程序
# =============================================================================
class Watchdog:
    """程序看门狗类 - Quectel专用"""
    def __init__(self, timeout, callback):
        self.timeout = timeout
        self.callback = callback
        self.timer = None
        self.is_alive = False
        self.last_feed_time = utime.time()

    def start(self):
        """启动看门狗"""
        self.is_alive = True
        self.last_feed_time = utime.time()
        self._schedule_timer()
        print("看门狗已启动")

    def stop(self):
        """停止看门狗"""
        self.is_alive = False
        # 由于使用 _thread 模块启动的线程无法直接取消，我们只需要设置标志位
        self.timer = None
        print("看门狗已停止")

    def feed(self):
        """喂狗"""
        if self.is_alive:
            self.last_feed_time = utime.time()
            

    def _schedule_timer(self):
        """调度定时器"""
        # 不需要取消之前的线程，因为它们会检查 is_alive 标志位
        self.timer = _thread.start_new_thread(self._timer_thread, ())

    def _timer_thread(self):
        while self.is_alive:
            # 检查距离上次喂狗的时间
            if utime.time() - self.last_feed_time > self.timeout:
                self._on_timeout()
                break
            utime.sleep(1)  # 每秒检查一次

    def _on_timeout(self):
        """超时回调"""
        print("看门狗超时，程序将重启")
        self.callback()


# =============================================================================
# 主函数
# 程序入口，负责初始化各种组件并启动主循环
# =============================================================================
def main():
    """主函数 - Quectel专用"""
    # 记录程序启动时间
    start_time = utime.time()
    # 记录最后一次收到STM32数据的时间
    last_stm32_data_time = utime.time()
    # 标记是否已上报过超时异常
    timeout_event_reported = False
    # 数据收集缓冲区（按包序存储）
    data_buffer = {}
    # 记录最后一次数据上传时间
    last_upload_time = utime.time()

    def restart_program():
        """重启程序"""
        print("正在重启程序...")
        from misc import Power
        Power.powerRestart()

    # 初始化看门狗
    watchdog = Watchdog(WATCHDOG_INTERVAL, restart_program)
    watchdog.start()

    # 上电附网过程状态打印
    print("=" * 50)
    print("应急跌落事件监控系统 - 启动中")
    print("=" * 50)
    
    # 检查SIM卡状态
    print("1 - 正在检测SIM卡状态...")
    sim_retry = 0
    SIM_RETRY_MAX = 30
    sim_ok = False
    while True:
        sim_retry += 1
        if sim_retry > SIM_RETRY_MAX:
            print("SIM卡检测超时！")
            break
        
        try:
            simnum = sim.getImsi()  # 获取SIM卡IMSI
            if simnum and '460' in str(simnum):
                print("SIM卡状态正常")
                print("IMSI:", simnum)
                sim_ok = True
                break
            else:
                print("SIM卡状态异常，重试中...")
        except Exception as e:
            print("获取SIM卡信息失败: %s" % e)
            
        utime.sleep(1)  # 等待1秒
    
    # 获取ICCID
    if sim_ok:
        try:
            iccid = sim.getIccid()
            if iccid and iccid != "":
                print("ICCID:", iccid)
            else:
                print("ICCID获取失败！")
        except Exception as e:
            print("获取ICCID失败: %s" % e)
    
    # 获取IMEI
    try:
        imei = modem.getDevImei()
        if imei and imei != "":
            print("IMEI:", imei)
        else:
            print("IMEI获取失败！")
    except Exception as e:
            print("获取IMEI失败: %s" % e)
    
    # 网络注册状态
    print("\n2 - 正在检测网络注册状态...")
    print("stagecode说明: 1-SIM卡检测; 2-网络注册; 3-PDP Context激活")
    print("subcode说明: stage=3时，1表示激活成功; stage=2时，1表示注册成功")
    
    netstatus = [0, 0]  # [SIM卡状态, 网络状态]
    if sim_ok:
        stagecode, subcode = checkNet.wait_network_connected(20)
        print("\r\nstagecode = %d, subcode = %d" % (stagecode, subcode))
        
        if stagecode == 3 and subcode == 1:
            print("网络连接正常，可以进行数据传输")
            netstatus[1] = 1
        else:
            print("网络连接失败")
            netstatus[1] = 0
        utime.sleep(1)
    
    # 网络信息打印
    print("\n3 - 网络状态信息:")
    try:
        print("网络状态:", net.getState())
        print("信号强度:", net.csqQueryPoll())
        print("运营商:", net.operatorName())
    except Exception as e:
            print("获取网络信息失败: %s" % e)
    
    # 从基站获取时间并更新 RTC（增加超时机制）
    print("\n4 - 正在从基站获取时间...")
    time_sync_success = False
    time_sync_timeout = 30  # 时间同步超时时间（秒）
    start_sync_time = utime.time()
    
    while utime.time() - start_sync_time < time_sync_timeout:
        try:
            nt_result = net.nitzTime()
            print("net.nitzTime() 返回值:", nt_result)  # 打印原始返回值，用于调试
            
            if isinstance(nt_result, tuple) and len(nt_result) > 0:
                time_str = nt_result[0]
                print("解析到的时间字符串:", repr(time_str))  # 打印原始时间字符串，用于调试
                
                if time_str.strip() != "":
                    date_str, time_str, tz_str, _ = time_str.split()
                    
                    year = int(date_str[0:2]) + 2000
                    month = int(date_str[3:5])
                    day = int(date_str[-2:])
                    
                    hour = int(time_str[0:2])
                    minute = int(time_str[3:5])
                    second = int(time_str[-2:])
                    
                    timezone_offset = int(tz_str)
                    hour += timezone_offset
                    
                    week = 0
                    microsecond = 0
                    
                    if year != 2000:
                        ret = rtc.datetime([year, month, day, week, hour, minute, second, microsecond])
                        if ret == 0:
                            # 打印获取到的时间
                            print("时间同步成功，获取到的时间: %04d-%02d-%02d %02d:%02d:%02d" % (year, month, day, hour, minute, second))
                            time_sync_success = True
                            break
                        else:
                            print("时间同步失败，重试中...")
                    else:
                        print("时间错误，重试中...")
                else:
                    print("时间字符串为空，重试中...")
            else:
                print("获取基站时间失败，重试中...")
                
            utime.sleep(2)  # 等待2秒后重试
        except Exception as e:
            print("获取时间失败: %s，重试中..." % e)
            utime.sleep(2)
    
    if not time_sync_success:
        print("时间同步超时（%d秒），使用默认时间" % time_sync_timeout)
        
    # 打印当前RTC时间，验证同步结果
    try:
        current_time = rtc.datetime()
        print("当前RTC时间: %04d-%02d-%02d %02d:%02d:%02d" % (
            current_time[0], current_time[1], current_time[2],
            current_time[4], current_time[5], current_time[6]
        ))
    except Exception as e:
        print("读取RTC时间失败: %s" % e)
    
    print("=" * 50)
    
    # 初始化STM32通信
    stm32 = STM32Communication(SERIAL_PORT, BAUD_RATE)
    if not stm32.connect():
        print("无法连接到STM32，程序退出")
        watchdog.stop()
        return

    # 初始化MQTT客户端（使用稳定实现）
    mqtt_client = MyMQTTClient(
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
    
    print("MQTT订阅主题: %s" % mqtt_client.topic_down)
    mqtt_client.publish_up_power_on_event()
    mqtt_client.loop_forever()  # 启动MQTT监听线程

    # 不再主动发送下行心跳包，仅在收到STM32的心跳包时回复
    try:
        while True:
            # 定期喂狗（防止长时间没有数据导致超时）
            if utime.time() - start_time > WATCHDOG_INTERVAL / 2:
                watchdog.feed()
                start_time = utime.time()

            # 读取STM32发送的数据帧（上行）
            frames = stm32.read_frame()

            for cmd, data_len, data in frames:
                # 更新最后一次收到STM32数据的时间
                last_stm32_data_time = utime.time()
                # 重置超时事件上报标记
                timeout_event_reported = False

                # 根据命令码处理数据
                if cmd == CMD_UP_DATA_UPLOAD:
                    # 解析STM32上传的传感器数据（上行）
                    sensor_data_list = stm32.parse_sensor_data(data)
                    if sensor_data_list:
                        # 将数据存入缓冲区（按包序存储）
                        for sensor_data in sensor_data_list:
                            packet_order = sensor_data['packet_order']
                            data_buffer[packet_order] = sensor_data
                    # 喂狗
                    watchdog.feed()
                elif cmd == CMD_UP_CONFIG_REPLY:
                    # 解析STM32回复的配置参数（上行）
                    config = stm32.parse_config_data(data)
                    if config:
                        mqtt_client.publish_up_config_reply(config)
                    # 喂狗
                    watchdog.feed()
                elif cmd == CMD_UP_HEARTBEAT:
                    # 解析STM32发送的心跳包（上行）并回复（下行）
                    status = stm32.parse_heartbeat_data(data)
                    if status is not None:
                        stm32.send_frame(CMD_DOWN_HEARTBEAT_REPLY, struct.pack('B', status))
                        mqtt_client.publish_up_heartbeat(status)
                    # 喂狗
                    watchdog.feed()
                elif cmd == CMD_UP_RESET_REPLY:
                    # 解析STM32回复的复位命令（上行）
                    reset_status = stm32.parse_reset_data(data)
                    if reset_status is not None:
                        mqtt_client.publish_up_reset_reply(reset_status)
                    # 喂狗
                    watchdog.feed()
                else:
                    # 喂狗
                    watchdog.feed()

            # 检查是否需要上传数据（减少频率）
            if utime.time() - last_upload_time >= UPLOAD_INTERVAL and data_buffer:
                sorted_packet_orders = sorted(data_buffer.keys())
                sorted_sensor_data = [data_buffer[order] for order in sorted_packet_orders]
                
                if mqtt_client.publish_up_sensor_data(sorted_sensor_data):
                    data_buffer.clear()
                
                last_upload_time = utime.time()
            
            # 定期检查MQTT连接状态
            mqtt_client.check_connection()
            # 检测STM32数据超时
            if utime.time() - last_stm32_data_time > STM32_TIMEOUT_INTERVAL:
                if not timeout_event_reported:
                    print("STM32数据超时，上报异常事件")
                    mqtt_client.publish_up_exception_event(
                        event_type="SENSOR_REPORT_TIMEOUT",
                        description="超过%d秒未收到STM32数据" % STM32_TIMEOUT_INTERVAL
                    )
                    timeout_event_reported = True
                # 即使超时也要喂狗，防止程序重启
                watchdog.feed()

            # 短暂休眠，提高响应速度
            utime.sleep_ms(10)

    except Exception as e:
        print("程序异常: %s" % e)
    finally:
        # 清理资源
        stm32.disconnect()
        mqtt_client.disconnect()
        watchdog.stop()
        print("程序已退出")


if __name__ == "__main__":
    main()
