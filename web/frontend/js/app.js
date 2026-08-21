/**
 * 应急跌落事件监控系统 - Web前端主逻辑（Vue3）
 * 对标 qt 上位机的展示功能：
 * - 数据总览：实时表格（WebSocket 推送，新数据置顶）
 * - 加速度/角速度/姿态/环境：ECharts 曲线（滑动窗口）
 * - 位置：高德地图标记
 * - 历史查询 + CSV 导出（REST API）
 */
const { createApp, reactive, ref } = Vue;

createApp({
    setup() {
        // ------------------------------------------------------------------ 状态
        const config = reactive({ fieldOrder: [], fieldNames: {}, fieldUnits: {}, eventTypes: {}, fieldCategories: {}, charts: {} });
        const devices = ref([]);
        const currentImei = ref('');
        const eventFilter = ref('');
        const activeTab = ref('overview');
        const wsConnected = ref(false);
        const mqttStatus = ref('连接中...');
        const lastUpdate = ref('');
        const latestValues = reactive({ pressure: null, altitude: null });

        const rows = ref([]);           // 实时数据（新数据置顶）
        const maxRows = 500;
        let rowKeySeq = 0;

        // 历史查询
        const historyStart = ref('');
        const historyEnd = ref('');
        const historyEvent = ref('');
        const historyRows = ref([]);
        const historyTotal = ref(null);
        const historyQueried = ref(false);

        const tabs = [
            { key: 'overview', name: '数据总览' },
            { key: 'accel', name: '加速度' },
            { key: 'gyro', name: '角速度' },
            { key: 'attitude', name: '姿态' },
            { key: 'env', name: '环境' },
            { key: 'location', name: '位置' },
            { key: 'history', name: '历史查询' },
        ];

        // 图表定义：tab key -> [chartKey, elId, fields]
        const tabCharts = {
            accel: [['accel', 'chart-accel', ['accel_x', 'accel_y', 'accel_z']]],
            gyro: [['gyro', 'chart-gyro', ['gyro_x', 'gyro_y', 'gyro_z']]],
            attitude: [
                ['pitch', 'chart-pitch', ['attitude1']],
                ['roll', 'chart-roll', ['attitude2']],
            ],
            env: [['env', 'chart-env', ['pressure', 'altitude']]],
        };
        const initedCharts = new Set();

        let ws = null;
        let wsRetryTimer = null;

        // ------------------------------------------------------------------ 初始化
        async function init() {
            await loadConfig();
            await loadDevices();
            connectWs();
            pollStatus();
        }

        async function loadConfig() {
            const resp = await fetch('/api/config');
            Object.assign(config, await resp.json());
        }

        async function loadDevices() {
            const resp = await fetch('/api/devices');
            devices.value = await resp.json();
            // 当前设备已不在列表中则重置为全部
            if (currentImei.value && !devices.value.some(d => d.imei === currentImei.value)) {
                currentImei.value = '';
            }
        }

        async function pollStatus() {
            try {
                const resp = await fetch('/api/status');
                const s = await resp.json();
                mqttStatus.value = s.mqtt;
            } catch (e) { /* 后端不可达时静默 */ }
            setTimeout(pollStatus, 10000);
        }

        // ------------------------------------------------------------------ WebSocket
        function connectWs() {
            const proto = location.protocol === 'https:' ? 'wss' : 'ws';
            ws = new WebSocket(`${proto}://${location.host}/ws`);

            ws.onopen = () => {
                wsConnected.value = true;
                // 同步当前关注的设备
                ws.send(JSON.stringify({ imei: currentImei.value || null }));
            };
            ws.onmessage = (ev) => {
                const msg = JSON.parse(ev.data);
                if (msg.type === 'hello') {
                    mqttStatus.value = msg.mqtt;
                } else if (msg.type === 'data') {
                    handleIncoming(msg.imei, msg.items);
                }
            };
            ws.onclose = () => {
                wsConnected.value = false;
                clearTimeout(wsRetryTimer);
                wsRetryTimer = setTimeout(connectWs, 3000);
            };
            ws.onerror = () => ws.close();
        }

        function syncWatchImei() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ imei: currentImei.value || null }));
            }
        }

        // ------------------------------------------------------------------ 数据处理
        function handleIncoming(imei, items) {
            lastUpdate.value = new Date().toLocaleTimeString();

            // 设备列表懒更新：新设备出现时刷新下拉
            if (!devices.value.some(d => d.imei === imei)) {
                loadDevices();
            }

            if (currentImei.value && imei !== currentImei.value) return;

            // 新数据置顶
            const stamped = items.map(item => ({ ...item, _key: ++rowKeySeq }));
            rows.value.unshift(...stamped);
            if (rows.value.length > maxRows) {
                rows.value.length = maxRows;
            }

            // 曲线 + 地图 + 数值卡片（按时间顺序逐点推进）
            for (const item of items) {
                const ts = String(item.timestamp || '').slice(11, 19) || new Date().toLocaleTimeString();
                // 所有已初始化的图表都推数据，切回时不缺曲线
                for (const chartKey of initedCharts) {
                    ChartManager.push(chartKey, ts, item);
                }
                if (item.pressure !== undefined && item.pressure !== '') latestValues.pressure = item.pressure;
                if (item.altitude !== undefined && item.altitude !== '') latestValues.altitude = item.altitude;
                if (item.longitude && item.latitude && activeTab.value === 'location') {
                    MapView.updateLocation(parseFloat(item.latitude), parseFloat(item.longitude));
                }
            }
        }

        // ------------------------------------------------------------------ 事件处理
        function onDeviceChange() {
            rows.value = [];
            ChartManager.clearAll();
            MapView.reset();
            latestValues.pressure = null;
            latestValues.altitude = null;
            syncWatchImei();
            // 预取该设备最近数据，进入页面即有内容
            prefill();
        }

        async function prefill() {
            try {
                const params = new URLSearchParams({ limit: '200' });
                if (currentImei.value) params.set('imei', currentImei.value);
                const resp = await fetch(`/api/history?${params}`);
                const result = await resp.json();
                // 接口返回按时间倒序，反转为时间正序后回放
                const ordered = (result.rows || []).slice().reverse();
                if (ordered.length) {
                    rows.value = ordered.map(item => ({ ...item, _key: ++rowKeySeq })).reverse();
                    for (const item of ordered) {
                        const ts = String(item.timestamp || '').slice(11, 19);
                        for (const chartKey of initedCharts) {
                            ChartManager.push(chartKey, ts, item);
                        }
                        if (item.longitude && item.latitude) {
                            // 预取阶段只把最后位置画上，不逐点刷新地图
                            lastPrefillPosition = { lat: parseFloat(item.latitude), lon: parseFloat(item.longitude) };
                        }
                    }
                    if (lastPrefillPosition) {
                        MapView.updateLocation(lastPrefillPosition.lat, lastPrefillPosition.lon);
                    }
                }
            } catch (e) { /* 预取失败不影响实时功能 */ }
        }
        let lastPrefillPosition = null;

        function switchTab(key) {
            activeTab.value = key;
            // 图表/地图容器从 display:none 变可见后需要重算尺寸
            requestAnimationFrame(() => {
                if (tabCharts[key]) {
                    for (const [chartKey, elId, fields] of tabCharts[key]) {
                        if (!initedCharts.has(chartKey)) {
                            const def = config.charts[chartKey] || {};
                            ChartManager.init(chartKey, elId,
                                def.title || chartKey,
                                def.fields || fields,
                                config.fieldNames, config.fieldUnits);
                            initedCharts.add(chartKey);
                            // 用已有实时数据回填曲线
                            replayRows(chartKey);
                        }
                        ChartManager.resize(chartKey);
                    }
                }
                if (key === 'location') {
                    if (!MapView.init()) {
                        // AMap SDK 未就绪时稍后重试
                        setTimeout(() => { MapView.init(); MapView.resize(); }, 800);
                    } else {
                        MapView.resize();
                    }
                }
            });
        }

        /** 把当前内存中的历史行回填到刚初始化的图表 */
        function replayRows(chartKey) {
            const ordered = rows.value.slice().reverse();   // rows 为新数据置顶
            for (const item of ordered) {
                const ts = String(item.timestamp || '').slice(11, 19);
                ChartManager.push(chartKey, ts, item);
            }
        }

        // ------------------------------------------------------------------ 历史查询
        async function queryHistory() {
            const params = new URLSearchParams({ limit: '1000' });
            if (currentImei.value) params.set('imei', currentImei.value);
            if (historyStart.value) params.set('start', toDbTime(historyStart.value));
            if (historyEnd.value) params.set('end', toDbTime(historyEnd.value));
            if (historyEvent.value) params.set('event', historyEvent.value);

            const resp = await fetch(`/api/history?${params}`);
            const result = await resp.json();
            historyRows.value = result.rows || [];
            historyTotal.value = result.total;
            historyQueried.value = true;
        }

        function exportCsv() {
            const params = new URLSearchParams();
            if (currentImei.value) params.set('imei', currentImei.value);
            if (historyStart.value) params.set('start', toDbTime(historyStart.value));
            if (historyEnd.value) params.set('end', toDbTime(historyEnd.value));
            if (historyEvent.value) params.set('event', historyEvent.value);
            window.open(`/api/export.csv?${params}`, '_blank');
        }

        /** datetime-local 值 "2026-02-11T10:00" -> 数据库格式 "2026-02-11 10:00:00" */
        function toDbTime(v) {
            return v ? v.replace('T', ' ') + ':00' : '';
        }

        // ------------------------------------------------------------------ 展示辅助
        const filteredRows = Vue.computed(() => {
            if (!eventFilter.value) return rows.value;
            return rows.value.filter(r => r.event === eventFilter.value);
        });

        function formatCell(v) {
            if (v === null || v === undefined || v === '') return '-';
            if (typeof v === 'number') {
                // 保留合理精度，避免浮点长尾
                return Math.abs(v) >= 1000 ? v.toLocaleString('zh-CN')
                     : (Number.isInteger(v) ? v : parseFloat(v.toFixed(6)));
            }
            if (typeof v === 'string' && config.eventTypes[v]) return config.eventTypes[v];
            return v;
        }

        // ------------------------------------------------------------------ 挂载
        Vue.onMounted(init);

        return {
            config, devices, currentImei, eventFilter, activeTab, tabs,
            wsConnected, mqttStatus, lastUpdate, latestValues,
            rows: filteredRows, maxRows,
            historyStart, historyEnd, historyEvent, historyRows, historyTotal, historyQueried,
            onDeviceChange, switchTab, loadDevices, queryHistory, exportCsv, formatCell,
        };
    },
}).mount('#app');
