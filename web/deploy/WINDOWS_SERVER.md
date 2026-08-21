# Windows Server 2022 部署指南

目标：把 Web 套件部署到运行 mosquitto 的公网服务器（120.27.250.30 / kingnike.top），
本地电脑浏览器直接访问。

服务器环境：Windows Server 2022 数据中心版，2核 / 2GB 内存 / 50GB 硬盘，已运行 mosquitto。

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

## 七、上线检查清单

- [ ] `config.py` 中 MQTT_BROKER 已改 127.0.0.1
- [ ] WEB_PASSWORD / SESSION_SECRET 已改为强随机值
- [ ] 服务器时区为北京时间（`tzutil /g` 应显示 "China Standard Time"）
- [ ] 防火墙 + 云安全组已放行 8000
- [ ] 浏览器能登录并看到实时数据
- [ ] 数据看板显示存储状态正常
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
