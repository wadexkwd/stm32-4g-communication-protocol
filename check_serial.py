import sys
import serial
import struct
import random

print("Python版本:", sys.version)
print("pyserial版本:", serial.VERSION)

# 测试基本功能
try:
    # 测试结构体打包
    test_data = struct.pack('BhhhhhhhhId', 1, 100, -200, 10000, 50, -30, 20, 10, -5, 180, 101325, 116.397, 39.907)
    print("结构体打包测试成功，数据长度:", len(test_data))
    
    # 测试随机数生成
    random_data = random.randint(-2000, 2000)
    print("随机数生成测试成功:", random_data)
    
    print("\n✓ 程序基本功能测试通过")
    
except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    sys.exit(1)
