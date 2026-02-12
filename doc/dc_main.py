from machine import Pin
from machine import ExtInt
from machine import UART
from machine import RTC
from umqtt import MQTTClient
from misc import Power
import utime
import ujson
import modem
import sim
import net
import pm
import checkNet
import quecgnss
import log
import _thread
import dataCall
import cellLocator
import app_fota


################################# USR CONFIG#######################################
USR_CONFIG_UART_RX_TIMEOUT_MS = 500
USR_CONFIG_SW_VERSION = 1014           #app程序也就是本文件main.py的版本，！！！不要去改变这个变量的名称，因为云端服务器会提取这个变量的值用于FOTA版本判断
USR_CONFIG_BASE_LOC_TIMEOUT_SEC =10    #基站定位等待超时时间，单位秒
USR_CONFIG_LOWPOWER_MODE =1            #低功耗模式，1开启，0关闭
USR_CONFIG_DEFAULT_IMEI = '999999999999999'
################################## MODBUS #########################################
# 功能码
READ_COILS = 0x01  # 读线圈
READ_DISCRETE_INPUTS = 0x02  # 读离散量输入
READ_HOLDING_REGISTERS = 0x03  # 读保持寄存器
READ_INPUT_REGISTERS = 0x04  # 读输入寄存器
WRITE_SINGLE_COIL = 0x05  # 写单个线圈
WRITE_SINGLE_REGISTER = 0x06  # 写单个寄存器
READ_EXCEPTION_STATUS = 0x07  # 读取异常状态
DIAGNOSTICS = 0x08  # 诊断
GET_COM_EVENT_COUNTER = 0x0B  # 获取com事件计数器
GET_COM_EVENT_LOG = 0x0C  # 获取com事件LOG
WRITE_MULTIPLE_COILS = 0x0F  # 写多个线圈
WRITE_MULTIPLE_REGISTERS = 0x10  # 写多个寄存器
REPORT_SERVER_ID = 0x11  # 报告服务器ID
READ_FILE_RECORD = 0x14  # 读文件记录
WRITE_FILE_RECORD = 0x15  # 写文件记录
MASK_WRITE_REGISTER = 0x16  # 屏蔽写寄存器
READ_WRITE_MULTIPLE_REGISTERS = 0x17  # 读/写多个寄存器
READ_FIFO_QUEUE = 0x18  # 读取FIFO队列
READ_DEVICE_IDENTIFICATION = 0x2B  # 读设备识别码

# 异常码
ILLEGAL_FUNCTION = 0x01  # 非法功能
ILLEGAL_DATA_ADDRESS = 0x02  # 非法数据地址
ILLEGAL_DATA_VALUE = 0x03  # 非法数据值
SERVER_DEVICE_FAILURE = 0x04  # 从站设备故障
ACKNOWLEDGE = 0x05  # 确认
SERVER_DEVICE_BUSY = 0x06  # 从属设备忙
MEMORY_PARITY_ERROR = 0x08  # 存储奇偶性差错
GATEWAY_PATH_UNAVAILABLE = 0x0A  # 不可用网关路径
DEVICE_FAILED_TO_RESPOND = 0x0B  # 网关目标设备响应失败

# PDU 常量表
CRC_LENGTH = 0x02  # CRC长度
ERROR_BIAS = 0x80  # 错误基数
RESPONSE_HDR_LENGTH = 0x02  # 响应HDR长度
ERROR_RESP_LEN = 0x05  # 错误注册长度
FIXED_RESP_LEN = 0x08  # 固定注册长度
MBAP_HDR_LENGTH = 0x07  # HDR包头长度
#############################校验#################################################
CRC16_TABLE = (
    0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241, 0xC601,
    0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440, 0xCC01, 0x0CC0,
    0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40, 0x0A00, 0xCAC1, 0xCB81,
    0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841, 0xD801, 0x18C0, 0x1980, 0xD941,
    0x1B00, 0xDBC1, 0xDA81, 0x1A40, 0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01,
    0x1DC0, 0x1C80, 0xDC41, 0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0,
    0x1680, 0xD641, 0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081,
    0x1040, 0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
    0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441, 0x3C00,
    0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41, 0xFA01, 0x3AC0,
    0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840, 0x2800, 0xE8C1, 0xE981,
    0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41, 0xEE01, 0x2EC0, 0x2F80, 0xEF41,
    0x2D00, 0xEDC1, 0xEC81, 0x2C40, 0xE401, 0x24C0, 0x2580, 0xE541, 0x2700,
    0xE7C1, 0xE681, 0x2640, 0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0,
    0x2080, 0xE041, 0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281,
    0x6240, 0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
    0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41, 0xAA01,
    0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840, 0x7800, 0xB8C1,
    0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41, 0xBE01, 0x7EC0, 0x7F80,
    0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40, 0xB401, 0x74C0, 0x7580, 0xB541,
    0x7700, 0xB7C1, 0xB681, 0x7640, 0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101,
    0x71C0, 0x7080, 0xB041, 0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0,
    0x5280, 0x9241, 0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481,
    0x5440, 0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
    0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841, 0x8801,
    0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40, 0x4E00, 0x8EC1,
    0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41, 0x4400, 0x84C1, 0x8581,
    0x4540, 0x8701, 0x47C0, 0x4680, 0x8641, 0x8201, 0x42C0, 0x4380, 0x8341,
    0x4100, 0x81C1, 0x8081, 0x4040
)



#定义参数和寄存器关系
#保持寄存器
REG_ADDR_HOLD_POWER_ONOFF_TOTAL = 0x3000  # 开关机(总)
REG_ADDR_HOLD_POWER_ONOFF_DC = 0x3001     # 开关DC
REG_ADDR_HOLD_POWER_ONOFF_AC = 0x3002     # 开关AC
REG_ADDR_HOLD_POWER_ONOFF_LIGHT = 0x3003  # 开关LIGHT
REG_ADDR_HOLD_GPS_ONOFF = 0x3004          # GPS开关
REG_ADDR_HOLD_LED_BRIGHTNESS = 0x3005      # LED亮度
# 从0x3006到0x300F为预留参数段

#输入寄存器
REG_ADDR_INPUT_FIRMWARE_VERSION = 0x3100  # 版本号
REG_ADDR_INPUT_CHARGING_POWER = 0x3101    # 充电功率
REG_ADDR_INPUT_FULL_CHARGE_DURATION = 0x3102  # 充满时长
REG_ADDR_INPUT_DISCHARGE_POWER = 0x3103    # 放电功率
REG_ADDR_INPUT_DISCHARGE_DURATION = 0x3104  # 放电时长
REG_ADDR_INPUT_CURRENT_BATTERY_LEVEL = 0x3105  # 现有电量
# REG_ADDR_INPUT_LATITUDE_SIGN = 0x3106       # 纬度数据正负
# REG_ADDR_INPUT_LATITUDE_DATA_PART1 = 0x3107 # 纬度定位数据1
# REG_ADDR_INPUT_LATITUDE_DATA_PART2 = 0x3108 # 纬度定位数据2
# REG_ADDR_INPUT_LATITUDE_DATA_PART3 = 0x3109 # 纬度定位数据3
# REG_ADDR_INPUT_LONGITUDE_SIGN = 0x310A      # 经度数据正负
# REG_ADDR_INPUT_LONGITUDE_DATA_PART1 = 0x310B # 经度定位数据1
# REG_ADDR_INPUT_LONGITUDE_DATA_PART2 = 0x310C # 经度定位数据2
# REG_ADDR_INPUT_LONGITUDE_DATA_PART3 = 0x310D # 经度定位数据3
REG_ADDR_INPUT_LED_BRIGHTNESS_STATUS = 0x310E  # LED亮度状态
REG_ADDR_INPUT_CURRENT_STATUS_BITS = 0x310F   # 各功能部分当前状态(位)
REG_ADDR_INPUT_FAULT_CODE = 0x3110            # 故障码
# ... 0x3110 至 0x301F 为备用显示参数1~16，

