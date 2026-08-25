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
import re
import threading
import time

import paho.mqtt.client as mqtt

from config import (MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD,
                    MQTT_CLIENT_ID, MQTT_TOPIC_UP_PREFIX)

# ---- 设备日志相关 ----
# broker 系统日志主题（需在 mosquitto 配置 log_dest topic 才会发布客户端连接/断开消息）
_SYS_LOG_PREFIX = '$SYS/broker/log/'
# 设备客户端 ID 即 IMEI（纯数字），用于从 broker 日志中识别设备、排除工具类客户端
_DEVICE_ID_RE = re.compile(r'^\d{10,}$')
_RE_CLIENT_CONNECTED = re.compile(r"New client connected from \S+ as (\S+)")
_RE_CLIENT_DISCONNECTED = re.compile(r"Client (\S+) disconnected")
_RE_CLIENT_CLOSED = re.compile(r"Client (\S+) closed its connection")


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
        # 后台监听开关：关闭的设备数据直接丢弃（不入库不推送）。
        # 缓存 + 每 30 秒从库刷新一次，避免每条消息查库
        self._disabled = set()
        self._disabled_checked_at = 0.0
        self._disabled_lock = threading.Lock()

    def refresh_disabled(self):
        """立即从库刷新"已关闭监听"设备列表（配置变更后由 Web 层调用，或定时自动刷新）"""
        try:
            disabled = set(self.database.get_disabled_devices())
        except Exception:
            return
        with self._disabled_lock:
            self._disabled = disabled
            self._disabled_checked_at = time.monotonic()

    # ------------------------------------------------------------------ 运行控制
    def run(self):
        self.refresh_disabled()   # 启动时先加载一次监听开关配置
        while not self._stop_event.is_set():
            try:
                self._set_status("正在连接数据接收服务...")
                self._connect_and_loop()
            except Exception as e:
                self._set_status(f"数据接收连接失败（{e}），5秒后重试")
                self._log('', 'error', 'MQTT_SERVICE', f'后端数据接收连接失败（{e}），5秒后重试')
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
            # 同时订阅 broker 系统日志，用于记录设备连接/断开 MQTT 的事件
            client.subscribe([(topic, 0), (_SYS_LOG_PREFIX + '#', 0)])
            self._set_status("数据接收正常（后台监听全部设备上报）")
        else:
            self.connected = False
            self._set_status(f"数据接收连接失败（错误码 {rc}）")
            self._log('', 'error', 'MQTT_SERVICE', f'后端连接 MQTT 服务器失败（错误码 {rc}）')

    def _on_disconnect(self, client, userdata, rc, properties=None, reason_code=None):
        self.connected = False
        self._set_status("数据接收已断开，正在重连...")
        # rc/reason_code 为 0 表示主动断开（服务停止），不记录；其余为异常掉线
        normal = (rc == 0) or (reason_code is not None and getattr(reason_code, 'value', 1) == 0)
        if not normal:
            reason = getattr(reason_code, 'name', None) or f'码 {rc}'
            self._log('', 'warn', 'MQTT_SERVICE', f'后端与 MQTT 服务器异常断开（{reason}），自动重连中')

    def _on_message(self, client, userdata, msg):
        """消息接收回调：解析 -> 入库 -> 通知 Web 层"""
        try:
            # broker 系统日志（$SYS/broker/log/...）：识别设备连接/断开
            if msg.topic.startswith(_SYS_LOG_PREFIX):
                self._handle_broker_log(msg.payload.decode('utf-8', 'replace'))
                return

            # 从主题提取 IMEI（up/{imei}）
            imei = msg.topic[len(MQTT_TOPIC_UP_PREFIX):] if msg.topic.startswith(MQTT_TOPIC_UP_PREFIX) else msg.topic
            if not imei:
                return

            # 该设备已关闭后台监听：直接丢弃（不入库不推送）
            if not self._is_listening(imei):
                return

            payload = msg.payload.decode('utf-8')
            items = self._parse_payload(payload)
            if not items:
                return

            # 关键事件写入设备日志（正常传感器数据与周期心跳不记录）
            self._log_device_events(imei, items)

            # 入库（失败不阻断广播）
            try:
                self.database.save_data(items, imei)
            except Exception as e:
                self._set_status(f"数据入库失败: {e}")
                self._log('', 'error', 'MQTT_SERVICE', f'数据入库失败: {e}')

            if self.on_data:
                try:
                    self.on_data(imei, items)
                except Exception:
                    pass
        except Exception as e:
            self._set_status(f"消息处理失败: {e}")

    # ------------------------------------------------------------------ 设备日志
    def _log(self, imei, level, event, detail):
        """写一条设备/服务日志（失败只更新状态，不影响消息处理）"""
        try:
            self.database.save_device_log(imei, level, event, detail)
        except Exception as e:
            self._set_status(f"日志写入失败: {e}")

    def _log_device_events(self, imei, items):
        """把上报数据中的关键事件（上电/超时/配置回复等）写入设备日志

        正常传感器数据（SENSOR_DATA）与周期心跳（HEARTBEAT）不记录。
        """
        for item in items:
            event = item.get('event', '')
            if not event or event in ('SENSOR_DATA', 'HEARTBEAT'):
                continue
            if event == 'POWER_ON':
                version = item.get('version', '')
                self._log(imei, 'info', 'POWER_ON',
                          '设备上电/重启' + (f'（应用版本 {version}）' if version else ''))
            elif event == 'SENSOR_REPORT_TIMEOUT':
                self._log(imei, 'warn', 'SENSOR_REPORT_TIMEOUT',
                          item.get('description') or '超过设定时间未收到传感器数据')
            elif event == 'CONFIG_REPLY':
                self._log(imei, 'info', 'CONFIG_REPLY',
                          f"采样间隔 {item.get('sample_interval')}s / 上传间隔 {item.get('upload_interval')}s / 数据格式 {item.get('data_format')}")
            elif event == 'RESET_REPLY':
                self._log(imei, 'info', 'RESET_REPLY', f"复位命令已执行（状态 {item.get('reset_status')}）")
            else:
                # 未识别的事件类型：原样记录，便于排查新增事件
                desc = item.get('description', '')
                self._log(imei, 'info', event, desc or '收到未分类事件')

    def _handle_broker_log(self, line):
        """解析 mosquitto 系统日志行，记录设备连接/断开 MQTT 的事件

        设备的 MQTT 客户端 ID 即 IMEI（纯数字），据此过滤出设备、
        排除后端自身与调试工具等非设备客户端。
        """
        try:
            m = _RE_CLIENT_CONNECTED.search(line)
            if m:
                cid = m.group(1)
                if cid != MQTT_CLIENT_ID and _DEVICE_ID_RE.match(cid):
                    self._log(cid, 'info', 'DEVICE_MQTT_CONNECTED', '设备连接 MQTT 服务器')
                return
            m = _RE_CLIENT_DISCONNECTED.search(line)
            if m:
                cid = m.group(1)
                if cid != MQTT_CLIENT_ID and _DEVICE_ID_RE.match(cid):
                    self._log(cid, 'info', 'DEVICE_MQTT_DISCONNECTED', '设备正常断开（发出断开报文）')
                return
            m = _RE_CLIENT_CLOSED.search(line)
            if m:
                cid = m.group(1)
                if cid != MQTT_CLIENT_ID and _DEVICE_ID_RE.match(cid):
                    self._log(cid, 'warn', 'DEVICE_MQTT_DISCONNECTED',
                              '设备异常断开（未发断开报文，可能断电/断网/信号丢失）')
        except Exception:
            pass    # 日志解析失败不影响主流程

    # ------------------------------------------------------------------ 监听开关
    def _is_listening(self, imei):
        """设备是否处于监听状态；缓存超过 30 秒自动刷新一次"""
        with self._disabled_lock:
            if time.monotonic() - self._disabled_checked_at > 30:
                refresh = True
            else:
                refresh = False
        if refresh:
            self.refresh_disabled()
        with self._disabled_lock:
            return imei not in self._disabled

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
