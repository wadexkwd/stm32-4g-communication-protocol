# 应急跌落事件监控系统

铁塔作业人员安全监控：STM32 终端（MPU6050 + 气压计 + GNSS）→ 4G 模块（移远 EC800M-CN，QPython）→ MQTT 云端（mosquitto）→ 上位机展示。

## 目录结构

```
dwdl/
├── device/          终端 4G 模块固件（QPython，运行于 EC800M-CN）
│   └── main.py      串口收 STM32 数据帧 + MQTT 上报 + 心跳 + 看门狗
├── qt/              PySide6 上位机（MQTT 订阅 + 数据表格/图表 + 高德地图 + SQLite 存储）
│   ├── tests/       地图/网络加载等调试测试脚本
│   └── tools/       数据库/WebEngine 环境检查脚本
├── simulator/       电脑端模拟器（模拟终端向 MQTT 发包）
├── web/             Web 版监控系统（本地部署：FastAPI + SQLite + 浏览器前端，功能对标 qt 上位机，详见 web/README.md）
├── tests/           协议与解析测试
│   ├── protocol/    C 版协议帧打包/解析测试（含源码与编译产物）
│   ├── precision/   浮点精度 / JSON / 结构体对齐解析测试
│   ├── simulation/  模拟器与上位机冒烟测试
│   └── data/        测试数据（sensor_data.xlsx、日志样本）
├── tools/           辅助工具脚本（MQTT 监听、Excel 检查、串口读取、GitHub 仓库管理等）
├── doc/             项目文档
│   ├── STM32_4G_Communication_Protocol.md   串口通信协议（帧格式/命令码/校验）
│   ├── 项目介绍.md
│   └── reference/   参考代码（dc_main.py，其他 QPython 工程）
├── log/             实机联调日志（2026-02-11/12，IMEI 861197...）
└── ai/              （空，预留）
```

## 运行入口

| 用途 | 命令 |
|---|---|
| 上位机 | `python qt/main_window.py`（依赖见 `qt/requirements.txt`：PySide6 / paho-mqtt / openpyxl） |
| Web 版监控 | `cd web/backend && python app.py`，浏览器访问 http://127.0.0.1:8000 |
| 模拟器 | `python simulator/main_simulation.py`（在仓库根目录运行） |
| MQTT 监听 | `python tools/mqtt_listener.py` |

## 说明

- MQTT 服务器地址目前硬编码在各入口文件中（`device/main.py`、`qt/config.py`、`simulator/main_simulation.py`），修改时需同步多处。
- `tools/check_excel.py`、`tools/read_co.py` 按相对路径读写数据文件，需在仓库根目录运行，或在 `tests/data/` 下执行。
- 当前版本 v1.0（2026-02-13），报警功能未实现，仅数据采集与展示。
