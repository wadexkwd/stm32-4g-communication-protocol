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
        const connected = ref(false);       // 是否已连接设备（默认不连接，手动点按钮才连）
        const eventFilter = ref('');
        const activeTab = ref('overview');
        const wsConnected = ref(false);
        const mqttStatus = ref('连接中...');
        const lastUpdate = ref('');
        const latestValues = reactive({ pressure: null, altitude: null });

        const rows = Vue.shallowRef([]);   // 实时数据（新数据置顶）。shallowRef 避免上万字段深层代理开销
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
        /** 统一API请求：会话过期(401)时跳转登录页 */
        async function apiFetch(url, opts) {
            const resp = await fetch(url, opts);
            if (resp.status === 401) {
                location.href = '/login';
                throw new Error('未登录');
            }
            return resp;
        }

        async function init() {
            await loadConfig();
            await loadDevices();
            connectWs();
            pollStatus();
        }

        async function loadConfig() {
            const resp = await apiFetch('/api/config');
            Object.assign(config, await resp.json());
        }

        async function loadDevices() {
            const resp = await apiFetch('/api/devices');
            devices.value = await resp.json();
            // 当前设备已不在列表中则重置为全部
            if (currentImei.value && !devices.value.some(d => d.imei === currentImei.value)) {
                currentImei.value = '';
            }
        }

        async function pollStatus() {
            try {
                const resp = await apiFetch('/api/status');
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
                // 同步当前连接状态（未连接则推送哨兵，让后端停止推送）
                syncWatchImei();
            };
            ws.onmessage = (ev) => {
                const msg = JSON.parse(ev.data);
                if (msg.type === 'hello') {
                    mqttStatus.value = msg.mqtt;
                } else if (msg.type === 'data') {
                    handleIncoming(msg.imei, msg.items);
                }
            };
            ws.onclose = (ev) => {
                wsConnected.value = false;
                // 1008 = 服务端鉴权拒绝（会话过期），跳转登录页
                if (ev.code === 1008) {
                    location.href = '/login';
                    return;
                }
                clearTimeout(wsRetryTimer);
                wsRetryTimer = setTimeout(connectWs, 3000);
            };
            ws.onerror = () => ws.close();
        }

        function syncWatchImei() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                // 未连接时用哨兵值让后端停止向本客户端推送
                ws.send(JSON.stringify({ imei: connected.value ? currentImei.value : '__paused__' }));
            }
        }

        // ------------------------------------------------------------------ 连接控制
        /** 连接设备：必须先在下拉框选中某个设备 */
        function connectDevice() {
            if (!currentImei.value || connected.value) return;
            connected.value = true;
            syncWatchImei();
            // 连接后预取该设备最近数据，立即有内容可看
            prefill();
        }

        /** 断开连接：停止接收数据，已显示的内容保留 */
        function disconnectDevice() {
            if (!connected.value) return;
            connected.value = false;
            pendingItems = [];
            syncWatchImei();
        }

        // ------------------------------------------------------------------ 数据处理
        // 攒批缓冲：WS 收到的数据先进缓冲，UI 每 UI_FLUSH_MS 毫秒统一刷新一次，
        // 避免逐条插入表格/逐点重绘图表造成高 CPU 占用
        let pendingItems = [];
        const UI_FLUSH_MS = 1000;

        function handleIncoming(imei, items) {
            // 未连接设备时不处理任何数据（后端持续入库不受影响）
            if (!connected.value) return;
            lastUpdate.value = new Date().toLocaleTimeString();

            // 设备列表懒更新：新设备出现时刷新下拉
            if (!devices.value.some(d => d.imei === imei)) {
                loadDevices();
            }

            if (currentImei.value && imei !== currentImei.value) return;
            pendingItems.push(...items);
        }

        /** 定时批量刷新表格/曲线/地图（每 UI_FLUSH_MS 一次） */
        function flushPending() {
            if (!pendingItems.length) return;
            const items = pendingItems;
            pendingItems = [];

            // 表格：新数据置顶（仅当"数据总览"页可见时才触发渲染，
            // 其他 Tab 下只写数组不重绘，切回时在 switchTab 里补触发）
            rows.value.unshift(...items.map(item => ({ ...item, _key: ++rowKeySeq })));
            if (rows.value.length > maxRows) {
                rows.value.length = maxRows;
            }
            if (activeTab.value === 'overview') {
                Vue.triggerRef(rows);
            }

            // 曲线：逐点写入缓冲，只重绘当前 Tab 可见的图表
            let lastItem = null;
            for (const item of items) {
                lastItem = item;
                const ts = String(item.timestamp || '').slice(11, 19) || new Date().toLocaleTimeString();
                for (const chartKey of initedCharts) {
                    ChartManager.push(chartKey, ts, item);
                }
            }
            for (const [chartKey] of (tabCharts[activeTab.value] || [])) {
                ChartManager.flush(chartKey);
            }

            // 数值卡片 + 地图（每周期只刷一次，用最新一条）
            if (lastItem) {
                if (lastItem.pressure !== undefined && lastItem.pressure !== '') latestValues.pressure = lastItem.pressure;
                if (lastItem.altitude !== undefined && lastItem.altitude !== '') latestValues.altitude = lastItem.altitude;
                if (lastItem.longitude && lastItem.latitude && activeTab.value === 'location') {
                    MapView.updateLocation(parseFloat(lastItem.latitude), parseFloat(lastItem.longitude));
                }
            }
        }

        // ------------------------------------------------------------------ 事件处理
        function onDeviceChange() {
            // 切换设备时自动断开，需重新点"连接设备"（连接必须是显式动作）
            if (connected.value) {
                disconnectDevice();
            }
            rows.value = [];
            pendingItems = [];
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
                const resp = await apiFetch(`/api/history?${params}`);
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
                    for (const [ck] of (tabCharts[activeTab.value] || [])) {
                        ChartManager.flush(ck);
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
                // 切回数据总览：补触发表格渲染（其他 Tab 期间数据只写数组没重绘）
                if (key === 'overview') {
                    Vue.triggerRef(rows);
                }
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
                        } else {
                            // 该图表在前台期间数据只进了缓冲，切回来立即补绘
                            ChartManager.flush(chartKey);
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
            ChartManager.flush(chartKey);
        }

        // ------------------------------------------------------------------ 历史查询
        async function queryHistory() {
            const params = new URLSearchParams({ limit: '1000' });
            if (currentImei.value) params.set('imei', currentImei.value);
            if (historyStart.value) params.set('start', toDbTime(historyStart.value));
            if (historyEnd.value) params.set('end', toDbTime(historyEnd.value));
            if (historyEvent.value) params.set('event', historyEvent.value);

            const resp = await apiFetch(`/api/history?${params}`);
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

        /** 跳转数据看板页 */
        function goDashboard() {
            location.href = '/dashboard.html';
        }

        // ------------------------------------------------------------------ 展示辅助
        // 表格只渲染最新 VISIBLE_ROWS 条（数据保留 maxRows 条），控制 DOM 规模
        const VISIBLE_ROWS = 50;
        const filteredRows = Vue.computed(() => {
            const list = eventFilter.value
                ? rows.value.filter(r => r.event === eventFilter.value)
                : rows.value;
            return list.slice(0, VISIBLE_ROWS);
        });

        function formatCell(v) {
            if (v === null || v === undefined || v === '') return '-';
            if (typeof v === 'number') {
                // 保留合理精度，避免浮点长尾（不用 toLocaleString，ICU 格式化开销大）
                return Number.isInteger(v) ? String(v) : String(parseFloat(v.toFixed(6)));
            }
            if (typeof v === 'string' && config.eventTypes[v]) return config.eventTypes[v];
            return v;
        }

        // ------------------------------------------------------------------ 挂载
        Vue.onMounted(() => {
            init();
            // UI 统一节流刷新
            setInterval(flushPending, UI_FLUSH_MS);
        });

        return {
            config, devices, currentImei, connected, eventFilter, activeTab, tabs,
            wsConnected, mqttStatus, lastUpdate, latestValues,
            filteredRows, maxRows,
            historyStart, historyEnd, historyEvent, historyRows, historyTotal, historyQueried,
            connectDevice, disconnectDevice,
            onDeviceChange, switchTab, loadDevices, queryHistory, exportCsv, formatCell, goDashboard,
        };
    },
}).mount('#app');
