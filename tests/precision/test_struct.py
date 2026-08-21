import struct
import random

# 计算格式字符串对应的字节长度
def calculate_struct_size():
    # 尝试打包数据以计算字节长度
    # 根据协议文档创建一个43字节的模拟数据
    data = bytearray(43)
    # 填充一些随机值
    for i in range(43):
        data[i] = random.randint(0, 255)
    data = bytes(data)
    
    print(f"Packed data length: {len(data)} bytes")
    print(f"Data: {data}")
    
    # 检查是否与预期的43字节一致
    if len(data) == 43:
        print("Data length matches expected 43 bytes")
    else:
        print(f"Data length mismatch: expected 43 bytes, got {len(data)} bytes")

if __name__ == "__main__":
    calculate_struct_size()
