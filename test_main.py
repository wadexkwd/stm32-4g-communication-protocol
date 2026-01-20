#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - 4G模块QPython实现
功能测试模块
"""

import unittest
import sys
import os

# 添加当前目录到模块搜索路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import (
    STM32Communication,
    MQTTClient,
    Watchdog
)


class TestSTM32Communication(unittest.TestCase):
    """STM32Communication类测试"""

    def test_calculate_checksum(self):
        """测试校验和计算"""
        stm32 = STM32Communication("/dev/ttyS0", 115200)
        cmd = 0x01
        data_len = 5
        data = b'\x01\x02\x03\x04\x05'
        checksum = stm32.calculate_checksum(cmd, data_len, data)

        # 手动计算校验和
        manual_checksum = cmd
        manual_checksum ^= (data_len >> 8) & 0xFF
        manual_checksum ^= data_len & 0xFF
        for byte in data:
            manual_checksum ^= byte

        self.assertEqual(checksum, manual_checksum)
        print("校验和计算测试通过")

    def test_pack_frame(self):
        """测试帧打包"""
        stm32 = STM32Communication("/dev/ttyS0", 115200)
        cmd = 0x01
        data = b'\x01\x02\x03'
        frame = stm32.pack_frame(cmd, data)

        self.assertEqual(len(frame), 2 + 1 + 2 + 3 + 1 + 2)  # 帧头(2) + 命令(1) + 长度(2) + 数据(3) + 校验(1) + 帧尾(2)
        self.assertEqual(frame[:2], b'\xAA\x55')  # 帧头
        self.assertEqual(frame[-2:], b'\x55\xAA')  # 帧尾
        self.assertEqual(frame[2], cmd)  # 命令码
        self.assertEqual(int.from_bytes(frame[3:5], 'little'), len(data))  # 数据长度

        print("帧打包测试通过")

    def test_unpack_frame(self):
        """测试帧解包"""
        stm32 = STM32Communication("/dev/ttyS0", 115200)
        cmd = 0x01
        data = b'\x01\x02\x03'
        frame = stm32.pack_frame(cmd, data)
        unpacked_cmd, unpacked_len, unpacked_data = stm32.unpack_frame(frame)

        self.assertEqual(unpacked_cmd, cmd)
        self.assertEqual(unpacked_len, len(data))
        self.assertEqual(unpacked_data, data)

        print("帧解包测试通过")


class TestWatchdog(unittest.TestCase):
    """Watchdog类测试"""

    def test_watchdog_initialization(self):
        """测试看门狗初始化"""
        def dummy_callback():
            pass

        watchdog = Watchdog(5, dummy_callback)
        self.assertFalse(watchdog.is_alive)
        print("看门狗初始化测试通过")

    def test_watchdog_feed(self):
        """测试喂狗功能"""
        def dummy_callback():
            pass

        watchdog = Watchdog(2, dummy_callback)
        watchdog.start()
        initial_time = watchdog.timer._when
        watchdog.feed()
        new_time = watchdog.timer._when

        self.assertNotEqual(initial_time, new_time)
        watchdog.stop()
        print("喂狗功能测试通过")


class TestMQTTClient(unittest.TestCase):
    """MQTTClient类测试"""

    def test_initialization(self):
        """测试MQTT客户端初始化"""
        mqtt_client = MQTTClient(
            "mqtt.example.com",
            1883,
            "test_user",
            "test_password",
            "test_topic",
            "test_control_topic"
        )
        self.assertFalse(mqtt_client.is_connected)
        print("MQTT客户端初始化测试通过")


def run_tests():
    """运行所有测试"""
    print("开始运行测试...\n")

    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestSTM32Communication))
    test_suite.addTest(unittest.makeSuite(TestWatchdog))
    test_suite.addTest(unittest.makeSuite(TestMQTTClient))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 输出测试结果
    print(f"\n测试总结:")
    print(f"通过测试数量: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败测试数量: {len(result.failures)}")
    print(f"错误测试数量: {len(result.errors)}")

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    if result.wasSuccessful():
        print("\n所有测试通过！")


if __name__ == "__main__":
    run_tests()  