#定义保持寄存器参数字典
g_modbus_hold_paras_dic = {
    0x3000: {"name": "power_onoff_total", "unit": None, "value": 0,"setflag":False},
    0x3001: {"name": "power_onoff_dc", "unit": None, "value": 0,"setflag":False},
    0x3002: {"name": "power_onoff_ac", "unit": None, "value": 0,"setflag":False},
    0x3003: {"name": "power_onoff_light", "unit": None, "value": 0,"setflag":False},
    0x3004: {"name": "gps_onoff", "unit": None, "value": 0,"setflag":False},
    0x3005: {"name": "led_brightness", "unit": "%", "value": 0,"setflag":False},
}

#定义输入寄存器参数字典
g_modbus_input_paras_dic = {
    0x3100: {"name": "firmware_version", "unit": "N/A", "value": 0},
    0x3101: {"name": "charging_power", "unit": "W", "value": 0},
    0x3102: {"name": "full_charge_duration", "unit": "HHMM", "value": 0},
    0x3103: {"name": "discharge_power", "unit": "W", "value": 0},
    0x3104: {"name": "discharge_duration", "unit": "HHMM", "value": 0},
    0x3105: {"name": "current_battery_level", "unit": "%", "value": 0},
    #经纬度由EC800M内部获取，不需要经过modbus，读的时候注意这里寄存器地址的非连续
    # 0x3106: {"name": "latitude_sign", "unit": "N/A", "value": 0}, #EC800M模块内部获取，不需要modbus
    # 0x3107: {"name": "latitude_data_part1", "unit": "N/A", "value": 0},
    # 0x3108: {"name": "latitude_data_part2", "unit": "N/A", "value": 0},
    # 0x3109: {"name": "latitude_data_part3", "unit": "N/A", "value": 0},
    # 0x310A: {"name": "longitude_sign", "unit": "N/A", "value": 0},
    # 0x310B: {"name": "longitude_data_part1", "unit": "N/A", "value": 0},
    # 0x310C: {"name": "longitude_data_part2", "unit": "N/A", "value": 0},
    # 0x310D: {"name": "longitude_data_part3", "unit": "N/A", "value": 0},
    0x310E: {"name": "led_brightness_status", "unit": "%", "value": 0},
    0x310F: {"name": "current_status_bits", "unit": "N/A", "value": 0},
    0x3110: {"name": "fault_code", "unit": "N/A", "value": 0},
#     0x3111: {"name":"reserved1","unit":"N/A","value":0},
#     0x3112: {"name":"reserved2","unit":"N/A","value":0},
#     0x3113: {"name":"reserved3","unit":"N/A","value":0}, 
}
#声明经度纬度变量
longitude=0
latitude=0
loc_state='V' #V表示没有定位，A表示GPS定位成功，B表示基站定位成功
#参数被mqtt下发控制更改标志
hold_reg_change_flag=False
#rtc全局变量
rtc=RTC()
day=0
month=0
year=0
hour=0
minute=0
second=0
imei_str=USR_CONFIG_DEFAULT_IMEI
pack_sn=0
#################################modbus初始化############################################
class ModbusInit:
    def __init__(self, uartport, baudrate, databits, parity, stopbit, flowctl):
        self.uart = UART(uartport, baudrate, databits, parity, stopbit, flowctl)

    @staticmethod
    def divmod_low_high(addr):  # 分离高低字节
        high, low = divmod(addr, 0x100)
        # Grey_log.debug("addr:0x{:04X}  high:0x{:02X}  low:0x{:02X}".format(addr, high, low))
        return high, low

    def calc_crc(self, string_byte):  # 生成CRC
        crc = 0xFFFF
        for pos in string_byte:
            crc ^= pos
            for i in range(8):
                if (crc & 1) != 0:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        gen_crc = hex(((crc & 0xff) << 8) + (crc >> 8))
        int_crc = int(gen_crc, 16)
        return self.divmod_low_high(int_crc)

    @staticmethod
    def split_return_bytes(ret_bytes):  # 转换二进制
        ret_str = binascii.hexlify(ret_bytes, ',')  # 二进制转字符串, 以','分隔.
        return ret_str.split(b",")  # 转换为列表, 以','分隔.

    # def read_uart(self):  # UART接收
    #     num = self.uart.any()
    #     msg = self.uart.read(num)
    #     # Grey_log.debug('UART接收数据: ')
    #     # for i in range(num):
    #     #     Grey_log.debug('0x{:02X}'.format(msg[i]))
    #     # ret_str = binascii.hexlify(msg, ',')  # 二进制转字符串, 以','分隔.
    #     ret_list = []
    #     for byte in msg:
    #         ret_list.append(byte)

    #     # 使用列表推导式和 format 函数将每个字节转换为十六进制格式，并用空格分隔
    #     hex_str = ' '.join(['{:02X}'.format(byte) for byte in ret_list])

    #     # 打印转换后的十六进制字符串
    #     print('UART接收数据(HEX): ' + hex_str)
        
    #     return ret_list
    def read_uart(self, timeout_ms):
        """
        UART接收数据，增加超时参数。
        
        :param timeout_ms: 超时时间，单位为毫秒
        :return: 接收到的数据列表
        """
        start_time = utime.ticks_ms()  # 获取当前的毫秒时间
        num = 0
        rx_data = []
        
        # 超时循环，等待数据
        while utime.ticks_diff(utime.ticks_ms(), start_time) < timeout_ms:
            num = self.uart.any()  # 检查是否有数据可读
            if num > 0:
                break  # 如果有数据，跳出循环
            utime.sleep_ms(1)  # 减少CPU占用，每次检查间隔1ms

        if num > 0:
            msg = self.uart.read(num)  # 读取数据
            # 将数据转换为十六进制字符串
            hex_str = ' '.join(['{:02X}'.format(byte) for byte in msg])
            
            
            # 等待1ms读取剩余数据
            utime.sleep_ms(1)
            additional_num = self.uart.any()
            if additional_num > 0:
                # 如果还有数据，追加到msg
                msg.extend(self.uart.read(additional_num))
            print('UART接收数据(HEX): ' + hex_str)
            
            return msg
        else:
            print("Timeout occurred, no data received.")
            return rx_data

    def write_coils(self, slave, const, start, coil_qty):  # UART发送
        start_h, start_l = self.divmod_low_high(start)
        coil_qty_h, coil_qty_l = self.divmod_low_high(coil_qty)
        data = bytearray([slave, const, start_h, start_l, coil_qty_h, coil_qty_l])
        # Grey_log.debug(data)
        crc = self.calc_crc(data)
        # Grey_log.debug("crc_high:0x{:02X}  crc_low:0x{:02X}".format(crc[0], crc[1]))
        for num in crc:
            data.append(num)
        self.uart.write(data)
        # Grey_log.debug('UART发送数据: ')
        # dataLen = len(data)
        # for i in range(dataLen):
        #     Grey_log.debug('0x{:02X}'.format(data[i]))
        ret_str = self.split_return_bytes(data)
        # 使用列表推导式和 format 函数将每个字节转换为十六进制格式，并用空格分隔
        hex_str = ' '.join(['{:02X}'.format(byte) for byte in ret_str])

        # 打印转换后的十六进制字符串
        print('UART发送数据(HEX): ' + hex_str)
        return True
    
    def write_hold(self,slave,cmd,reg_addr,value):
        addr_h,addr_l = self.divmod_low_high(reg_addr)
        value_h,value_l = self.divmod_low_high(value)
        data = bytearray([slave,cmd,addr_h,addr_l,value_h,value_l])
        crc = self.calc_crc(data)
        for num in crc:
            data.append(num)
        self.uart.write(data)
        # 使用列表推导式和 format 函数将每个字节转换为十六进制格式，并用空格分隔
        hex_str = ' '.join(['{:02X}'.format(byte) for byte in data])
        # 打印转换后的十六进制字符串
        print('UART发送数据(HEX): ' + hex_str)
        
        # 等待并读取响应, 正常响应数据和发送数据一样，异常时返回命令为0x80+cmd
        response = self.read_uart(USR_CONFIG_UART_RX_TIMEOUT_MS)
        if response:
            # 解析响应数据
            #返回指令判断
            response_cmd=response[1]
            if response_cmd == (cmd | 0x80):
                print("write hold fail!")
                return None
            
            if (len(response)) <= (len(data)):
                #解析地址
                ack_addr = (response[2] << 8) + response[3]
                #解析值
                ack_value = (response[4] << 8) + response[5]       

                # 打印寄存器地址和对应的返回值               
                print("Register 0x{:04X}: Value 0x{:04X}".format(ack_addr, ack_value))
                
                if ack_addr != reg_addr:       
                    print("write hold: ack addr check fail!")
                    
                if ack_value != value:
                    print("write hold: ack value fail!")    
            else:
                print("write hold: ack reponse length err.")
            
        else:
            print("No response received from UART.")
        
        
    def query_multiple_registers(self, slave_id, cmd, start_address, quantity):
        """
        查询多个寄存器的值，并更新全局变量。
        :param slave_id: 从机地址
        :param start_address: 起始寄存器地址
        :param quantity: 要读取的寄存器数量
        :return: 寄存器值列表
        """
        start_addr_h, start_addr_l = self.divmod_low_high(start_address)
        quantity_h, quantity_l = self.divmod_low_high(quantity)

        # 构造查询请求
        data = bytearray([
            slave_id, 
            cmd, 
            start_addr_h, 
            start_addr_l, 
            quantity_h, 
            quantity_l
        ])
        # 计算CRC并发送请求
        crc = self.calc_crc(data)
