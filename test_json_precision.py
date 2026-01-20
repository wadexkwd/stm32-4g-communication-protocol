import json
import struct

def test_json_float_precision():
    # 创建一个测试数据，包含高精度的浮点数
    test_data = {
        'longitude': 116.3974199,
        'latitude': 39.9086923,
        'accel_x': 1.23456789,
        'pressure': 101325.123456
    }
    
    # 使用 json.dumps 转换为 JSON 字符串
    json_str = json.dumps(test_data)
    
    print("JSON string: {}".format(json_str))
    
    # 解析精度
    long_part = json_str.split('longitude":')[1].split(',')[0]
    lat_part = json_str.split('latitude":')[1].split(',')[0]
    
    print("Longitude precision: {}".format(long_part))
    print("Latitude precision: {}".format(lat_part))
    
    print("\n--- Struct unpack test ---")
    # 测试 struct.unpack 的行为
    binary_data = struct.pack('<dd', 116.3974199, 39.9086923)
    unpacked_data = struct.unpack('<dd', binary_data)
    
    print("Unpacked longitude: {}".format(unpacked_data[0]))
    print("Unpacked latitude: {}".format(unpacked_data[1]))
    
    # 转换为 JSON
    json_str2 = json.dumps({'longitude': unpacked_data[0], 'latitude': unpacked_data[1]})
    print("\nJSON string from unpacked: {}".format(json_str2))

if __name__ == "__main__":
    print("Testing json float precision...")
    test_json_float_precision()
