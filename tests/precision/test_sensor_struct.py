import struct
import random

# 模拟传感器数据
def get_test_sensor_data():
    return {
        'packet_order': random.randint(0, 255),
        'accel_x': random.randint(-32768, 32767),
        'accel_y': random.randint(-32768, 32767),
        'accel_z': random.randint(-32768, 32767),
        'gyro_x': random.randint(-32768, 32767),
        'gyro_y': random.randint(-32768, 32767),
        'gyro_z': random.randint(-32768, 32767),
        'angle_x': random.randint(-32768, 32767),
        'angle_y': random.randint(-32768, 32767),
        'angle_z': random.randint(-32768, 32767),
        'pressure': random.randint(0, 4294967295),
        'longitude': random.uniform(-180, 180),
        'latitude': random.uniform(-90, 90)
    }

# 计算 stm32_simulation_test.py 中使用的格式字符串对应的字节长度
def calculate_sensor_struct_size():
    # 获取测试数据
    sensor_data = get_test_sensor_data()
    
    # 打包数据（使用 stm32_simulation_test.py 中的格式）
    data_bytes = struct.pack(
        '<BhhhhhhhhhIdd',
        sensor_data['packet_order'],
        sensor_data['accel_x'],
        sensor_data['accel_y'],
        sensor_data['accel_z'],
        sensor_data['gyro_x'],
        sensor_data['gyro_y'],
        sensor_data['gyro_z'],
        sensor_data['angle_x'],
        sensor_data['angle_y'],
        sensor_data['angle_z'],
        sensor_data['pressure'],
        sensor_data['longitude'],
        sensor_data['latitude']
    )
    
    # 计算并打印字节长度
    actual_length = len(data_bytes)
    expected_length = 39  # 协议文档中规定的长度
    
    print(f"Actual packed sensor data length: {actual_length} bytes")
    print(f"Expected sensor data length: {expected_length} bytes")
    
    # 转换为十六进制字符串
    hex_str = ' '.join(f'{byte:02X}' for byte in data_bytes)
    print(f"Packed data: {hex_str}")
    
    if actual_length == expected_length:
        print("✓ Sensor data length matches protocol")
    else:
        print("✗ Sensor data length mismatch")
    
    return actual_length

# 测试打包和解包
def test_pack_unpack():
    print("Testing sensor data packing and unpacking:")
    
    sensor_data = get_test_sensor_data()
    print("\nOriginal sensor data:")
    for key, value in sensor_data.items():
        print(f"  {key}: {value}")
    
    # 打包
    data_bytes = struct.pack(
        '<BhhhhhhhhhIdd',
        sensor_data['packet_order'],
        sensor_data['accel_x'],
        sensor_data['accel_y'],
        sensor_data['accel_z'],
        sensor_data['gyro_x'],
        sensor_data['gyro_y'],
        sensor_data['gyro_z'],
        sensor_data['angle_x'],
        sensor_data['angle_y'],
        sensor_data['angle_z'],
        sensor_data['pressure'],
        sensor_data['longitude'],
        sensor_data['latitude']
    )
    
    print(f"\nPacked length: {len(data_bytes)} bytes")
    
    # 解包
    unpacked_data = struct.unpack('<BhhhhhhhhhIdd', data_bytes)
    print("\nUnpacked sensor data:")
    print(f"  packet_order: {unpacked_data[0]}")
    print(f"  accel_x: {unpacked_data[1]}")
    print(f"  accel_y: {unpacked_data[2]}")
    print(f"  accel_z: {unpacked_data[3]}")
    print(f"  gyro_x: {unpacked_data[4]}")
    print(f"  gyro_y: {unpacked_data[5]}")
    print(f"  gyro_z: {unpacked_data[6]}")
    print(f"  angle_x: {unpacked_data[7]}")
    print(f"  angle_y: {unpacked_data[8]}")
    print(f"  angle_z: {unpacked_data[9]}")
    print(f"  pressure: {unpacked_data[10]}")
    print(f"  longitude: {unpacked_data[11]}")
    print(f"  latitude: {unpacked_data[12]}")

if __name__ == "__main__":
    print("Testing sensor data structure...")
    print("=" * 50)
    calculate_sensor_struct_size()
    print("=" * 50)
    test_pack_unpack()
