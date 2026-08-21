import json
import struct
import random

def test_precision_fix():
    """使用标准json模块测试经度和纬度精度"""
    
    # 生成测试数据
    test_data = {
        'packet_order': random.randint(0, 255),
        'accel_x': random.randint(-32768, 32767),
        'longitude': random.uniform(-180, 180),
        'latitude': random.uniform(-90, 90)
    }
    
    print(f"原始经度: {test_data['longitude']}")
    print(f"原始纬度: {test_data['latitude']}")
    
    # 直接序列化
    json_str1 = json.dumps(test_data)
    print(f"\n直接序列化JSON: {json_str1}")
    
    # 使用格式化后的浮点数
    formatted_data = {
        'packet_order': test_data['packet_order'],
        'accel_x': test_data['accel_x'],
        'longitude': float("{0:.8f}".format(test_data['longitude'])),
        'latitude': float("{0:.8f}".format(test_data['latitude']))
    }
    
    json_str2 = json.dumps(formatted_data)
    print(f"格式化后序列化JSON: {json_str2}")
    
    # 检查精度
    check_precision(json_str1, "直接序列化")
    check_precision(json_str2, "格式化后")
    
    print("\n" + "-"*50)
    print("使用struct.pack/unpack测试:")
    
    data_bytes = struct.pack('<Bhd', 
        test_data['packet_order'],
        test_data['accel_x'],
        test_data['longitude']
    )
    
    unpacked = struct.unpack('<Bhd', data_bytes)
    print(f"解包后的经度: {unpacked[2]}")
    
    formatted_lon = float("{0:.8f}".format(unpacked[2]))
    print(f"格式化后的经度: {formatted_lon}")
    
    print(f"JSON序列化: {json.dumps({'longitude': formatted_lon})}")

def check_precision(json_str, label):
    if 'longitude' in json_str:
        long_part = json_str.split('longitude":')[1].split(',')[0]
        if '.' in long_part:
            decimal_digits = len(long_part.split('.')[1])
            print(f"{label} - 经度小数位数: {decimal_digits}")
    
    if 'latitude' in json_str:
        lat_part = json_str.split('latitude":')[1].split(',')[0]
        if '.' in lat_part:
            decimal_digits = len(lat_part.split('.')[1])
            print(f"{label} - 纬度小数位数: {decimal_digits}")

print("测试经度和纬度精度修复")
print("="*50)

for i in range(3):
    print(f"\n--- 测试 {i+1} ---")
    test_precision_fix()

print("\n" + "="*50)
print("结论: 格式化到8位小数可以确保JSON序列化时有足够的精度")
