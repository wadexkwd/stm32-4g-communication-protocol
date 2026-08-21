# Windows Server 2022 部署指南

目标：把 Web 套件部署到运行 mosquitto 的公网服务器（120.27.250.30 / kingnike.top），
本地电脑浏览器直接访问。

服务器环境：Windows Server 2022 数据中心版，2核 / 2GB 内存 / 50GB 硬盘，已运行 mosquitto。

## 整体流程速览

```
装 Python -> 拷代码 -> 改配置(MQTT地址/密码/密钥) -> pip install -> 试运行验证
-> 开防火墙(8000) -> NSSM 注册服务 -> 收紧 mosquitto 认证 -> 上线检查
（备案通过后：域名 + Caddy HTTPS）
```

## 一、安装 Python

1. 下载 Python 3.11+（Windows installer 64-bit）：https://www.python.org/downloads/windows/
2. 安装时**勾选 "Add python.exe to PATH"**
3. 验证（新开命令行）：
   ```bat
   python --version
   ```

## 二、部署代码

方式 A（推荐，服务器装 git）：
```bat
git clone https://github.com/wadexkwd/stm32-4g-communication-protocol.git C:\dwdl
```

方式 B：本地把 `web/` 整个目录拷贝到服务器（如 `C:\dwdl\web`）。

## 三、修改配置

编辑 `C:\dwdl\web\backend\config.py`：

```python
MQTT_BROKER = "127.0.0.1"      # 与本机 mosquitto 通信（原来是 120.27.250.30）
WEB_PASSWORD = "改成你自己的强密码"      # 登录密码，必改！
SESSION_SECRET = "改成一串随机字符"      # 会话签名密钥，必改！
```

生成随机密钥可在命令行执行：
```bat
python -c "import secrets; print(secrets.token_hex(32))"
```

## 四、安装依赖并试运行

```bat
cd C:\dwdl\web\backend
pip install -r requirements.txt
python app.py
```

服务器本机浏览器访问 http://127.0.0.1:8000 验证：出现登录页、输入密码后能看到数据。

## 五、开放防火墙端口

管理员命令行执行：
```bat
netsh advfirewall firewall add rule name="dwdl-web" dir=in action=allow protocol=TCP localport=8000
```

（若服务器在阿里云等云平台，还需在控制台**安全组**放行 TCP 8000 入方向。）

本地电脑浏览器访问：**http://120.27.250.30:8000**

> **域名与备案说明**：kingnike.top 未备案前，国内服务器用域名走 80/443 端口会被
> 云厂商拦截，所以现阶段用 **IP:8000 直连**。备案通过后再绑定域名并加 HTTPS
> （推荐 Caddy，自动申请证书，配置见本文末尾"可选：域名+HTTPS"）。

## 六、注册为 Windows 服务（开机自启、崩溃自动拉起）

使用 NSSM（Non-Sucking Service Manager）：

1. 下载：https://nssm.cc/download ，解压得到 `nssm.exe`（放到如 `C:\tools\`）
2. 管理员命令行执行（按实际路径调整 python.exe 与项目路径）：
   ```bat
   C:\tools\nssm.exe install dwdl-web "C:\Program Files\Python311\python.exe" "C:\dwdl\web\backend\app.py"
   C:\tools\nssm.exe set dwdl-web AppDirectory "C:\dwdl\web\backend"
   C:\tools\nssm.exe set dwdl-web AppStdout "C:\dwdl\web\backend\service.log"
   C:\tools\nssm.exe set dwdl-web AppStderr "C:\dwdl\web\backend\service.err.log"
   C:\tools\nssm.exe set dwdl-web AppRotateFiles 1
   C:\tools\nssm.exe start dwdl-web
   ```
3. 验证：`sc query dwdl-web` 显示 RUNNING；重启服务器后服务自动启动。

日常管理：
```bat
C:\tools\nssm.exe restart dwdl-web     :: 重启（改配置后）
C:\tools\nssm.exe stop dwdl-web        :: 停止
C:\tools\nssm.exe remove dwdl-web confirm   :: 卸载服务
```

## 七、收紧 mosquitto 认证（强烈建议）

**现状风险**：mosquitto 当前无密码（`allow_anonymous` 默认放行），1883 端口暴露公网--
任何人扫到 IP 都能连上来**收听全部设备数据（含人员位置）甚至伪造下发消息**。
Web 加了登录页只是保护了展示层，MQTT 这扇门也要锁上。

