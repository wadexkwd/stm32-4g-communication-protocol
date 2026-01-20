import serial
import time

# ====== 用户配置区 ======
SERIAL_PORT = 'COM4'      # ←←← 请修改为你的串口号
BAUD_RATE = 9600
TIMEOUT = 1               # 串口超时（秒）
WORK_MODE = 'active'      # 'active' 或 'passive'
READ_INTERVAL = 2.0       # 被动模式下的读取间隔（秒）
# =======================

def bytes_to_hex_str(data):
    """将 bytes 或 list[int] 转为 'FF 19 02 ...' 格式的字符串"""
    if isinstance(data, bytes):
        return ' '.join(f'{b:02X}' for b in data)
    elif isinstance(data, (list, tuple)):
        return ' '.join(f'{b:02X}' for b in data)
    else:
        return str(data)

def calculate_checksum(data):
    """计算校验和：对索引1～7求和，取反加1，&0xFF"""
    if len(data) < 9:
        return None
    s = sum(data[1:8])
    return ((~s) + 1) & 0xFF

def parse_response(frame):
    """解析9字节响应帧，返回CO浓度（ppm）或None"""
    if len(frame) != 9:
        print("❌ 帧长度错误")
        return None
    if frame[0] != 0xFF:
        print("❌ 起始位错误")
        return None
    # if frame[1] != 0x86:
    #     print(f"⚠️ 命令异常: 0x{frame[1]:02X}")
 

    calc_cs = calculate_checksum(frame)
    recv_cs = frame[8]
    if calc_cs != recv_cs:
        print(f"❌ 校验失败 | 计算: 0x{calc_cs:02X}, 收到: 0x{recv_cs:02X}")
        return None
    if frame[1] == 0x19: #主动上报的数据
        co_ppm = (frame[4] << 8) | frame[5]
    else: #读取命令的响应数据
        co_ppm = (frame[6] << 8) | frame[7]
    return co_ppm

def send_frame(ser, frame_bytes):
    """发送一个完整的9字节命令帧，并打印HEX"""
    if isinstance(frame_bytes, list):
        frame_bytes = bytes(frame_bytes)
    ser.write(frame_bytes)
    print(f"[TX] {bytes_to_hex_str(frame_bytes)}")

def main():
    # 定义命令帧
    CMD_SET_ACTIVE = [0xFF, 0x01, 0x78, 0x40, 0x00, 0x00, 0x00, 0x00, 0x47]
    CMD_SET_PASSIVE = [0xFF, 0x01, 0x78, 0x41, 0x00, 0x00, 0x00, 0x00, 0x46]
    CMD_READ = [0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79]

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        print(f"🔌 连接串口 {SERIAL_PORT} @ {BAUD_RATE} bps")
        
        # 步骤1: 发送模式设置指令
        if WORK_MODE == 'active':
            print("⚙️ 设置模组为【主动模式】...")
            send_frame(ser, CMD_SET_ACTIVE)
        elif WORK_MODE == 'passive':
            print("⚙️ 设置模组为【被动模式】...")
            send_frame(ser, CMD_SET_PASSIVE)
        else:
            raise ValueError("WORK_MODE 必须是 'active' 或 'passive'")

        # 等待模组处理指令（短暂延时）
        time.sleep(0.5)

        # 清空可能的残留响应
        ser.reset_input_buffer()
        print("✅ 模式设置完成，开始数据交互...\n")

        buffer = []
        last_read_time = time.time()

        while True:
            current_time = time.time()

            # === 被动模式：定时发送读取命令 ===
            if WORK_MODE == 'passive':
                if current_time - last_read_time >= READ_INTERVAL:
                    send_frame(ser, CMD_READ)
                    last_read_time = current_time

            # === 接收并处理所有可用数据 ===
            if ser.in_waiting > 0:
                raw = ser.read(ser.in_waiting)
                print(f"[RX] {bytes_to_hex_str(raw)}")
                buffer.extend(list(raw))

                # 尝试从buffer中提取完整帧
                while len(buffer) >= 9:
                    if buffer[0] == 0xFF:
                        candidate = buffer[:9]
                        co = parse_response(candidate)
                        if co is not None:
                            ts = time.strftime('%Y-%m-%d %H:%M:%S')
                            mode_str = "主动" if WORK_MODE == 'active' else "被动"
                            print(f"✅ [{ts}] [{mode_str}模式] CO 浓度: {co} ppm")
                            # 写入日志文件
                            log_entry = f"{ts},{co}\n"
                            with open('read_co_log.txt', 'a', encoding='utf-8') as log_file:
                                log_file.write(log_entry)
                            buffer = buffer[9:]
                        else:
                            print("⚠️ 帧解析失败，跳过首字节重新同步")
                            buffer.pop(0)
                    else:
                        buffer.pop(0)  # 丢弃非起始字节

            else:
                time.sleep(0.01)

    except serial.SerialException as e:
        print(f"🚨 串口错误: {e}")
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
    except KeyboardInterrupt:
        print("\n🛑 用户中断程序")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("🔌 串口已关闭")

if __name__ == "__main__":
    main()
