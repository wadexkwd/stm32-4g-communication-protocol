#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
详细测试高德地图API加载过程
"""

import sys
import os
import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEnginePage

class TestWebEnginePage(QWebEnginePage):
    """捕获 JavaScript 控制台输出的自定义页面"""
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        level_str = str(level)
        print(f"[JS] {level_str} (line {line_number}): {message}")

class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("高德地图API详细测试")
        self.setGeometry(100, 100, 900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.web_view = QWebEngineView()
        self.web_view.setPage(TestWebEnginePage())
        
        layout.addWidget(self.web_view)
        
        self.web_view.loadFinished.connect(self.on_load_finished)
        self.web_view.titleChanged.connect(self.on_title_changed)
        self.web_view.urlChanged.connect(self.on_url_changed)
        
        self.load_test_page()

    def load_test_page(self):
        print("正在加载详细测试页面...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>高德地图API详细测试</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                .result {{ margin: 10px 0; padding: 10px; border-radius: 5px; }}
                .success {{ background-color: #d4edda; color: #155724; }}
                .error {{ background-color: #f8d7da; color: #721c24; }}
                .info {{ background-color: #d1ecf1; color: #0c5460; }}
                #log {{ 
                    margin-top: 20px; 
                    border: 1px solid #ccc; 
                    padding: 10px; 
                    max-height: 300px; 
                    overflow-y: scroll; 
                    background-color: #f8f9fa;
                    font-family: monospace;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <h1>高德地图API详细测试</h1>
            
            <div id="result" class="result info">
                <strong>测试开始</strong> 正在加载和测试高德地图API...
            </div>
            
            <div id="info">
                <h3>系统信息:</h3>
                <p>时间: <span id="time">{self.get_current_time()}</span></p>
                <p>User Agent: <span id="user_agent"></span></p>
                <p>API Key: <span id="api_key">431d3bb1fa78eef96736dc499113fca2</span></p>
                <p>Security Key: <span id="security_key">dd1127e11e1f2d5504a2f2ec9824eb78</span></p>
            </div>
            
            <div id="log"></div>
            
            <script type="text/javascript">
                // 日志记录函数
                function log(msg, type = 'info') {{
                    const logDiv = document.getElementById('log');
                    const time = new Date().toLocaleTimeString();
                    const entry = document.createElement('div');
                    entry.className = type;
                    entry.innerHTML = `<span style="color: #666;">${{time}}</span> - ${{msg}}`;
                    logDiv.appendChild(entry);
                    logDiv.scrollTop = logDiv.scrollHeight;
                }}
                
                // 显示用户代理信息
                document.getElementById('user_agent').textContent = navigator.userAgent;
                log('用户代理: ' + navigator.userAgent);
                
                // 测试1: 基本网络连通性
                log('测试1: 检查网络连通性');
                
                function testNetwork() {{
                    log('测试连接到高德地图服务器...');
                    
                    // 配置安全密钥
                    window._AMapSecurityConfig = {{
                        securityJsCode: 'dd1127e11e1f2d5504a2f2ec9824eb78'
                    }};
                    log('安全密钥配置完成');
                    
                    // 测试加载高德地图API
                    const script = document.createElement('script');
                    script.src = 'https://webapi.amap.com/maps?v=2.0&key=431d3bb1fa78eef96736dc499113fca2';
                    log('正在加载高德地图API: ' + script.src);
                    
                    script.onload = function() {{
                        log('✅ 高德地图API加载成功');
                        log('AMap对象类型: ' + typeof AMap);
                        
                        if (typeof AMap !== 'undefined') {{
                            log('✅ AMap对象已定义');
                            document.getElementById('result').className = 'result success';
                            document.getElementById('result').innerHTML = '<strong>API加载成功!</strong>';
                            
                            testMapInit();
                        }} else {{
                            log('❌ AMap对象未定义');
                            document.getElementById('result').className = 'result error';
                            document.getElementById('result').innerHTML = '<strong>API加载失败!</strong><br>AMap对象未定义';
                        }}
                    }};
                    
                    script.onerror = function(event) {{
                        log('❌ 高德地图API加载失败');
                        log('错误事件: ' + JSON.stringify(event));
                        document.getElementById('result').className = 'result error';
                        document.getElementById('result').innerHTML = '<strong>API加载失败!</strong><br>脚本加载错误';
                    }};
                    
                    script.onabort = function() {{
                        log('❌ 高德地图API加载被中断');
                        document.getElementById('result').className = 'result error';
                        document.getElementById('result').innerHTML = '<strong>API加载被中断!</strong>';
                    }};
                    
                    document.head.appendChild(script);
                    log('脚本元素已添加到页面');
                }}
                
                // 测试2: 地图初始化
                function testMapInit() {{
                    log('测试2: 地图初始化');
                    try {{
                        const mapDiv = document.createElement('div');
                        mapDiv.id = 'map';
                        mapDiv.style.width = '100%';
                        mapDiv.style.height = '400px';
                        mapDiv.style.border = '1px solid #ccc';
                        mapDiv.style.marginTop = '20px';
                        document.body.appendChild(mapDiv);
                        
                        log('地图容器创建成功');
                        
                        const map = new AMap.Map('map', {{
                            center: [116.397428, 39.90923],
                            zoom: 13
                        }});
                        
                        log('✅ 地图初始化成功');
                        document.getElementById('result').innerHTML = '<strong>地图加载完成!</strong>';
                        
                        // 添加地图控件
                        map.addControl(new AMap.Scale()); // 比例尺控件
                        map.addControl(new AMap.ToolBar()); // 工具栏控件
                        log('地图控件添加成功');
                        
                    }} catch (error) {{
                        log('❌ 地图初始化失败: ' + error.message);
                        log('错误堆栈: ' + error.stack);
                        document.getElementById('result').className = 'result error';
                        document.getElementById('result').innerHTML = '<strong>地图初始化失败!</strong><br>' + error.message;
                    }}
                }}
                
                // 超时检查
                const timeout = setTimeout(function() {{
                    log('⚠️ 超时检查: 15秒后仍未完成加载');
                    if (typeof AMap === 'undefined') {{
                        log('❌ AMap对象在15秒后仍未加载');
                        document.getElementById('result').className = 'result error';
                        document.getElementById('result').innerHTML = '<strong>加载超时!</strong><br>API加载时间超过15秒';
                    }}
                }}, 15000);
                
                // 页面加载完成后开始测试
                window.onload = function() {{
                    log('✅ 页面加载完成，开始执行测试');
                    testNetwork();
                }};
                
                // 检查页面加载时间
                log('页面加载时间: ' + new Date().toLocaleTimeString());
            </script>
        </body>
        </html>
        '''
        
        temp_file = os.path.join(current_dir, "temp_detailed_test.html")
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        file_url = QUrl.fromLocalFile(temp_file)
        self.web_view.load(file_url)
        
        print(f"加载详细测试页面: {file_url.toString()}")

    def get_current_time(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def on_load_finished(self, success):
        print(f"详细测试页面加载完成: {success}")
        
        if success:
            print("详细测试页面加载成功")
            # 延迟执行检查，确保页面脚本有时间运行
            self.after_load_check()
        else:
            print("详细测试页面加载失败")
            self.show_error()

    def on_title_changed(self, title):
        print(f"页面标题: {title}")

    def on_url_changed(self, url):
        print(f"URL: {url.toString()}")

    def after_load_check(self):
        print("执行页面加载后检查...")
        
        self.web_view.page().runJavaScript(
            "document.getElementById('result').textContent", 
            lambda text: print(f"结果信息: {text.strip()}")
        )
        
        self.web_view.page().runJavaScript(
            "typeof AMap", 
            lambda amap_type: print(f"AMap 对象类型: {amap_type}")
        )
        
        self.web_view.page().runJavaScript(
            "document.getElementById('log')?.textContent || '未找到日志元素'", 
            lambda log_text: print(f"日志信息:\n{log_text}")
        )

    def show_error(self):
        error_html = '''
        <html>
        <body style="background-color: #ffcccc; padding: 20px;">
            <h1 style="color: red;">页面加载失败</h1>
            <p>无法加载详细测试页面。</p>
        </body>
        </html>
        '''
        self.web_view.setHtml(error_html)

def main():
    print("=== 高德地图API详细测试 ===")
    
    app = QApplication(sys.argv)
    
    try:
        window = TestWindow()
        window.show()
        print("详细测试窗口显示成功")
        
        result = app.exec()
        
        # 清理临时文件
        temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_detailed_test.html")
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        print(f"详细测试完成，返回码: {result}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        print(f"堆栈跟踪: {traceback.format_exc()}")
        result = 1
    
    print("\n=== 测试结束 ===")
    sys.exit(result)

if __name__ == "__main__":
    main()