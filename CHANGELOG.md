# 更新日志

本项目所有显著变更将记录在此文件中。
格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [未发布] - 2026-08-21

### 新增

- **Web 版监控系统（`web/`，本地部署）**：对标 qt 上位机的浏览器版方案
  - 后端 FastAPI：后台线程订阅云端 MQTT `up/+` 通配所有设备，解析入库 SQLite（表结构与 qt 方案一致），REST API（设备列表/历史查询/CSV 导出/状态）+ WebSocket 实时推送 + 托管前端静态页
  - 前端无构建静态页（CDN 引 Vue3 / ECharts / 高德 JS API）：数据总览实时表格、加速度/角速度/姿态/环境四组曲线（滑动窗口）、高德地图标记（自 qt 内嵌地图 JS 移植）、历史查询与 CSV 导出、多设备切换
  - 已用 `simulator/main_simulation.py` 完成全链路验证（入库 800+ 条、WS 推送、按设备过滤、CSV 导出均通过）
  - 详见 `web/README.md`
- 根目录 `README.md`：项目结构说明、运行入口（含 Web 版启动方式）、已知事项
- `.gitignore`：忽略 `__pycache__/`、`*.pyc`、`*.db`、`*.xls`

### 变更

- **项目目录结构整理**（`git mv` 移动，保留历史）：
  - 根目录 40+ 测试脚本归类至 `tests/protocol/`（C 协议帧测试）、`tests/precision/`（精度/解析测试）、`tests/simulation/`（模拟器/上位机冒烟）、`tests/data/`（测试数据）
  - 模拟器移至 `simulator/`，辅助脚本移至 `tools/`（mqtt_listener、串口/Excel 检查、GitHub 仓库管理等）
  - qt 目录内测试脚本归类至 `qt/tests/`、环境检查脚本归类至 `qt/tools/`
  - 参考代码 `dc_main.py` 移至 `doc/reference/`

### 移除

- 移除误提交的 `qt/__pycache__/` 编译产物（6 个 .pyc）

## [历史版本]

- v1.0（2026-02-13）：完成核心功能开发（终端固件、MQTT 链路、Qt 上位机、模拟器）
