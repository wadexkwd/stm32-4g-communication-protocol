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
- `.gitignore`：忽略 `__pycache__/`、`*.pyc`、`*.db`、`*.xls`、`web/backend/archive/`
- **Web 版功能增强**（同日第二批改动）：
  - **设备连接控制**：默认不连接，须在下拉框选定设备后点「连接设备」才读取该设备数据（断开后端推送省流量），可手动断开；切换设备自动断开，连接始终为显式动作
  - **数据看板页**（`dashboard.html`，主页按钮跳转）：设备总数/在线/离线汇总卡片、24h 超时告警与上电重启统计、设备位置分布地图（在线绿/离线灰/告警红描边，点击定位）、设备情况总览表、近 24h 异常事件按小时分布堆叠柱状图
  - **数据保留策略**（`backend/retention.py`）：默认保留 30 天，过期数据先流式归档为 CSV.gz（`archive/` 目录）再删除并 VACUUM 回收空间；归档失败则跳过删除（宁占盘不丢数）；配置见 `config.py`（`RETENTION_DAYS=0` 可关闭）
  - 看板新增存储状态：库内总记录/数据库体积卡片 + 保留策略与最近清理状态行
  - Vue 3.4.38 / ECharts 5.5.0 下载至 `web/frontend/vendor/` 本地引用，摆脱 jsdelivr CDN 依赖（内网可部署）
  - **Web 访问认证**：密码登录页 + HMAC 签名 HttpOnly Cookie 会话（12 小时），页面/API/WebSocket 全部要求登录，会话过期自动跳回登录页；公网部署前需修改 `WEB_PASSWORD`/`SESSION_SECRET`
  - **Windows Server 部署指南**（`web/deploy/WINDOWS_SERVER.md`）：Python 安装、配置要点、防火墙/安全组、NSSM 注册 Windows 服务、备案后域名+HTTPS（Caddy）方案
  - 新增接口：`GET /api/dashboard`（设备/异常/存储/保留策略聚合）、`POST /api/login`/`api/logout`、数据库层新增保留策略支撑查询

### 变更

- **Web 前端性能优化**（修复页面持续运行时 CPU 占用过高、整机卡顿）：
  - 修复首屏白屏 bug：模板绑定的 `filteredRows` 未从 setup 返回，渲染抛 TypeError 导致根节点为空
  - 攒批节流：WS 数据先进缓冲，UI 每 1 秒统一刷新一次（原为逐条插入表格/逐点全量重绘图表，约 50 次 setOption+10 次全表重排每秒）
  - 数据容器改 `shallowRef`，避免 500 条 × 20 字段的深层响应式代理开销
  - 只重绘当前 Tab 可见的图表；表格仅在「数据总览」页激活时更新 DOM（切换 Tab 时补绘/补触发）
  - 表格可见行数 500 -> 50；单元格格式化弃用 `toLocaleString`
- **项目目录结构整理**（`git mv` 移动，保留历史）：
  - 根目录 40+ 测试脚本归类至 `tests/protocol/`（C 协议帧测试）、`tests/precision/`（精度/解析测试）、`tests/simulation/`（模拟器/上位机冒烟）、`tests/data/`（测试数据）
  - 模拟器移至 `simulator/`，辅助脚本移至 `tools/`（mqtt_listener、串口/Excel 检查、GitHub 仓库管理等）
  - qt 目录内测试脚本归类至 `qt/tests/`、环境检查脚本归类至 `qt/tools/`
  - 参考代码 `dc_main.py` 移至 `doc/reference/`

### 移除

- 移除误提交的 `qt/__pycache__/` 编译产物（6 个 .pyc）

## [历史版本]

- v1.0（2026-02-13）：完成核心功能开发（终端固件、MQTT 链路、Qt 上位机、模拟器）
