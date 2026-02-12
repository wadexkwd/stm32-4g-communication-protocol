#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试地图组件功能 - 支持离线地图
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView

class TestMapWindow(QMainWindow):
    """测试地图组件的窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("地图组件测试 - 支持离线地图")
        self.setGeometry(100, 100, 1400, 900)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 布局
        layout = QVBoxLayout(central_widget)
        
        # 地图视图
        self.map_view = QWebEngineView()
        self.map_view.setMinimumHeight(400)
        layout.addWidget(self.map_view)
        
        # 连接页面加载完成信号
        self.map_view.loadFinished.connect(self.on_page_load_finished)
        self.map_view.titleChanged.connect(self.on_title_changed)
        self.map_view.urlChanged.connect(self.on_url_changed)
        
        # 加载地图
        self.load_leaflet_map()
    
    def load_leaflet_map(self):
        """加载 Leaflet 地图"""
        print("正在加载 Leaflet 地图...")
        
        # 检查本地 Leaflet 库是否可用
        current_dir = os.path.dirname(os.path.abspath(__file__))
        leaflet_dir = os.path.join(current_dir, "leaflet")
        
        if os.path.exists(leaflet_dir) and os.path.exists(os.path.join(leaflet_dir, "leaflet.js")):
            print("本地 Leaflet 库可用，使用离线地图模式")
            self.load_offline_map()
        else:
            print("本地 Leaflet 库不可用，尝试使用在线地图")
            self.load_online_map()
    
    def load_offline_map(self):
        """加载离线地图"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "test_map_offline.html")
        
        print(f"HTML 文件路径: {html_file}")
        
        if os.path.exists(html_file):
            print("HTML 文件存在")
            file_url = QUrl.fromLocalFile(html_file)
            print(f"加载 URL: {file_url.toString()}")
            
            self.map_view.load(file_url)
            print("地图加载命令已发送")
        else:
            print(f"错误: HTML 文件不存在: {html_file}")
            self.show_error()
    
    def load_online_map(self):
        """加载在线地图"""
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
                    background-color: #f0f0f0;
                }
                #map {
                    height: 100%;
                    width: 100%;
                    background-color: #e0e0e0;
                }
                .status {
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    background: white;
                    padding: 10px;
                    border-radius: 5px;
                    z-index: 1000;
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="status" id="status">加载中...</div>
            <div id="map"></div>
            
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
                integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
                crossorigin=""></script>
            
            <script>
                console.log('Leaflet 地图初始化开始');
                
                // 初始化地图
                var map = L.map('map').setView([39.9042, 116.4074], 13);
                console.log('地图对象创建成功');
                
                // 添加 OpenStreetMap 瓦片图层
                var tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '© OpenStreetMap'
                }).addTo(map);
                
                // 瓦片图层加载事件
                tileLayer.on('tileload', function(event) {
                    console.log('瓦片加载成功:', event.tile);
                });
                
                tileLayer.on('tileerror', function(event) {
                    console.log('瓦片加载失败:', event);
                });
                
                // 地图加载完成事件
                map.on('load', function() {
                    console.log('地图加载完成');
                    document.getElementById('status').textContent = '地图加载成功';
                });
                
                // 初始化标记
                var marker = null;
                
                // 更新地图标记的函数
                function updateMarker(latitude, longitude) {
                    console.log('更新标记到:', latitude, longitude);
                    var latLng = L.latLng(latitude, longitude);
                    
                    if (marker) {
                        marker.setLatLng(latLng);
                    } else {
                        marker = L.marker(latLng).addTo(map);
                    }
                    
                    // 缩放地图到标记位置
                    map.setView(latLng, 15);
                }
                
                // 检查 Leaflet 是否初始化成功
                if (map) {
                    console.log('Leaflet 地图初始化成功');
                } else {
                    console.error('Leaflet 地图初始化失败');
                }
            </script>
        </body>
        </html>
        """
        
        print("正在加载在线地图 HTML...")
        self.map_view.setHtml(map_html)
        print("地图 HTML 加载完成")
    
    def on_page_load_finished(self, success):
        """页面加载完成回调"""
        print(f"加载完成: {success}")
        
        if success:
            print("地图页面加载成功")
            self.check_map_content()
            
            # 页面加载完成后测试更新地图标记
            self.test_update_map()
        else:
            print("地图页面加载失败")
            self.show_error()
    
    def on_title_changed(self, title):
        """标题变化回调"""
        print(f"页面标题: {title}")
    
    def on_url_changed(self, url):
        """URL 变化回调"""
        print(f"URL: {url.toString()}")
    
    def check_map_content(self):
        """检查地图内容"""
        self.map_view.page().runJavaScript(
            "document.hidden", 
            lambda hidden: print(f"页面是否隐藏: {hidden}")
        )
        
        self.map_view.page().runJavaScript(
            "document.getElementById('map').getBoundingClientRect()", 
            lambda rect: print(f"地图容器尺寸: {rect}")
        )
        
        self.map_view.page().runJavaScript(
            "document.documentElement.outerHTML", 
            lambda result: print("页面内容预览:\n" + result[:500])
        )
        
        self.map_view.page().runJavaScript(
            "document.getElementById('status')?.textContent || '未找到状态元素'",
            lambda text: print(f"状态信息: {text.strip()}")
        )
        
        self.map_view.page().runJavaScript(
            "typeof L !== 'undefined' ? 'Leaflet 已加载' : 'Leaflet 未加载'",
            lambda result: print(f"Leaflet 状态: {result}")
        )
        
        self.map_view.page().runJavaScript(
            "typeof map !== 'undefined' ? '地图对象已初始化' : '地图对象未初始化'",
            lambda result: print(f"地图对象状态: {result}")
        )
        
        self.map_view.page().runJavaScript(
            "map ? map.hasLayer(map._layers[Object.keys(map._layers)[1]]) : false",
            lambda hasLayer: print(f"地图是否有 TileLayer: {hasLayer}")
        )
    
    def test_update_map(self):
        """测试更新地图标记"""
        # 测试北京天安门位置
        latitude = 39.9042
        longitude = 116.4074
        
        print(f"正在更新地图标记到: 纬度 {latitude}, 经度 {longitude}")
        
        # 调用 JavaScript 函数更新地图
        js_code = f"updateMarker({latitude}, {longitude});"
        self.map_view.page().runJavaScript(js_code, self.on_js_result)
        
        print(f"地图标记更新命令已发送")
    
    def update_map(self, longitude, latitude):
        """更新地图标记位置"""
        # 调用 JavaScript 函数更新地图
        js_code = f"updateMarker({latitude}, {longitude});"
        self.map_view.page().runJavaScript(js_code)
    
    def on_js_result(self, result):
        """JavaScript 执行结果回调"""
        print("JavaScript 执行结果:", result)
    
    def show_error(self):
        """显示错误信息"""
        error_html = """
        <html>
        <body style="background-color: #ffcccc; padding: 20px;">
            <h1 style="color: red;">地图加载失败</h1>
            <p>无法加载地图页面。</p>
            <p>请检查：</p>
            <ul>
                <li>HTML 文件是否存在</li>
                <li>PySide6 WebEngine 是否正常工作</li>
                <li>网络连接是否正常</li>
            </ul>
        </body>
        </html>
        """
        self.map_view.setHtml(error_html)

def main():
    """主函数"""
    print("=== 地图组件测试程序 ===")
    
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建测试窗口
    window = TestMapWindow()
    window.show()
    
    # 运行应用程序
    try:
        result = app.exec()
        print(f"应用程序退出，返回码: {result}")
    except Exception as e:
        print(f"应用程序异常: {e}")
        import traceback
        print(f"堆栈跟踪: {traceback.format_exc()}")
        result = 1
    
    print("\n=== 程序结束 ===")
    sys.exit(result)

if __name__ == "__main__":
    main()