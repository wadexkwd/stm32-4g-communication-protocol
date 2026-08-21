#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - Web后端MQTT服务模块
功能：
- 后台线程运行 paho-mqtt 客户端，订阅 up/+ 通配所有设备
- 消息解析逻辑与 qt/mqtt_thread.py 保持一致：
  1) {"event": "...", "version": ..., "data": [...]}   批量传感器数据
  2) [ {...}, {...} ]                                   裸数组
  3) {"event": "POWER_ON", ...}                          单对象（上电包/超时包）
- 解析结果写入数据库，并通过回调交给 Web 层广播
"""

import json
import threading

import paho.mqtt.client as mqtt

from config import (MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD,
                    MQTT_CLIENT_ID, MQTT_TOPIC_UP_PREFIX)


class MqttService(threading.Thread):
    """MQTT 订阅服务（后台线程）"""

    def __init__(self, database, on_data=None):
        super().__init__(daemon=True, name='mqtt-service')
        self.database = database
        self.on_data = on_data          # 回调: on_data(imei, items) 在 MQTT 线程中被调用
        self.client = None
        self.connected = False
        self._stop_event = threading.Event()
        self.status = "未启动"
        self._status_lock = threading.Lock()

    # ------------------------------------------------------------------ 运行控制
    def run(self):
        while not self._stop_event.is_set():
            try:
                self._set_status("正在连接MQTT服务器...")
                self._connect_and_loop()
            except Exception as e:
                self._set_status(f"MQTT连接失败: {e}，5秒后重试")
                self._stop_event.wait(5)

    def stop(self):
        self._stop_event.set()
        client = self.client
        self.client = None
        if client:
            try:
                client.disconnect()
            except Exception:
                pass

    def _set_status(self, text):
        with self._status_lock:
            self.status = text

    def get_status(self):
        with self._status_lock:
            return self.status

    # ------------------------------------------------------------------ MQTT 回调
    def _connect_and_loop(self):
        client = mqtt.Client(
            client_id=f"{MQTT_CLIENT_ID}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        if MQTT_USERNAME:
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.reconnect_delay_set(min_delay=5, max_delay=300)
        client.keepalive = 120
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect

        self.client = client
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=120)
        # loop_forever 内部自动重连，异常时抛出由外层 while 捕获
        client.loop_forever(retry_first_connection=True)

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.connected = True
            topic = f"{MQTT_TOPIC_UP_PREFIX}+"
            client.subscribe(topic)
            self._set_status(f"MQTT已连接，订阅主题: {topic}")
        else:
            self.connected = False
            self._set_status(f"MQTT连接失败，错误码: {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None, reason_code=None):
        self.connected = False
        self._set_status("MQTT连接断开，正在重连...")

    def _on_message(self, client, userdata, msg):
        """消息接收回调：解析 -> 入库 -> 通知 Web 层"""
        try:
            # 从主题提取 IMEI（up/{imei}）
            imei = msg.topic[len(MQTT_TOPIC_UP_PREFIX):] if msg.topic.startswith(MQTT_TOPIC_UP_PREFIX) else msg.topic
            if not imei:
                return

            payload = msg.payload.decode('utf-8')
            items = self._parse_payload(payload)
            if not items:
                return

            # 入库（失败不阻断广播）
            try:
                self.database.save_data(items, imei)
            except Exception as e:
                self._set_status(f"数据入库失败: {e}")

            if self.on_data:
                try:
                    self.on_data(imei, items)
                except Exception:
                    pass
        except Exception as e:
            self._set_status(f"消息处理失败: {e}")

    # ------------------------------------------------------------------ 消息解析
    @staticmethod
    def _parse_payload(payload):
        """解析消息负载，返回统一的 dict 列表（解析规则与 qt/mqtt_thread.py 一致）"""
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return []

        if isinstance(data, dict) and "data" in data:
            if isinstance(data["data"], list):
                # 批量数据：为每个数据项补充事件类型和版本信息
                event_type = data.get("event", "")
                version = data.get("version", "")
                items = []
                for item in data["data"]:
                    if not isinstance(item, dict):
                        continue
                    item = item.copy()
                    item["event"] = event_type
                    item["version"] = version
                    items.append(item)
                return items
            return []
        if isinstance(data, list):
            # 裸数组：补充默认事件类型
            items = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                item = item.copy()
                if "event" not in item:
                    item["event"] = "SENSOR_DATA"
                items.append(item)
            return items
        if isinstance(data, dict) and "event" in data:
            # 单对象（上电包、超时包等一次性事件）
            return [data]
        return []