#         print("crc_high:0x{:02X}  crc_low:0x{:02X}".format(crc[0], crc[1]))
        for num in crc:
            data.append(num)
        #data.extend(crc)  # 将CRC值附加到数据末尾
        self.uart.write(data)
#         print("query_multiple_registers send:\r\n")   
        # 使用列表推导式和 format 函数将每个字节转换为十六进制格式，并用空格分隔
        hex_str = ' '.join(['{:02X}'.format(byte) for byte in data])

        # 打印转换后的十六进制字符串
        print('UART发送数据(HEX): ' + hex_str)
        
        # 等待并读取响应
        response = self.read_uart(USR_CONFIG_UART_RX_TIMEOUT_MS)
        if response:
            # 解析响应数据
            # ADDR对比
            if response[0] != slave_id:
                print("addr error! Get uart again!")
                response = self.read_uart(USR_CONFIG_UART_RX_TIMEOUT_MS)
                if response is None:
                    return None
            # cmd 对比
            if response[1] != cmd:
                print("cmd error! Get uart again!")
                response = self.read_uart(USR_CONFIG_UART_RX_TIMEOUT_MS)
                if response is None:
                    return None
                if response[1] != cmd:
                    print("cmd error! return!")
                    return None
                
            # response_length = (response[3] << 8) + response[4]  # 响应数据的长度，不包括CRC校验
            response_length = response[2]
#             print("len of response={}".format(len(response)))
#             print("response_length={}".format(response_length))
            
            if response_length + 5 == len(response):  # 检查响应长度是否正确
                register_values = []
                for i in range(3, 3 + response_length, 2):
                    register_value = (response[i] << 8) + response[i + 1]
                    register_values.append(register_value)

                # 打印寄存器地址和对应的返回值
                for reg_index, value in enumerate(register_values):
                    reg_addr = start_address + reg_index
#                     print("Register 0x{:04X}: Value 0x{:04X}".format(reg_addr, value))
                return register_values
            else:
                print("Response length is incorrect or response is empty.")
        else:
            print("No response received from UART.")

            










# RS485串口信息,EC800, uart2=main_uart
_uartport = UART.UART2  # 串口
_baudrate = 115200  # 波特率
_databits = 8  # 数据位
_parity = 0  # 偶校验
_stopbit = 1  # 停止位
_flowctl = 0  # 流控

SLAVE_ID =0X0F #电池从机地址
HOLD_REG_CNT= 6 #保持寄存器数量
HOLD_REG_ADDR_START = REG_ADDR_HOLD_POWER_ONOFF_TOTAL #保持寄存器起始地址

INPUT_REG_CNT1=6 #第一段输入寄存器数量，因为中间有一部分是经纬度寄存器，从机不支持读取，所以输入寄存器被分成了两段
INPUT_REG_ADDR_START1 = REG_ADDR_INPUT_FIRMWARE_VERSION #第一段输入寄存器起始地址

INPUT_REG_CNT2=3 #第二段输入寄存器数量
INPUT_REG_ADDR_START2 = REG_ADDR_INPUT_LED_BRIGHTNESS_STATUS #第二段输入寄存器起始地址

###################外部中断###############################################
def Extfun(args):#外部中断，进行项目停止的
    global flag
    flag=1
    print('### interrupt  {} ###'.format(args)) # args[0]:gpio号 args[1]:上升沿或下降沿
    print(flag)
extint = ExtInt(ExtInt.GPIO27, ExtInt.IRQ_FALLING, ExtInt.PULL_PU, Extfun)#定义外部中断
extint.enable()
###################modbus 初始化########################################################


RS=Pin(Pin.GPIO10, Pin.OUT,Pin.PULL_DISABLE , 1)##设置485输出高电平，发数据

modbus = ModbusInit(_uartport, _baudrate, _databits, _parity, _stopbit, _flowctl)

#################### net 初始化###############################
netstatus=[0,0]#网络状态信息，分别代表存储卡信息和注册网络情况
sim_retry=0
SIM_RETRY_MAX = 30
while True:
    sim_retry+=1
    if sim_retry > SIM_RETRY_MAX:
        print("sim retry timeout!")
        break
    
    simnum=sim.getImsi()#获取卡号信息
    
    # 使用正则表达式检查 simnum 中是否包含至少一个数字
    # if simnum and str(simnum).strip():
    if '460' in str(simnum):
        print ('simcard is ok')
        netstatus[0]=1
        print("Sim Card OK!")   
        print("IMSI:",simnum)
        break
    else:
        print ('simcard is error')
        netstatus[0]=0
    utime.sleep(1)  # 等待1秒
   

iccid=sim.getIccid()#读取卡号
if iccid and iccid != "":
    print("ICCID:",iccid)
else:
    print("ICCID get fail!")
    
imei=modem.getDevImei()#读取imei
if imei and imei != "":
    print("IMEI:",imei)
    imei_str=imei
else:
    print("IMEI get fail!")
print("stagecode: 1 - 正在检测SIM卡状态； 2 - 正在检测网络注册状态； 3 - 正在检测PDP Context激活状态。")
print("subcode: stage = 3时，state表示PDP Context激活状态，0表示没有激活成功，1表示激活成功。")
print("stage = 2时，state表示网络注册状态，0-没有注册，MT也没有再搜索,1-注册完成，本地网络,2-没有注册，但是MT在尝试搜索,3-拒绝注册")
if netstatus[0]==1:#表明获取到卡了
    stagecode, subcode = checkNet.wait_network_connected(20)#这个是阻塞的，必须网络成功之后，才会进入下一步
    print('\r\n--------\r\nstagecode = {}, subcode = {}'.format(stagecode, subcode))
    if stagecode==3 and subcode==1:#表明网络正常，可以进行数据推送
        print('net is ok\r\n--------\r\n')
        netstatus[1]=1
    else:
        print('net is error\r\n--------\r\n')
        netstatus[1]=0
    utime.sleep(1)  # 等待1秒
    
