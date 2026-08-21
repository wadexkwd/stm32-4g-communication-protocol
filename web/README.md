# Web 版监控系统（本地部署）

对标 `qt/` 上位机的浏览器版：FastAPI 后端从云端 MQTT（订阅 `up/+` 通配所有设备）接收终端数据，写入本地 SQLite，并通过 REST + WebSocket 提供给浏览器前端展示。

## 功能

- 数据总览：实时表格（新数据置顶，事件类型着色）
- 加速度 / 角速度 / 姿态（俯仰角+翻滚角）/ 环境（气压+高度）：ECharts 曲线，滑动窗口保留最近 120 点
- 位置：高德地图圆形标记 + 坐标标签跟随（复用 qt 方案的 key 与刷新策略）
- 历史查询（按设备/时间段/事件类型）+ CSV 导出
- 多设备支持：后端订阅 `up/+`，前端下拉切换关注设备

## 部署与启动

```bash
cd web/backend
pip install -r requirements.txt
python app.py
```

浏览器访问 http://127.0.0.1:8000

配置（MQTT 地址、数据库路径、监听端口、登录密码、数据保留策略）见 `backend/config.py`；
`DATABASE_FILE` 可改为指向 qt 方案的 `sensor_data.db` 共用历史数据（表结构一致）。

## 访问认证

- 首次访问跳转登录页，输入密码（`config.py` 的 `WEB_PASSWORD`）后获得 12 小时会话（HMAC 签名 HttpOnly Cookie）
- 所有 `/api/*`、WebSocket 及页面均要求登录；会话过期后自动跳回登录页
- **公网部署前务必修改 `WEB_PASSWORD` 和 `SESSION_SECRET`**

## 公网服务器部署

部署到运行 mosquitto 的公网服务器（含 Windows Server 2022 服务注册、防火墙、
域名+HTTPS 方案）见 `deploy/WINDOWS_SERVER.md`。

## 目录结构

```
web/
├── backend/
│   ├── app.py            FastAPI 入口：REST + WebSocket + 静态托管
│   ├── mqtt_service.py   MQTT 订阅线程（解析逻辑与 qt/mqtt_thread.py 一致）
│   ├── database.py       SQLite 读写（表结构与 qt/database_manager.py 一致）
│   ├── config.py         配置与字段定义
│   └── requirements.txt
└── frontend/
    ├── index.html        页面骨架（CDN 引 Vue3 / ECharts / 高德JS API）
    ├── css/style.css
    └── js/
        ├── app.js        Vue3 主逻辑：设备切换、WS 实时数据、历史查询
        ├── charts.js     ECharts 图表封装（滑动窗口 + 禁动画）
        └── map.js        高德地图（自 qt/main_window.py 内嵌 JS 移植）
```

## 接口

| 方法  | 路径              | 说明                                               |
| --- | --------------- | ------------------------------------------------ |
| GET | /api/config     | 字段名/单位/分类/事件类型等展示配置                              |
| GET | /api/status     | 后端 MQTT 连接状态                                     |
| GET | /api/devices    | 设备列表（IMEI + 最近上报时间 + 记录数）                        |
| GET | /api/history    | 历史查询：imei / start / end / event / limit / offset |
| GET | /api/export.csv | CSV 导出（带 BOM，Excel 可直接打开）                        |
| WS  | /ws             | 实时数据推送；客户端发 `{"imei": "xxx"}` 切换关注设备             |

## 验证

本机无真实设备时，可用仓库根目录的模拟器发包验证全链路：

```bash
python simulator/main_simulation.py
```
