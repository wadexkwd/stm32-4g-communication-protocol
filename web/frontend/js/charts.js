/**
 * 应急跌落事件监控系统 - ECharts 图表封装
 * 对标 qt 方案的 QChart 曲线（加速度/角速度/俯仰角/翻滚角）
 * 维护滑动窗口：只保留最近 MAX_POINTS 个采样点，禁用动画保证性能
 */
const ChartManager = {
    MAX_POINTS: 120,

    charts: {},        // key -> echarts 实例
    buffers: {},       // key -> {times: [], series: {field: []}}

    /**
     * 初始化一个折线图
     * @param {string} key    图表标识（accel/gyro/pitch/roll/env）
     * @param {string} elId   容器元素 id
     * @param {string} title  图表标题
     * @param {Array}  fields 字段列表（每个字段一条曲线）
     * @param {Object} names  字段 -> 曲线名
     * @param {Object} units  字段 -> 单位
     */
    init(key, elId, title, fields, names, units) {
        const el = document.getElementById(elId);
        if (!el) return;
        const chart = echarts.init(el);
        const unitSet = [...new Set(fields.map(f => units[f] || ''))];

        chart.setOption({
            title: { text: title, left: 10, top: 8, textStyle: { fontSize: 14 } },
            tooltip: { trigger: 'axis' },
            legend: { top: 8, right: 10 },
            grid: { left: 60, right: 30, top: 48, bottom: 30 },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: [],
                axisLabel: { fontSize: 10 },
            },
            yAxis: unitSet.length === 1
                ? { type: 'value', name: unitSet[0] }
                // 多单位（如 气压kPa + 高度m）时使用双 Y 轴
                : unitSet.map(u => ({ type: 'value', name: u })),
            series: fields.map((f, i) => ({
                name: `${names[f] || f}${units[f] ? ' (' + units[f] + ')' : ''}`,
                type: 'line',
                showSymbol: false,
                animation: false,               // 禁用动画，提高性能（同 qt 方案）
                yAxisIndex: unitSet.length > 1 ? Math.min(i, unitSet.length - 1) : 0,
                data: [],
            })),
        });

        this.charts[key] = chart;
        this.buffers[key] = { times: [], series: Object.fromEntries(fields.map(f => [f, []])) };
    },

    /** 追加一个数据点（timestamp 为时间标签）。仅写缓冲区，不触发重绘 */
    push(key, timestamp, valuesByField) {
        const buf = this.buffers[key];
        if (!buf) return;
        buf.times.push(timestamp);
        for (const field in buf.series) {
            const v = valuesByField[field];
            buf.series[field].push(typeof v === 'number' ? v : parseFloat(v));
        }
        if (buf.times.length > this.MAX_POINTS) {
            buf.times.shift();
            for (const field in buf.series) buf.series[field].shift();
        }
    },

    /**
     * 把缓冲区渲染到图表（由调用方节流，例如每 500ms 一次；
     * 不传 key 则刷新全部图表）
     */
    flush(key) {
        if (key !== undefined) {
            this._render(key);
            return;
        }
        Object.keys(this.buffers).forEach(k => this._render(k));
    },

    /** 清空某图表（切换设备时调用） */
    clear(key) {
        const buf = this.buffers[key];
        if (!buf) return;
        buf.times.length = 0;
        for (const field in buf.series) buf.series[field].length = 0;
        this._render(key);
    },

    clearAll() {
        Object.keys(this.buffers).forEach(k => this.clear(k));
    },

    _render(key) {
        const chart = this.charts[key];
        const buf = this.buffers[key];
        if (!chart || !buf) return;
        const fields = Object.keys(buf.series);
        chart.setOption({
            xAxis: { data: buf.times },
            series: fields.map(f => ({ data: buf.series[f] })),
        });
    },

    /** 容器尺寸变化时调用（Tab 切换后） */
    resize(key) {
        if (key) {
            this.charts[key] && this.charts[key].resize();
        } else {
            Object.values(this.charts).forEach(c => c.resize());
        }
    },
};
