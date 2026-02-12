#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - MQTT消息处理模块
功能：
- 封装MQTT连接、订阅、消息接收和处理功能
- 运行在独立线程中，避免阻塞UI
"""

import time
import json
from PySide6.QtCore import QThread, Signal
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD

class MqttThread(QThread):
    """MQTT消息处理线程"""
    
    # 信号定义
    message_received = Signal(str, str)  # 原始数据
    sensor_data_received = Signal(list)  # 解析后的传感器数据
    connection_status = Signal(str)  # 连接状态
    error_occurred = Signal(str)  # 错误信息
    
    def __init__(self, imei):
        super().__init__()
        self.imei = imei
        self.client = None
        self.connected = False
        self.running = False
    
    def run(self):
        """线程运行函数"""
        self.running = True
        self._connect_mqtt()
    
    def _connect_mqtt(self):
        """连接到MQTT服务器"""
        try:
            # 创建MQTT客户端
            client_id = f"qt_listener_{self.imei}"
            self.client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
            
            # 设置回调函数
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            self.client.on_log = self._on_log
            
            # 设置认证信息
            if MQTT_USERNAME:
                self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            
            # 设置连接参数
            self.client.reconnect_delay_set(min_delay=5, max_delay=300)
            self.client.keepalive = 120
            self.client.max_queued_messages_set(1000)
            self.client.connect_timeout = 60
            
            # 连接到MQTT服务器
            self.connection_status.emit(f"正在连接到MQTT服务器: {MQTT_BROKER}:{MQTT_PORT}")
            self.client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=120)
            
            # 使用 loop_start 替代 loop_forever，以便能够更好地控制停止
            self.client.loop_start()
            
            # 保持线程运行直到停止信号
            while self.running:
                time.sleep(0.1)
            
            # 停止网络循环
            self.client.loop_stop()
            
        except Exception as e:
            self.error_occurred.emit(f"连接失败: {str(e)}")
    
    def _on_connect(self, client, userdata, flags, rc, properties):
        """连接成功回调"""
        if rc == 0:
            self.connected = True
            topic = f"up/{self.imei}"
            client.subscribe(topic)
            self.connection_status.emit(f"✅ MQTT连接成功，已订阅主题: {topic}")
        else:
            self.connected = False
            self.connection_status.emit(f"❌ MQTT连接失败，错误码: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            # 解码消息
            payload = msg.payload.decode('utf-8')
            self.message_received.emit(msg.topic, payload)
            
            # 解析JSON格式消息
            try:
                data = json.loads(payload)
                
                # 解析消息格式 {"event": "SENSOR_DATA", "data": [...]}
                if isinstance(data, dict) and "data" in data:
                    if isinstance(data["data"], list):
                        # 为每个数据项添加事件类型和版本信息
                        event_type = data.get("event", "")
                        version = data.get("version", "")
                        enhanced_data = []
                        for item in data["data"]:
                            item_with_event = item.copy()
                            item_with_event["event"] = event_type
                            item_with_event["version"] = version
                            enhanced_data.append(item_with_event)
                        self.sensor_data_received.emit(enhanced_data)
                    else:
                        self.connection_status.emit(f"收到非列表格式数据")
                elif isinstance(data, list):
                    # 如果直接是数组格式，为每个数据项添加默认事件类型
                    enhanced_data = []
                    for item in data:
                        if "event" not in item:
                            item_with_event = item.copy()
                            item_with_event["event"] = "SENSOR_DATA"
                            enhanced_data.append(item_with_event)
                        else:
                            enhanced_data.append(item)
                    self.sensor_data_received.emit(enhanced_data)
                elif isinstance(data, dict) and "event" in data:
                    # 处理单个JSON对象格式（如上电包、超时包）
                    self.sensor_data_received.emit([data])
                else:
                    self.connection_status.emit(f"收到非预期格式消息")
                    
            except json.JSONDecodeError:
                self.connection_status.emit("收到非JSON格式消息")
                
        except Exception as e:
            self.error_occurred.emit(f"消息处理失败: {str(e)}")
    
    def _on_disconnect(self, client, userdata, rc, properties, reason_code):
        """断开连接回调"""
        self.connected = False
        self.connection_status.emit("🔌 MQTT连接已断开，正在尝试重连...")
    
    def _on_log(self, client, userdata, level, buf):
        """日志回调"""
        if level == mqtt.MQTT_LOG_WARNING:
            self.connection_status.emit(f"⚠️ 警告: {buf}")
        elif level == mqtt.MQTT_LOG_ERROR:
            self.connection_status.emit(f"❌ 错误: {buf}")
    
    def stop(self):
        """停止MQTT客户端"""
        self.running = False
        if self.client:
            # 首先停止消息处理
            self.client.on_message = lambda *args: None
            
            # 取消订阅主题
            try:
                self.client.unsubscribe(f"up/{self.imei}")
            except Exception as e:
                pass
                
            # 断开连接
            try:
                self.client.disconnect()
            except Exception as e:
                pass
                
            # 停止网络循环
            try:
                self.client.loop_stop()
            except Exception as e:
                pass
                
            # 等待一段时间确保连接完全关闭
            time.sleep(0.5)
            
            # 释放客户端资源
            self.client = None