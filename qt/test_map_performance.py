#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试地图组件性能的脚本
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWebEngineWidgets import QWebEngineView

class TestMapPerformance(QMainWindow):
    """测试地图组件性能的窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("地图组件性能测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 布局
        layout = QVBoxLayout(central_widget)
        
        # 地图视图
        self.map_view = QWebEngineView()
        self.map_view.setMinimumHeight(400)
        layout.addWidget(self.map_view)
        
        # 测试按钮
        self.test_button = QPushButton("测试地图更新性能")
        self.test_button.clicked.connect(self.start_performance_test)
        layout.addWidget(self.test_button)
        
        # 结果显示
        self.result_label = QLabel("点击按钮开始性能测试")
        layout.addWidget(self.result_label)
        
        # 加载 Leaflet 地图
        self.load_leaflet_map()
        
        # 记录测试结果
        self.update_times = []
    
    def load_leaflet_map(self):
        """加载 Leaflet 地图"""
        map_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>地图展示</title>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
                integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
                crossorigin=""/>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    height: 100%;
                    width: 100%;
                }
                #map {
                    height: 100%;
                    width: 100%;
                }
            </style>
        </head>
        <body>
            <div id="map"></div>
            
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
                integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
                crossorigin=""></script>
            
            <script>
                // 初始化地图
                var map = L.map('map').setView([39.9042, 116.4074], 13);
                
                // 添加 OpenStreetMap 瓦片图层
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '© OpenStreetMap'
                }).addTo(map);
                
                // 初始化标记
                var marker = null;
                
                // 更新地图标记的函数
                function updateMarker(latitude, longitude) {
                    var latLng = L.latLng(latitude, longitude);
                    
                    if (marker) {
                        marker.setLatLng(latLng);
                    } else {
                        marker = L.marker(latLng).addTo(map);
                    }
                    
                    // 缩放地图到标记位置
                    map.setView(latLng, 15);
                }
            </script>
        </body>
        </html>
        """
        
        self.map_view.setHtml(map_html)
    
    def update_map(self, longitude, latitude):
        """更新地图标记位置（优化：使用定时器限制更新频率）"""
        # 避免频繁更新地图，设置500ms的更新间隔
        if hasattr(self, 'map_update_timer'):
            return
        
        # 创建定时器，500ms后执行地图更新
        self.map_update_timer = QTimer()
        self.map_update_timer.setSingleShot(True)
        self.map_update_timer.timeout.connect(lambda: self._actual_map_update(longitude, latitude))
        self.map_update_timer.start(500)
    
    def _actual_map_update(self, longitude, latitude):
        """实际执行地图更新的函数"""
        # 调用 JavaScript 函数更新地图
        start_time = time.time()
        js_code = f"updateMarker({latitude}, {longitude});"
        self.map_view.page().runJavaScript(js_code)
        # 清除定时器引用
        delattr(self, 'map_update_timer')
        
        # 记录更新时间
        update_time = (time.time() - start_time) * 1000  # 转换为毫秒
        self.update_times.append(update_time)
    
    def start_performance_test(self):
        """开始性能测试"""
        self.result_label.setText("正在测试地图更新性能...")
        self.update_times = []
        
        # 模拟多个位置更新
        locations = [
            (116.4074, 39.9042),  # 北京
            (121.4737, 31.2304),  # 上海
            (113.2644, 23.1291),  # 广州
            (120.1551, 30.2741),  # 杭州
            (117.2008, 39.0842),  # 天津
            (118.7969, 32.0603),  # 南京
            (122.2008, 30.2741)   # 宁波
        ]
        
        # 使用定时器逐个更新位置
        for i, (longitude, latitude) in enumerate(locations):
            QTimer.singleShot(i * 1000, lambda lng=longitude, lat=latitude: self.update_map(lng, lat))
        
        # 显示结果
        QTimer.singleShot((len(locations) + 1) * 1000, self.show_performance_results)
    
    def show_performance_results(self):
        """显示性能测试结果"""
        if len(self.update_times) > 0:
            average_time = sum(self.update_times) / len(self.update_times)
            min_time = min(self.update_times)
            max_time = max(self.update_times)
            
            result_text = (
                f"地图更新性能测试结果：\n"
                f"总更新次数：{len(self.update_times)}\n"
                f"平均更新时间：{average_time:.2f}ms\n"
                f"最小更新时间：{min_time:.2f}ms\n"
                f"最大更新时间：{max_time:.2f}ms\n"
                f"更新间隔：500ms（已优化）"
            )
            
            self.result_label.setText(result_text)
        else:
            self.result_label.setText("性能测试失败：未记录到地图更新时间")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建测试窗口
    window = TestMapPerformance()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()