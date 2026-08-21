import struct
import random

def test_struct_alignment():
    """测试struct模块的字节对齐问题"""
    print("测试不同对齐方式对传感器数据打包字节长度的影响")
    print("=" * 60)
    
    # 测试数据
    sensor_data = {
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
    
    # 1. 默认对齐方式（native）
    try:
        packed_native = struct.pack(
            'BhhhhhhhhhIdd',
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
        print(f"默认对齐方式 (native): {len(packed_native)} bytes")
    except Exception as e:
        print(f"默认对齐方式失败: {e}")
    
    # 2. 无对齐方式（@）
    try:
        packed_at = struct.pack(
            '@BhhhhhhhhhIdd',
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
        print(f"无对齐方式 (@): {len(packed_at)} bytes")
    except Exception as e:
        print(f"无对齐方式失败: {e}")
    
    # 3. 标准对齐方式（=）
    try:
        packed_standard = struct.pack(
            '=BhhhhhhhhhIdd',
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
        print(f"标准对齐方式 (=): {len(packed_standard)} bytes")
    except Exception as e:
        print(f"标准对齐方式失败: {e}")
    
    # 4. 小端对齐方式（<）
    try:
        packed_little = struct.pack(
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
        print(f"小端对齐方式 (<): {len(packed_little)} bytes")
    except Exception as e:
        print(f"小端对齐方式失败: {e}")
    
    # 5. 大端对齐方式（>）
    try:
        packed_big = struct.pack(
            '>BhhhhhhhhhIdd',
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
        print(f"大端对齐方式 (>): {len(packed_big)} bytes")
    except Exception as e:
        print(f"大端对齐方式失败: {e}")
    
    print("=" * 60)
    
    # 计算各个字段的理论大小
    field_sizes = {
        'packet_order': 1,  # B (unsigned char)
        'accel_x': 2,       # h (short)
        'accel_y': 2,       # h
        'accel_z': 2,       # h
        'gyro_x': 2,        # h
        'gyro_y': 2,        # h
        'gyro_z': 2,        # h
        'angle_x': 2,       # h
        'angle_y': 2,       # h
        'angle_z': 2,       # h
        'pressure': 4,      # I (unsigned int)
        'longitude': 8,     # d (double)
        'latitude': 8       # d
    }
    
    total_theoretical = sum(field_sizes.values())
    print(f"理论总字节数: {total_theoretical} bytes")
    
    return packed_little, total_theoretical

def test_packing_unpacking():
    """测试使用小端无对齐方式的打包和解包"""
    print("\n测试小端无对齐方式的打包和解包:")
    print("=" * 60)
    
    sensor_data = {
        'packet_order': 1,
        'accel_x': 100,
        'accel_y': 200,
        'accel_z': 300,
        'gyro_x': -10,
        'gyro_y': -20,
        'gyro_z': -30,
        'angle_x': 15,
        'angle_y': -25,
        'angle_z': 35,
        'pressure': 101325,
        'longitude': 116.397,
        'latitude': 39.907
    }
    
    try:
        # 使用小端无对齐方式打包
        packed_data = struct.pack(
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
        
        print(f"打包后的字节长度: {len(packed_data)} bytes")
        
        # 解包
        unpacked_data = struct.unpack('<BhhhhhhhhhIdd', packed_data)
        
        print("\n解包后的数据:")
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
        
        # 验证数据是否一致
        all_match = True
        if unpacked_data[0] != sensor_data['packet_order']:
            all_match = False
        if unpacked_data[1] != sensor_data['accel_x']:
            all_match = False
        if unpacked_data[2] != sensor_data['accel_y']:
            all_match = False
        if unpacked_data[3] != sensor_data['accel_z']:
            all_match = False
        if unpacked_data[4] != sensor_data['gyro_x']:
            all_match = False
        if unpacked_data[5] != sensor_data['gyro_y']:
            all_match = False
        if unpacked_data[6] != sensor_data['gyro_z']:
            all_match = False
        if unpacked_data[7] != sensor_data['angle_x']:
            all_match = False
        if unpacked_data[8] != sensor_data['angle_y']:
            all_match = False
        if unpacked_data[9] != sensor_data['angle_z']:
            all_match = False
        if unpacked_data[10] != sensor_data['pressure']:
            all_match = False
        if abs(unpacked_data[11] - sensor_data['longitude']) > 1e-6:
            all_match = False
        if abs(unpacked_data[12] - sensor_data['latitude']) > 1e-6:
            all_match = False
            
        if all_match:
            print("\n✓ 打包和解包数据一致")
        else:
            print("\n✗ 打包和解包数据不一致")
            
    except Exception as e:
        print(f"错误: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    print("Python struct模块字节对齐测试")
    packed, expected = test_struct_alignment()
    test_packing_unpacking()
