#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - 电脑端模拟实现
功能：
- 模拟main.py的行为
- 启动时发送上电包到MQTT服务器
- 每1秒发送10个传感器数据包
"""

import time
import json
import random
from datetime import datetime
import paho.mqtt.client as mqtt

# =============================================================================
# 配置参数
# =============================================================================
MQTT_BROKER = "120.27.250.30"  # MQTT服务器地址
MQTT_PORT = 1883  # MQTT端口
MQTT_USERNAME = ""  # MQTT用户名
MQTT_PASSWORD = ""  # MQTT密码
APP_VERSION = 1001  # 应用程序版本号
UPLOAD_INTERVAL = 1  # 数据上传间隔（秒）
PACKET_COUNT_PER_UPLOAD = 10  # 每次上传的数据包数量

# 设备IMEI号
IMEI = "861197065268692"

# =============================================================================
# MQTT客户端类
# =============================================================================
class MyMQTTClient:
    """MQTT客户端类 - 电脑端模拟实现"""
    def __init__(self, broker, port, username, password, imei):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.imei = imei
        self.topic_up = f"up/{imei}"  # 上行数据主题，包含IMEI
        self.topic_down = f"down/{imei}"  # 下行控制主题，包含IMEI
        self.client = None
        self.is_connected = False

    def connect(self):
        """连接MQTT服务器"""
        try:
            self.client = mqtt.Client(client_id=self.imei)
            self.client.username_pw_set(self.username, self.password)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            print(f"正在连接MQTT服务器: {self.broker}:{self.port}")
            return True
        except Exception as e:
            print(f"MQTT连接失败: {e}")
            return False

    def on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            print("MQTT连接成功")
            self.is_connected = True
            # 订阅下行主题
            self.client.subscribe(self.topic_down)
            print(f"已订阅主题: {self.topic_down}")
        else:
            print(f"MQTT连接失败，错误码: {rc}")
            self.is_connected = False

    def on_message(self, client, userdata, msg):
        """下行消息接收回调"""
        print(f"收到下行控制消息: {msg.topic} -> {msg.payload.decode('utf-8')}")

    def publish_up_power_on_event(self):
        """发布上电事件到云端"""
        if not self.is_connected:
            print("MQTT未连接，无法发布上电事件")
            return False

        try:
            payload = json.dumps({
                'event': 'POWER_ON',
                'timestamp': self.format_timestamp(),
                'version': APP_VERSION,
                'imei': self.imei
            })
            self.client.publish(self.topic_up, payload.encode('utf-8'), qos=0)
            print(f"已发布上电事件，主题: {self.topic_up}")
            return True
        except Exception as e:
            print(f"发布上电事件失败: {e}")
            return False

    def publish_up_sensor_data(self, sensor_data_list):
        """发布上行传感器数据到云端"""
        if not self.is_connected:
            print("MQTT未连接，无法发布传感器数据")
            return False

        try:
            # 为每个传感器数据添加版本字段
            data_with_version = []
            for sensor_data in sensor_data_list:
                sensor_data['version'] = APP_VERSION
                data_with_version.append(sensor_data)
                
            payload = json.dumps({
                'event': 'SENSOR_DATA',
                'data': data_with_version,
                'version': APP_VERSION
            })
            self.client.publish(self.topic_up, payload.encode('utf-8'), qos=0)
            print(f"已发布上行传感器数据，共 {len(data_with_version)} 个样本，主题: {self.topic_up}")
            return True
        except Exception as e:
            print(f"发布上行传感器数据失败: {e}")
            return False

    def format_timestamp(self, timestamp=None):
        """将时间戳格式化为 yyyy-mm-dd hh:mm:ss 格式的字符串"""
        try:
            if timestamp is None:
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"时间格式化失败: {e}")
            return str(timestamp)

    def disconnect(self):
        """断开MQTT连接"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
            print("MQTT连接已断开")

# =============================================================================
# 模拟数据生成函数
# =============================================================================
def generate_sensor_data(packet_order, base_data):
    """生成模拟传感器数据"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 在基础数据上添加一些随机噪声
    sensor_data = {
        'packet_order': packet_order,
        'accel_x': base_data['accel_x'] + random.randint(-2, 2),
        'accel_y': base_data['accel_y'] + random.randint(-2, 2),
        'accel_z': base_data['accel_z'] + random.randint(-2, 2),
        'gyro_x': base_data['gyro_x'] + random.randint(-1, 1),
        'gyro_y': base_data['gyro_y'] + random.randint(-1, 1),
        'gyro_z': base_data['gyro_z'] + random.randint(-1, 1),
        'angle_x': base_data['angle_x'] + random.randint(-1, 1),
        'angle_y': base_data['angle_y'] + random.randint(-1, 1),
        'angle_z': base_data['angle_z'] + random.randint(-1, 1),
        'attitude1': base_data['attitude1'] + random.randint(-2, 2),
        'attitude2': base_data['attitude2'] + random.randint(-2, 2),
        'pressure': base_data['pressure'] + random.randint(-5, 5),
        'altitude': round(base_data['altitude'] + random.uniform(-0.02, 0.02), 2),
        'longitude': round(base_data['longitude'] + random.uniform(-0.000001, 0.000001), 8),
        'latitude': round(base_data['latitude'] + random.uniform(-0.000001, 0.000001), 8),
        'timestamp': timestamp
    }
    
    return sensor_data

def generate_base_sensor_data():
    """生成基础传感器数据（基于log文件中的数据）"""
    return {
        'accel_x': 59,
        'accel_y': -2,
        'accel_z': 72,
        'gyro_x': -10,
        'gyro_y': -14,
        'gyro_z': -5,
        'angle_x': -10,
        'angle_y': -14,
        'angle_z': -5,
        'attitude1': -3,
        'attitude2': -409,
        'pressure': 96314,
        'altitude': 425.75,
        'longitude': 104.7463432,
        'latitude': 31.4627341
    }

# =============================================================================
# 主函数
# =============================================================================
def main():
    """主函数"""
    print("=" * 50)
    print("应急跌落事件监控系统 - 电脑端模拟")
    print("=" * 50)
    
    # 初始化MQTT客户端
    mqtt_client = MyMQTTClient(
        MQTT_BROKER,
        MQTT_PORT,
        MQTT_USERNAME,
        MQTT_PASSWORD,
        IMEI
    )
    
    if not mqtt_client.connect():
        print("无法连接到MQTT服务器，程序退出")
        return
    
    # 等待连接成功
    time.sleep(2)
    
    # 发送上电包
    mqtt_client.publish_up_power_on_event()
    
    # 初始化数据包序号
    packet_order = 1
    # 生成基础传感器数据
    base_sensor_data = generate_base_sensor_data()
    
    try:
        while True:
            # 生成传感器数据
            sensor_data_list = []
            for i in range(PACKET_COUNT_PER_UPLOAD):
                sensor_data = generate_sensor_data(packet_order, base_sensor_data)
                sensor_data_list.append(sensor_data)
                packet_order += 1
            
            # 发布传感器数据
            mqtt_client.publish_up_sensor_data(sensor_data_list)
            
            # 等待指定间隔
            time.sleep(UPLOAD_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n程序被手动终止")
    finally:
        # 清理资源
        mqtt_client.disconnect()
        print("程序已退出")

if __name__ == "__main__":
    main()