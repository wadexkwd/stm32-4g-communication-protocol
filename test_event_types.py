import paho.mqtt.client as mqtt
import json
import time
import random

# 配置
MQTT_BROKER = "120.27.250.30"
MQTT_PORT = 1883
TEST_IMEI = "861197065268692"

def on_connect(client, userdata, flags, rc, properties):
    print(f"连接成功，返回码: {rc}")

def on_publish(client, userdata, mid, reason_code, properties):
    print(f"消息发布成功，消息ID: {mid}, 结果码: {reason_code}")

# 创建MQTT客户端
client = mqtt.Client(client_id=f"test_publisher_{random.randint(1, 1000)}", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_publish = on_publish

# 连接到MQTT服务器
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_start()

# 发送上电包
power_on_data = {
    "event": "POWER_ON",
    "data": [{
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "V1.0",
        "packet_order": "1"
    }]
}

print("发送上电包...")
client.publish(f"up/{TEST_IMEI}", json.dumps(power_on_data), qos=1)

time.sleep(1)

# 发送传感器数据包
sensor_data = {
    "event": "SENSOR_DATA",
    "data": [{
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "V1.0",
        "packet_order": "2",
        "accel_x": random.randint(-1000, 1000),
        "accel_y": random.randint(-1000, 1000),
        "accel_z": random.randint(-1000, 1000),
        "gyro_x": random.randint(-360, 360),
        "gyro_y": random.randint(-360, 360),
        "gyro_z": random.randint(-360, 360),
        "angle_x": random.randint(-180, 180),
        "angle_y": random.randint(-180, 180),
        "angle_z": random.randint(-180, 180),
        "attitude1": random.randint(0, 360),
        "attitude2": random.randint(0, 360),
        "pressure": random.randint(80000, 100000),
        "altitude": random.randint(0, 1000),
        "longitude": random.uniform(-180, 180),
        "latitude": random.uniform(-90, 90)
    }]
}

print("发送传感器数据包...")
client.publish(f"up/{TEST_IMEI}", json.dumps(sensor_data), qos=1)

time.sleep(1)

# 发送传感器数据超时事件包
timeout_data = {
    "event": "SENSOR_REPORT_TIMEOUT",
    "data": [{
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "V1.0",
        "packet_order": "3"
    }]
}

print("发送传感器数据超时事件包...")
client.publish(f"up/{TEST_IMEI}", json.dumps(timeout_data), qos=1)

# 等待消息发送完成
time.sleep(2)

print("测试完成")
client.loop_stop()
client.disconnect()