print("\r\n--------")        
print("net state:",net.getState())
print("csq:",net.csqQueryPoll())        
print("operator:",net.operatorName())
print("--------\r\n")

#连上网之后，从基站读时间
nt_result=net.nitzTime()
print(nt_result)
# 检查nt_result是否为元组
# 
if isinstance(nt_result, tuple) and len(nt_result) > 0:
    # 提取时间信息的字符串
    time_str = nt_result[0]
    print("base time: {}".format(time_str))
    
    # 检查时间字符串是否为空
    if time_str.strip() != "":
        # 分割字符串以获取日期、时间和时区
        date_str, time_str, tz_str, _ = time_str.split()   
#     print(date_str)
#     print(time_str)
#     print(tz_str)
        # 进一步分割日期和时间以获取单独的组成部分
        year = int(date_str[0:2])+2000  # 2-digit year, 需要根据实际情况可能要转换为四位数
        month = int(date_str[3:5])
        day = int(date_str[-2:])        #-2表示截取末尾两位

        hour = int(time_str[0:2])
        minute = int(time_str[3:5])
        second = int(time_str[-2:])

        # 时区是东八区，即UTC+8
        timezone_offset = int(tz_str)
        hour+=timezone_offset
        
        #week在设置时间时不起作用，填0即可
        week=0
        microsecond=0
        print("base time: {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(year, month, day, hour, minute, second))
        if False:
            if year != 2000 : #年份有正常值  
                print("update base time: {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(year, month, day, hour, minute, second))
                if rtc is not None:
                    ret=rtc.datetime([year, month, day, week, hour, minute, second, microsecond])
                    ret_str = "suc" if ret == 0 else "fail"
                    print("set time {}!".format(ret_str))
                else:
                    print("rtc instance is null. Cancel base time update.")
            else : #时间错误
                print("time err:{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(year, month, day, hour, minute, second))
                print("Cancel base time update.")
    else:
        print("Time string is empty, cannot split.")
else:
    #获取失败返回-1
    print("get base time fail or NITZ time is not a tuple.")
    
#基站定位，0-成功，-1-失败
def loc_by_base():
    global longitude,latitude,loc_state
    ret=0
    base_loc=cellLocator.getLocation("www.queclocator.com", 80, "1Aj721iw35y0j842", USR_CONFIG_BASE_LOC_TIMEOUT_SEC,1)
#     print("cellLocator.getLocation ret:{}".format(base_loc))
    if isinstance(base_loc, tuple) : #判断是否为元组
#         print("base_loc is a tuple.")
        if base_loc[0] != 0.0: #有值
            # 解析元组中的参数
            longitude = base_loc[0]  # 经度
            latitude = base_loc[1]   # 纬度
            if len(base_loc) >= 3: #存在第3个元素才解析误差
                error = base_loc[2]      # 误差
            loc_state = 'B' #B表示基站定位成功
            print("基站定位成功，坐标：(",longitude,",",latitude,"),误差：",error,"米")
            ret= 0
        else: #没值，获取失败
            loc_state = 'V'
            print("基站定位失败，没有获取到坐标！ret={}".format(base_loc))
            ret= -1
    else:  #基站定位也失败了
        loc_state='V'
        print("基站定位失败，模块返回错误！ret={}".format(base_loc))
        ret= -1
        
    return ret
#########################MQTT自定义类以及上电后需要运行的代码#####################################

# 调用disconnect后会通过该状态回收线程资源
TaskEnable = True
# 设置日志输出级别
log.basicConfig(level=log.INFO)
mqtt_log = log.getLogger("MQTT")


# 封装mqtt，使其可以支持更多自定义逻辑
class MqttClient():
    '''
    mqtt init
    '''

    # 说明：reconn该参数用于控制使用或关闭umqtt内部的重连机制，默认为True，使用内部重连机制。
    # 如需测试或使用外部重连机制可参考此示例代码，测试前需将reconn=False,否则默认会使用内部重连机制！
    def __init__(self, clientid, server, port, user=None, password=None, keepalive=0, ssl=False, ssl_params={},
                 reconn=False):
        self.__clientid = clientid
        self.__pw = password
        self.__server = server
        self.__port = port
        self.__uasename = user
        self.__keepalive = keepalive
        self.__ssl = ssl
        self.__ssl_params = ssl_params
        self.topic = None
        self.qos = None
        # 网络状态标志
        self.__nw_flag = True
        # 创建互斥锁
        self.mp_lock = _thread.allocate_lock()
        # 创建类的时候初始化出mqtt对象
        self.client = MQTTClient(self.__clientid, self.__server, self.__port, self.__uasename, self.__pw,
                                 keepalive=self.__keepalive, ssl=self.__ssl, ssl_params=self.__ssl_params,
                                 reconn=reconn)

    def connect(self):
        '''
        连接mqtt Server
        '''
        self.client.connect()
        # 注册网络回调函数，网络状态发生变化时触发
        flag = dataCall.setCallback(self.nw_cb)
        if flag != 0:
            # 回调注册失败
            raise Exception("Network callback registration failed")

    def set_callback(self, sub_cb):
        '''
        设置mqtt回调消息函数
        '''
        self.client.set_callback(sub_cb)

    def error_register_cb(self, func):
        '''
        注册一个接收umqtt内线程异常的回调函数
        '''
        self.client.error_register_cb(func)

    def subscribe(self, topic, qos=0):
        '''
        订阅Topic
        '''
        self.topic = topic  # 保存topic ，多个topic可使用list保存
        self.qos = qos  # 保存qos
        self.client.subscribe(topic, qos)

    def publish(self, topic, msg, qos=0):
        '''
        发布消息
        '''
        self.client.publish(topic, msg, qos)

    def disconnect(self):
        '''
        关闭连接
        '''
        global TaskEnable
        # 关闭wait_msg的监听线程
        TaskEnable = False
        # 关闭之前的连接，释放资源
        self.client.disconnect()

    def reconnect(self):
        '''
        mqtt 重连机制(该示例仅提供mqtt重连参考，根据实际情况调整)
        PS：1.如有其他业务需要在mqtt重连后重新开启，请先考虑是否需要释放之前业务上的资源再进行业务重启
            2.该部分需要自己根据实际业务逻辑添加，此示例只包含mqtt重连后重新订阅Topic
        '''
        # 判断锁是否已经被获取
        if self.mp_lock.locked():
            return
        self.mp_lock.acquire()
        # 重新连接前关闭之前的连接，释放资源(注意区别disconnect方法，close只释放socket资源，disconnect包含mqtt线程等资源)
        self.client.close()
        # 重新建立mqtt连接
        while True:
            net_sta = net.getState()  # 获取网络注册信息
            if net_sta != -1 and net_sta[1][0] == 1:
                call_state = dataCall.getInfo(1, 0)  # 获取拨号信息
                if (call_state != -1) and (call_state[2][0] == 1):
                    try:
                        # 网络正常，重新连接mqtt
                        self.connect()
                    except Exception as e:
                        # 重连mqtt失败, 5s继续尝试下一次
                        self.client.close()
                        utime.sleep(5)
                        continue
                else:
                    # 网络未恢复，等待恢复
                    utime.sleep(10)
                    continue
                # 重新连接mqtt成功，订阅Topic
                try:
                    # 多个topic采用list保存，遍历list重新订阅
                    if self.topic is not None:
                        self.client.subscribe(self.topic, self.qos)
                    self.mp_lock.release()
                except:
                    # 订阅失败，重新执行重连逻辑
                    self.client.close()
                    utime.sleep(5)
                    continue
            else:
                utime.sleep(5)
                continue
            break  # 结束循环
        # 退出重连
        return True

    def nw_cb(self, args):
        '''
        dataCall 网络回调
        '''
        nw_sta = args[1]
        if nw_sta == 1:
            # 网络连接
            mqtt_log.info("*** network connected! ***")
            self.__nw_flag = True
        else:
            # 网络断线
            mqtt_log.info("*** network not connected! ***")
            self.__nw_flag = False

    def __listen(self):
        while True:
            try:
                if not TaskEnable:
                    break
                self.client.wait_msg()
            except OSError as e:
                # 判断网络是否断线
                if not self.__nw_flag:
                    # 网络断线等待恢复进行重连
                    self.reconnect()
                # 在socket状态异常情况下进行重连
                elif self.client.get_mqttsta() != 0 and TaskEnable:
                    self.reconnect()
                else:
                    # 这里可选择使用raise主动抛出异常或者返回-1
                    return -1

    def loop_forever(self):
        _thread.start_new_thread(self.__listen, ())
        
    # 发布数据到MQTT服务器
    def publish_data_to_mqtt(self):
        global pack_sn
        pack_sn+=1
        if pack_sn >= 255:
            pack_sn=1
        # 创建MQTT客户端
    #     client = umqtt.MQTTClient(client_id=MQTT_CLIENT_ID, server=MQTT_SERVER, port=MQTT_PORT,
    #                               user=MQTT_USER, password=MQTT_PASSWORD)
        
        # 设置自动重连
    #     client.reconn = True

        # 连接到MQTT服务器
    #     client.connect(clean_session=True)

        # 订阅主题（如果有需要）
    #     client.subscribe('test/topic_cmd', qos=0)
        
        
        # 定义上报数据的函数
        def prepare_data():
            # 组合保持寄存器和输入寄存器的值
    #         data = {}
    #         data.update(g_modbus_hold_paras_dic)  # 更新字典
    #         data.update(g_modbus_input_paras_dic)  # 更新字典
            global latitude,longitude,imei_str,pack_sn #声明引入全局变量
            # 假设 g_modbus_hold_paras_dic 和 g_modbus_input_paras_dic 是已经存在的字典
            hold_registers = g_modbus_hold_paras_dic
            input_registers = g_modbus_input_paras_dic

            # 提取所需的字段
            hold_data = {params['name']: params['value'] for name, params in hold_registers.items()}
            input_data = {params['name']: params['value'] for name, params in input_registers.items()}

            # 合并两个字典,Python3.5以上才支持**hold_data方式解包字典
    #         combined_data = {**hold_data, **input_data}
            combined_data={}
            combined_data.update(hold_data)
            combined_data.update(input_data)
            
            #添加经纬度
            combined_data['latitude'] = latitude
            combined_data['longitude'] = longitude
            combined_data['loc_state'] = loc_state
            #添加app软件版本
            combined_data['sw_ver'] = USR_CONFIG_SW_VERSION
            #添加包序
            combined_data['pack_sn'] = pack_sn
            #添加imei
            combined_data['imei'] = imei_str

            # 将合并后的字典转换为JSON格式
    #         json_data = ujson.dumps(combined_data)

            
            # 将字典转换为JSON字符串进行上报
            return ujson.dumps(combined_data).encode('utf-8')
        

        # 发布数据到MQTT服务器之前，检查client是否为None
        if self.client is None:
            print("MQTT client is not initialized.")
        else:
            try:
                # 定义上报数据的函数
                data_to_publish = prepare_data()
                if imei_str == USR_CONFIG_DEFAULT_IMEI:
                    print("\r\n#####IMEI usr default: {}.#######\r\n".format(USR_CONFIG_DEFAULT_IMEI))
                topic_up='topic_up/{}'.format(imei_str)
                topic_up_str=topic_up.encode('utf-8')
                self.client.publish(topic_up_str, data_to_publish)  # 发布数据到指定的topic
                print("Data published to MQTT broker,Topic is :", topic_up_str)
                print(data_to_publish)
            except Exception as e:
                print("Failed to publish data to MQTT broker:", e)
            
        # 等待消息（如果有订阅）
        # client.wait_msg()

        # 断开连接
    #     client.disconnect()

#自定义错误回调
def err_cb(error):
        '''
        接收umqtt线程内异常的回调函数
        '''
        mqtt_log.info(error)
        c.reconnect() # 可根据异常进行重连
#下发命令解析        
def process_mqtt_message(json_str):
    try:
        # 将JSON字符串解析为字典
        message_dict = ujson.loads(json_str)
        
        global hold_reg_change_flag  # 在函数内部声明全局变量
        
        # 遍历解析后的字典中的每个参数
        for name, value in message_dict.items():
            # 遍历g_modbus_hold_paras_dic字典以找到寄存器地址
            for reg_addr, params in g_modbus_hold_paras_dic.items():
                if params['name'] == name:
                    # 检查值是否与当前值不同
                    if params['value'] != value:
                        # 打印更新信息
                        print("参数 '%s' 更新为 %d" % (name,value))
                        # 更新字典中的值
                        g_modbus_hold_paras_dic[reg_addr]['value'] = value
                        g_modbus_hold_paras_dic[reg_addr]['setflag'] = True#置位配置标志
                        hold_reg_change_flag=True
                        # 这里添加您的控制代码，例如发送更新到硬件等
                        # update_hardware(reg_addr, value)
                    break  # 找到匹配项后退出循环
            else:
                print("未找到参数 '%s'" % name)

    except json.JSONDecodeError as e:
        print("解析JSON失败: '%s'" % e)
    except Exception as e:
        print("处理MQTT消息失败: '%s'" % e)      
# MQTT订阅回调函数（收到消息后的回调）
def sub_cb(topic, msg):
    print("Received message: ", msg.decode('utf-8'), "from topic: ", topic)
    process_mqtt_message(msg.decode('utf-8'))  # 解码消息并处理
    
# 创建MQTT客户端
# client = MQTTClient(client_id=MQTT_CLIENT_ID, server=MQTT_SERVER, port=MQTT_PORT,keepalive=60)
#  # 设置自动重连
# client.reconn = True
# 
# #配置回调
# client.set_callback(sub_callback)
# 
# # 连接到MQTT服务器
# client.connect(clean_session=True)
# 
# # 订阅主题（如果有需要）
# client.subscribe('test/topic_cmd', qos=0)

# MQTT服务器配置
MQTT_SERVER = '120.27.250.30'  # 替换为你的MQTT服务器IP或域名
MQTT_PORT = 1883  # MQTT端口，如果是MQTT over SSL/TLS，请改为8883
if netstatus[1] == 1:
    MQTT_CLIENT_ID=imei
else:
    MQTT_CLIENT_ID = 'quectel_client'  # 客户端ID，应该是唯一的
MQTT_USER = ''  # MQTT用户名，如果不需要认证则留空
MQTT_PASSWORD = ''  # MQTT密码，如果不需要认证则留空
c = MqttClient(MQTT_CLIENT_ID, MQTT_SERVER, MQTT_PORT, reconn=False)
# 设置消息回调
c.set_callback(sub_cb)
# 设置异常回调
c.error_register_cb(err_cb)
# 建立连接
c.connect()
# 订阅主题
topic_down="topic_down/{}".format(imei_str)
topic_down_str=topic_down.encode('utf-8')
c.subscribe(topic_down.encode('utf-8'))
print("订阅下行主题：",topic_down_str)
# mqtt_log.info("Connected to ", MQTT_SERVER, "subscribed to /test/topic_cmd.")
# 发布消息
# c.publish(b"/public/TEST/quecpython758", b"my name is Quecpython!")
# mqtt_log.info("Publish topic: /public/TEST/quecpython758, msg: my name is Quecpython")
# 监听mqtt消息
mqtt_log.info("start mqtt recv thread.")
c.loop_forever()
# 等待5s接收消息
# PS:如果需要测试重连，包括服务器断开连接等情况，请注释掉c.disconnect()和utime.sleep(5)
# utime.sleep(5)
# 关闭连接
# c.disconnect()

##########################GPS 初始化#####################
def gpsinit():
    ret = quecgnss.init()
    if ret == 0:
        print('GNSS init ok.')
        return 0
    else:
        print('GNSS init failed.')
        return -1
#gps开启，打开gps时不管之前状态都先初始化一次,初始化完自动打开
def gps_on():
    ret=gpsinit()
    if ret == 0:
        print('GNSS start ok.')
        return 0
    else:
        print('GNSS start failed.')
        return -1
#gps关闭
def gps_off():
    ret = quecgnss.gnssEnable(0)
    if ret == 0:
        print('GNSS stop ok.')
        return 0
    else:
        print('GNSS stop failed.')
        return -1
    
#gps解析函数
def parse_gnrmc(data):
    """
    解析GNRMC语句并返回GPS信息。
    
    :param data: 包含GNRMC语句的字符串。
    :return: 一个包含GPS信息的字典或者在未找到GNRMC语句时返回None。
    """
#     print("get gps string.")
    # 查找GNRMC语句
    gnrmc_prefix = 'GNRMC,'
    if gnrmc_prefix in data:
        # 字符串中只包含一个元组，我们需要取出其中的字符串部分
        gps_data_str = data
        # 使用split方法找到第一个$GNRMC
        start_index = gps_data_str.rfind('$GNRMC')

        if start_index != -1:
            #从$GNRMC开始，截取到字符串末尾
            gnrmc_sentence = gps_data_str[start_index:]

            # 现在我们需要找到这个语句的结束位置，即\r\n
            end_index = gnrmc_sentence.find('\r\n')

            # 如果找到了\r\n，就截取$GNRMC语句
            if end_index != -1:
                gnrmc_sentence = gnrmc_sentence[:end_index]
                print(gnrmc_sentence)
            else:
                print("End of GNRMC sentence not found.")
        else:
            print("Start of GNRMC sentence not found.")
            
        gnrmc_data = gnrmc_sentence.split(gnrmc_prefix)[1]  # 切分数据获取GNRMC部分
        fields = gnrmc_data.split(',')  # 按逗号分割字段,这里filelds从第一个时间开始了，没有GNRMC字符串

        # 检查数据字段是否足够
        if len(fields) >= 12:
            # 解析字段
            gps_info = {
                'validity': fields[1],  # 'A'表示有效定位，'V'表示无效定位
                'latitude': None if fields[2] == '' else float(fields[2]),#纬度
                'lat_dir': fields[3] if fields[3] != '' else None,#N_S
                'longitude': None if fields[4] == '' else float(fields[4]),#经度
                'lon_dir': fields[5] if fields[5] != '' else None,#W_E
                'speed': None if fields[6] == '' else float(fields[6]),
                'course': None if fields[7] == '' else float(fields[7]),
                'date': fields[8] if fields[8] != '' else None,  # 日期格式为DDMMYY
                'time': fields[0] if fields[0] != '' else None,  # 时间格式为HHMMSS
                'mode': fields[11] if fields[11] != '' else None  # 定位模式：A=自主定位, D=差分定位, E=估算, N=未定位, S=模拟/仿真
            }
            if gps_info['validity'] == 'A': #定位成功才打印
                for key, value in gps_info.items():
    #                 print(f"{key}: {value}")#python3.6以前版本不支持这个语法
                    print("{}: {}".format(key, value))
            
            return gps_info
        else:
            print("gps len ={}, <12!".format(len(fields)))
    else:
        print("NO GNRMC message!")
        
    return None

#定义GPS获取函数并返回解析结果
def get_gps_coordinates(quecgnss):
    """
    获取GPS坐标并返回经度和纬度。
    
    :param quecgnss: GPS模块的实例，提供get_state和read方法。
    :return: 一个包含经度和纬度的元组，如果未定位成功则返回None。
    """
    # 检查GPS状态
    if quecgnss.get_state() == 2:
        data = quecgnss.read(1024)  #返回的是一个元组，包含两个元素，第一个是数据长度1024，第二个才是GPS信息
#     if True: 
#         data=(1024, ',2,14,03,25,241,31,09,19,318,,16,78,336,,26,46,039,,0*6E\r\n$GPGSV,4,3,14,28,17,089,,199,,,37,42,37,126,,50,33,121,40,0*6B\r\n$GPGSV,4,4,14,40,25,246,,41,46,217,41,0*65\r\n$GBGSV,5,1,19,07,56,175,31,10,47,188,39,19,06,166,37,22,45,204,45,0*7A\r\n$GBGSV,5,2,19,29,24,132,41,01,32,123,,02,47,216,,04,19,111,,0*79\r\n$GBGSV,5,3,19,05,29,243,,06,65,030,,08,01,193,,09,62,346,,0*7A\r\n$GBGSV,5,4,19,13,08,204,,16,63,039,,21,45,286,,26,18,272,,0*7E\r\n$GBGSV,5,5,19,30,21,073,,36,40,049,,03,,,38,0*7F\r\n$GNVTG,,T,,M,0.199,N,0.368,K,A*31\r\n$GNRMC,134832.00,A,3127.32492,N,10443.09311,E,0.339,,190824,,,A,V*15\r\n$GNGGA,134832.00,3127.32492,N,10443.09311,E,1,10,1.45,599.4,M,,M,,*52\r\n$GNGSA,A,3,08,27,03,04,31,,,,,,,,2.45,1.45,1.97,1*05\r\n$GNGSA,A,3,07,10,19,22,29,,,,,,,,2.45,1.45,1.97,4*0D\r\n$GPGSV,4,1,14,04,54,313,17,08,19,186,38,27,42,158,37,31,43,067,32,0*6D\r\n$GPGSV,4,2,14,03,25,241,30,09,19,318,,16,78,336,,26,46,039,,0*6F\r\n$GPGSV,4,3,14,28,17,089,,199,,,36,42,37,126,,50,33,121,40,0*6A\r\n$GPGSV,4,4,14,40,25,246,,41,46,217,41,0*65\r\n$GBGSV,5,1,1')
        if isinstance(data,tuple):
#             if data[0] != 0:
#                 print(data)
            gps_string=data[1]
            gps_ret=parse_gnrmc(gps_string) #返回gps_info字典，包含所有需要的信息包括经纬度，速度等
            return gps_ret
        else:
            print("无GPS数据响应！")
        
    # 如果没有成功获取坐标，返回None
    return None

#定义GPS经纬度处理函数，转化为度
def convert_latitude(latitude, lat_dir):
    # 步骤1: 将纬度除以100，得到整数部分和小数部分
    lat_int = int(latitude // 100)  # 整数部分，度
    lat_dec = latitude % 100 /60 # 小数部分，转换为浮点数度

    # 步骤4: 合并整体度数
    total_latitude = lat_int + lat_dec

    # 步骤5: 根据lat_dir控制latitude的正负值
    if lat_dir.upper() == 'S':  # 如果纬度方向是南纬，取负值
        total_latitude = -abs(total_latitude)
    else:  # 否则，取正值
        total_latitude = abs(total_latitude)

    return total_latitude


def convert_longitude(longitude, long_dir):
    """
    Convert longitude to a floating point number with decimal degrees and sign.

    :param longitude: The longitude value in the format ddmm.mmmmm
    :param long_dir: The direction of the longitude, 'E' for East, 'W' for West
    :return: The converted longitude as a floating point number
    """
    # 步骤1: 将经度除以100，得到整数部分和小数部分
    long_int = int(longitude // 100)  # 整数部分，度
    long_dec = longitude % 100 / 60.0  # 小数部分，转换为分再转换为度

    # 步骤4: 合并整体度数
    total_longitude = long_int + long_dec

    # 步骤5: 根据long_dir控制longitude的正负值
    if long_dir.upper() == 'W':  # 如果经度方向是西经，取负值
        total_longitude = -total_longitude
    else:  # 否则，取正值
        total_longitude = total_longitude

    return total_longitude

def update_rtc_by_gps(date,time):
    global rtc 
    global day,month,year,hour,minute,second
    if rtc is None:
        print("rtc instance is null. Cancel update rtc by gps.")
        return -1
    # 解析日期
    day = int(date[0:2])  # 日
    month = int(date[2:4])  # 月
    year = int(date[4:6]) + 2000  # 年，假设是2000年之后

    # 解析时间 134832.00
    hour = int(time[0:2]) +8 # 时, 修正北京时间时区
    minute = int(time[2:4])  # 分
    second = int(time[4:6])  # 秒
    microsecond = int(time[-2:])  # 毫秒

    # 忽略week参数，设置为0
    week = 0
    if day == 0 or month == 0 or year == 0:
        print("gps time err.")
        return -1
    
    #配置RTC，返回0->SUC,-1->FAIL
    print("update gps time: {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(year, month, day, hour, minute, second))
    ret = rtc.datetime(year, month, day, week, hour, minute, second, microsecond)
    ret_str = "suc" if ret == 0 else "fail"
    print("set time {}!".format(ret_str))
    return ret


##########################自定义modbus读从机接口###################################

#定义读取保持寄存器参数接口
def read_all_hold_regs():
    print("Read hold registers:")
    register_values = modbus.query_multiple_registers(SLAVE_ID, READ_HOLDING_REGISTERS, HOLD_REG_ADDR_START, HOLD_REG_CNT)
    print("Register values:", register_values)
    cur_hold_values=register_values
    # 更新保持寄存器参数字典 g_modbus_hold_paras_dic
    if register_values:
        for i, value in enumerate(register_values):
            reg_addr = HOLD_REG_ADDR_START + i
            g_modbus_hold_paras_dic[reg_addr]['value'] = value
    print("\r\n")
    
#定义读取输入寄存器参数接口    
def read_all_input_regs():
    print("Read input registers part1:")
    register_values = modbus.query_multiple_registers(SLAVE_ID, READ_INPUT_REGISTERS, INPUT_REG_ADDR_START1, INPUT_REG_CNT1)
    print("Register values:", register_values)
    # 更新输入寄存器参数字典 g_modbus_input_paras_dic
    if register_values:
        for i, value in enumerate(register_values):
            reg_addr = INPUT_REG_ADDR_START1 + i
            g_modbus_input_paras_dic[reg_addr]['value'] = value
    print("\r\n")
    
    print("Read input registers part2:")
    register_values = modbus.query_multiple_registers(SLAVE_ID, READ_INPUT_REGISTERS, INPUT_REG_ADDR_START2, INPUT_REG_CNT2)
    print("Register values:", register_values)
    # 更新输入寄存器参数字典 g_modbus_input_paras_dic
    if register_values:
        for i, value in enumerate(register_values):
            reg_addr = INPUT_REG_ADDR_START2 + i
            g_modbus_input_paras_dic[reg_addr]['value'] = value
    print("\r\n")

#开机读取所有参数
print("delay 2s to wait for slave device poweron.")
utime.sleep(2)#等2秒，等从机起来
read_all_hold_regs()
read_all_input_regs()

#开机上报一次参数
if c is not None:
    print("Poweron event!")
    c.publish_data_to_mqtt()
    
################# FOTA 初始化########################
fota = app_fota.new()


################ 低功耗配置####################
# 创建wakelock锁
lpm_fd = pm.create_wakelock("lp_lock", len("lp_lock"))
# 设置自动休眠模式
pm.autosleep(USR_CONFIG_LOWPOWER_MODE)

################GPS初始化######################
if g_modbus_hold_paras_dic[REG_ADDR_HOLD_GPS_ONOFF]['value'] == 1:
    gpsinit()#上电读从机gps开关状态，以决定是否开启gps
else:
    loc_by_base()#基站定位
####### while大循环 ############################
mqtt_send_cnt=0
read_itv_ctr_cnt=0
gps_itv_ctr_cnt =0
fota_itv_ctr_cnt =0
baseloc_itv_ctr_cnt=0
MAIN_LOOP_DELAY_ITV_SEC = 1
READ_ITV_SEC = 30 #读从机输入寄存器间隔，单位秒
GPS_ITV_SEC = 15 #读GPS状态间隔，单位秒
gps_fail_cnt=0 #gps定位失败次数统计，用于激活基站定位
BASE_LOC_ITV_SEC = 300 #如果GPS失败超过XXX，执行一次基站定位

FOTA_ITV_SEC = 60 # FOTA判断间隔，单位秒

print("\r\n----App start run. 上电时长：{}秒.----".format(utime.time()))
print("USR APP VER: {}".format(USR_CONFIG_SW_VERSION))

try:
    while True:
        utime.sleep(MAIN_LOOP_DELAY_ITV_SEC)
        print('.')
        # if flag==1:#通过按键来关闭运行
        #     utime.sleep(1)#单位是s 
        #     break
        # RS.write(1)
        # utime.sleep(0.1)
        # if modbus.write_coils(0x02, WRITE_SINGLE_COIL, 0X0000, 0xFF00):#打开继电器
        #     RS.write(0)
        #     retstr = modbus.read_uart()
        #     print(retstr)
        # utime.sleep_ms(1000)
        # RS.write(1)
        # utime.sleep(0.1)
        # if modbus.write_coils(0x02, WRITE_SINGLE_COIL, 0X0000, 0x0000):#关闭继电器
        #     RS.write(0)
        #     retstr = modbus.read_uart()
        # utime.sleep_ms(1000)
        # Grey_log.info('User Code End\r\n\r\n')
        ########################读从机状态和参数########################
        read_itv_ctr_cnt+=1
        itv=READ_ITV_SEC/MAIN_LOOP_DELAY_ITV_SEC
        if read_itv_ctr_cnt%itv == 0:
            print("\r\n----Heartbeat event! 上电时长：{}秒.----".format(utime.time()))
            print("USR APP VER: {}".format(USR_CONFIG_SW_VERSION))
            rtc_date = rtc.datetime()
            print("{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(rtc_date[0], rtc_date[1], rtc_date[2], rtc_date[4], rtc_date[5], rtc_date[6]))

            print("read itv [%d]sec! read all input regs."%READ_ITV_SEC)
            read_all_input_regs()        
            c.publish_data_to_mqtt()
            
        if False:    
            print("********************************")
            utime.sleep(1)
            read_all_hold_regs()

            utime.sleep(1)
            read_all_input_regs()
            print("********************************")
            
        
        #######################字典数据打印#####################
        if hold_reg_change_flag == True:
            hold_reg_change_flag=False
            print("\r\n----Cmd event! 上电时长：{}秒.----".format(utime.time()))
            print("USR APP VER: {}".format(USR_CONFIG_SW_VERSION))
            rtc_date = rtc.datetime()
            print("{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(rtc_date[0], rtc_date[1], rtc_date[2], rtc_date[4], rtc_date[5], rtc_date[6]))
            # 打印保持寄存器参数字典的JSON字符串
            print("Hold Registers Parameters Dictionary JSON:")
            print(ujson.dumps(g_modbus_hold_paras_dic))
            #改变的参数写入从机
            for reg_addr, params in g_modbus_hold_paras_dic.items():
                if params['setflag'] == True:
                    print("Write hold : %d ,value=%d " % (reg_addr,params['value']))
                    modbus.write_hold(SLAVE_ID, WRITE_SINGLE_REGISTER, reg_addr, params['value'])
            
            #gps 开关在本机控制，特殊处理
            if g_modbus_hold_paras_dic[REG_ADDR_HOLD_GPS_ONOFF]['setflag'] == True:
                if g_modbus_hold_paras_dic[REG_ADDR_HOLD_GPS_ONOFF]['value'] == 1:
                    gps_on()
                else:
                    gps_off()
            #清除标志
            for reg_addr, params in g_modbus_hold_paras_dic.items():
                if params['setflag'] == True:
                    params['setflag'] = False
            #写完了读一下
            utime.sleep(1)
            read_all_hold_regs()
            #上报最新状态
            c.publish_data_to_mqtt()
            
        if False:
            # 打印输入寄存器参数字典的JSON字符串
            print("Input Registers Parameters Dictionary JSON:")
            print(ujson.dumps(g_modbus_input_paras_dic))
           
           
        #######################写保持寄存器###################   
        if False:            
            if cur_hold_values is not None and len(cur_hold_values)>=6 :
                print("write holds.")
                cur_hold_values[0] = 1 - cur_hold_values[0]
                cur_hold_values[1] = 1 - cur_hold_values[1]
                cur_hold_values[2] = 1 - cur_hold_values[2]
                cur_hold_values[3] = 1 - cur_hold_values[3]
                cur_hold_values[4] = 1 - cur_hold_values[4]
                cur_hold_values[5] += 1
                cur_hold_values[5] = 50 if cur_hold_values[5] >= 100 else cur_hold_values[5]
                
                modbus.write_hold(SLAVE_ID, WRITE_SINGLE_REGISTER, REG_ADDR_HOLD_POWER_ONOFF_TOTAL, cur_hold_values[0])
                modbus.write_hold(SLAVE_ID, WRITE_SINGLE_REGISTER, REG_ADDR_HOLD_POWER_ONOFF_DC, cur_hold_values[1])
                modbus.write_hold(SLAVE_ID, WRITE_SINGLE_REGISTER, REG_ADDR_HOLD_POWER_ONOFF_AC, cur_hold_values[2])
                modbus.write_hold(SLAVE_ID, WRITE_SINGLE_REGISTER, REG_ADDR_HOLD_POWER_ONOFF_LIGHT, cur_hold_values[3])
                modbus.write_hold(SLAVE_ID, WRITE_SINGLE_REGISTER, REG_ADDR_HOLD_GPS_ONOFF, cur_hold_values[4])
                modbus.write_hold(SLAVE_ID, WRITE_SINGLE_REGISTER, REG_ADDR_HOLD_LED_BRIGHTNESS, cur_hold_values[5])
        
        
        
        #######################GPS FUNCTION############################
        if True:
            #gps get,gps_onoff=1
            if g_modbus_hold_paras_dic[REG_ADDR_HOLD_GPS_ONOFF]['value'] == 1:
                gps_itv_ctr_cnt+=1
                itv=GPS_ITV_SEC/MAIN_LOOP_DELAY_ITV_SEC
                if gps_itv_ctr_cnt%itv == 0:
                    print("\r\n----GPS update event! 上电时长：{}秒.----".format(utime.time()))
                    print("USR APP VER: {}".format(USR_CONFIG_SW_VERSION))
                    rtc_date = rtc.datetime()
                    print("{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(rtc_date[0], rtc_date[1], rtc_date[2], rtc_date[4], rtc_date[5], rtc_date[6]))               
                    print("gps itv [%d]sec! read gps." % GPS_ITV_SEC)
                    gps=get_gps_coordinates(quecgnss)
                    if gps:
                        if gps['validity'] == 'A': #有合法值
                            gps_fail_cnt=0 #清除计数器
                            loc_state='A' #A表示GPS定位成功
                            longitude = round(convert_longitude(gps['longitude'], gps['lon_dir']), 8)
                            latitude = round(convert_latitude(gps['latitude'], gps['lat_dir']), 8)
                            print("GPS经纬度: (", longitude, ", ", latitude, ")")
    #                         update_rtc_by_gps(gps['date'],gps['time'])
                        else: #没有定位成功                       
                            gps_fail_cnt+=1
                            print("GPS搜星中或定位失败！[{}]".format(gps_fail_cnt))
                            gitv=BASE_LOC_ITV_SEC//GPS_ITV_SEC #计算需要进入gps采样多少次满足基站定位间隔
                            if gps_fail_cnt%gitv == 0:
                                loc_by_base()
                    else: #没有gps_info结果返回                   
                        gps_fail_cnt+=1
                        print("GPS获取失败！[{}]".format(gps_fail_cnt))
                        gitv=BASE_LOC_ITV_SEC//GPS_ITV_SEC #计算需要进入gps采样多少次满足基站定位间隔
                        if gps_fail_cnt%gitv == 0:
                            loc_by_base()
            #gps_onoff=0,使用基站定位
            else:
                baseloc_itv_ctr_cnt+=1
                itv=BASE_LOC_ITV_SEC//MAIN_LOOP_DELAY_ITV_SEC
                if baseloc_itv_ctr_cnt % itv == 0:
                    rtc_date = rtc.datetime()
                    print("{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(rtc_date[0], rtc_date[1], rtc_date[2], rtc_date[4], rtc_date[5], rtc_date[6]))
                    loc_by_base()
                
        ###################### FOTA ###########################
        if True:
            fota_itv_ctr_cnt+=1
            itv=FOTA_ITV_SEC/MAIN_LOOP_DELAY_ITV_SEC
            if fota_itv_ctr_cnt % itv == 0:
                print("\r\n----Fota event! 上电时长：{}秒.----".format(utime.time()))
                print("USR APP VER: {}".format(USR_CONFIG_SW_VERSION))
                rtc_date = rtc.datetime()
                print("{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(rtc_date[0], rtc_date[1], rtc_date[2], rtc_date[4], rtc_date[5], rtc_date[6]))
                try:
                    request_url = 'http://120.27.250.30/main_py.aspx?deviceVersion={}'.format(USR_CONFIG_SW_VERSION)
                    ret = fota.download(request_url, '/usr/main.py')  # 下载
                    if ret == 0:  # 0-下载成功
                        print("app download suc! Ready to reboot.")
                        fota.set_update_flag()  # 设置升级标志
                        Power.powerRestart()  # 重启
                    else:  # -1表示下载失败
                        print("there is no app needing to download or downloading is fail.{}".format(ret))
                except Exception as e:
                    print("An fota error occurred: {}".format(e))
                    # 这里可以添加任何其他的错误处理代码
                    # 例如，重试下载，或者执行一些清理工作
                    # 然后继续执行程序的其余部分
                finally:
                    # 无论是否发生异常，都会执行这里的代码
                    # 可以放置一些清理资源的代码
                    print("Continuing...")
                    # 程序的其余部分
                
        ###################### MQTT ###########################
        #此处为测试，正式程序mqtt放到了read_itv_ctr_cnt逻辑和hold_reg_change_flag逻辑中
        if False:
            #mqtt send
            utime.sleep(1)
            mqtt_send_cnt+=1
            if mqtt_send_cnt%5 == 0:
                print("MQTT Send:")
                c.publish_data_to_mqtt()
        
        #mqtt recv 测试
#         client.wait_msg()

except Exception as e:
    print("An error occurred:", e)
finally:
    extint.disable()  # 禁用外部中断

# 清理工作
print("Program terminated.")

