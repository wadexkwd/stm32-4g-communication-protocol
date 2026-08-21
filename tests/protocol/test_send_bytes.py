#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 stm32_simulation_test.py 中的发送字节打印功能
"""

import sys
import io
from unittest.mock import Mock
import stm32_simulation_test as stm32

def test_send_bytes_printing():
    """测试发送字节时的打印功能"""
    print("=" * 50)
    print("测试发送字节打印功能")
    print("=" * 50)
    
    # 模拟串口
    mock_ser = Mock()
    mock_ser.is_open = True
    
    # 创建STM32Simulator实例并模拟串口连接
    simulator = stm32.STM32Simulator("COM5", 115200)
    simulator.is_connected = True
    simulator.ser = mock_ser
    
    # 捕获打印输出
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    try:
        # 创建传感器数据生成器
        data_generator = stm32.SensorDataGenerator()
        
        # 使用 generate_sensor_data 方法生成完整的传感器数据
        sensor_data = data_generator.generate_sensor_data()
        
        data_bytes = data_generator.sensor_data_to_bytes(sensor_data)
        
        # 发送帧
        result = simulator.send_frame(stm32.CMD_DATA_UPLOAD, data_bytes)
        
        # 恢复标准输出
        sys.stdout = sys.__stdout__
        
        print(f"发送结果: {'成功' if result else '失败'}")
        print()
        
        # 检查是否有发送字节的打印输出
        output = captured_output.getvalue()
        print("捕获到的输出:")
        print(output)
        
        # 验证是否包含发送字节的信息
        if "发送字节:" in output:
            print("✓ 发送字节的打印功能正常工作")
            # 提取并打印发送的字节内容
            lines = output.split('\n')
            for line in lines:
                if "发送字节:" in line:
                    print(f"发送的字节: {line.strip()}")
        else:
            print("❌ 没有捕获到发送字节的打印输出")
            
    except Exception as e:
        sys.stdout = sys.__stdout__
        print(f"测试过程中发生错误: {e}")
        return False
        
    return True

def test_pack_frame():
    """测试打包帧功能"""
    print("\n" + "=" * 50)
    print("测试打包帧功能")
    print("=" * 50)
    
    try:
        simulator = stm32.STM32Simulator("COM5", 115200)
        
        # 创建传感器数据生成器
        data_generator = stm32.SensorDataGenerator()
        
        # 使用 generate_sensor_data 方法生成完整的传感器数据
        sensor_data = data_generator.generate_sensor_data()
        
        data_bytes = data_generator.sensor_data_to_bytes(sensor_data)
        
        # 打包帧
        frame = simulator.pack_frame(stm32.CMD_DATA_UPLOAD, data_bytes)
        
        print(f"帧长度: {len(frame)} 字节")
        print(f"帧内容: {' '.join(f'{byte:02X}' for byte in frame)}")
        
        # 验证帧格式
        assert frame[:2] == stm32.FRAME_HEADER, "帧头不正确"
        assert frame[-2:] == stm32.FRAME_TAIL, "帧尾不正确"
        
        print("✓ 帧打包功能正常")
        return True
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    test_send_bytes_printing()
    test_pack_frame()
    
    print("\n" + "=" * 50)
    print("所有测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
