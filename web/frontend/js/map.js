/**
 * 应急跌落事件监控系统 - 高德地图模块
 * 从 qt/main_window.py 内嵌地图 JS 移植：
 * - CircleMarker 圆形标记 + 坐标标签跟随显示
 * - 位置变化超过 50 米才刷新（避免 GPS 抖动频繁重绘）
 * - 最近 3 条位置更新日志
 */
const MapView = {
    map: null,
    marker: null,
    label: null,
    locationLog: [],
    lastLocation: null,

    // 地球半径（米），用于计算两点距离
    EARTH_RADIUS: 6371000,
    // 距离阈值（米）：小于该值不刷新位置
    UPDATE_DISTANCE_THRESHOLD: 50,

    init() {
        if (this.map) return true;
        const container = document.getElementById('map-container');
        if (!container || typeof AMap === 'undefined') return false;

        this.map = new AMap.Map(container, {
            zoom: 13,
            center: [116.397428, 39.90923],
            viewMode: '2D',
            mapStyle: 'amap://styles/normal',
        });

        // 地图控件
        try {
            if (typeof AMap.Scale === 'function') this.map.addControl(new AMap.Scale({}));
            if (typeof AMap.ToolBar === 'function') this.map.addControl(new AMap.ToolBar({}));
        } catch (e) { /* 控件加载失败不影响主流程 */ }

        // 初始圆形标记
        this.marker = new AMap.CircleMarker({
            center: [116.397428, 39.90923],
            radius: 8,
            strokeColor: '#007bff',
            strokeWeight: 2,
            fillColor: '#ffffff',
            fillOpacity: 0.8,
            map: this.map,
        });

        // 坐标信息标签
        this.label = new AMap.Text({
            text: '-',
            anchor: 'bottom-left',
            style: {
                'background-color': 'white',
                'border': '1px solid #007bff',
                'padding': '4px 8px',
                'border-radius': '4px',
                'font-size': '12px',
                'color': '#007bff',
                'font-weight': 'bold',
                'white-space': 'nowrap',
            },
            position: [116.397428, 39.90923],
            map: this.map,
        });

        // 位置更新日志面板
        const logDiv = document.createElement('div');
        logDiv.className = 'map-log';
        logDiv.innerHTML = '<h4>最近位置更新</h4><div class="entries"></div>';
        container.appendChild(logDiv);

        const infoDiv = document.createElement('div');
        infoDiv.className = 'map-info';
        infoDiv.textContent = '等待设备上报位置...';
        container.appendChild(infoDiv);
        this.infoDiv = infoDiv;
        this.logEntriesDiv = logDiv.querySelector('.entries');

        // 当前坐标跟随标签
        const curDiv = document.createElement('div');
        curDiv.className = 'map-current';
        container.appendChild(curDiv);
        this.curDiv = curDiv;

        return true;
    },

    /** 更新位置（latitude/longitude 为数值） */
    updateLocation(latitude, longitude) {
        if (!this.map || !latitude || !longitude) return;
        try {
            // 距离过近不刷新，避免抖动（同 qt 方案）
            if (this.lastLocation) {
                const distance = this._distance(
                    this.lastLocation.latitude, this.lastLocation.longitude,
                    latitude, longitude);
                if (distance < this.UPDATE_DISTANCE_THRESHOLD) return;
            }

            this.map.setZoomAndCenter(15, [longitude, latitude]);

            if (this.marker) this.map.remove(this.marker);
            this.marker = new AMap.CircleMarker({
                center: [longitude, latitude],
                radius: 8,
                strokeColor: '#007bff',
                strokeWeight: 2,
                fillColor: '#ffffff',
                fillOpacity: 0.8,
                map: this.map,
            });

            if (this.label) this.map.remove(this.label);
            this.label = new AMap.Text({
                text: `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`,
                anchor: 'bottom-left',
                style: {
                    'background-color': 'white',
                    'border': '1px solid #007bff',
                    'padding': '4px 8px',
                    'border-radius': '4px',
                    'font-size': '12px',
                    'color': '#007bff',
                    'font-weight': 'bold',
                    'white-space': 'nowrap',
                },
                position: [longitude, latitude],
                map: this.map,
            });

            // 当前坐标跟随标记
            const pixel = this.map.lngLatToContainer([longitude, latitude]);
            this.curDiv.textContent = `位置: ${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;
            this.curDiv.style.left = pixel.x + 'px';
            this.curDiv.style.top = (pixel.y - 40) + 'px';
            this.curDiv.style.transform = 'translate(-50%, 0)';

            if (this.infoDiv) this.infoDiv.textContent = `当前位置: ${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;
            this._addLocationLog(latitude, longitude);
            this.lastLocation = { latitude, longitude };
        } catch (e) {
            console.error('更新地图位置失败:', e);
        }
    },

    /** 重置（切换设备时）：回到默认视野，清空日志 */
    reset() {
        this.lastLocation = null;
        this.locationLog = [];
        if (this.logEntriesDiv) this.logEntriesDiv.innerHTML = '';
        if (this.curDiv) { this.curDiv.textContent = ''; }
        if (this.infoDiv) this.infoDiv.textContent = '等待设备上报位置...';
        if (this.map) this.map.setZoomAndCenter(13, [116.397428, 39.90923]);
    },

    resize() {
        this.map && this.map.resize && this.map.resize();
    },

    _addLocationLog(latitude, longitude) {
        this.locationLog.unshift({
            time: new Date().toLocaleTimeString(),
            latitude, longitude,
        });
        if (this.locationLog.length > 3) this.locationLog.pop();

        if (!this.logEntriesDiv) return;
        this.logEntriesDiv.innerHTML = this.locationLog.map(entry =>
            `<div class="entry"><span class="time">[${entry.time}]</span><br>` +
            `${entry.latitude.toFixed(6)}, ${entry.longitude.toFixed(6)}</div>`
        ).join('');
    },

    /** 两点间距离（米），Haversine 公式 */
    _distance(lat1, lon1, lat2, lon2) {
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return this.EARTH_RADIUS * c;
    },
};