### 7.1 创建账号密码文件

mosquitto 安装目录（默认 `C:\Program Files\mosquitto\`）下，管理员命令行执行：

```bat
cd "C:\Program Files\mosquitto"
mosquitto_passwd.exe -c C:\dwdl\mosquitto_pw dwdl
```

（`dwdl` 为用户名，按提示输入两遍密码；密码文件放 `C:\dwdl\mosquitto_pw`，
不要放在 mosquitto 安装目录，升级时不易丢失。）

### 7.2 修改 mosquitto.conf

编辑 `C:\Program Files\mosquitto\mosquitto.conf`，追加：

```
allow_anonymous false
password_file C:\dwdl\mosquitto_pw
```

### 7.3 重启 mosquitto

```bat
net stop mosquitto && net start mosquitto
```

（若是手动运行的进程，先 taskkill 再重新启动；如果 mosquitto 未注册为服务：
`sc create mosquitto binPath= "C:\Program Files\mosquitto\mosquitto.exe" start= auto`）

### 7.4 所有 MQTT 客户端同步配置（重要！）

开启认证后，**所有**连这个 broker 的客户端都要带账号密码，改完各自配置后重启：

| 客户端 | 配置位置 | 字段 |
|---|---|---|
| Web 后端 | `web/backend/config.py` | `MQTT_USERNAME` / `MQTT_PASSWORD`（重启服务） |
| 终端固件 | `device/main.py` | `MQTT_USERNAME` / `MQTT_PASSWORD`（需重新烧录/下载到 EC800M） |
| 本地 Web 版 | 本地 `web/backend/config.py` | 同上 |
| qt 上位机 | `qt/config.py` | `MQTT_USERNAME` / `MQTT_PASSWORD` |
| 模拟器 | `simulator/main_simulation.py` | 对应 USERNAME/PASSWORD 变量 |

> 注意终端固件升级窗口：设备在野外时改了 broker 认证会导致其掉线无法上报，
> 建议在设备可统一维护的时间窗口操作；或先用 mosquitto 的
> `per_listener_settings` 双监听（老端口匿名一段时间）做灰度过渡。

### 7.5 验证

```bat
:: 无密码应被拒
mosquitto_sub.exe -h 127.0.0.1 -t "up/#" -C 1
:: 带密码应能收到数据
mosquitto_sub.exe -h 127.0.0.1 -u dwdl -P 密码 -t "up/#" -C 1
```

浏览器刷新 Web 页面，确认实时数据仍在滚动（即 Web 后端已用新账号连上）。

## 八、上线检查清单

- [ ] `config.py` 中 MQTT_BROKER 已改 127.0.0.1
- [ ] WEB_PASSWORD / SESSION_SECRET 已改为强随机值
- [ ] 服务器时区为北京时间（`tzutil /g` 应显示 "China Standard Time"）
- [ ] 防火墙 + 云安全组已放行 8000
- [ ] 浏览器能登录并看到实时数据
- [ ] 数据看板显示存储状态正常
- [ ] mosquitto 认证已收紧（第七节），所有客户端已同步账号并验证上报正常
- [ ] 磁盘水位：50GB 盘 + 30 天保留策略足够（1 台设备约 5GB 热数据）；设备增多时
      注意 `archive/` 目录增长，可定期清理最老的归档

## 可选：域名 + HTTPS（备案通过后）

1. 服务器 DNS 解析：kingnike.top A 记录 -> 120.27.250.30
2. 下载 Caddy（https://caddyserver.com/download ，Windows 版单文件）
3. 同目录创建 `Caddyfile`：
   ```
   kingnike.top {
       reverse_proxy 127.0.0.1:8000
   }
   ```
4. 管理员运行 `caddy run`（自动申请 Let's Encrypt 证书），验证后用 NSSM 注册为服务。
5. 之后访问 https://kingnike.top （WebSocket 自动升级为 wss，代码无需改动）。

## 常见问题

- **页面打不开**：依次查 云安全组 -> Windows 防火墙 -> 服务是否 RUNNING（`sc query dwdl-web`）
- **登录后看不到数据**：查 mosquitto 是否在跑（`tasklist | findstr mosquitto`），
  看 `service.err.log` 里 MQTT 连接状态
- **MQTT 连不上**：确认 mosquitto 监听的是 1883（`netstat -ano | findstr 1883`），
  且未配置为仅本机回环之外的绑定限制
- **改了配置不生效**：`nssm restart dwdl-web` 重启服务
