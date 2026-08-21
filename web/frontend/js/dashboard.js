/**
 * 应急跌落事件监控系统 - 数据看板
 * 展示：设备总数/在线离线/异常统计、设备位置分布地图、设备情况总览表、上报量柱状图
 * 数据来自 GET /api/dashboard，每 refreshSec 秒自动刷新
 */
const { createApp, reactive, ref, onMounted } = Vue;

const REFRESH_MS = 10000;

createApp({
    setup() {
        const summary = reactive({ total: 0, online: 0, offline: 0, alarm_24h: 0, poweron_24h: 0 });
        const storage = reactive({ total_rows: null, db_size_mb: null, oldest_time: null });
        const retention = reactive({ days: 0, archive_enabled: false, last_run: null });
        const devices = ref([]);
        let eventsHourly = {};          // { 'YYYY-MM-DD HH:00': {事件类型: 次数} }
        const loading = ref(true);
        const lastUpdate = ref('');
        const refreshSec = REFRESH_MS / 1000;

        let map = null;
        let overlays = [];          // 当前地图覆盖物（marker/label）
        let eventChart = null;

        // ------------------------------------------------------------------ 数据加载
        async function fetchData() {
            loading.value = true;
            try {
                const resp = await fetch('/api/dashboard');
                const data = await resp.json();
                Object.assign(summary, {
                    total: data.total, online: data.online, offline: data.offline,
                    alarm_24h: data.alarm_24h, poweron_24h: data.poweron_24h,
                });
                devices.value = data.devices;
                if (data.storage) Object.assign(storage, data.storage);
                if (data.retention) Object.assign(retention, data.retention);
                eventsHourly = data.events_hourly || {};
                lastUpdate.value = new Date().toLocaleTimeString();
                renderMarkers();
                renderEventChart();
            } catch (e) {
                console.error('看板数据加载失败:', e);
            } finally {
                loading.value = false;
            }
        }

        // ------------------------------------------------------------------ 地图
        function initMap() {
            if (map || typeof AMap === 'undefined') return !!map;
            map = new AMap.Map('dash-map', {
                zoom: 4,
                center: [105, 35],
                viewMode: '2D',
                mapStyle: 'amap://styles/normal',
            });
            try {
                if (typeof AMap.Scale === 'function') map.addControl(new AMap.Scale({}));
            } catch (e) { /* 控件失败不影响主流程 */ }
            return true;
        }

        function renderMarkers() {
            if (!initMap()) return;
            if (overlays.length) {
                map.remove(overlays);
                overlays = [];
            }
            for (const d of devices.value) {
                const lon = parseFloat(d.longitude), lat = parseFloat(d.latitude);
                if (!lon || !lat) continue;

                // 标记颜色：告警(红描边) > 离线(灰) > 在线(绿)
                const stroke = d.timeout_24h > 0 ? '#cc3333'
                             : (d.online ? '#2e9e44' : '#999999');
                const fill = d.online ? '#d4f0da' : '#eeeeee';

                const marker = new AMap.CircleMarker({
                    center: [lon, lat],
                    radius: 8,
                    strokeColor: stroke,
                    strokeWeight: 2,
                    fillColor: fill,
                    fillOpacity: 0.9,
                    map: map,
                    extData: d,
                });
                marker.on('click', () => locateDevice(d));

                const label = new AMap.Text({
                    text: `${d.imei}\n${d.online ? '在线' : '离线'}${d.timeout_24h ? ' · 告警' + d.timeout_24h : ''}`,
                    anchor: 'top-center',
                    style: {
                        'background-color': 'white',
                        'border': `1px solid ${stroke}`,
                        'padding': '3px 8px',
                        'border-radius': '4px',
                        'font-size': '11px',
                        'color': '#333',
                        'white-space': 'nowrap',
                        'text-align': 'center',
                    },
                    position: [lon, lat],
                    map: map,
                });
                overlays.push(marker, label);
            }
        }

        function locateDevice(d) {
            const lon = parseFloat(d.longitude), lat = parseFloat(d.latitude);
            if (map && lon && lat) {
                map.setZoomAndCenter(12, [lon, lat]);
            }
        }

        // ------------------------------------------------------------------ 异常事件时间轴（按小时堆叠柱状图）
        function renderEventChart() {
            const el = document.getElementById('event-chart');
            if (!el) return;
            if (!eventChart) {
                eventChart = echarts.init(el);
            }
            // 生成完整的 24 小时时间轴（缺失的小时补 0，保证时间轴连续）
            const hours = [];
            const now = new Date();
            now.setMinutes(0, 0, 0);
            for (let i = 23; i >= 0; i--) {
                const d = new Date(now.getTime() - i * 3600 * 1000);
                const p = n => String(n).padStart(2, '0');
                hours.push(`${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:00`);
            }
            const key = h => h.slice(5, 13);   // 显示 "MM-DD HH:00"
            const timeout = hours.map(h => (eventsHourly[h] || {})['SENSOR_REPORT_TIMEOUT'] || 0);
            const poweron = hours.map(h => (eventsHourly[h] || {})['POWER_ON'] || 0);

            eventChart.setOption({
                tooltip: {
                    trigger: 'axis',
                    axisPointer: { type: 'shadow' },
                    formatter: (params) => {
                        const total = params.reduce((s, p) => s + p.value, 0);
                        if (!total) return `${params[0].name}<br>无异常事件`;
                        return params.filter(p => p.value > 0)
                            .map(p => `${p.marker} ${p.seriesName}: ${p.value} 次`).join('<br>');
                    },
                },
                legend: { show: false },   // 标题栏已有图例
                grid: { left: 40, right: 16, top: 16, bottom: 24 },
                xAxis: {
                    type: 'category',
                    data: hours.map(key),
                    axisLabel: { fontSize: 10, interval: 3 },
                },
                yAxis: {
                    type: 'value', name: '次',
                    minInterval: 1,       // 事件次数为整数
                },
                series: [
                    {
                        name: '数据超时', type: 'bar', stack: 'event',
                        data: timeout, itemStyle: { color: '#cc3333' }, animation: false,
                        barMaxWidth: 20,
                    },
                    {
                        name: '上电/重启', type: 'bar', stack: 'event',
                        data: poweron, itemStyle: { color: '#b8860b' }, animation: false,
                        barMaxWidth: 20,
                    },
                ],
            });
        }

        // ------------------------------------------------------------------ 挂载
        onMounted(() => {
            fetchData();
            setInterval(fetchData, REFRESH_MS);
            // AMap SDK 异步加载完成后再画一次标记
            setTimeout(() => { renderMarkers(); eventChart && eventChart.resize(); }, 1500);
            window.addEventListener('resize', () => {
                eventChart && eventChart.resize();
                map && map.resize && map.resize();
            });
        });

        return { summary, storage, retention, devices, loading, lastUpdate, refreshSec, fetchData, locateDevice };
    },
}).mount('#app');
