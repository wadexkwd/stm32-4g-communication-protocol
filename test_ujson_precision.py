#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 ujson 对浮点数精度的处理
"""

import sys

try:
    import ujson
    print("✅ 成功导入 ujson")
except ImportError:
    print("❌ 无法导入 ujson，尝试使用标准 json 库")
    import json as ujson

def test_json_precision():
    """测试 JSON 序列化时的浮点数精度"""
    print("\n测试浮点数精度...")
    
    # 测试数据
    test_lon = 116.39741856
    test_lat = 39.90873124
    
    print("原始经度: %.8f" % test_lon)
    print("原始纬度: %.8f" % test_lat)
    
    # 创建测试对象
    test_data = {
        'longitude': test_lon,
        'latitude': test_lat
    }
    
    # 使用 ujson 序列化
    try:
        json_str = ujson.dumps(test_data)
        print("\nujson 序列化结果:", repr(json_str))
        
        # 检查是否保留了足够的小数位数
        if '116.39741856' in json_str and '39.90873124' in json_str:
            print("✅ 精度保持良好")
        elif '116.3974' in json_str and '39.9087' in json_str:
            print("⚠️  精度被截断到4位小数")
        elif '116.40' in json_str and '39.91' in json_str:
            print("❌ 精度严重截断到2位小数")
        else:
            print("❓ 精度未知")
            
        # 反序列化后检查精度
        parsed_data = ujson.loads(json_str)
        lon_diff = abs(parsed_data['longitude'] - test_lon)
        lat_diff = abs(parsed_data['latitude'] - test_lat)
        
        print("\n反序列化后精度检查:")
        print("经度差异: %.12f" % lon_diff)
        print("纬度差异: %.12f" % lat_diff)
        
        if lon_diff < 0.00000001 and lat_diff < 0.00000001:
            print("✅ 精度符合要求")
        else:
            print("❌ 精度不符合要求")
            
    except Exception as e:
        print("❌ 序列化/反序列化失败:", e)
        import traceback
        print("堆栈:", traceback.format_exc())
        
def test_with_formatting():
    """测试格式化后的浮点数"""
    print("\n测试格式化后的浮点数...")
    
    test_lon = 116.39741856
    test_lat = 39.90873124
    
    # 格式化后再序列化
    formatted_data = {
        'longitude': float("%.8f" % test_lon),
        'latitude': float("%.8f" % test_lat)
    }
    
    try:
        json_str = ujson.dumps(formatted_data)
        print("ujson 序列化结果:", repr(json_str))
        
        if '116.39741856' in json_str and '39.90873124' in json_str:
            print("✅ 格式化后精度保持良好")
        elif '116.3974' in json_str and '39.9087' in json_str:
            print("⚠️  格式化后精度仍被截断")
        else:
            print("❓ 精度未知")
            
    except Exception as e:
        print("❌ 测试失败:", e)
        
def test_with_string():
    """测试字符串格式化"""
    print("\n测试字符串格式化...")
    
    test_lon = 116.39741856
    test_lat = 39.90873124
    
    # 保存为字符串
    string_data = {
        'longitude': "%.8f" % test_lon,
        'latitude': "%.8f" % test_lat
    }
    
    try:
        json_str = ujson.dumps(string_data)
        print("ujson 序列化结果:", repr(json_str))
        
        if '116.39741856' in json_str and '39.90873124' in json_str:
            print("✅ 字符串格式精度完美")
            
    except Exception as e:
        print("❌ 测试失败:", e)
        
if __name__ == "__main__":
    print("=" * 50)
    print("测试 ujson 浮点数精度")
    print("=" * 50)
    
    test_json_precision()
    test_with_formatting()
    test_with_string()
