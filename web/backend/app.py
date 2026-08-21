#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - Web后端入口（FastAPI）
功能：
- 启动 MQTT 服务（后台线程订阅 up/+，入库）
- REST API：设备列表 / 历史查询 / CSV导出 / 前端配置 / 服务状态
- WebSocket /ws：实时推送新数据到浏览器
- 托管 frontend 静态文件

启动方式（在 web/backend 目录下）：
    pip install -r requirements.txt
    python app.py
浏览器访问 http://127.0.0.1:8000
"""

import asyncio
import csv
import io
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import (WEB_HOST, WEB_PORT, FRONTEND_DIR, FIELD_ORDER, FIELD_NAMES,
                    EVENT_TYPES, FIELD_UNITS, FIELD_CATEGORIES, CHARTS,
                    RETENTION_DAYS, ARCHIVE_ENABLED)
from database import Database
from mqtt_service import MqttService
from retention import RetentionService


# =============================================================================
# 全局对象
# =============================================================================
database = Database()
mqtt_service = None          # lifespan 中创建
retention_service = None     # lifespan 中创建
main_loop = None             # 主事件循环，供 MQTT 线程投递广播任务

# 已连接的 WebSocket 客户端：{websocket: 关注的imei(None表示全部)}
ws_clients: dict = {}


def broadcast_data(imei, items):
    """MQTT 线程回调：把新数据投递到 asyncio 事件循环广播"""
    if main_loop is None or not ws_clients:
        return
    asyncio.run_coroutine_threadsafe(_do_broadcast(imei, items), main_loop)


async def _do_broadcast(imei, items):
    dead = []
    for ws, watch in list(ws_clients.items()):
        if watch is not None and watch != imei:
            continue
        try:
            await ws.send_json({"type": "data", "imei": imei, "items": items})
        except Exception:
            dead.append(ws)
    for ws in dead:
        ws_clients.pop(ws, None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_service, retention_service, main_loop
    main_loop = asyncio.get_running_loop()
    mqtt_service = MqttService(database, on_data=broadcast_data)
    mqtt_service.start()
    retention_service = RetentionService(database)
    retention_service.start()
    yield
    mqtt_service.stop()
    retention_service.stop()


app = FastAPI(title="应急跌落事件监控系统 Web后端", lifespan=lifespan)


# =============================================================================
# REST API
# =============================================================================
@app.get("/api/config")
async def api_config():
    """前端展示配置：字段名/单位/分类/事件类型/图表定义"""
    return {
        "fieldOrder": FIELD_ORDER,
        "fieldNames": FIELD_NAMES,
        "fieldUnits": FIELD_UNITS,
        "fieldCategories": FIELD_CATEGORIES,
        "eventTypes": EVENT_TYPES,
        "charts": CHARTS,
    }


@app.get("/api/status")
async def api_status():
    """后端与MQTT连接状态"""
    return {
        "mqtt": mqtt_service.get_status() if mqtt_service else "未启动",
        "mqtt_connected": mqtt_service.connected if mqtt_service else False,
        "clients": len(ws_clients),
    }


@app.get("/api/devices")
async def api_devices():
    """设备列表（含最近上报时间与记录数）"""
    return database.get_devices()


@app.get("/api/history")
async def api_history(
    imei: str = Query(None, description="设备IMEI，为空则查全部"),
    start: str = Query(None, description="开始时间 YYYY-MM-DD HH:MM:SS"),
    end: str = Query(None, description="结束时间 YYYY-MM-DD HH:MM:SS"),
    event: str = Query(None, description="事件类型（原始值，如 SENSOR_DATA）"),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    """历史数据查询（分页，按接收时间倒序）"""
    rows = database.query_data(imei=imei, start_time=start, end_time=end,
                               event=event, limit=limit, offset=offset)
    total = database.count_data(imei=imei, start_time=start, end_time=end, event=event)
    return {"total": total, "limit": limit, "offset": offset, "rows": rows}


@app.get("/api/export.csv")
async def api_export_csv(
    imei: str = Query(None),
    start: str = Query(None),
    end: str = Query(None),
    event: str = Query(None),
):
    """按条件导出CSV（带BOM，Excel可直接打开）"""
    rows = database.query_data(imei=imei, start_time=start, end_time=end,
                               event=event, limit=1000000)
    if not rows:
        return JSONResponse({"error": "没有符合条件的数据"}, status_code=404)

    buf = io.StringIO()
    writer = csv.writer(buf)
    header = ['id'] + [FIELD_NAMES.get(col, col) for col in FIELD_ORDER] + ['IMEI', '接收时间']
    writer.writerow(header)
    for row in rows:
        line = [row.get('id', '')]
        line += [row.get(col, '') for col in FIELD_ORDER]
        line += [row.get('imei', ''), row.get('received_time', '')]
        writer.writerow(line)

    filename = f"sensor_data_{imei or 'all'}_{len(rows)}.csv"
    return StreamingResponse(
        iter([b'\xef\xbb\xbf' + buf.getvalue().encode('utf-8')]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@app.get("/api/dashboard")
async def api_dashboard(online_sec: int = Query(60, ge=5, description="最后上报距今多少秒内视为在线")):
    """数据看板：设备总数/在线状态/最新位置/异常事件统计"""
    devices = database.get_devices()
    latest = {row['imei']: row for row in database.get_latest_rows_by_device()}
    events_24h = database.get_recent_event_counts(24)
    volume_24h = database.get_recent_volume(24)
    events_hourly = database.get_recent_events_hourly(24)

    now = datetime.now()
    result = []
    online_count = 0
    alarm_24h_total = 0
    poweron_24h_total = 0
    for d in devices:
        imei = d['imei']
        last = latest.get(imei, {})
        # 在线判断：最后上报时间距今小于 online_sec 秒
        online = False
        try:
            last_dt = datetime.strptime(d['last_time'], '%Y-%m-%d %H:%M:%S.%f')
            online = (now - last_dt).total_seconds() < online_sec
        except (ValueError, TypeError):
            pass
        ev = events_24h.get(imei, {})
        timeout_cnt = ev.get('SENSOR_REPORT_TIMEOUT', 0)
        poweron_cnt = ev.get('POWER_ON', 0)
        alarm_24h_total += timeout_cnt
        poweron_24h_total += poweron_cnt
        if online:
            online_count += 1
        result.append({
            'imei': imei,
            'online': online,
            'last_time': d['last_time'],
            'total_count': d['count'],
            'volume_24h': volume_24h.get(imei, 0),
            'timeout_24h': timeout_cnt,
            'poweron_24h': poweron_cnt,
            'version': last.get('version', ''),
            'last_event': last.get('event', ''),
            'last_sensor_time': last.get('timestamp', ''),
            'longitude': last.get('longitude'),
            'latitude': last.get('latitude'),
            'altitude': last.get('altitude'),
            'pressure': last.get('pressure'),
        })

    return {
        'total': len(result),
        'online': online_count,
        'offline': len(result) - online_count,
        'alarm_24h': alarm_24h_total,
        'poweron_24h': poweron_24h_total,
        'online_sec': online_sec,
        'devices': result,
        # 近24h异常事件按小时分布（时间轴）：{ 'YYYY-MM-DD HH:00': {事件类型: 次数} }
        'events_hourly': events_hourly,
        # 存储与保留策略状态
        'storage': database.get_storage_stats(),
        'retention': {
            'days': RETENTION_DAYS,
            'archive_enabled': ARCHIVE_ENABLED,
            'last_run': retention_service.last_result if retention_service else None,
        },
    }


# =============================================================================
# WebSocket：实时数据推送
# =============================================================================
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global main_loop
    await ws.accept()
    # 可通过查询参数指定关注设备：/ws?imei=xxx
    watch = ws.query_params.get("imei")
    ws_clients[ws] = watch
    try:
        # 先推一波当前状态，便于前端初始化
        await ws.send_json({
            "type": "hello",
            "mqtt": mqtt_service.get_status() if mqtt_service else "未启动",
        })
        while True:
            # 客户端可发 {"imei": "xxx"} 切换关注的设备，或 {"imei": null} 关注全部
            msg = await ws.receive_json()
            if isinstance(msg, dict) and "imei" in msg:
                ws_clients[ws] = msg["imei"]
    except WebSocketDisconnect:
        pass
    finally:
        ws_clients.pop(ws, None)


# =============================================================================
# 静态前端托管（放在最后，避免覆盖 /api、/ws 路由）
# =============================================================================
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run("app:app", host=WEB_HOST, port=WEB_PORT, log_level="info")
